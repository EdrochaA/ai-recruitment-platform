from datetime import datetime
from uuid import uuid4

from app.domain.entities.application import Application
from app.domain.ports.application_repository import ApplicationRepository


class CreateApplication:
    def __init__(self, repository: ApplicationRepository):
        self.repository = repository

    def execute(
        self,
        job_offer_id: str,
        candidate_name: str,
        candidate_email: str,
        cv_text: str,
    ) -> Application:
        application = Application(
            id=str(uuid4()),
            job_offer_id=job_offer_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            cv_text=cv_text,
            created_at=datetime.utcnow(),
        )
        return self.repository.save(application)