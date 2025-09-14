from pathlib import Path

from flask import send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest.fields import Upload
from marshmallow import Schema
from marshmallow import fields as ma_fields

from ..common.error_handler import custom_error_handler
from ..common.temp_file import TempFile
from .face_rec import FaceRecognizer


class FaceUploadSchema(Schema):
    face = Upload(required=True)
    vector = Upload(required=True)


class RegisteredPersonSchema(Schema):
    id = ma_fields.Int(dump_only=True)
    name = ma_fields.Str(dump_only=True)
    keyFaceId = ma_fields.Int(dump_only=True)


class RegisteredFaceSchema(Schema):
    id = ma_fields.Str(dump_only=True)
    personId = ma_fields.Int(dump_only=True)
    personName = ma_fields.Str(dump_only=True)


class UpdatedPersonSchema(Schema):
    name = ma_fields.Str(load_default=None)
    keyFaceId = ma_fields.Int(load_default=None)
    isHidden = ma_fields.Bool(load_default=None)


def register_face_rec_resources(*, bp: Blueprint, store: FaceRecognizer):
    @bp.route("/detect")
    class Recognize(MethodView):
        @custom_error_handler
        def post(self, session_id):
            raise Exception("Not implemented Yet")

        @custom_error_handler
        @bp.response(200)
        def get(self, session_id):
            return {"message": "Post the file to upload"}

    @bp.route("/face/register/person/new/<name>")
    class FaceRegisterPerson(MethodView):
        @custom_error_handler
        @bp.arguments(FaceUploadSchema, location="files")
        @bp.response(201, RegisteredFaceSchema)
        def post(self, args, name):
            face = store.register_face(
                name=name, face=args["face"], vector=args["vector"]
            )
            return face.model_dump()

    @bp.route("/face/reassign/<int:id>/new/<name>")
    class FaceReassignNew(MethodView):
        @custom_error_handler
        def put(self, face_id, new_person_name):
            face = store.update_face(face_id=face_id, new_person_name=new_person_name)
            if not face:
                raise FileNotFoundError
            return face.model_dump()

    @bp.route("/face/reassign/<int:id>/known/<known_id>")
    class FaceReassignKnown(MethodView):
        @custom_error_handler
        def put(self, face_id, new_person_id):
            face = store.update_face(face_id=face_id, new_person_id=new_person_id)
            if not face:
                raise FileNotFoundError
            return face.model_dump()

    @bp.route("/face/<id>")
    class Face(MethodView):
        @custom_error_handler
        @bp.response(200, RegisteredFaceSchema)
        def get(self, id):
            face = store.get_face(id=id)
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
        @bp.response(200, RegisteredPersonSchema)
        def get(self, id):
            person = store.get_person_by_face(id=id)
            return person.model_dump()

    @bp.route("/persons")
    class Persons(MethodView):
        @custom_error_handler
        @bp.response(200, RegisteredPersonSchema(many=True))
        def get(self):
            persons = store.get_all_persons()
            return [person.model_dump() for person in persons]

    @bp.route("/person/<int:id>")
    class Person(MethodView):
        @custom_error_handler
        @bp.response(200, RegisteredPersonSchema)
        def get(self, id):
            person = store.get_person(id=id)
            return person.model_dump()

        @bp.arguments(UpdatedPersonSchema, location="form")
        @bp.response(200, RegisteredPersonSchema)
        def put(self, args, id):
            person = store.update_person(**args)
            return person.model_dump()

        def delete(self, person_id):
            if store.forget_person(person_id=person_id):
                return {"status": f"face with id {person_id} deleted"}
            raise FileNotFoundError  ## Recheck error
