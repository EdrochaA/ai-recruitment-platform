"""
Adapter: KeywordCandidateRanker

Fallback ranker that scores candidates using keyword matching
against the job offer's required skills and existing CV analysis data.

Used when AgentCore is unavailable or not configured.
No LLM is involved — pure Python heuristics.
"""

from __future__ import annotations

import logging

from app.domain.ports.candidate_ranker import (
    CandidateInput,
    CandidateRankerPort,
    RankedCandidate,
)

logger = logging.getLogger("keyword-candidate-ranker")


class KeywordCandidateRanker(CandidateRankerPort):
    """Ranks candidates with keyword matching (no LLM required)."""

    def rank(
        self,
        job_offer_title: str,
        job_offer_description: str,
        required_skills: list[str],
        candidates: list[CandidateInput],
        top_n: int,
    ) -> tuple[list[RankedCandidate], str]:
        required = [s.lower() for s in required_skills]

        scored = sorted(
            [self._score(c, required) for c in candidates],
            key=lambda x: x[0],
            reverse=True,
        )
        top = scored[:top_n]

        ranked = [
            RankedCandidate(
                rank=i + 1,
                application_id=cand.application_id,
                candidate_name=cand.candidate_name,
                candidate_email=cand.candidate_email,
                score=score,
                ranking_reason=reason + " ⚠️ (ranking por keywords — agente IA no disponible)",
                cv_summary=cand.cv_analysis_summary,
                skills=cand.cv_analysis_technical_skills,
                experience=cand.cv_analysis_experience,
                cv_processing_status="processed",
                cv_analysis_status=cand.cv_analysis_status,
            )
            for i, (score, reason, cand) in enumerate(top)
        ]

        names = ", ".join(
            f"#{r.rank} {r.candidate_name} ({r.score}/100)" for r in ranked
        )
        summary = f"Ranking por keywords (sin agente IA). Top {len(ranked)}: {names}."
        return ranked, summary

    # ── Internal ───────────────────────────────────────────────────────────

    def _score(
        self,
        c: CandidateInput,
        required: list[str],
    ) -> tuple[int, str, CandidateInput]:
        reasons: list[str] = []

        candidate_skills = [s.lower() for s in c.cv_analysis_technical_skills]
        text_lower = (c.cv_text or "").lower()

        matches_struct = [
            s for s in required
            if any(s in cs or cs in s for cs in candidate_skills)
        ]
        matches_text = [s for s in required if s in text_lower]
        all_matches = list(dict.fromkeys(matches_struct + matches_text))

        if c.cv_analysis_status == "completed":
            score = min(100, 50 + len(all_matches) * 10)
            if c.cv_analysis_summary:
                reasons.append(c.cv_analysis_summary[:200])
        elif c.cv_text:
            score = min(70, 20 + len(all_matches) * 10)
        else:
            score = 10

        if all_matches:
            reasons.append(f"Skills coincidentes: {', '.join(all_matches[:5])}")
        if c.cv_analysis_experience:
            reasons.append(f"Experiencia: {c.cv_analysis_experience[:150]}")

        reason = " · ".join(reasons) or "Sin datos suficientes"
        return score, reason, c
