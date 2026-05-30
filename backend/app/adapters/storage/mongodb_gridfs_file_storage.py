from datetime import datetime
from typing import Any

from gridfs import GridFS
from pymongo.database import Database

from app.domain.ports.file_storage import FileStorage


class MongoGridFSFileStorage(FileStorage):
    def __init__(self, db: Database):
        self.fs = GridFS(db)

    def save(
        self,
        file_bytes: bytes,
        folder: str,
        filename: str,
        content_type: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        extra_metadata: dict[str, Any] = dict(metadata or {})
        extra_metadata.setdefault("application_id", folder)
        extra_metadata.setdefault("original_filename", filename)
        if content_type:
            extra_metadata.setdefault("content_type", content_type)
        extra_metadata.setdefault("uploaded_at", datetime.utcnow())
        extra_metadata.setdefault("size_bytes", len(file_bytes))

        file_id = self.fs.put(
            file_bytes,
            filename=filename,
            content_type=content_type,
            metadata=extra_metadata,
        )
        return str(file_id)
