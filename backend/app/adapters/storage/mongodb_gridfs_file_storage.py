from datetime import datetime
import logging
from typing import Any
from bson import ObjectId

from gridfs import GridFS
from pymongo.database import Database

from app.domain.ports.file_storage import FileStorage


logger = logging.getLogger(__name__)


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
        logger.info("CV upload started: folder=%s filename=%s", folder, filename)

        extra_metadata: dict[str, Any] = {
            "filename": filename,
            "folder": folder,
            "content_type": content_type,
            "uploaded_at": datetime.utcnow(),
            **dict(metadata or {}),
        }

        file_id = self.fs.put(
            file_bytes,
            filename=filename,
            content_type=content_type,
            metadata=extra_metadata,
        )

        logger.info("CV saved in GridFS: filename=%s", filename)
        logger.info("GridFS file_id=%s", file_id)

        return str(file_id)

    def get(self, storage_key: str) -> bytes:
        logger.info("Fetching CV from GridFS: storage_key=%s", storage_key)
        grid_out = self.fs.get(ObjectId(storage_key))
        return grid_out.read()
