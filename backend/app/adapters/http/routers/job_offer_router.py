"""
JobOffer Router
HTTP endpoints for job offer management
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.adapters.http.schemas.job_offer_schemas import (
    CreateJobOfferRequest,
    UpdateJobOfferRequest,
    UpdateJobOfferStatusRequest,
    JobOfferResponse,
    JobOfferListResponse,
)
from app.shared.dependencies import get_update_job_offer_use_case

router = APIRouter(prefix="/job-offers", tags=["Job Offers"])
logger = logging.getLogger(__name__)

# This will be injected by main.py
job_offer_service = None


def set_job_offer_service(service):
    """Set the job offer service (called from main.py)"""
    global job_offer_service
    job_offer_service = service


def get_auth_service():
    """Get auth service from router (will be set from main.py)"""
    from app.adapters.http.routers.auth_router import auth_service
    return auth_service


def get_user_from_token(authorization: Optional[str] = Header(None)):
    """Extract user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    auth_service = get_auth_service()
    
    if not auth_service:
        return None
    
    payload = auth_service.token_service.verify_token(token)
    if not payload:
        return None
    
    return payload


def _require_job_offer_manage_role(payload: dict) -> None:
    user_role = payload.get("role")
    if user_role not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin users can manage job offers",
        )


def _map_job_offer_update_error(error: ValueError) -> HTTPException:
    message = str(error)
    if message == "JOB_OFFER_NOT_FOUND":
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job offer not found")
    if message == "JOB_OFFER_FORBIDDEN":
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this job offer")
    if message == "JOB_OFFER_INVALID_STATUS":
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job offer status")
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.post("", response_model=JobOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_job_offer(
    request: CreateJobOfferRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new job offer (HR and Admin only)
    
    Requires valid JWT token in Authorization header.
    """
    if not job_offer_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job offer service not initialized",
        )

    # Get user from token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    auth_service = get_auth_service()
    payload = auth_service.token_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Verify user is HR or Admin
    user_role = payload.get("role")
    if user_role not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin users can create job offers"
        )
    
    try:
        result = await job_offer_service.create_job_offer(
            creator_email=payload.get("email"),
            title=request.title,
            company=request.company,
            description=request.description,
            location=request.location,
            salary_min=request.salary_min or 0.0,
            salary_max=request.salary_max or 0.0,
            currency=request.currency or "EUR",
            employment_type=request.employment_type or "full-time",
            required_skills=request.required_skills or [],
            nice_to_have_skills=request.nice_to_have_skills or [],
        )
        return result
    except ValueError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating job offer"
        )


@router.get("", response_model=JobOfferListResponse)
async def list_job_offers():
    """
    Get all open job offers (public endpoint)
    """
    if not job_offer_service:
        logger.error("job_offer_service is not initialized in list_job_offers")
        return {"offers": [], "total": 0}

    try:
        result = await job_offer_service.get_open_offers()
        return result
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching job offers"
        )


@router.get("/my-offers", response_model=JobOfferListResponse)
async def get_my_offers(authorization: Optional[str] = Header(None)):
    """
    Get job offers created by the current user (HR/Admin only)
    """
    if not job_offer_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job offer service not initialized",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    token = authorization.split(" ")[1]
    auth_service = get_auth_service()
    payload = auth_service.token_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Verify user is HR or Admin
    user_role = payload.get("role")
    if user_role not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin users can view their offers"
        )
    
    try:
        result = await job_offer_service.get_my_offers(payload.get("user_id"))
        return result
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching your offers"
        )


@router.put("/{offer_id}", response_model=JobOfferResponse)
async def update_job_offer(
    offer_id: str,
    request: UpdateJobOfferRequest,
    authorization: Optional[str] = Header(None),
    use_case = Depends(get_update_job_offer_use_case),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ")[1]
    auth_service = get_auth_service()
    payload = auth_service.token_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    _require_job_offer_manage_role(payload)

    try:
        result = await use_case.execute(
            offer_id=offer_id,
            actor_role=payload.get("role"),
            actor_user_id=payload.get("user_id"),
            title=request.title,
            company=request.company,
            location=request.location,
            description=request.description,
            employment_type=request.employment_type,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
            required_skills=request.required_skills,
            nice_to_have_skills=request.nice_to_have_skills,
        )
        return result
    except ValueError as exc:
        raise _map_job_offer_update_error(exc)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating job offer",
        )


@router.patch("/{offer_id}/status", response_model=JobOfferResponse)
async def update_job_offer_status(
    offer_id: str,
    request: UpdateJobOfferStatusRequest,
    authorization: Optional[str] = Header(None),
    use_case = Depends(get_update_job_offer_use_case),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ")[1]
    auth_service = get_auth_service()
    payload = auth_service.token_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    _require_job_offer_manage_role(payload)

    try:
        result = await use_case.execute(
            offer_id=offer_id,
            actor_role=payload.get("role"),
            actor_user_id=payload.get("user_id"),
            status=request.status,
        )
        return result
    except ValueError as exc:
        raise _map_job_offer_update_error(exc)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating job offer status",
        )
