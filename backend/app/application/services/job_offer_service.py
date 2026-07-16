"""
JobOffer Service - Application Layer
Coordinates job offer use cases
"""

from datetime import datetime
from typing import List

from app.domain.entities.job_offer import JobOffer, JobOfferStatus
from app.domain.entities.user import UserRole
from app.domain.ports.job_offer_repository_port import JobOfferRepositoryPort
from app.domain.ports.user_repository_port import UserRepositoryPort


class JobOfferService:
    """Application service for job offer operations"""
    
    def __init__(
        self,
        job_offer_repository: JobOfferRepositoryPort,
        user_repository: UserRepositoryPort
    ):
        """Initialize job offer service with dependencies"""
        self.job_offer_repository = job_offer_repository
        self.user_repository = user_repository
    
    async def create_job_offer(
        self,
        creator_email: str,
        title: str,
        company: str,
        description: str,
        location: str,
        salary_min: float = 0.0,
        salary_max: float = 0.0,
        currency: str = "EUR",
        employment_type: str = "full-time",
        required_skills: List[str] = None,
        nice_to_have_skills: List[str] = None,
    ) -> dict:
        """Create a new job offer (only HR and Admin can create)"""
        # Verify creator is HR or Admin
        creator = await self.user_repository.get_user_by_email(creator_email)
        if not creator:
            raise ValueError("Creator user not found")
        
        if not creator.is_hr() and not creator.is_admin():
            raise ValueError("Only HR and Admin users can create job offers")
        
        # Create job offer
        job_offer = JobOffer(
            id="",  # Will be set by repository
            title=title,
            company=company,
            description=description,
            location=location,
            created_by=creator.id,
            created_at=datetime.utcnow(),
            status=JobOfferStatus.OPEN,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=employment_type,
            required_skills=required_skills or [],
            nice_to_have_skills=nice_to_have_skills or [],
        )
        
        # Save to repository
        created_offer = await self.job_offer_repository.create_job_offer(job_offer)
        
        return self._job_offer_to_dict(created_offer)
    
    async def get_open_offers(self) -> dict:
        """Get all open job offers (public)"""
        offers = await self.job_offer_repository.list_open_offers()
        return {
            "offers": [self._job_offer_to_dict(offer) for offer in offers],
            "total": len(offers)
        }
    
    async def get_my_offers(self, creator_id: str) -> dict:
        """Get job offers created by current user (HR/Admin only)"""
        offers = await self.job_offer_repository.list_offers_by_creator(creator_id)
        return {
            "offers": [self._job_offer_to_dict(offer) for offer in offers],
            "total": len(offers)
        }
    
    def _job_offer_to_dict(self, offer: JobOffer) -> dict:
        """Convert JobOffer to dictionary"""
        return {
            "id": offer.id,
            "title": offer.title,
            "company": offer.company,
            "description": offer.description,
            "location": offer.location,
            "salary_min": offer.salary_min,
            "salary_max": offer.salary_max,
            "currency": offer.currency,
            "employment_type": offer.employment_type,
            "required_skills": offer.required_skills,
            "nice_to_have_skills": offer.nice_to_have_skills,
            "status": offer.status.value,
            "created_by": offer.created_by,
            "created_at": offer.created_at.isoformat(),
        }
