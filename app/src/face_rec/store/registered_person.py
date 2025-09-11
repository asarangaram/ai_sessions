from typing import List, Optional, Self

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, relationship


def person_db(db, dbModel):
    class RegisteredPersonInDB(dbModel):
        __tablename__ = "person"
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        key_face_id = db.Column(db.String(36), nullable=True)
        is_hidden = db.Column(db.Boolean, default=False, nullable=False)
        is_deleted = db.Column(db.Boolean, default=False, nullable=False)

        faces = relationship(
            "RegisteredFaceInDB", back_populates="person", cascade="all, delete-orphan"
        )

        def __init__(
            self,
            name: str,
            is_hidden: bool = False,
            key_face_id: Optional[str] = None,
            _allow_direct_init: bool = False,  # 👈 guard flag
        ):
            if not _allow_direct_init:
                raise TypeError("Use Person.create() to instantiate a Person object")
            self.name = name
            self.is_hidden = is_hidden
            self.key_face_id = key_face_id

        def __repr__(self):
            return (
                f"<Person(id={self.id}, name={self.name}, "
                f"is_hidden={self.is_hidden}, key_face_id={self.key_face_id})>"
            )

        # --- Helper to get session (works in both worlds) ---
        @classmethod
        def _session(cls) -> Session:
            # Flask-SQLAlchemy attaches `db.session`
            if hasattr(db, "session"):
                return db.session
            # plain SQLAlchemy: user must set one manually
            raise RuntimeError("No session available: provide a SQLAlchemy session")

        # --- Queries ---
        @classmethod
        def find_all(cls, include_deleted: bool = False) -> List[Self]:
            session = cls._session()
            query = session.query(cls)
            if not include_deleted:
                query = query.filter_by(is_deleted=False)
            return query.all()

        @classmethod
        def find_by_id(cls, id: int) -> Optional[Self]:
            session = cls._session()
            return session.get(cls, id)

        # --- Create ---
        @classmethod
        def create(
            cls,
            name: str,
            is_hidden: bool = False,
            key_face_id: Optional[str] = None,
        ) -> Self:
            session = cls._session()
            person = cls(
                _allow_direct_init=True,
                name=name,
                is_hidden=is_hidden,
                key_face_id=key_face_id,
            )
            try:
                session.add(person)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to create person: {str(e)}")
            return person

        # --- Update ---
        def update(
            self,
            name: Optional[str] = None,
            is_hidden: Optional[bool] = None,
            key_face_id: Optional[str] = None,
        ) -> Self:
            session = self._session()
            if name is not None:
                self.name = name
            if is_hidden is not None:
                self.is_hidden = is_hidden
            if key_face_id is not None:
                self.key_face_id = key_face_id
            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to update person: {str(e)}")
            return self

        # --- Soft delete ---
        def toBin(self):
            session = self._session()
            self.is_deleted = True
            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to soft delete person: {str(e)}")

        def restore(self):
            session = self._session()
            if not self.is_deleted:
                raise ValueError("Person is not deleted")
            self.is_deleted = False
            try:
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to restore person: {str(e)}")

        def delete(self):
            session = self._session()
            try:
                session.delete(self)
                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise ValueError(f"Failed to hard delete person: {str(e)}")

        def to_json(self):
            print(self.faces)
            return {
                "id": self.id,
                "name": self.name,
                "key_face_id": (
                    self.key_face_id if self.key_face_id else self.faces[0].id
                ),
                "is_hidden": self.is_hidden,
            }

    return RegisteredPersonInDB
