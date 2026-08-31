from typing import Literal

from pydantic import BaseModel, Field


class ChatbotContextRequest(BaseModel):
    page: Literal[
        "job_offers",
        "job_detail",
        "applications",
        "hr_dashboard",
        "candidate_dashboard",
        "unknown",
    ] = "unknown"
    job_offer_id: str | None = None
    application_id: str | None = None


class ChatbotMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: ChatbotContextRequest = ChatbotContextRequest()


class ChatbotMessageResponse(BaseModel):
    answer: str
    intent: Literal[
        "general_help",
        "job_offer_help",
        "application_help",
        "cv_help",
        "hr_help",
        "unknown",
    ]
    suggestions: list[str]


# ── Ranking schemas ────────────────────────────────────────────────────────

class RankCandidatesRequest(BaseModel):
    job_offer_title: str = Field(..., min_length=1, max_length=200)
    top_n: int = Field(3, ge=1, le=10)


class RankedCandidateItem(BaseModel):
    rank: int
    application_id: str
    candidate_name: str
    candidate_email: str
    score: int
    ranking_reason: str
    cv_summary: str | None = None
    skills: list[str] = []
    experience: str | None = None
    cv_processing_status: str = "unknown"
    cv_analysis_status: str = "pending"


class RankCandidatesResponse(BaseModel):
    found: bool
    message: str
    job_offer_title: str
    job_offer_description: str | None = None
    total_candidates: int
    evaluable_candidates: int = 0
    candidates_without_cv: int = 0
    candidates_without_cv_text: int = 0
    ranked_candidates: list[RankedCandidateItem]
