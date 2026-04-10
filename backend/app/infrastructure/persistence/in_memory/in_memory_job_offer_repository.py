from typing import List

from app.domain.entities.job_offer import JobOffer
from app.domain.ports.job_offer_repository import JobOfferRepository


class InMemoryJobOfferRepository(JobOfferRepository):
    def __init__(self):
        self._job_offers: List[JobOffer] = []

    def save(self, job_offer: JobOffer) -> JobOffer:
        self._job_offers.append(job_offer)
        return job_offer

    def list_all(self) -> List[JobOffer]:
        return self._job_offers.copy()