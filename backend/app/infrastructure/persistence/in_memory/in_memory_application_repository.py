from typing import List

from app.domain.entities.application import Application
from app.domain.ports.application_repository import ApplicationRepository


class InMemoryApplicationRepository(ApplicationRepository):
    def __init__(self):
        self._applications: List[Application] = []

    def save(self, application: Application) -> Application:
        self._applications.append(application)
        return application

    def find_by_job_offer(self, job_offer_id: str) -> List[Application]:
        return [
            app for app in self._applications if app.job_offer_id == job_offer_id
        ]