from app.domain.ports.chatbot_service import ChatbotService


class SendChatbotMessage:
    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    def execute(
        self,
        message: str,
        role: str,
        page: str,
        job_offer_id: str | None = None,
        application_id: str | None = None,
    ) -> dict:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("Message cannot be empty")

        if len(normalized_message) > 1000:
            raise ValueError("Message exceeds maximum length of 1000 characters")

        normalized_role = (role or "candidate").strip().lower()
        if normalized_role not in {"candidate", "hr", "admin"}:
            normalized_role = "candidate"

        normalized_page = (page or "unknown").strip().lower()

        return self.chatbot_service.send_message(
            message=normalized_message,
            role=normalized_role,
            page=normalized_page,
            job_offer_id=job_offer_id,
            application_id=application_id,
        )
