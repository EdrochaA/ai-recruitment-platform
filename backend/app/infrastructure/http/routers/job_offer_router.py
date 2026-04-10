from fastapi import APIRouter, Depends, status

from app.application.use_cases.create_job_offer import CreateJobOffer
from app.application.use_cases.list_job_offers import ListJobOffers
from app.infrastructure.http.schemas.job_offer_schema import (
    CreateJobOfferRequest,
    JobOfferResponse,
)
from app.shared.dependencies import (
    get_create_job_offer_use_case,
    get_list_job_offers_use_case,
)

router = APIRouter(prefix="/job-offers", tags=["Job Offers"])


@router.post("", response_model=JobOfferResponse, status_code=status.HTTP_201_CREATED)
def create_job_offer(
    request: CreateJobOfferRequest,
    use_case: CreateJobOffer = Depends(get_create_job_offer_use_case),
):
    job_offer = use_case.execute(
        title=request.title,
        description=request.description,
        location=request.location,
    )
    return JobOfferResponse(
        id=job_offer.id,
        title=job_offer.title,
        description=job_offer.description,
        location=job_offer.location,
        status=job_offer.status,
        created_at=job_offer.created_at,
    )


@router.get("", response_model=list[JobOfferResponse])
def list_job_offers(
    use_case: ListJobOffers = Depends(get_list_job_offers_use_case),
):
    job_offers = use_case.execute()
    return [
        JobOfferResponse(
            id=job_offer.id,
            title=job_offer.title,
            description=job_offer.description,
            location=job_offer.location,
            status=job_offer.status,
            created_at=job_offer.created_at,
        )
        for job_offer in job_offers
    ]