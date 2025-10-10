import os
import re
import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

import cv2
import numpy as np
from loguru import logger
from PIL import Image
from werkzeug.datastructures import FileStorage

from .face import (
    DetectedFace,
    Face,
    RecognizedPerson,
    RegisteredFace,
    RegisteredPerson,
)
from .proc import DetectionModel, EmbeddingModel, align_and_crop
from .store import FaceVectorStore, faces_db, person_db, store_version_db
from .store.face_vector_store import FaceIdWithConfidence


class FaceRecognizer:
    face_table_name = "face"
    face_vector_table = "face"
    person_table_name = "person"

    def __init__(
        self,
        *,
        db,
        dbModel,
        vectordb,
        face_dir: str,
        is_interactive: bool = False,
        detector: DetectionModel,
        embedding_model: EmbeddingModel,
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
        self.detector = detector
        self.embedding_model = embedding_model

    @classmethod
    def vector_tables(cls):
        return [cls.face_vector_table]

    @classmethod
    def tables(cls):
        return [cls.face_table_name, cls.person_table_name]

    def _save_file(
        self, id: int, img: Union[np.ndarray, Image.Image, FileStorage], ext="png"
    ) -> Path:

        if isinstance(img, Image.Image):
            logger.info(self.format_message(f"Received PIL Image"))
        elif isinstance(img, np.ndarray):
            logger.info(self.format_message(f"Received CV2 Image"))
        elif isinstance(img, FileStorage):
            logger.info(self.format_message("Received Uploaded File"))
        else:

            logger.info(
                self.format_message(
                    "img must be a PIL Image or NumPy array or a FileStorage"
                )
            )

            raise TypeError("img must be a PIL Image or NumPy array or a Path")

        folder = Path(self.face_dir)
        folder.mkdir(parents=True, exist_ok=True)

        logger.info(self.format_message(f"Faces are stored in {str(folder)}"))

        if isinstance(img, FileStorage):
            logger.info(self.format_message("uploaded file"))
            logger.info(
                self.format_message(f"Look for extension in file name {img.name}")
            )
            ext1 = img.name
            _, ext1 = os.path.splitext(img.filename)
            if ext1:
                ext = ext1
            else:
                logger.info(
                    self.format_message(f"No extension is provided with uploaded file!")
                )

        if ext.startswith("."):
            ext = ext[1:]

        logger.info(self.format_message(f"file extension will be {ext}"))

        file_name = f"{id:06d}_1.{ext}"
        file_path = folder / f"{file_name}"

        if not file_path.exists():
            logger.info(self.format_message(f"{file_name} is Not available"))
            counter = 2
            while True:
                file_name = f"{id:06d}_{counter}.{ext}"
                file_path = folder / f"{file_name}"
                if not file_path.exists():
                    break
                counter += 1
            logger.info(self.format_message(f"{file_name} is available"))
        else:
            logger.info(self.format_message(f"{file_name} is available"))

        logger.info(self.format_message(f"target file name is {str(file_path)}"))
        logger.info(self.format_message(f"Saving..."))
        if isinstance(img, Image.Image):
            img.save(file_path)
        elif isinstance(img, np.ndarray):
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            Image.fromarray(img_rgb).save(file_path)
        elif isinstance(img, FileStorage):
            img.save(file_path)
        else:
            logger.info(self.format_message("This should not have happened."))
            raise TypeError("img must be a PIL Image or NumPy array or a Path")

        logger.info(self.format_message("file saved successfully"))
        return file_name

    def remove_file(self, file_name: str):
        folder = Path(self.face_dir)
        file_path = folder / f"{file_name}"
        if file_path.exists():
            file_path.unlink()

    def normalize_text(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"\s+", " ", s)
        s = s.strip()
        return s

    def register_face(
        self,
        name: Optional[str],
        face: Union[np.ndarray, Image.Image, FileStorage],
        vector: Union[np.ndarray, FileStorage],
    ) -> RegisteredPerson:
        file_name = None
        try:
            if name:
                name = self.normalize_text(name)
                # Create or retrive person
                person = self.RegisteredPerson.find_by_name(name=name)

            if name and person:
                logger.info(self.format_message(f"person with name {name} found in db"))
            else:
                if name:
                    logger.info(
                        self.format_message(f"No person named {name} found. creating")
                    )
                else:
                    logger.info(self.format_message(f"An unnamed entity is created"))
                person = self.RegisteredPerson.create(name=name)
                if not person:
                    logger.info(
                        self.format_message(f"Failed to get person with name: {name}")
                    )
                    return None
                self.format_message(
                    f"successfully created a person with id {person.id}, name {person.name}"
                )

            if isinstance(vector, FileStorage):
                self.format_message(
                    f"vector file {vector.name} is being loaded into np array"
                )
                vector = np.load(vector)
            elif not isinstance(vector, np.ndarray):
                logger.info(
                    self.format_message(
                        f"vector must be a NumPy array or a FileStorage"
                    )
                )
                raise TypeError("vector must be a NumPy array or a path string")

            if len(vector) != 512:
                self.format_message(
                    f"expected 512 sized vector, found ${len(vector)} sized vectort"
                )
                raise TypeError(
                    f"vector must be a NumPy array of 512 elements, but vector size is {len(vector)}"
                )
            else:
                logger.info(self.format_message(f"valid 512 sized vector is provided"))

            logger.info(
                self.format_message(
                    f"Searching vector database for exact match. (> 0.99)"
                )
            )
            found: list[FaceIdWithConfidence] = self.faceVectorStore.vector_search(
                vector=vector
            )
            if found and len(found) > 0 and found[0].confidence > 0.99:
                face = self.RegisteredFace.get_face(id=found[0].id)
                self.format_message(
                    "found exact match  in vector db, registration not required"
                )
                person = face.person
                result = RegisteredPerson(
                    id=person.id,
                    name=person.name,
                    keyFaceId=(
                        person.key_face_id if person.key_face_id else person.faces[0].id
                    ),
                    isHidden=person.is_hidden,
                    faces=[face.id for face in person.faces],
                )
                logger.info(
                    self.format_message(f"returning {result.model_dump_json()}")
                )
                return result
            elif found and len(found) > 0:
                self.format_message(
                    f"found matching vectors with maximum confidence of {found[0].confidence}, but not exact match"
                )
            else:
                logger.info(self.format_message("no match found"))

            logger.info(self.format_message(f"proceeding to register"))
            file_name = self._save_file(id=person.id, img=face)
            logger.info(self.format_message(f"face is saved with name {file_name}"))
            face = self.RegisteredFace.create(person_id=person.id, path=file_name)
            if not face:
                raise Exception("Failed to register face")
            logger.info(self.format_message(f"Saving the vector into vector store"))
            self.faceVectorStore.add(id=face.id, vector=vector)
            logger.info(self.format_message(f"face is successfull registerred! {face}"))

            person = face.person
            result = RegisteredPerson(
                id=person.id,
                name=person.name,
                keyFaceId=(
                    person.key_face_id if person.key_face_id else person.faces[0].id
                ),
                isHidden=person.is_hidden,
                faces=[face.id for face in person.faces],
            )
            logger.info(self.format_message(f"returning {result.model_dump_json()}"))
            return result
        except Exception as e:
            logger.info(self.format_message("removing the stored file"))
            # Remove file here
            if file_name:
                self.remove_file(file_name=file_name)
            logger.info(self.format_message(f"Exception while registerring face {e}"))
            logger.error(self.format_message(f"Exception while registerring face {e}"))
            raise

    def search_face(
        self,
        *,
        face: Union[np.ndarray, Image.Image, FileStorage],
        vector: Union[np.ndarray, FileStorage],
        threshold: float = 0.3,
        count: int = 2,
    ) -> List[RecognizedPerson]:
        if isinstance(face, FileStorage):
            logger.info(self.format_message(f"search requested for {face}"))
        else:
            logger.info(self.format_message("search requested for for binary image"))
        try:
            if isinstance(vector, FileStorage):
                logger.info(
                    self.format_message(
                        f"vector file {vector.name} is being loaded into np array"
                    )
                )
                vector = np.load(vector)
            elif not isinstance(vector, np.ndarray):
                logger.info(
                    self.format_message(
                        f"vector must be a NumPy array or a FileStorage"
                    )
                )
                raise TypeError("vector must be a NumPy array or a path string")

            if len(vector) != 512:
                logger.info(
                    self.format_message(
                        f"expected 512 sized vector, found ${len(vector)} sized vectort"
                    )
                )
                raise TypeError(
                    f"vector must be a NumPy array of 512 elements, but vector size is {len(vector)}"
                )
            else:
                logger.info(self.format_message(f"valid 512 sized vector is provided"))

            logger.info(
                self.format_message(
                    f"Searching vector database for exact match. (> 0.99)"
                )
            )
            results: list[FaceIdWithConfidence] = self.faceVectorStore.vector_search(
                vector=vector, count=count, threshold=threshold
            )

            if results:
                logger.info(
                    self.format_message(
                        f"found {len(results)} faces matching for the preference (count={count}, threshold={threshold} )"
                    )
                )

                for result in results:
                    logger.info(result)

            persons = []
            if results and len(results) > 1:
                personMap = {}
                for result in results:
                    logger.info(f"process face.id={result.id} ")
                    id = result.id
                    registeredFace = self.RegisteredFace.get_face(id=id)

                    if registeredFace:
                        if not registeredFace.person.id in personMap.keys():
                            personMap[registeredFace.person.id] = result.confidence
                            persons.append(
                                RecognizedPerson(
                                    id=registeredFace.person.id,
                                    name=registeredFace.person.name,
                                    confidence=result.confidence,
                                )
                            )
                        else:
                            logger.info(
                                "ignoring duplicate entry for person id = {registeredFace.person.id}"
                            )
                    else:
                        logger.info(f"id={result.id} not registerred")
                print(personMap)
            else:
                # if not found, register without name, this will help to group unknown people
                logger.info("face not found, registerring")
                person = self.register_face(name=None, face=face, vector=vector)
                logger.info(f"registerred person {person.id}")

                persons.append(
                    RecognizedPerson(id=person.id, name=person.name, confidence=1.0)
                )

            logger.info(
                self.format_message(
                    f"persons: {' '.join([person.model_dump_json() for person in persons])}"
                )
            )

            return persons
        except Exception as e:
            logger.error(self.format_message(f"Exception while searching face {e}"))
            raise

    def detect_and_register_face(
        self, path: str, person_id: int = None, person_name: str = None
    ) -> Optional[RegisteredPerson]:
        """
        POST /register/face

        """
        logger.info(
            self.format_message(
                f'register_face: {f"id={person_id}" if person_id else f"name={person_name}"} -> {path}'
            )
        )

        detected_faces = self.detector.scan(path=path)

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

        face_embedding = self.embedding_model.extract_face_embedding(aligned_img)

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
    ) -> List[RegisteredPerson]:
        """
        Register multiple faces at once.
        - known_faces: map of existing person_id to list of face image files
        - new_faces: map of new person_name to list of face image files
        Returns: all registered faces
        """
        identities = [t[0] for t in faces]
        image_files = [t[1] for t in faces]

        detected_faces_batch = self.detector.batch_scan(path=image_files)

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
            face_embedding = self.embedding_model.extract_face_embedding(aligned_img)
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
        persons = []
        all = self.RegisteredPerson.find_all()

        for item in all:
            if len(item.faces) > 0:
                logger.info(self.format_message(f"adding {item.name} "))
                logger.info(self.format_message(f"{item.to_json()}"))
                persons.append(
                    RegisteredPerson(
                        id=item.id,
                        name=item.name,
                        keyFaceId=item.key_face_id,
                        isHidden=1 if item.is_hidden else 0,
                        faces=[face.id for face in item.faces],
                    )
                )
            else:
                logger.info(
                    self.format_message(
                        f"skipping {item.name} as no face is associated"
                    )
                )
                logger.info(self.format_message(f"{item.to_json()}"))
        return persons

    def get_person_by_id(self, id: int) -> Optional[RegisteredPerson]:
        """
        GET /person/{id}
        """
        item = self.RegisteredPerson.find_by_id(id=id)
        if item and not item.is_deleted:
            return RegisteredPerson(
                id=item.id,
                name=item.name,
                keyFaceId=item.key_face_id,
                isHidden=1 if item.is_hidden else 0,
                faces=[face.id for face in item.faces],
            )
        return None

    def get_person_by_name(self, name: str) -> Optional[RegisteredPerson]:
        """
        GET /person/{id}
        """
        item = self.RegisteredPerson.find_by_name(name=name)
        if item and item.is_deleted != True:
            return RegisteredPerson(
                id=item.id,
                name=item.name,
                keyFaceId=item.key_face_id,
                isHidden=1 if item.is_hidden else 0,
                faces=[face.id for face in item.faces],
            )
        return None

    def get_face(self, id: int) -> str:
        """
        GET /face/{id}
        - returns the image
        """
        face = self.RegisteredFace.get_face(id=id)
        logger.info(self.format_message(f"got face {face.to_json()}"))
        file_name = f"{face.path}"
        path = Path(self.face_dir) / file_name
        logger.info(self.format_message(f"file path is {path}"))
        return path

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

        detected_faces = self.detector.scan(path=path)

        aligned_faces = []
        for index, face in enumerate(detected_faces.results):
            x1, y1, x2, y2 = map(int, face["bbox"])
            # cropped_face = detected_faces.image[y1:y2, x1:x2]
            landmarks = [landmark["landmark"] for landmark in face["landmarks"]]
            aligned_face, _ = align_and_crop(detected_faces.image, landmarks)
            image_path, vector_path, identifier = on_get_face_identity(index)
            cv2.imwrite(str(image_path), aligned_face)

            vector = self.embedding_model.extract_face_embedding(aligned_face)
            np.save(vector_path, vector)

            aligned_faces.append(
                DetectedFace(
                    bbox=(x1, y1, x2, y2), landmarks=landmarks, image=identifier
                )
            )
            logger.info(
                self.format_message(f"face {index} is saved with identity {identifier}")
            )
        return aligned_faces, None

    def format_message(self, msg: str):
        msg = msg[0].upper() + msg[1:] if msg else msg
        return msg
