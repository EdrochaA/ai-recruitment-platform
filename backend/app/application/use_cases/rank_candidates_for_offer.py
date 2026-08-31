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
                "evaluable_candidates": 0,
                "candidates_without_cv": 0,
                "candidates_without_cv_text": 0,
                "ranked_candidates": [],
            }

        applications = self.application_repository.find_by_job_offer(job_offer.id)
        apps_with_cv = [a for a in applications if a.cv_storage_key]
        candidates_without_cv = len(applications) - len(apps_with_cv)

        if not apps_with_cv:
            return {
                "found": True,
                "message": self._build_user_message(
                    job_offer_title=job_offer.title,
                    total_candidates=len(applications),
                    evaluable_candidates=0,
                    candidates_without_cv=candidates_without_cv,
                    candidates_without_cv_text=0,
                    requested_top_n=top_n,
                    ranked_count=0,
                ),
                "job_offer_title": job_offer.title,
                "job_offer_description": job_offer.description,
                "total_candidates": len(applications),
                "evaluable_candidates": 0,
                "candidates_without_cv": candidates_without_cv,
                "candidates_without_cv_text": 0,
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
        candidates_without_cv_text = len(apps_with_cv) - len(candidate_inputs)

        if not candidate_inputs:
            return {
                "found": True,
                "message": self._build_user_message(
                    job_offer_title=job_offer.title,
                    total_candidates=len(applications),
                    evaluable_candidates=0,
                    candidates_without_cv=candidates_without_cv,
                    candidates_without_cv_text=candidates_without_cv_text,
                    requested_top_n=top_n,
                    ranked_count=0,
                ),
                "job_offer_title": job_offer.title,
                "job_offer_description": job_offer.description,
                "total_candidates": len(applications),
                "evaluable_candidates": 0,
                "candidates_without_cv": candidates_without_cv,
                "candidates_without_cv_text": candidates_without_cv_text,
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
            "message": self._build_user_message(
                job_offer_title=job_offer.title,
                total_candidates=len(applications),
                evaluable_candidates=len(candidate_inputs),
                candidates_without_cv=candidates_without_cv,
                candidates_without_cv_text=candidates_without_cv_text,
                requested_top_n=top_n,
                ranked_count=len(ranked),
                ranker_summary=summary,
            ),
            "job_offer_title": job_offer.title,
            "job_offer_description": job_offer.description,
            "total_candidates": len(applications),
            "evaluable_candidates": len(candidate_inputs),
            "candidates_without_cv": candidates_without_cv,
            "candidates_without_cv_text": candidates_without_cv_text,
            "ranked_candidates": ranked,
        }

    # ── Internal helpers ────────────────────────────────────────────────────

    def _build_user_message(
        self,
        job_offer_title: str,
        total_candidates: int,
        evaluable_candidates: int,
        candidates_without_cv: int,
        candidates_without_cv_text: int,
        requested_top_n: int,
        ranked_count: int,
        ranker_summary: str | None = None,
    ) -> str:
        if total_candidates == 0:
            return (
                f"La oferta '{job_offer_title}' existe pero todavía no tiene "
                "candidaturas. No se ha generado ningún ranking."
            )

        total_label = "candidatura" if total_candidates == 1 else "candidaturas"
        message = (
            f"Se encontraron **{total_candidates} {total_label}** para "
            f"'{job_offer_title}'."
        )

        if evaluable_candidates == 0:
            message += " Ninguna pudo evaluarse: "
        else:
            evaluation_verb = "pudo evaluarse" if evaluable_candidates == 1 else "pudieron evaluarse"
            message += f" De ellas, **{evaluable_candidates} {evaluation_verb}**"

        exclusions: list[str] = []
        if candidates_without_cv:
            no_cv_verb = "no se evaluó" if candidates_without_cv == 1 else "no se evaluaron"
            exclusions.append(
                f"**{candidates_without_cv} {no_cv_verb} porque "
                f"{'no tiene' if candidates_without_cv == 1 else 'no tienen'} CV subido**"
            )
        if candidates_without_cv_text:
            no_text_verb = "no pudo evaluarse" if candidates_without_cv_text == 1 else "no pudieron evaluarse"
            exclusions.append(
                f"**{candidates_without_cv_text} {no_text_verb} porque "
                f"{'su CV no contiene' if candidates_without_cv_text == 1 else 'sus CV no contienen'} "
                "texto extraíble**"
            )

        if exclusions:
            if len(exclusions) == 1:
                exclusions_text = exclusions[0]
            else:
                exclusions_text = " y ".join(exclusions)
            if evaluable_candidates == 0:
                message += exclusions_text + "."
            else:
                message += "; " + exclusions_text + "."
        elif evaluable_candidates > 0:
            message += "."

        if evaluable_candidates == 0:
            return message + " No se ha generado ningún ranking."

        expected_count = min(requested_top_n, evaluable_candidates)
        if ranked_count == expected_count:
            message += (
                f" Se muestra el top {ranked_count} entre las candidaturas "
                "evaluables."
            )
        else:
            message += (
                f" Se obtuvieron {ranked_count} resultados válidos de los "
                f"{expected_count} solicitados."
            )

        if ranker_summary:
            message += f"\n\n{ranker_summary}"
        return message

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
