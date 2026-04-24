from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.application import Application


class ApplicationRepository(ABC):
    @abstractmethod
    def save(self, application: Application) -> Application:
        pass

    @abstractmethod
    def find_by_job_offer(self, job_offer_id: str) -> List[Application]:
        pass

    @abstractmethod
    def find_by_id(self, application_id: str) -> Optional[Application]:
        pass

    @abstractmethod
    def update(self, application: Application) -> Application:
        pass