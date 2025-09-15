import os
import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

import cv2
import numpy as np
from loguru import logger
from PIL import Image
from werkzeug.datastructures import FileStorage

from .face import DetectedFace, Face, RegisteredFace, RegisteredPerson
from .proc import DetectionModel, EmbeddingModel, align_and_crop
from .store import FaceVectorStore, faces_db, person_db, store_version_db
from .store.face_vector_store import FaceIdWithConfidence


class FaceRecognizer:
    face_table_name = "face"
    face_vector_table = "face"
    person_table_name = "person"

    def __init__(
        self, db, dbModel, vectordb, face_dir: str, is_interactive: bool = False
    ):
        self.db = db  # to debug
        self.dbModel = dbModel  # to debug
        self.vectordb = vectordb  # to debug
        self.face_dir = face_dir
        self.is_interactive = is_interactive

        self.RegisteredFace = faces_db(db, dbModel)
        self.RegisteredPerson = person_db(db, dbModel)
        self.StoreVersion = store_version_db(
            db, dbModel, [self.RegisteredFace, self.RegisteredPerson]
        )

        self.faceVectorStore = FaceVectorStore(
            vectordb, table_name=self.face_vector_table
        )

    @classmethod
    def vector_tables(cls):
        return [cls.face_vector_table]

    @classmethod
    def tables(cls):
        return [cls.face_table_name, cls.person_table_name]

    def _save_file(
        self, name: str, img: Union[np.ndarray, Image.Image, FileStorage], ext="png"
    ) -> Path:
        folder = Path(self.face_dir)
        folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Faces are stored in {str(folder)}")

        if isinstance(img, FileStorage):
            logger.info(f"derive extension from file {img.name}")
            ext1 = img.name
            _, ext1 = os.path.splitext(img.filename)
            if ext1:
                ext = ext1
            else:
                logger.info(f"No extension is provided with uploaded file!")

        if ext.startswith("."):
            ext = ext[1:]

        logger.info(f"file extension will be {ext}")

        file_name = f"{name}_1.{ext}"
        file_path = folder / f"{file_name}"

        if not file_path.exists():
            logger.info(f"{file_name} is Not available")
            counter = 2
            while True:
                file_name = f"{name}_{counter}.{ext}"
                file_path = folder / f"{file_name}"
                if not file_path.exists():
                    break
                counter += 1
            logger.info(f"{file_name} is available")
        else:
            logger.info(f"{file_name} is available")

        logger.info(f"target file name is {str(file_path)}")
        if isinstance(img, Image.Image):
            logger.info(f"img is a PIL Image, saving...")
            img.save(file_path)
        elif isinstance(img, np.ndarray):
            logger.info(f"img is a CV2 Image, saving...")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            Image.fromarray(img_rgb).save(file_path)
        elif isinstance(img, FileStorage):
            logger.info("saving received file")
            img.save(file_path)
        else:
            logger.info("img must be a PIL Image or NumPy array or a FileStorage")
            raise TypeError("img must be a PIL Image or NumPy array or a Path")

        logger.info("file saved successfully")
        return file_name

    def register_face(
        self,
        name: str,
        face: Union[np.ndarray, Image.Image, FileStorage],
        vector: Union[np.ndarray, FileStorage],
    ) -> RegisteredFace:
        try:
            # Create or retrive person
            person = self.RegisteredPerson.find_by_name(name=name)

            if not person:
                logger.info(f"no person named {name} found. creating")
                person = self.RegisteredPerson.create(name)
                if not person:
                    logger.info(f"failed to get person with name: {name}")
                    return None
                logger.info(
                    f"successfully created a person with id {person.id}, name {person.name}"
                )
            else:
                logger.info(f"person with name {name} found in db")

            if isinstance(vector, FileStorage):
                logger.info(f"vector file {vector.name} is being loaded into np array")
                vector = np.load(vector)
            elif not isinstance(vector, np.ndarray):
                logger.info(f"vector must be a NumPy array or a FileStorage")
                raise TypeError("vector must be a NumPy array or a path string")

            if len(vector) != 512:
                logger.info(
                    f"expected 512 sized vector, found ${len(vector)} sized vectort"
                )
                raise TypeError(
                    f"vector must be a NumPy array of 512 elements, but vector size is {len(vector)}"
                )
            else:
                logger.info(f"valid 512 sized vector is provided")

            logger.info(f"Searching vector database for exact match. (> 0.99)")
            found: list[FaceIdWithConfidence] = self.faceVectorStore.vector_search(
                vector=vector
            )
            if found and len(found) > 0 and found[0].confidence > 0.99:
                face = self.RegisteredFace.get_face(id=found[0].id)
                logger.info(
                    "found exact match  in vector db, registration not required"
                )
                result = RegisteredFace(id=face.id, personName=face.person.name)
                logger.info(f"returning {result.model_dump_json()}")
                return result
            elif found and len(found) > 0:
                logger.info(
                    f"found matching vectors with maximum confidence of {found[0].confidence}, but not exact match"
                )
            else:
                logger.info("no match found")

            logger.info(f"proceeding to register")
            file_name = self._save_file(name=person.name, img=face)
            logger.info(f"face is saved with name {file_name}")
            face = self.RegisteredFace.create(person_id=person.id, path=file_name)
            if not face:
                logger.warning(f"failed to get save face for identity {person.id}")
                raise Exception("Failed to register face")
            logger.info(f"Saving the vector into vector store")
            self.faceVectorStore.add(id=face.id, vector=vector)
        except Exception as e:
            logger.info("removing the stored file")
            # REmove file here
            logger.info(f"Exception while registerring face {e}")
            logger.error(f"Exception while registerring face {e}")
            raise

        logger.info(f"face is successfull registerred! {face}")

        result = RegisteredFace(
            id=face.id, personName=face.person.name, personId=face.person.id
        )
        logger.info(f"returning {result.model_dump_json()}")
        return result

    def detect_and_register_face(
        self, path: str, person_id: int = None, person_name: str = None
    ) -> Optional[RegisteredFace]:
        """
        POST /register/face

        """
        logger.info(
            f'register_face: {f"id={person_id}" if person_id else f"name={person_name}"} -> {path}'
        )
        detector = DetectionModel()
        detected_faces = detector.scan(path=path)

        num_faces = len(detected_faces.results)
        if num_faces > 1:
            logger.warning(
                f"Skipped {detected_faces.info} as it contains more than one face ({num_faces} faces detected)."
            )
            return None
        elif num_faces == 0:
            logger.warning(f"Skipped {detected_faces.info} as no faces were detected.")
            return None

        result = detected_faces.results[0]

        aligned_img, _ = align_and_crop(
            detected_faces.image,
            [landmark["landmark"] for landmark in result["landmarks"]],
        )
        embedding_model = EmbeddingModel()
        face_embedding = embedding_model.extract_face_embedding(aligned_img)

        face = self.register_face(
            name=person_id if person_id else person_name,
            face=aligned_img,
            vector=face_embedding,
        )

        if self.is_interactive:
            self.show_face(face)

        return face

    def register_faces_no_batch(self, faces: List[Tuple[Union[int, str], str]]):
        registerd_faces = []
        for identity, path in faces:
            face = None
            if isinstance(identity, int):
                face = self.detect_and_register_face(path=path, person_id=identity)
            elif isinstance(identity, str):
                face = self.detect_and_register_face(path=path, person_name=identity)
            if face:
                registerd_faces.append(face)
        return registerd_faces

    def register_faces(
        self, faces: List[Tuple[Union[int, str], str]]
    ) -> List[RegisteredFace]:
        """
        Register multiple faces at once.
        - known_faces: map of existing person_id to list of face image files
        - new_faces: map of new person_name to list of face image files
        Returns: all registered faces
        """
        identities = [t[0] for t in faces]
        image_files = [t[1] for t in faces]

        detector = DetectionModel()
        detected_faces_batch = detector.batch_scan(path=image_files)

        embedding_model = EmbeddingModel()
        embedding = []
        saved_faces = []
        for identity, detected_faces in zip(identities, detected_faces_batch):
            num_faces = len(detected_faces.results)
            if num_faces > 1:
                logger.warning(
                    f"Skipped {detected_faces.info} as it contains more than one face ({num_faces} faces detected)."
                )
                continue
            elif num_faces == 0:
                logger.warning(
                    f"Skipped {detected_faces.info} as no faces were detected."
                )
                continue

            result = detected_faces.results[0]

            aligned_img, _ = align_and_crop(
                detected_faces.image,
                [landmark["landmark"] for landmark in result["landmarks"]],
            )
            face_embedding = embedding_model.extract_face_embedding(aligned_img)
            result = detected_faces.results[0]
            embedding.append((identity, aligned_img, face_embedding))
            face = self.register_face(
                name=identity,
                face=aligned_img,
                vector=face_embedding,
            )

            if face:
                saved_faces.append(face)

        return saved_faces

    def forget_face(self, face_id: str) -> bool:
        """
        DELETE /faces/{id}
        """
        face = self.RegisteredFace.get_face(id=id)

        face.delete()
        person = self.RegisteredPerson.get_person(face.person_id)
        if person.faces < 1:
            person.delete()
        return True

    def forget_person(self, person_id: int) -> bool:
        """
        DELETE /persons/{id}
        """
        person = self.RegisteredPerson.get_person(id=person_id)
        person.delete()
        return True

    def get_all_persons(self) -> List[RegisteredPerson]:
        """
        GET /persons
        """
        all = self.RegisteredPerson.get_persons()
        persons = []
        for item in all:
            persons.append(
                RegisteredPerson(id=item.id, name=item.name, keyFaceId=item.key_face_id)
            )
        return persons

    def get_person(self, id: int) -> RegisteredPerson:
        """
        GET /person/{id}
        """
        item = self.RegisteredPerson.get_person(id=id)
        return RegisteredPerson(id=item.id, name=item.name, keyFaceId=item.key_face_id)

    def get_face(self, id: int) -> str:
        """
        GET /face/{id}
        - returns the image
        """
        face = self.RegisteredFace.get_face(id=id)
        file_name = f"{face.person.name}_{face.person.id}"
        return Path.joinpath(self.face_dir, f"{file_name}.png")

    def get_person_by_face(self, id: int) -> RegisteredPerson:
        """
        GET /face/{id}/person
        - returns the image
        """
        face = self.RegisteredFace.get_face(id=id)
        item = face.person

        return RegisteredPerson(id=item.id, name=item.name, keyFaceId=item.key_face_id)

    def update_person(
        self,
        id: int,
        new_name: str = None,
        is_hidden: bool = None,
        key_face_id: int = None,
    ) -> RegisteredPerson:
        """
        PUT	/persons/{person_id}
        """
        current = self.RegisteredPerson.get_person(id=id)
        item = current.update(
            name=new_name, is_hidden=is_hidden, key_face_id=key_face_id
        )
        return RegisteredPerson(id=item.id, name=item.name, keyFaceId=item.key_face_id)

    def update_face(
        self, face_id: int, new_person_id: int = None, new_person_name: str = None
    ) -> RegisteredFace:
        """
        PUT /faces/{id}/reassign
        """
        if not new_person_id:
            if new_person_name:
                person = self.RegisteredPerson.create(name=new_person_name)
                new_person_id = person.id
            else:
                raise Exception("Name this")

        current = self.RegisteredFace.get_face(id=id)
        f = current.update(person_id=new_person_id)
        return RegisteredFace(id=f.id, personId=person.id, personName=person.name)

    def recognize_faces(
        self, path: str, on_get_face_identity: Callable[[int], Tuple[str, str, str]]
    ) -> List[Face]:
        aligned_faces, _ = self.detect_and_align_faces(
            path=path, on_get_face_identity=on_get_face_identity
        )
        faces_only = [entry.model_dump() for entry in aligned_faces]
        return faces_only

    def detect_and_align_faces(
        self, path: str, on_get_face_identity: Callable[[int], Tuple[str, str]]
    ) -> List[Tuple[np.array, list, DetectedFace]]:
        detector = DetectionModel()
        detected_faces = detector.scan(path=path)

        aligned_faces = []
        for index, face in enumerate(detected_faces.results):
            x1, y1, x2, y2 = map(int, face["bbox"])
            # cropped_face = detected_faces.image[y1:y2, x1:x2]
            landmarks = [landmark["landmark"] for landmark in face["landmarks"]]
            aligned_face, _ = align_and_crop(detected_faces.image, landmarks)
            image_path, vector_path, identifier = on_get_face_identity(index)
            cv2.imwrite(str(image_path), aligned_face)
            embedding_model = EmbeddingModel()
            vector = embedding_model.extract_face_embedding(aligned_face)
            np.save(vector_path, vector)

            aligned_faces.append(
                DetectedFace(
                    bbox=(x1, y1, x2, y2), landmarks=landmarks, image=identifier
                )
            )
            logger.info(f"face {index} is saved with identity {identifier}")
        return aligned_faces, None
