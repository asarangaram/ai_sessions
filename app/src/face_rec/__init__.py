import os
from pathlib import Path
from types import SimpleNamespace

from flask import Flask
from flask_socketio import SocketIO
from flask_smorest import Blueprint
import lancedb
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

from .resources import register_face_rec_resources

from .face_rec import FaceRecognizer


def create_db(path, preserve_past: bool = True):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    engine = sa.create_engine(f"sqlite:///{path}", echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    db = SimpleNamespace(
        session=session,
        engine=engine,
        Column=sa.Column,
        Integer=sa.Integer,
        String=sa.String,
        Boolean=sa.Boolean,
        ForeignKey=sa.ForeignKey,
    )
    if not preserve_past:
        metadata = sa.MetaData()
        inspector = sa.inspect(engine)
        for table_name in FaceRecognizer.tables():
            if table_name in inspector.get_table_names():
                table = sa.Table(table_name, metadata, autoload_with=engine)
                table.drop(engine)
    return db


def create_vector_db(path, preserve_past: bool = True):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    db = lancedb.connect(path)
    if not preserve_past:
        for table_name in FaceRecognizer.vector_tables():
            if table_name in db.table_names():
                tbl = db.open_table(table_name)
                tbl.delete("true")
    return db


def setup_face_dir(face_dir: str, preserve_past: bool = True):
    os.makedirs(face_dir, exist_ok=True)
    if not preserve_past:
        for filename in os.listdir(face_dir):
            file_path = os.path.join(face_dir, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # remove file or symlink
    return face_dir


def load(store_dir, preserve_past: bool = True):
    db = create_db(f"{store_dir}/store.db", preserve_past=preserve_past)
    vectordb = create_vector_db(f"{store_dir}/vector.db", preserve_past=preserve_past)
    Base = declarative_base()
    face_dir = setup_face_dir(
        face_dir=f"{store_dir}/images", preserve_past=preserve_past
    )

    recogniser = FaceRecognizer(
        db=db,
        dbModel=Base,
        vectordb=vectordb,
        face_dir=face_dir,
        is_interactive=False,
    )
    Base.metadata.create_all(db.engine)
    recogniser.StoreVersion.track_table()
    return recogniser
