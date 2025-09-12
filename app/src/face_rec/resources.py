from flask import send_file
from flask.views import MethodView
from flask_smorest import Blueprint, abort, Schema
from flask_smorest.fields import Upload
from marshmallow import fields as ma_fields
from werkzeug.datastructures import FileStorage


from ..common.temp_file import TempFile
from face_rec import FaceRecognizer


class FaceUploadSchema(Schema):
    face = Upload(required=True)  # Name of the file field must be 'face'
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
    @bp.route("/face/register/person/new/<name>")
    class FaceRegisterPersonNew(MethodView):
        @bp.arguments(FaceUploadSchema, location="files")
        @bp.response(201, RegisteredFaceSchema)
        def post(self, args, name):
            face_file: TempFile = TempFile(args["face"])
            vector_file: TempFile = TempFile(args["vector"])

            face = store.register_face(
                identity=name, face=face_file.path, vector=vector_file.path
            )
            face_file.remove()
            vector_file.remove()
            return face.model_dump()

    @bp.route("/face/register/known/<int:id>")
    class FaceRegisterKnown(MethodView):
        @bp.arguments(FaceUploadSchema, location="files")
        @bp.response(201, RegisteredFaceSchema)
        def post(self, args, id):
            temp_file: TempFile = TempFile(args["face"])
            face = store.register_face(path=temp_file.path, identity=id)
            temp_file.remove()
            return face.model_dump()

    @bp.route("/face/reassign/<int:id>/new/<name>")
    class FaceReassignNew(MethodView):
        def put(self, face_id, new_person_name):
            face = store.update_face(face_id=face_id, new_person_name=new_person_name)
            if not face:
                raise FileNotFoundError
            return face.model_dump()

    @bp.route("/face/reassign/<int:id>/known/<known_id>")
    class FaceReassignKnown(MethodView):
        def put(self, face_id, new_person_id):
            face = store.update_face(face_id=face_id, new_person_id=new_person_id)
            if not face:
                raise FileNotFoundError
            return face.model_dump()

    @bp.route("/face/<id>")
    class Face(MethodView):
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
        @bp.response(200, RegisteredPersonSchema)
        def get(self, id):
            person = store.get_person_by_face(id=id)
            return person.model_dump()

    @bp.route("/persons")
    class Persons(MethodView):
        @bp.response(200, RegisteredPersonSchema(many=True))
        def get(self):
            persons = store.get_all_persons()
            return [person.model_dump() for person in persons]

    @bp.route("/person/<int:id>")
    class Person(MethodView):
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
