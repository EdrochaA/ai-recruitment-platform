"""
JobOffer Router
HTTP endpoints for job offer management
"""

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional

from app.adapters.http.schemas.job_offer_schemas import (
    CreateJobOfferRequest,
    JobOfferResponse,
    JobOfferListResponse,
)

router = APIRouter(prefix="/job-offers", tags=["Job Offers"])

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


@router.post("", response_model=JobOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_job_offer(
    request: CreateJobOfferRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new job offer (HR and Admin only)
    
    Requires valid JWT token in Authorization header.
    """
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating job offer"
        )


@router.get("", response_model=JobOfferListResponse)
async def list_job_offers():
    """
    Get all open job offers (public endpoint)
    """
    try:
        result = await job_offer_service.get_open_offers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching job offers"
        )


@router.get("/my-offers", response_model=JobOfferListResponse)
async def get_my_offers(authorization: Optional[str] = Header(None)):
    """
    Get job offers created by the current user (HR/Admin only)
    """
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
        result = await job_offer_service.get_my_offers(payload.get("email"))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching your offers"
        )
