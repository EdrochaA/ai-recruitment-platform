from pathlib import Path
from uuid import uuid4
from app.domain.ports.file_storage import FileStorage


class LocalFileStorage(FileStorage):
    def __init__(self, base_path: str = "storage/cvs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        file_bytes: bytes,
        folder: str,
        filename: str,
    ) -> str:
        extension = Path(filename).suffix.lower()
        safe_filename = f"{uuid4()}{extension}"

        target_folder = self.base_path / folder
        target_folder.mkdir(parents=True, exist_ok=True)

        file_path = target_folder / safe_filename
        file_path.write_bytes(file_bytes)

        return str(file_path)