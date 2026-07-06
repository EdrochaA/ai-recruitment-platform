"""
Use case: rank the top-N candidates for a given job offer.

Flow:
1. Find offer by title (partial, case-insensitive).
2. Load all applications that have a CV uploaded.
3. Ensure cv_text is extracted for each (auto-process if missing).
4. Delegate ranking to CandidateRankerPort:
   - Primary:  AgentCoreCandidateRanker  → LLM reasons about the candidates.
   - Fallback: KeywordCandidateRanker    → pure Python keyword matching.
5. Return top N with scores and explanations.

The use case itself contains NO scoring logic — that belongs to the ranker adapters.
"""

from __future__ import annotations

import logging
from typing import Any

from app.domain.ports.candidate_ranker import CandidateInput, CandidateRankerPort
from app.domain.ports.cv_text_extractor import CVTextExtractor
from app.domain.ports.file_storage import FileStorage
from app.domain.ports.job_application_repository import JobApplicationRepository

logger = logging.getLogger("rank-candidates")


class RankCandidatesForOffer:
    """Orchestrates CV reading and delegates ranking to the injected ranker port."""

    def __init__(
        self,
        job_offer_repository: Any,
        application_repository: JobApplicationRepository,
        cv_text_extractor: CVTextExtractor,
        file_storage: FileStorage,
        candidate_ranker: CandidateRankerPort,
    ) -> None:
        self.job_offer_repository = job_offer_repository
        self.application_repository = application_repository
        self.cv_text_extractor = cv_text_extractor
        self.file_storage = file_storage
        self.candidate_ranker = candidate_ranker

    # ── Public API ──────────────────────────────────────────────────────────

    def execute(self, job_offer_title: str, top_n: int = 3) -> dict:
        job_offer = self._find_offer_by_title(job_offer_title)
        if not job_offer:
            return {
                "found": False,
                "message": (
                    f"No encontré ninguna oferta con el título '{job_offer_title}'. "
                    "Verifica el nombre exacto."
                ),
                "job_offer_title": job_offer_title,
                "job_offer_description": None,
                "total_candidates": 0,
                "ranked_candidates": [],
            }

        applications = self.application_repository.find_by_job_offer(job_offer.id)
        apps_with_cv = [a for a in applications if a.cv_storage_key]

        if not apps_with_cv:
            return {
                "found": True,
                "message": (
                    f"La oferta '{job_offer.title}' existe pero todavía "
                    "no tiene candidatos con CV subido."
                ),
                "job_offer_title": job_offer.title,
                "job_offer_description": job_offer.description,
                "total_candidates": 0,
                "ranked_candidates": [],
            }

        # Ensure cv_text is extracted for every candidate before ranking
        for app in apps_with_cv:
            if not app.cv_text and app.cv_storage_key:
                try:
                    file_bytes = self.file_storage.get(app.cv_storage_key)
                    app.cv_text = self.cv_text_extractor.extract_text(
                        file_bytes, filename=app.cv_original_filename
                    )
                    app.cv_processing_status = "processed"
                    self.application_repository.update(app)
                    logger.info("Auto-extracted CV text for application %s", app.id)
                except Exception as exc:
                    logger.warning(
                        "Could not extract CV text for application %s: %s", app.id, exc
                    )

        # Build CandidateInput objects for the ranker port
        candidate_inputs = [
            CandidateInput(
                application_id=app.id,
                candidate_name=app.candidate_name,
                candidate_email=app.candidate_email,
                cv_text=app.cv_text or "",
                cv_analysis_summary=app.cv_analysis_summary,
                cv_analysis_technical_skills=(
                    app.cv_analysis_technical_skills
                    or app.cv_analysis_skills
                    or []
                ),
                cv_analysis_experience=app.cv_analysis_experience,
                cv_analysis_status=app.cv_analysis_status or "pending",
            )
            for app in apps_with_cv
            if app.cv_text  # only send candidates with text to the ranker
        ]

        if not candidate_inputs:
            return {
                "found": True,
                "message": (
                    f"Hay {len(apps_with_cv)} candidatos en '{job_offer.title}' "
                    "pero ninguno tiene texto de CV extraído todavía."
                ),
                "job_offer_title": job_offer.title,
                "job_offer_description": job_offer.description,
                "total_candidates": len(apps_with_cv),
                "ranked_candidates": [],
            }

        # ── Delegate to the ranker port (AgentCore LLM or keyword fallback) ──
        ranked_list, summary = self.candidate_ranker.rank(
            job_offer_title=job_offer.title,
            job_offer_description=job_offer.description or "",
            required_skills=list(job_offer.required_skills or []),
            candidates=candidate_inputs,
            top_n=top_n,
        )

        ranked = [
            {
                "rank": r.rank,
                "application_id": r.application_id,
                "candidate_name": r.candidate_name,
                "candidate_email": r.candidate_email,
                "score": r.score,
                "ranking_reason": r.ranking_reason,
                "cv_summary": r.cv_summary,
                "skills": r.skills,
                "experience": r.experience,
                "cv_processing_status": r.cv_processing_status,
                "cv_analysis_status": r.cv_analysis_status,
            }
            for r in ranked_list
        ]

        return {
            "found": True,
            "message": summary,
            "job_offer_title": job_offer.title,
            "job_offer_description": job_offer.description,
            "total_candidates": len(apps_with_cv),
            "ranked_candidates": ranked,
        }

    # ── Internal helpers ────────────────────────────────────────────────────

    def _find_offer_by_title(self, title: str) -> Any | None:
        title_lower = title.lower().strip()

        if hasattr(self.job_offer_repository, "find_by_title"):
            return self.job_offer_repository.find_by_title(title_lower)

        all_offers: list[Any] = []
        if hasattr(self.job_offer_repository, "list_all"):
            all_offers = self.job_offer_repository.list_all()

        for offer in all_offers:
            if offer.title.lower() == title_lower:
                return offer
        for offer in all_offers:
            if title_lower in offer.title.lower() or offer.title.lower() in title_lower:
                return offer
        return None
