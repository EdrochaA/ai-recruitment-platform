"""
JobOffer Repository Port - Interface for job offer persistence
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.job_offer import JobOffer


class JobOfferRepositoryPort(ABC):
    """Abstract interface for job offer data operations"""
    
    @abstractmethod
    async def create_job_offer(self, job_offer: JobOffer) -> JobOffer:
        """Create a new job offer"""
        pass
    
    @abstractmethod
    async def get_job_offer(self, offer_id: str) -> Optional[JobOffer]:
        """Get job offer by ID"""
        pass
    
    @abstractmethod
    async def list_open_offers(self) -> List[JobOffer]:
        """List all open job offers"""
        pass
    
    @abstractmethod
    async def list_offers_by_creator(self, creator_id: str) -> List[JobOffer]:
        """List job offers created by a specific HR/Admin"""
        pass
    
    @abstractmethod
    async def update_job_offer(self, offer_id: str, job_offer: JobOffer) -> Optional[JobOffer]:
        """Update a job offer"""
        pass
    
    @abstractmethod
    async def delete_job_offer(self, offer_id: str) -> bool:
        """Delete a job offer"""
        pass
