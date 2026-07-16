from typing import List

from app.domain.entities.job_application import JobApplication
from app.domain.ports.job_application_repository import JobApplicationRepository


class ListApplicationsByJobOffer:
    def __init__(self, repository: JobApplicationRepository):
        self.repository = repository

    def execute(self, job_offer_id: str) -> List[JobApplication]:
        return self.repository.find_by_job_offer(job_offer_id)