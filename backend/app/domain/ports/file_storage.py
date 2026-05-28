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