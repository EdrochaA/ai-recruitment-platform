"""
JobOffer Entity - Pure Domain Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from enum import Enum


class JobOfferStatus(str, Enum):
    """Job offer status"""
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


@dataclass
class JobOffer:
    """Pure domain model for JobOffer"""
    id: str
    title: str
    company: str
    description: str
    location: str
    created_by: str  # User ID of creator (HR or Admin)
    created_at: datetime
    status: JobOfferStatus = JobOfferStatus.OPEN
    salary_min: float = 0.0
    salary_max: float = 0.0
    currency: str = "EUR"
    employment_type: str = "full-time"  # full-time, part-time, contract
    required_skills: List[str] = field(default_factory=list)
    nice_to_have_skills: List[str] = field(default_factory=list)
    
    def is_open(self) -> bool:
        """Check if offer is open for applications"""
        return self.status == JobOfferStatus.OPEN
    
    def close(self) -> None:
        """Close the offer"""
        self.status = JobOfferStatus.CLOSED
    
    def archive(self) -> None:
        """Archive the offer"""
        self.status = JobOfferStatus.ARCHIVED