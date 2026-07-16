from typing import List, Optional

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

    def find_by_id(self, job_offer_id: str) -> Optional[JobOffer]:
        for job_offer in self._job_offers:
            if job_offer.id == job_offer_id:
                return job_offer
        return None

    def update_job_offer(self, offer_id: str, job_offer: JobOffer) -> Optional[JobOffer]:
        for index, existing_offer in enumerate(self._job_offers):
            if existing_offer.id == offer_id:
                job_offer.id = existing_offer.id
                self._job_offers[index] = job_offer
                return job_offer
        return None

    def find_by_title(self, title: str) -> Optional[JobOffer]:
        """Find by partial, case-insensitive title match."""
        title_lower = title.lower().strip()
        # Exact match first
        for offer in self._job_offers:
            if offer.title.lower() == title_lower:
                return offer
        # Partial match
        for offer in self._job_offers:
            if title_lower in offer.title.lower() or offer.title.lower() in title_lower:
                return offer
        return None
