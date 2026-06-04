from abc import ABC, abstractmethod


class ChatbotService(ABC):
    @abstractmethod
    def send_message(
        self,
        message: str,
        role: str,
        page: str,
        job_offer_id: str | None = None,
        application_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        pass
