from app.application.use_cases.create_job_offer import CreateJobOffer
from app.application.use_cases.list_job_offers import ListJobOffers
from app.infrastructure.persistence.in_memory.in_memory_job_offer_repository import (
    InMemoryJobOfferRepository,
)

job_offer_repository = InMemoryJobOfferRepository()


def get_create_job_offer_use_case() -> CreateJobOffer:
    return CreateJobOffer(job_offer_repository)


def get_list_job_offers_use_case() -> ListJobOffers:
    return ListJobOffers(job_offer_repository)