"""
JobOffer HTTP Request/Response Schemas
"""

from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class CreateJobOfferRequest(BaseModel):
    """Request schema for creating a job offer"""
    title: str
    description: str
    location: str
    company: Optional[str] = "Company"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = "EUR"
    employment_type: Optional[str] = "full-time"
    required_skills: Optional[List[str]] = None
    nice_to_have_skills: Optional[List[str]] = None


class UpdateJobOfferRequest(BaseModel):
    """Request schema for updating a job offer"""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    required_skills: Optional[List[str]] = None
    nice_to_have_skills: Optional[List[str]] = None


class UpdateJobOfferStatusRequest(BaseModel):
    """Request schema for updating job offer status"""
    status: Literal["open", "closed"]


class JobOfferResponse(BaseModel):
    """Job offer response schema"""
    id: str
    title: str
    company: str
    description: str
    location: str
    salary_min: float
    salary_max: float
    currency: str
    employment_type: str
    required_skills: List[str]
    nice_to_have_skills: List[str]
    status: str
    created_by: str
    created_at: datetime


class JobOfferListResponse(BaseModel):
    """List of job offers response"""
    offers: List[JobOfferResponse]
    total: int
