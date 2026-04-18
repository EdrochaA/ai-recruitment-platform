from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateApplicationRequest(BaseModel):
    job_offer_id: str
    candidate_name: str = Field(..., min_length=2, max_length=100)
    candidate_email: EmailStr
    cv_text: str = Field(..., min_length=10)


class ApplicationResponse(BaseModel):
    id: str
    job_offer_id: str
    candidate_name: str
    candidate_email: str
    cv_text: str
    created_at: datetime