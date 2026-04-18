from typing import List

from app.domain.entities.application import Application
from app.domain.ports.application_repository import ApplicationRepository


class ListApplicationsByJobOffer:
    def __init__(self, repository: ApplicationRepository):
        self.repository = repository

    def execute(self, job_offer_id: str) -> List[Application]:
        return self.repository.find_by_job_offer(job_offer_id)