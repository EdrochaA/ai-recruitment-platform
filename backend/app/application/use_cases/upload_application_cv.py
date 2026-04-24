from datetime import datetime
from app.domain.entities.application import Application
from app.domain.ports.application_repository import ApplicationRepository
from app.domain.ports.file_storage import FileStorage


class UploadApplicationCV:
    def __init__(
        self,
        application_repository: ApplicationRepository,
        file_storage: FileStorage,
    ):
        self.application_repository = application_repository
        self.file_storage = file_storage

    def execute(
        self,
        application_id: str,
        original_filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> Application:
        application = self.application_repository.find_by_id(application_id)

        if not application:
            raise ValueError("Application not found")

        storage_key = self.file_storage.save(
            file_bytes=file_bytes,
            folder=application_id,
            filename=original_filename,
        )

        application.cv_original_filename = original_filename
        application.cv_storage_key = storage_key
        application.cv_content_type = content_type
        application.cv_size_bytes = len(file_bytes)
        application.cv_uploaded_at = datetime.utcnow()

        return self.application_repository.update(application)