from flask import  request
from flask.views import MethodView
import socketio
from .session_manager import ClientManager
from flask_smorest import abort

def register_sessions_resources(route, clientManager: ClientManager):
    @route.route("/<string:session_id>/upload")
    class SessionUpload(MethodView):
        @route.response(201)
        def post(self, session_id):
            uploaded_files = request.files.getlist("files")
            

            if not uploaded_files:
                abort(400, message={"message": "No file was uploaded."})

            session = clientManager.get_session(sid=session_id)
            
            if session:
                uploaded_file_details = session.upload_files(uploaded_files)
                total_files = session.get_file_count()
                return {
                    "message": "Files uploaded successfully",
                    "session_id": session_id,
                    "session_count": total_files,
                    "uploaded_files": uploaded_file_details,
                }
            else:
                return {
                    "message": "invalid session",
                }
                abort(400, message={"message": f"session {session_id} not found"})

    # This is only for debugging, session can't be disconnected with REST API
    @route.route("/<string:session_id>/disconnect")
    class SessionDisconnect(MethodView):
        @route.response(201)
        def delete(self, session_id):
            session = clientManager.get_session(sid=session_id)
            if session:
                socketio.emit("disconnect", room=session_id)
