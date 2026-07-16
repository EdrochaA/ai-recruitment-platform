from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.job_offer import JobOffer


class JobOfferRepository(ABC):
    @abstractmethod
    def save(self, job_offer: JobOffer) -> JobOffer:
        pass

    @abstractmethod
    def list_all(self) -> List[JobOffer]:
        pass

    @abstractmethod
    def find_by_id(self, job_offer_id: str) -> Optional[JobOffer]:
        pass