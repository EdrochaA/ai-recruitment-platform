from app.application.use_cases.create_job_offer import CreateJobOffer
from app.application.use_cases.list_job_offers import ListJobOffers
from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import (
    ListApplicationsByJobOffer,
)
from app.application.use_cases.upload_application_cv import UploadApplicationCV
from app.application.use_cases.process_application_cv import ProcessApplicationCV
from app.application.use_cases.analyze_application_cv import AnalyzeApplicationCV
from app.shared.dependency_container import get_container


def get_create_job_offer_use_case() -> CreateJobOffer:
    container = get_container()
    return CreateJobOffer(container.job_offer_repository)


def get_list_job_offers_use_case() -> ListJobOffers:
    container = get_container()
    return ListJobOffers(container.job_offer_repository)


def get_create_application_use_case() -> CreateApplication:
    container = get_container()
    return CreateApplication(container.application_repository)


def get_list_applications_use_case() -> ListApplicationsByJobOffer:
    container = get_container()
    return ListApplicationsByJobOffer(container.application_repository)


def get_upload_application_cv_use_case() -> UploadApplicationCV:
    container = get_container()
    return UploadApplicationCV(container.application_repository, container.file_storage)


def get_process_application_cv_use_case() -> ProcessApplicationCV:
    container = get_container()
    return ProcessApplicationCV(container.application_repository, container.cv_text_extractor)


def get_analyze_application_cv_use_case() -> AnalyzeApplicationCV:
    container = get_container()
    return AnalyzeApplicationCV(
        container.application_repository,
        container.job_offer_repository,
        container.cv_analyzer,
    )
