import inspect
import re
import zipfile
from io import BytesIO

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.responses import Response, StreamingResponse

from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import (
    ListApplicationsByJobOffer,
)
from app.application.use_cases.upload_application_cv import UploadApplicationCV
from app.application.use_cases.process_application_cv import ProcessApplicationCV
from app.application.use_cases.analyze_application_cv import AnalyzeApplicationCV

from app.adapters.http.schemas.application_schema import (
    CreateApplicationRequest,
    ApplicationResponse,
)

from app.shared.dependencies import (
    get_create_application_use_case,
    get_list_applications_use_case,
    get_upload_application_cv_use_case,
    get_process_application_cv_use_case,
    get_analyze_application_cv_use_case,
)
from app.shared.dependency_container import get_container

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


@router.post(
    "/{application_id}/cv/process",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
)
def process_application_cv(
    application_id: str,
    use_case: ProcessApplicationCV = Depends(get_process_application_cv_use_case),
):
    """Extract and process CV text from uploaded PDF."""
    try:
        application = use_case.execute(application_id=application_id)
        return ApplicationResponse(**application.__dict__)

    except ValueError as exc:
        error_detail = str(exc)
        # Distinguish between not found and processing error
        if "not found" in error_detail:
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=status_code,
            detail=error_detail,
        ) from exc


@router.post(
    "/{application_id}/cv/analyze",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_application_cv(
    application_id: str,
    use_case: AnalyzeApplicationCV = Depends(get_analyze_application_cv_use_case),
    authorization: str | None = Header(default=None, alias="Authorization"),
):
    """Analyze CV using intelligent CV analyzer.

    Extracts skills, experience and compatibility score based on job requirements.
    """
    container = get_container()
    if not container.auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ", 1)[1]
    payload = container.auth_service.token_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("role") not in {"hr", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR or admin can analyze CVs",
        )

    try:
        application = use_case.execute(application_id=application_id)
        return ApplicationResponse(**application.__dict__)

    except ValueError as exc:
        error_detail = str(exc)
        # Distinguish between not found and processing error
        if "not found" in error_detail:
            status_code = status.HTTP_404_NOT_FOUND
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=status_code,
            detail=error_detail,
        ) from exc


@router.get(
    "/{application_id}/cv/download",
    status_code=status.HTTP_200_OK,
)
def download_application_cv(application_id: str):
    container = get_container()
    application = container.application_repository.find_by_id(application_id)

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JobApplication not found: {application_id}",
        )

    if not application.cv_storage_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found for this application",
        )

    try:
        file_bytes = container.file_storage.get(application.cv_storage_key)
    except Exception as exc:
        error_detail = (
            "CV file could not be retrieved "
            f"(storage_key={application.cv_storage_key})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_detail,
        ) from exc

    filename = application.cv_original_filename or "cv.pdf"
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )


def _resolve_job_offer(job_offer_repository, job_offer_id: str):
    """Resolve job offer from repositories that may expose async or sync APIs."""
    if hasattr(job_offer_repository, "get_job_offer"):
        result = job_offer_repository.get_job_offer(job_offer_id)
        if inspect.isawaitable(result):
            return result
        return result

    if hasattr(job_offer_repository, "find_by_id"):
        return job_offer_repository.find_by_id(job_offer_id)

    return None


@router.get(
    "/job-offer/{job_offer_id}/cvs/download",
    status_code=status.HTTP_200_OK,
)
def download_job_offer_cvs(job_offer_id: str):
    container = get_container()

    job_offer_result = _resolve_job_offer(container.job_offer_repository, job_offer_id)
    if inspect.isawaitable(job_offer_result):
        import asyncio

        job_offer = asyncio.run(job_offer_result)
    else:
        job_offer = job_offer_result

    if not job_offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JobOffer not found: {job_offer_id}",
        )

    applications = container.application_repository.find_by_job_offer(job_offer_id)
    applications_with_cv = [app for app in applications if app.cv_storage_key]

    if not applications_with_cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CVs available for this job offer",
        )

    safe_offer_title = re.sub(
        r"[\\/:*?\"<>|]+",
        "_",
        (job_offer.title or "job-offer"),
    ).strip()
    if not safe_offer_title:
        safe_offer_title = "job-offer"

    zip_buffer = BytesIO()
    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for index, application in enumerate(applications_with_cv, start=1):
            try:
                file_bytes = container.file_storage.get(application.cv_storage_key)
            except Exception:
                continue

            cv_filename = application.cv_original_filename or f"cv-{index}.pdf"
            cv_filename = re.sub(r"[\\/:*?\"<>|]+", "_", cv_filename)
            arcname = f"{safe_offer_title}/{cv_filename}"
            zip_file.writestr(arcname, file_bytes)

    zip_buffer.seek(0)
    zip_filename = f"{safe_offer_title}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
        },
    )