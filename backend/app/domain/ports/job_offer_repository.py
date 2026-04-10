from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.job_offer import JobOffer


class JobOfferRepository(ABC):
    @abstractmethod
    def save(self, job_offer: JobOffer) -> JobOffer:
        pass

    @abstractmethod
    def list_all(self) -> List[JobOffer]:
        pass