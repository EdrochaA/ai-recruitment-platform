from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.application import Application


class ApplicationRepository(ABC):
    @abstractmethod
    def save(self, application: Application) -> Application:
        pass

    @abstractmethod
    def find_by_job_offer(self, job_offer_id: str) -> List[Application]:
        pass