from pathlib import Path

from flask import send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest.fields import Upload
from loguru import logger
from marshmallow import Schema
from marshmallow import fields as ma_fields

from ..common.error_handler import custom_error_handler
from ..common.temp_file import TempFile
from .face_rec import FaceRecognizer


class FaceUploadSchema(Schema):
    face = Upload(required=True)
    vector = Upload(required=True)


class RegisteredFaceSchema(Schema):
    id = ma_fields.Str(dump_only=True)
    personId = ma_fields.Int(dump_only=True)
    personName = ma_fields.Str(dump_only=True)


class UpdatedPersonSchema(Schema):
    name = ma_fields.Str(load_default=None)
    keyFaceId = ma_fields.Int(load_default=None)
    isHidden = ma_fields.Bool(load_default=None)


def register_face_rec_resources(*, bp: Blueprint, store: FaceRecognizer):
    @bp.route("/register_face/of/<string:name>")
    class FaceRegisterPerson(MethodView):
        @custom_error_handler
        @bp.arguments(FaceUploadSchema, location="files")
        def post(self, args, name):
            person = store.register_face(
                name=name, face=args["face"], vector=args["vector"]
            )
            return person.model_dump()

    @bp.route("/search")
    class FaceSearchPerson(MethodView):
        @custom_error_handler
        @bp.arguments(FaceUploadSchema, location="files")
        def post(
            self,
            args,
        ):
            persons = store.search_face(vector=args["vector"], face=args["vector"])
            return [person.model_dump() for person in persons]

    @bp.route("/<string:face_id>/reassign_to/<string:name>")
    class FaceReassignNew(MethodView):
        @custom_error_handler
        def put(self, face_id, new_person_name):
            face = store.update_face(face_id=face_id, new_person_name=new_person_name)
            if not face:
                raise FileNotFoundError
            return face.model_dump()

    @bp.route("/face/<id>")
    class Face(MethodView):
        @custom_error_handler
        def get(self, id):
            logger.info(f"/face/{id}")
            face = store.get_face(id=id)
            logger.info(f"face path is {face}")
            if not face.exists():
                raise FileNotFoundError
            return send_file(str(face), as_attachment=False)

        def delete(self, face_id):
            if store.forget_face(face_id=face_id):
                return {"status": f"face with id {face_id} deleted"}
            raise FileNotFoundError  ## Recheck error

    @bp.route("/face/<id>/person")
    class FacePerson(MethodView):
        @custom_error_handler
        def get(self, id):
            person = store.get_person_by_face(id=id)
            return person.model_dump()

    @bp.route("/persons")
    class Persons(MethodView):
        @custom_error_handler
        def get(self):
            try:
                logger.info("Persons: query received")
                persons = store.get_all_persons()
                logger.info(f"Persons: {len(persons)} items found")
                logger.info(persons)
                if len(persons) > 0:
                    result = [person.model_dump() for person in persons]
                    logger.info(f"Persons: returning {result}")
                    return result
                else:
                    result = []
                    logger.warning("Persons: Returns Empty")
                    return result
            except Exception as e:
                logger.error(f"Exception. {e}")
                raise

    @bp.route("/person/<int:id>")
    class Person(MethodView):
        @custom_error_handler
        def get(self, id):
            try:
                logger.info(f"Person {id}: query received")
                person = store.get_person_by_id(id=id)
                if person:
                    result = person.model_dump()
                    logger.info(f"Person {id}: returning {result}")
                    return result
                else:
                    logger.warning(f"Person {id}: not found")
                    raise FileNotFoundError  ## Recheck error
            except Exception as e:
                logger.error(f"Exception. {e}")
                raise

        @bp.arguments(UpdatedPersonSchema, location="form")
        def put(self, args, id):
            person = store.update_person(**args)
            return person.model_dump()

        def delete(self, person_id):
            if store.forget_person(person_id=person_id):
                return {"status": f"face with id {person_id} deleted"}
            raise FileNotFoundError  ## Recheck error
