from typing import List

from app.domain.entities.job_offer import JobOffer
from app.domain.ports.job_offer_repository import JobOfferRepository


class ListJobOffers:
    def __init__(self, repository: JobOfferRepository):
        self.repository = repository

    def execute(self) -> List[JobOffer]:
        return self.repository.list_all()