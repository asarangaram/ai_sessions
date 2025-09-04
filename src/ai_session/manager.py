import os
import shutil
import time
from werkzeug.utils import secure_filename

from ....web_socket.main.config import ConfigClass  # noqa: E402


class SessionManager:
    def __init__(self, sid):
        self.sid = sid
        self.last_active = time.time()
        self.session_folder_path = os.path.join(
            ConfigClass.SESSION_STORAGE_LOCATION, sid
        )
        if not os.path.exists(self.session_folder_path):
            os.makedirs(self.session_folder_path)

    def update(self):
        self.last_active = time.time()

    def is_expired(self, timeout_seconds):
        now = time.time()
        return now - self.last_active > timeout_seconds

    def wipeout(self):
        if os.path.exists(self.session_folder_path):
            shutil.rmtree(self.session_folder_path)

    def get_file_count(self) -> int:
        return len(
            [
                name
                for name in os.listdir(self.session_folder_path)
                if os.path.isfile(os.path.join(self.session_folder_path, name))
            ]
        )

    def upload_files(self, files):
        uploaded_file_details = []
        for uploaded_file in files:
            original_filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(self.session_folder_path, original_filename)

            # Check if the file already exists
            if os.path.exists(file_path):
                uploaded_file_details.append(
                    {
                        "filename": original_filename,
                        "status": "not uploaded",
                        "error": "File already exists. Not overwritten.",
                    }
                )
            else:
                # Save the file
                uploaded_file.save(file_path)
                uploaded_file_details.append(
                    {
                        "filename": original_filename,
                        "status": "uploaded successfully",
                    }
                )
        return uploaded_file_details


class ClientManager:
    NO_ACTIVITY_TIMEOUT = 60 * 60  # seconds

    def __init__(self):
        # {sid: last_activity_timestamp}
        self._clients = {}

    def create_session(self, sid: int):
        self._clients[sid] = SessionManager(sid)

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
        return session