from fastapi import APIRouter, Depends, status

from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import (
    ListApplicationsByJobOffer,
)
from app.infrastructure.http.schemas.application_schema import (
    CreateApplicationRequest,
    ApplicationResponse,
)
from app.shared.dependencies import (
    get_create_application_use_case,
    get_list_applications_use_case,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    request: CreateApplicationRequest,
    use_case: CreateApplication = Depends(get_create_application_use_case),
):
    application = use_case.execute(
        job_offer_id=request.job_offer_id,
        candidate_name=request.candidate_name,
        candidate_email=request.candidate_email,
        cv_text=request.cv_text,
    )
    return ApplicationResponse(**application.__dict__)


@router.get("/job-offer/{job_offer_id}", response_model=list[ApplicationResponse])
def list_applications_by_job_offer(
    job_offer_id: str,
    use_case: ListApplicationsByJobOffer = Depends(get_list_applications_use_case),
):
    applications = use_case.execute(job_offer_id)
    return [ApplicationResponse(**app.__dict__) for app in applications]