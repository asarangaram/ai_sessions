import uuid

import lancedb
import numpy as np
from lancedb.pydantic import LanceModel, Vector


class FaceRecognitionSchema(LanceModel):
    id: str  # Unique identifier for each entry
    vector: Vector(512)  # type: ignore # Face embeddings, fixed size of 512


class FaceVectorStore:
    def __init__(self, db, table_name: str):
        # Initialize the table
        if table_name not in db.table_names():
            tbl = db.create_table(
                table_name,
                schema=FaceRecognitionSchema,
                data=[
                    {"id": "rand_0", "vector": np.random.rand(512).astype(np.float32)}
                ],
            )

        else:
            tbl = db.open_table(table_name)
            schema_fields = [field.name for field in tbl.schema]
            if schema_fields != list(FaceRecognitionSchema.model_fields.keys()):
                raise RuntimeError(f"Table {table_name} has a different schema.")
        self.tbl = tbl

    def add(self, id: str, vector: Vector(512)):  # type: ignore
        self.tbl.add(data=[FaceRecognitionSchema(id=id, vector=vector)])

    def remove(self, id: str):
        self.tbl.delete(f"id = '{id}'")
        return True

    def search(self, id: str):
        result = self.tbl.search().where(f"id = '{id}'").limit(1).to_list()
        if result:
            return result[0]
        else:
            return None

    def vector_search(
        self,
        vector: Vector(512),  # type: ignore
        threshold: float = 0.85,
        metric_type: str = "cosine",
        count: int = 1,
    ) -> list[str, float]:
        threshold = 0.3
        faces_found = (
            self.tbl.search(vector, vector_column_name="vector")
            .metric(metric_type)
            .limit(count)
            .to_list()
        )
        result = []

        for face_found in faces_found:
            similarity_score = round(1 - face_found["_distance"], 2)
            if similarity_score >= threshold:
                identity = face_found["id"]
                result.append((identity, similarity_score))

        return result


if __name__ == "__main__":
    import logging
    import os
    import shutil
    import sys
    from pathlib import Path

    from ..proc.align_and_crop import align_and_crop
    from ..proc.face_detection import DetectionModel, EmbeddingModel

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logging.info("Quite test LanceDB model")
    # Database and table setup
    test_db_uri = "./artifacts/face_database_test.vec.db"
    table_name = "face"
    if os.path.isdir(test_db_uri):
        shutil.rmtree(test_db_uri)
    # Connect to the database
    db = lancedb.connect(uri=test_db_uri)

    vector_store = FaceVectorStore(db=db, table_name=table_name)
    schema_of_the_table = str(vector_store.tbl.schema)
    logging.info("Schema of the table")
    logging.info(vector_store.tbl.schema)
    logging.info("-" * 5)

    base_path = Path(
        "/home/anandas/demos/degirum_hailo_examples/assets/Friends_dataset"
    )

    faces = {
        str(f): str(uuid.uuid4())
        for f in [
            str(file)
            for file in base_path.rglob("*")
            if file.suffix.lower() in (".png", ".jpg", ".jpeg")
        ]
    }

    logging.warning("API: add ")
    count = 0
    for path, id in faces.items():
        detector = DetectionModel()
        detected_faces = detector.scan(path=path)

        num_faces = len(detected_faces.results)
        if num_faces > 1:
            logging.warning(
                f"Skipped {detected_faces.info} as it contains more than one face ({num_faces} faces detected)."
            )
        elif num_faces == 0:
            logging.warning(f"Skipped {detected_faces.info} as no faces were detected.")
        else:
            result = detected_faces.results[0]

            aligned_img, _ = align_and_crop(
                detected_faces.image,
                [landmark["landmark"] for landmark in result["landmarks"]],
            )
            embedding_model = EmbeddingModel()

            face_embedding = embedding_model.extract_face_embedding(aligned_img)

            vector_store.add(id=id, vector=face_embedding)
            if schema_of_the_table != str(vector_store.tbl.schema):
                logging.warning("Schama changed!!!")
                logging.warning(vector_store.tbl.schema)
                logging.warning("-" * 5)
        count = count + 1
    logging.info(f"Inserted {count} items")

    num_rows = len(vector_store.tbl)
    if num_rows == len(faces.keys()):
        logging.info(f"add(): vector table created with {num_rows} items")
    else:
        logging.error(
            f"not all items got inserted [given: {len(faces.keys())}, inserted: {num_rows}]."
        )

    logging.warning("API: search ")
    keys = list(faces.keys())[2:6]
    count = 0
    for key in keys:
        id = faces[key]
        result = vector_store.search(id=id)
        if result and result["id"] == id:
            count = count + 1

    if count != len(keys):
        logging.error("failed to retrive all items queried")
    else:
        logging.info("successfully retrived all items")

    result = vector_store.search(str(uuid.uuid4()))
    if result:
        logging.error("random id should not return a valid result")

    logging.warning("API: vector_search ")

    candidates = {
        "/home/anandas/demos/degirum_hailo_examples/assets/Friends.jpg": 6,
        "/home/anandas/demos/degirum_hailo_examples/assets/Friends1.jpg": 3,
    }

    for path, face_count in candidates.items():
        detector = DetectionModel()
        detected_faces = detector.scan(path=path)
        logging.info(f"found {len(detected_faces.results[0])} faces")
        if len(detected_faces.results) != face_count:
            logging.error(f"not all faces got detected in {path}")

        for result in detected_faces.results:
            result = detected_faces.results[0]

            aligned_img, _ = align_and_crop(
                detected_faces.image,
                [landmark["landmark"] for landmark in result["landmarks"]],
            )
            embedding_model = EmbeddingModel()
            face_embedding = embedding_model.extract_face_embedding(aligned_img)
            threshold = 0.5
            count = 1
            result = vector_store.vector_search(
                vector=face_embedding, threshold=threshold, count=count
            )
            if result:
                logging.info(
                    f'matches(threshold={threshold}, count={count}): {[f"id:{face[0]}, similarity score:{face[1]}" for face in result]} '
                )
            else:
                logging.error("Failed to detect known faces")

    logging.warning("API: remove ")
    count = 0
    for key in keys:
        id = faces[key]
        if vector_store.remove(id=id):
            result = vector_store.search(id=id)
            if result and result["id"] == id:
                logging.error("remove failed")

    num_rows = len(vector_store.tbl)
    if num_rows > len(faces.keys()) - len(keys):
        logging.error("not all items got removed.")
    elif num_rows < len(faces.keys()) - len(keys):
        logging.error("many items got removed than expected.")
    else:
        logging.info(f"successfully removed {len(keys)} items")

    sys.exit(1)

    if os.path.isdir(test_db_uri):
        shutil.rmtree(test_db_uri)
    logging.warning("== done == ")
