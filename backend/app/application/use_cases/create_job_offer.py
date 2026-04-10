from datetime import datetime
from uuid import uuid4

from app.domain.entities.job_offer import JobOffer
from app.domain.ports.job_offer_repository import JobOfferRepository


class CreateJobOffer:
    def __init__(self, repository: JobOfferRepository):
        self.repository = repository

    def execute(self, title: str, description: str, location: str) -> JobOffer:
        job_offer = JobOffer(
            id=str(uuid4()),
            title=title,
            description=description,
            location=location,
            status="open",
            created_at=datetime.utcnow(),
        )
        return self.repository.save(job_offer)