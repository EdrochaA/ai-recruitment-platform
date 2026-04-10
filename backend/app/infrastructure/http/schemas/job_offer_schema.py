from datetime import datetime

from pydantic import BaseModel, Field


class CreateJobOfferRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    location: str = Field(..., min_length=2, max_length=100)


class JobOfferResponse(BaseModel):
    id: str
    title: str
    description: str
    location: str
    status: str
    created_at: datetime