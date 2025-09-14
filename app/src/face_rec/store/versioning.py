from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, select, update, insert


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
        def get_version(cls) -> int:
            row = cls.query.get(0)
            return row.version if row else 0

        @classmethod
        def _increment_version(cls, mapper, connection, target):
            table = cls.__table__
            current = connection.execute(
                select(table.c.version).where(table.c.id == 0)
            ).scalar()

            if current is not None:
                connection.execute(
                    update(table).where(table.c.id == 0).values(version=current + 1)
                )
            else:
                connection.execute(insert(table).values(id=0, version=1))

        @classmethod
        def track_table(cls):
            """
            Call this to automatically track a table's inserts and updates.
            """
            for model in models:
                event.listen(model, "after_insert", cls._increment_version)
                event.listen(model, "after_update", cls._increment_version)

    return TableVersion
