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
