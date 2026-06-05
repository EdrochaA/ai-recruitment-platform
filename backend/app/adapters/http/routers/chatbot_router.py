import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.adapters.http.schemas.chatbot_schema import (
    ChatbotMessageRequest,
    ChatbotMessageResponse,
)
from app.application.use_cases.send_chatbot_message import SendChatbotMessage
from app.shared.dependencies import get_send_chatbot_message_use_case
from app.shared.dependency_container import get_container

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])
logger = logging.getLogger(__name__)


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

    role = str(payload.get("role") or "").strip().lower()

    if role not in {"hr", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chatbot access is restricted to HR and admin users",
        )

    try:
        result = use_case.execute(
            message=request.message,
            actor_id=(
                payload.get("user_id")
                or payload.get("email")
                or payload.get("username")
            ),
        )
        return ChatbotMessageResponse(**result)
    except ValueError as exc:
        logger.exception(exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.exception(exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chatbot request failed",
        ) from exc
