from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import (
    ListApplicationsByJobOffer,
)
from app.application.use_cases.upload_application_cv import UploadApplicationCV

from app.infrastructure.http.schemas.application_schema import (
    CreateApplicationRequest,
    ApplicationResponse,
)

from app.shared.dependencies import (
    get_create_application_use_case,
    get_list_applications_use_case,
    get_upload_application_cv_use_case,
)

router = APIRouter(prefix="/applications", tags=["Applications"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    request: CreateApplicationRequest,
    use_case: CreateApplication = Depends(get_create_application_use_case),
):
    application = use_case.execute(
        job_offer_id=request.job_offer_id,
        candidate_name=request.candidate_name,
        candidate_email=request.candidate_email,
    )
    return ApplicationResponse(**application.__dict__)


@router.get(
    "/job-offer/{job_offer_id}",
    response_model=list[ApplicationResponse],
)
def list_applications_by_job_offer(
    job_offer_id: str,
    use_case: ListApplicationsByJobOffer = Depends(get_list_applications_use_case),
):
    applications = use_case.execute(job_offer_id)
    return [ApplicationResponse(**app.__dict__) for app in applications]


@router.post(
    "/{application_id}/cv",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_cv(
    application_id: str,
    file: UploadFile = File(...),
    use_case: UploadApplicationCV = Depends(get_upload_application_cv_use_case),
):
    # Validar content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Validar que filename no sea None
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename",
        )

    filename = file.filename  # A partir de aquí es seguro (str)

    # Validar extensión
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .pdf extension",
        )

    # Leer archivo
    file_bytes = await file.read()

    # Validar tamaño
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds maximum allowed size of 5 MB",
        )

    try:
        application = use_case.execute(
            application_id=application_id,
            original_filename=filename,
            content_type=file.content_type or "application/pdf",
            file_bytes=file_bytes,
        )
        return ApplicationResponse(**application.__dict__)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc