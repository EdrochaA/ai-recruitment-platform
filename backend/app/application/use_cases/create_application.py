from datetime import datetime
from uuid import uuid4
from app.domain.entities.job_application import JobApplication
from app.domain.ports.job_application_repository import JobApplicationRepository


class CreateApplication:
    def __init__(self, repository: JobApplicationRepository):
        self.repository = repository

    def execute(
        self,
        job_offer_id: str,
        candidate_name: str,
        candidate_email: str,
    ) -> JobApplication:
        job_application = JobApplication(
            id=str(uuid4()),
            job_offer_id=job_offer_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            created_at=datetime.utcnow(),
        )
        return self.repository.save(job_application)