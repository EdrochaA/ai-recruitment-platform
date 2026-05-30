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
            "CV upload started: application_id=%s original_filename=%s",
            application_id,
            original_filename,
        )
        application = self.application_repository.find_by_id(application_id)

        if not application:
            raise ValueError(f"JobApplication not found: {application_id}")

        uploaded_at = datetime.utcnow()
        size_bytes = len(file_bytes)
        storage_key = self.file_storage.save(
            file_bytes=file_bytes,
            folder=application.id,
            filename=original_filename,
            content_type=content_type,
            metadata={
                "application_id": application.id,
                "candidate_email": application.candidate_email,
                "size_bytes": size_bytes,
            },
        )
        logger.info(
            "CV saved in GridFS: application_id=%s storage_key=%s",
            application_id,
            storage_key,
        )
        logger.info("GridFS file_id=%s", storage_key)

        application.cv_original_filename = original_filename
        application.cv_storage_key = storage_key
        application.cv_content_type = content_type
        application.cv_size_bytes = size_bytes
        application.cv_uploaded_at = uploaded_at

        updated_application = self.application_repository.update(application)
        logger.info("Application updated: application_id=%s", application_id)
        return updated_application