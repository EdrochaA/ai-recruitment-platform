from abc import ABC, abstractmethod


class FileStorage(ABC):
    @abstractmethod
    def save(
        self,
        file_bytes: bytes,
        folder: str,
        filename: str,
        content_type: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Returns storage key/path"""
        pass

    @abstractmethod
    def get(self, storage_key: str) -> bytes:
        """Returns file bytes by storage key/path"""
        pass