from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.adapters.http.schemas.chatbot_schema import (
    ChatbotMessageRequest,
    ChatbotMessageResponse,
)
from app.application.use_cases.send_chatbot_message import SendChatbotMessage
from app.shared.dependencies import get_send_chatbot_message_use_case
from app.shared.dependency_container import get_container

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/message", response_model=ChatbotMessageResponse)
def send_chatbot_message(
    request: ChatbotMessageRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    use_case: SendChatbotMessage = Depends(get_send_chatbot_message_use_case),
):
    container = get_container()
    if not container.auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = authorization.split(" ", 1)[1]
    payload = container.auth_service.token_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    role = str(payload.get("role") or "candidate")

    try:
        result = use_case.execute(
            message=request.message,
            role=role,
            page=request.context.page,
            job_offer_id=request.context.job_offer_id,
            application_id=request.context.application_id,
        )
        return ChatbotMessageResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
