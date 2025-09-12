from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

"""
Raise alarm if the version goes beyond 2 * 10^9
int holds upto 2,147,483,647
"""


def store_version_db(db, dbModel, models):
    class TableVersion(dbModel):
        __tablename__ = "store_version"
        id = db.Column(db.Integer, primary_key=True, default=1)
        version = db.Column(db.Integer, nullable=False, default=0)

        @classmethod
        def get_version(cls, table_name: str) -> int:
            row = cls.query.get(table_name)
            return row.version if row else 0

        @classmethod
        def _increment_version(cls, mapper, connection, target):
            table_name = target.__tablename__
            # Use sessionmaker bound to connection
            session = db.session
            version_row = session.get(cls, table_name)
            if not version_row:
                version_row = cls(table_name=table_name, version=1)
                session.add(version_row)
            else:
                version_row.version += 1
            session.commit()

        @classmethod
        def track_table(cls):
            """
            Call this to automatically track a table's inserts and updates.
            """
            for model in models:
                event.listen(model, "after_insert", cls._increment_version)
                event.listen(model, "after_update", cls._increment_version)
