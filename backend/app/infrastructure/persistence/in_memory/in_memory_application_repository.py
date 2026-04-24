from typing import List, Optional
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
            app for app in self._applications
            if app.job_offer_id == job_offer_id
        ]

    def find_by_id(self, application_id: str) -> Optional[Application]:
        for application in self._applications:
            if application.id == application_id:
                return application
        return None

    def update(self, application: Application) -> Application:
        for index, existing_application in enumerate(self._applications):
            if existing_application.id == application.id:
                self._applications[index] = application
                return application
        raise ValueError("Application not found")