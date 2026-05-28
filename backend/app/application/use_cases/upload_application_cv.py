from datetime import datetime
import logging
from app.domain.entities.job_application import JobApplication
from app.domain.ports.job_application_repository import JobApplicationRepository
from app.domain.ports.file_storage import FileStorage


logger = logging.getLogger(__name__)


class UploadApplicationCV:
    def __init__(
        self,
        application_repository: JobApplicationRepository,
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
    ) -> JobApplication:
        logger.info(
            "CV upload start: application_id=%s original_filename=%s",
            application_id,
            original_filename,
        )
        job_application = self.application_repository.find_by_id(application_id)

        if not job_application:
            raise ValueError(f"JobApplication not found: {application_id}")

        storage_key = self.file_storage.save(
            file_bytes=file_bytes,
            folder=application_id,
            filename=original_filename,
        )
        size_bytes = len(file_bytes)
        logger.info(
            "CV upload saved: application_id=%s storage_key=%s size_bytes=%s",
            application_id,
            storage_key,
            size_bytes,
        )

        job_application.cv_original_filename = original_filename
        job_application.cv_storage_key = storage_key
        job_application.cv_content_type = content_type
        job_application.cv_size_bytes = size_bytes
        job_application.cv_uploaded_at = datetime.utcnow()

        return self.application_repository.update(job_application)