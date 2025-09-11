from pathlib import Path
from flask import request, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest.fields import Upload
from marshmallow import Schema, fields
from loguru import logger
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
            try:
                session: SessionState = model.get_session(session_id)
                files = UploadFileSchema().load(request.files)
                uploaded_file = files.get("media")
                result = session.save_uploaded_image(uploaded_file)
                logger.info(f"successfully uploaded {uploaded_file.filename} ")
                return result
            except Exception as e:
                logger.exception(f" failed to upload {uploaded_file.filename} ")
                logger.exception(f"{e}")
            raise

        @custom_error_handler
        @bp.response(200)
        def get(self, session_id):
            return {"message": "Post the file to upload"}

    @bp.route("/<string:session_id>/face/<string:face_id>")
    class SessionDownloadFace(MethodView):
        @custom_error_handler
        @bp.response(201, UploadResponseSchema)
        def get(self, session_id, face_id):
            try:
                session: SessionState = model.get_session(session_id)
                path: Path = session.get_face_path(face_id)
                if not path.exists():
                    raise FileNotFoundError

                logger.info(f"successfully sent {face_id} ")
                return send_file(str(path), as_attachment=False)
            except Exception as e:
                logger.exception(f" failed to send {face_id} ")
                logger.exception(f"{e}")
                raise
