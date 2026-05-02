from typing import List, Optional
from app.domain.entities.job_application import JobApplication
from app.domain.ports.job_application_repository import JobApplicationRepository


class InMemoryJobApplicationRepository(JobApplicationRepository):
    def __init__(self):
        self._job_applications: List[JobApplication] = []

    def save(self, job_application: JobApplication) -> JobApplication:
        self._job_applications.append(job_application)
        return job_application

    def find_by_job_offer(self, job_offer_id: str) -> List[JobApplication]:
        return [
            job_app for job_app in self._job_applications
            if job_app.job_offer_id == job_offer_id
        ]

    def find_by_id(self, job_application_id: str) -> Optional[JobApplication]:
        for job_application in self._job_applications:
            if job_application.id == job_application_id:
                return job_application
        return None

    def update(self, job_application: JobApplication) -> JobApplication:
        for index, existing_job_application in enumerate(self._job_applications):
            if existing_job_application.id == job_application.id:
                self._job_applications[index] = job_application
                return job_application
        raise ValueError("JobApplication not found")
