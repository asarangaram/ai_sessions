import hashlib
import os
import tempfile
from typing import Any


class TempFile:
    """
    A utility class for managing temporary files.
    Ensures unique filenames and provides cleanup functionality.
    """

    def __init__(self, file: Any) -> None:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)

        # Avoid overwriting by adding a number if file exists
        base, ext = os.path.splitext(temp_path)
        counter = 1
        while os.path.exists(temp_path):
            temp_path = f"{base}_{counter}{ext}"
            counter += 1
        file.save(temp_path)
        self.path = temp_path

    def metadata(self):
        # TODO: use clmedia, currently has version conflict for numpy
        hash_md5 = hashlib.md5()
        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
            md5 = hash_md5.hexdigest()
        metadata = {"md5": md5}
        return metadata

    def remove(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
