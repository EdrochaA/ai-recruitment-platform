from app.domain.ports.chatbot_service import ChatbotService


class SendChatbotMessage:
    def __init__(self, chatbot_service: ChatbotService):
        self.chatbot_service = chatbot_service

    def execute(
        self,
        message: str,
        actor_id: str | None = None,
    ) -> dict:
        normalized_message = message.strip()
        if not normalized_message:
            raise ValueError("Message cannot be empty")

        if len(normalized_message) > 1000:
            raise ValueError("Message exceeds maximum length of 1000 characters")

        return self.chatbot_service.send_message(
            message=normalized_message,
            actor_id=actor_id,
        )
