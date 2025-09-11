from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest.fields import Upload
from marshmallow import Schema, fields

from ..common import custom_error_handler
from .model import AISessionManager, SessionState


class UploadFileSchema(Schema):
    media = Upload(required=True)


class UploadResponseSchema(Schema):
    file_identifier = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    md5 = fields.Str(dump_only=True)


def register_sessions_resources(*, bp: Blueprint, model: AISessionManager):
    @bp.route("/<string:session_id>/upload")
    class SessionUpload(MethodView):
        @custom_error_handler
        @bp.response(201, UploadResponseSchema)
        def post(self, session_id):
            session: SessionState = model.get_session(session_id)
            files = UploadFileSchema().load(request.files)
            result = session.upload_file(files.get("media"))
            return result

        @custom_error_handler
        @bp.response(200)
        def get(self, session_id):
            return {"message": "Post the file to upload"}
