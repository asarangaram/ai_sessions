from typing import Optional, Self
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
import uuid


def faces_db(db, dbModel):
    class RegisteredFaceInDB(dbModel):
        __tablename__ = "faces"

        id = db.Column(
            db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
        )
        path = db.Column(db.String, nullable=False)
        person_id = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)

        # Relationship back to Person
        person = relationship("RegisteredPersonInDB", back_populates="faces")

        def __init__(self, person_id: int, path: str, _allow_direct_init: bool = False):
            if not _allow_direct_init:
                raise TypeError("Use Face.create() to instantiate a Face object")
            self.person_id = person_id
            self.path = path

        def __repr__(self):
            return f"<Face(id={self.id}, person_id={self.person_id})>"

        # --- session helper ---
        @classmethod
        def _session(cls):
            if hasattr(db, "session"):
                return db.session
            raise RuntimeError("No session available: provide a SQLAlchemy session")

        # --- Get by ID ---
        @classmethod
        def get_face(cls, id: str) -> Optional[Self]:
            session = cls._session()
            return session.get(cls, id)

        # --- Create ---
        @classmethod
        def create(cls, person_id: int, path: str) -> Self:
            session = cls._session()
            face = cls(person_id=person_id, path=path, _allow_direct_init=True)
            try:
                session.add(face)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to create face: {str(e)}")
            return face

        # --- Update ---
        def update(
            self,
            person_id: int,
        ) -> Self:
            session = self._session()
            if person_id is not None:
                self.person_id = person_id
            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to update person: {str(e)}")
            return self

        # --- Delete ---
        def delete(self):
            session = self._session()
            try:
                session.delete(self)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to delete face: {str(e)}")
        
        def to_json(self):
            return {
                "person_id": self.person_id,
                "path": self.path,
                "person": self.person.to_json()
            }
             

    return RegisteredFaceInDB
