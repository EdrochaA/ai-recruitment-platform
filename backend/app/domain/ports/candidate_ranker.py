"""
Port: CandidateRankerPort

Defines the interface for ranking candidates against a job offer.
Implementations can be:
  - AgentCoreCandidateRanker: delegates reasoning to the LLM (primary)
  - KeywordCandidateRanker:   pure Python keyword matching (fallback)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CandidateInput:
    """Minimal candidate data sent to the ranker."""
    application_id: str
    candidate_name: str
    candidate_email: str
    cv_text: str
    cv_analysis_summary: str | None = None
    cv_analysis_technical_skills: list[str] = field(default_factory=list)
    cv_analysis_experience: str | None = None
    cv_analysis_status: str = "pending"


@dataclass
class RankedCandidate:
    """Single ranked result returned by the ranker."""
    rank: int
    application_id: str
    candidate_name: str
    candidate_email: str
    score: int          # 0-100
    ranking_reason: str
    cv_summary: str | None = None
    skills: list[str] = field(default_factory=list)
    experience: str | None = None
    cv_processing_status: str = "unknown"
    cv_analysis_status: str = "pending"


class CandidateRankerPort(ABC):
    """Abstract port for candidate ranking. Implementations injected at runtime."""

    @abstractmethod
    def rank(
        self,
        job_offer_title: str,
        job_offer_description: str,
        required_skills: list[str],
        candidates: list[CandidateInput],
        top_n: int,
    ) -> tuple[list[RankedCandidate], str]:
        """Rank candidates for a job offer.

        Args:
            job_offer_title: Title of the job offer.
            job_offer_description: Full description of the offer.
            required_skills: List of required skills for the position.
            candidates: List of candidate inputs (with CV text).
            top_n: Maximum number of candidates to return.

        Returns:
            Tuple of (ranked_candidates sorted desc by score, summary_message).
        """
