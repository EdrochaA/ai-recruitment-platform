"""
Internal data router — consumed by the blueprint-agent local tools.

Exposes raw recruitment data (offers, candidates, CV text) so that the
agent tools (agent/tools/recruitment_tools.py) can retrieve real data
from the platform and pass it to the LLM for reasoning.

Not exposed to the browser/frontend — only called from within the
AgentCore Runtime environment via RECRUITMENT_API_URL.

No business logic here — pure data retrieval.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.shared.dependency_container import get_container

router = APIRouter(prefix="/internal", tags=["Internal (MCP)"])
logger = logging.getLogger(__name__)


# ── Response schemas ───────────────────────────────────────────────────────

class JobOfferSummary(BaseModel):
    id: str
    title: str
    company: str
    description: str
    location: str
    status: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    employment_type: str


class CandidateSummary(BaseModel):
    application_id: str
    candidate_name: str
    candidate_email: str
    cv_text: str | None
    cv_processing_status: str | None
    cv_analysis_status: str
    cv_analysis_summary: str | None
    cv_analysis_technical_skills: list[str]
    cv_analysis_soft_skills: list[str]
    cv_analysis_experience: str | None
    cv_analysis_education: list[str]
    cv_analysis_languages: list[str]


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/job-offers", response_model=list[JobOfferSummary])
def list_job_offers_internal():
    """Return all job offers. Used by local agent tools."""
    container = get_container()
    offers = container.job_offer_repository.list_all()
    return [
        JobOfferSummary(
            id=o.id,
            title=o.title,
            company=o.company,
            description=o.description,
            location=o.location,
            status=o.status.value if hasattr(o.status, "value") else str(o.status),
            required_skills=list(o.required_skills or []),
            nice_to_have_skills=list(o.nice_to_have_skills or []),
            employment_type=o.employment_type or "full-time",
        )
        for o in offers
    ]


@router.get("/job-offers/by-title", response_model=JobOfferSummary | None)
def get_job_offer_by_title(
    title: str = Query(..., description="Partial or full job offer title"),
):
    """Find a job offer by title (partial, case-insensitive)."""
    container = get_container()

    offer = None
    if hasattr(container.job_offer_repository, "find_by_title"):
        offer = container.job_offer_repository.find_by_title(title)
    else:
        all_offers = container.job_offer_repository.list_all()
        title_lower = title.lower()
        for o in all_offers:
            if o.title.lower() == title_lower:
                offer = o
                break
        if not offer:
            for o in all_offers:
                if title_lower in o.title.lower():
                    offer = o
                    break

    if not offer:
        return None

    return JobOfferSummary(
        id=offer.id,
        title=offer.title,
        company=offer.company,
        description=offer.description,
        location=offer.location,
        status=offer.status.value if hasattr(offer.status, "value") else str(offer.status),
        required_skills=list(offer.required_skills or []),
        nice_to_have_skills=list(offer.nice_to_have_skills or []),
        employment_type=offer.employment_type or "full-time",
    )


@router.get("/candidates", response_model=list[CandidateSummary])
def list_candidates_for_offer(
    job_offer_title: str = Query(..., description="Job offer title to search candidates for"),
):
    """Return all candidates with CVs for a given offer. Auto-extracts CV text if not yet processed."""
    container = get_container()

    # Resolve offer
    offer = None
    if hasattr(container.job_offer_repository, "find_by_title"):
        offer = container.job_offer_repository.find_by_title(job_offer_title)
    else:
        all_offers = container.job_offer_repository.list_all()
        title_lower = job_offer_title.lower()
        for o in all_offers:
            if title_lower in o.title.lower() or o.title.lower() in title_lower:
                offer = o
                break

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No job offer found matching title: '{job_offer_title}'",
        )

    applications = container.application_repository.find_by_job_offer(offer.id)
    apps_with_cv = [a for a in applications if a.cv_storage_key]

    # Auto-extract CV text for any unprocessed application
    for app in apps_with_cv:
        if not app.cv_text:
            try:
                file_bytes = container.file_storage.get(app.cv_storage_key)
                app.cv_text = container.cv_text_extractor.extract_text(
                    file_bytes, filename=app.cv_original_filename
                )
                app.cv_processing_status = "processed"
                container.application_repository.update(app)
                logger.info("Auto-extracted CV text for application %s", app.id)
            except Exception as exc:
                logger.warning(
                    "Could not extract CV text for application %s: %s", app.id, exc
                )

    return [
        CandidateSummary(
            application_id=app.id,
            candidate_name=app.candidate_name,
            candidate_email=app.candidate_email,
            cv_text=app.cv_text,
            cv_processing_status=app.cv_processing_status,
            cv_analysis_status=app.cv_analysis_status or "pending",
            cv_analysis_summary=app.cv_analysis_summary,
            cv_analysis_technical_skills=app.cv_analysis_technical_skills or [],
            cv_analysis_soft_skills=app.cv_analysis_soft_skills or [],
            cv_analysis_experience=app.cv_analysis_experience,
            cv_analysis_education=app.cv_analysis_education or [],
            cv_analysis_languages=app.cv_analysis_languages or [],
        )
        for app in apps_with_cv
    ]


@router.get("/candidates/{application_id}/cv", response_model=dict)
def get_candidate_cv(
    application_id: str,
):
    """Return the full CV text for a single candidate."""
    container = get_container()

    app = container.application_repository.find_by_id(application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )

    cv_text = app.cv_text
    if not cv_text and app.cv_storage_key:
        try:
            file_bytes = container.file_storage.get(app.cv_storage_key)
            cv_text = container.cv_text_extractor.extract_text(
                file_bytes, filename=app.cv_original_filename
            )
            app.cv_text = cv_text
            app.cv_processing_status = "processed"
            container.application_repository.update(app)
        except Exception as exc:
            logger.warning("Could not extract CV text for %s: %s", application_id, exc)

    return {
        "application_id": app.id,
        "candidate_name": app.candidate_name,
        "candidate_email": app.candidate_email,
        "cv_text": cv_text or "",
        "cv_processing_status": app.cv_processing_status or "unknown",
    }
