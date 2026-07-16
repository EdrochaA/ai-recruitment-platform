from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.job_application import JobApplication


class JobApplicationRepository(ABC):
    @abstractmethod
    def save(self, job_application: JobApplication) -> JobApplication:
        pass

    @abstractmethod
    def find_by_job_offer(self, job_offer_id: str) -> List[JobApplication]:
        pass

    @abstractmethod
    def find_by_id(self, job_application_id: str) -> Optional[JobApplication]:
        pass

    @abstractmethod
    def update(self, job_application: JobApplication) -> JobApplication:
        pass
