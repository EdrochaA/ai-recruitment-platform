from abc import ABC, abstractmethod


class FileStorage(ABC):
    @abstractmethod
    def save(
        self,
        file_bytes: bytes,
        folder: str,
        filename: str,
    ) -> str:
        """Returns storage key/path"""
        pass