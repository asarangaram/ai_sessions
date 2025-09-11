import os
import shutil
import threading
import time
from pathlib import Path
from loguru import logger

import eventlet
from flask_socketio import emit
from PIL import Image
from werkzeug.utils import secure_filename

from ..common import ConfigClass, TempFile
from ..face_rec import FaceRecognizer, load


class SessionState:
    def __init__(self, sid):
        self.sid = sid
        self.last_active = time.time()
        self.session_path = Path(ConfigClass.UPLOAD_STORAGE_LOCATION) / "sessions" / sid
        if not os.path.exists(self.session_path):
            os.makedirs(self.session_path)

    @property
    def uploaded_img_path(self):
        path = self.session_path / "uploaded"
        if not path.exists():
            path.mkdir(exist_ok=True)
        return path

    def update(self):
        self.last_active = time.time()

    def is_expired(self, timeout_seconds):
        now = time.time()
        return now - self.last_active > timeout_seconds

    def wipeout(self):
        if os.path.exists(self.session_path):
            shutil.rmtree(self.session_path)

    def get_file_count(self) -> int:
        return len(
            [
                name
                for name in os.listdir(self.session_path)
                if os.path.isfile(os.path.join(self.session_path, name))
            ]
        )

    def upload_file(self, uploaded_file):
        try:
            temp_file = TempFile(uploaded_file)
            metadata = temp_file.metadata()
            md5 = metadata.get("md5")
            _, ext = uploaded_file.filename.split(".", 1)
            unique_name = md5 + "." + ext
            file_path = self.uploaded_img_path / unique_name
            result = {"file_identifier": unique_name, **metadata}
            if file_path.exists():
                result["status"] = "duplicate"
            else:
                shutil.move(temp_file.path, file_path)
                result["status"] = "success"
            if temp_file:
                temp_file.remove()
            logger.info(f"successfully uploaded {uploaded_file.filename} ")
            return result
        except Exception as e:
            logger.exception(f" failed to upload {uploaded_file.filename} ")
            raise

    def get_image_dimensions(self, image_path):
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            return None

    def recognize(self, recogniser: FaceRecognizer, identifier: str):
        self.emit_progress(f"Acquired hardware")
        file_path = self.uploaded_img_path / identifier

        if not os.path.exists(file_path):
            return False, f"file {identifier} doesn't exists"
        size = self.get_image_dimensions(file_path)

        result = recogniser.recognize_faces(str(file_path))

        self.emit_progress(f"faces detected")

        return {"faces": result, "dimension": size}, None

    def emit_progress(self, msg: str):
        emit("progress", msg, to=self.sid)

    def emit_result(self, result: str):
        emit("result", result, to=self.sid)


class AISessionManager:
    NO_ACTIVITY_TIMEOUT = 60 * 60  # seconds

    def __init__(self):
        self.recogniser = load(ConfigClass.UPLOAD_STORAGE_LOCATION, preserve_past=True)
        self.is_hw_in_use = False
        self.resource_lock = threading.Lock()
        self._clients = {}

    def create_session(self, sid: int):
        session = SessionState(sid)
        self._clients[sid] = session
        return session

    def update_activity(self, sid):
        session = self._clients.get(sid, None)
        if session:
            session.update()
        else:
            raise Exception(f"Session {sid} doesn't exists, reconnect")

    def remove_client(self, sid):
        session = self._clients.get(sid, None)
        if session:
            session.wipeout()
            self._clients.pop(sid, None)

    def get_idle_clients(self, timeout_seconds=NO_ACTIVITY_TIMEOUT):
        return [
            sid
            for sid, session in self._clients.items()
            if session.is_expired(timeout_seconds)
        ]

    def get_session(self, sid: int) -> SessionState:
        session = self._clients.get(sid, None)
        if session:
            return session
        else:
            raise Exception(f"Session {sid} doesn't exists, reconnect")

    def recognize(self, sid, identifier) -> bool:
        session: SessionState = self._clients.get(sid, None)
        if not session:
            raise Exception(f"Session {sid} doesn't exists, reconnect")
        session.emit_progress(f"Received Face Recognition request for {identifier}")
        with self.resource_lock:
            if self.is_hw_in_use:
                session.emit_result(
                    {
                        "identifier": identifier,
                        "status": "failed",
                        "error": f"Resource is busy",
                    }
                )
                return False
            self.is_hw_in_use = True

        result, error = session.recognize(self.recogniser, identifier)
        with self.resource_lock:
            self.is_hw_in_use = False
        if result:
            session.emit_result(
                {"identifier": identifier, "status": "success", **result}
            )
            return True
        else:
            session.emit_result(
                {"identifier": identifier, "status": "failed", "error": error}
            )
            return False
