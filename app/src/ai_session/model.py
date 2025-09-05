import os
import shutil
import time
from werkzeug.utils import secure_filename
from pathlib import Path

from .config import ConfigClass
from .temp_file import TempFile


class SessionManager:
    def __init__(self, sid):
        self.sid = sid
        self.last_active = time.time()
        self.session_path = Path(ConfigClass.UPLOAD_STORAGE_LOCATION) / sid
        if not os.path.exists(self.session_path):
            os.makedirs(self.session_path)

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
        temp_file = TempFile(uploaded_file)
        metadata = temp_file.metadata()
        md5 = metadata.get("md5")
        _, ext = uploaded_file.filename.split(".", 1)
        unique_name = md5 + "." + ext

        file_path = self.session_path / unique_name

        result = {"file_identifier": unique_name, **metadata}

        if file_path.exists():
            result["status"] = "duplicate"
        else:
            shutil.move(temp_file.path, file_path)
            result["status"] = "success"
        if temp_file:
            temp_file.remove()
        return result


class AISessionManager:
    NO_ACTIVITY_TIMEOUT = 60 * 60  # seconds

    def __init__(self):
        # {sid: last_activity_timestamp}
        self._clients = {}

    def create_session(self, sid: int):
        session = SessionManager(sid)
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

    def get_session(self, sid: int) -> SessionManager:
        session = self._clients.get(sid, None)
        if session:
            return session
        else:
            raise Exception(f"Session {sid} doesn't exists, reconnect")