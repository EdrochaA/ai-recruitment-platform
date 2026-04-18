from app.application.use_cases.create_job_offer import CreateJobOffer
from app.application.use_cases.list_job_offers import ListJobOffers
from app.infrastructure.persistence.in_memory.in_memory_job_offer_repository import (
    InMemoryJobOfferRepository,
)

from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import (
    ListApplicationsByJobOffer,
)
from app.infrastructure.persistence.in_memory.in_memory_application_repository import (
    InMemoryApplicationRepository,
)

# =========================
# REPOSITORIES
# =========================

job_offer_repository = InMemoryJobOfferRepository()
application_repository = InMemoryApplicationRepository()

# =========================
# JOB OFFER USE CASES
# =========================

def get_create_job_offer_use_case() -> CreateJobOffer:
    return CreateJobOffer(job_offer_repository)


def get_list_job_offers_use_case() -> ListJobOffers:
    return ListJobOffers(job_offer_repository)

# =========================
# APPLICATION USE CASES
# =========================

def get_create_application_use_case() -> CreateApplication:
    return CreateApplication(application_repository)


def get_list_applications_use_case() -> ListApplicationsByJobOffer:
    return ListApplicationsByJobOffer(application_repository)