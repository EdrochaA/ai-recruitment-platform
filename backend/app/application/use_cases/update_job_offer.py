import inspect
from typing import Any, Optional

from app.domain.entities.job_offer import JobOffer, JobOfferStatus


class UpdateJobOffer:
    def __init__(self, repository: Any):
        self.repository = repository

    async def execute(
        self,
        offer_id: str,
        actor_role: str,
        actor_user_id: str,
        title: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None,
        employment_type: Optional[str] = None,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        required_skills: Optional[list[str]] = None,
        nice_to_have_skills: Optional[list[str]] = None,
        status: Optional[str] = None,
    ) -> dict:
        offer = await self._get_offer(offer_id)
        if not offer:
            raise ValueError("JOB_OFFER_NOT_FOUND")

        if actor_role not in {"hr", "admin"}:
            raise ValueError("JOB_OFFER_FORBIDDEN")

        if actor_role == "hr" and offer.created_by != actor_user_id:
            raise ValueError("JOB_OFFER_FORBIDDEN")

        updated_offer = JobOffer(
            id=offer.id,
            title=title if title is not None else offer.title,
            company=company if company is not None else offer.company,
            description=description if description is not None else offer.description,
            location=location if location is not None else offer.location,
            created_by=offer.created_by,
            created_at=offer.created_at,
            status=self._normalize_status(status if status is not None else offer.status),
            salary_min=salary_min if salary_min is not None else offer.salary_min,
            salary_max=salary_max if salary_max is not None else offer.salary_max,
            currency=offer.currency,
            employment_type=employment_type if employment_type is not None else offer.employment_type,
            required_skills=list(required_skills) if required_skills is not None else list(offer.required_skills or []),
            nice_to_have_skills=list(nice_to_have_skills) if nice_to_have_skills is not None else list(offer.nice_to_have_skills or []),
        )

        saved_offer = await self._update_offer(offer_id, updated_offer)
        if not saved_offer:
            raise ValueError("JOB_OFFER_NOT_FOUND")

        return self._offer_to_dict(saved_offer)

    async def _get_offer(self, offer_id: str):
        getter = getattr(self.repository, "get_job_offer", None) or getattr(self.repository, "find_by_id", None)
        if getter is None:
            raise RuntimeError("Repository does not support fetching job offers")

        result = getter(offer_id)
        if inspect.isawaitable(result):
            return await result
        return result

    async def _update_offer(self, offer_id: str, job_offer: JobOffer):
        updater = getattr(self.repository, "update_job_offer", None)
        if updater is None:
            raise RuntimeError("Repository does not support updating job offers")

        result = updater(offer_id, job_offer)
        if inspect.isawaitable(result):
            return await result
        return result

    def _normalize_status(self, status_value: Any) -> JobOfferStatus:
        if isinstance(status_value, JobOfferStatus):
            return status_value

        try:
            return JobOfferStatus(str(status_value))
        except ValueError as exc:
            raise ValueError("JOB_OFFER_INVALID_STATUS") from exc

    def _offer_to_dict(self, offer: JobOffer) -> dict:
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
            "required_skills": list(offer.required_skills or []),
            "nice_to_have_skills": list(offer.nice_to_have_skills or []),
            "status": offer.status.value if hasattr(offer.status, "value") else str(offer.status),
            "created_by": offer.created_by,
            "created_at": offer.created_at.isoformat() if hasattr(offer.created_at, "isoformat") else offer.created_at,
        }