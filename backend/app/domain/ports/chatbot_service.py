from abc import ABC, abstractmethod


class ChatbotService(ABC):
    @abstractmethod
    def send_message(
        self,
        message: str,
        actor_id: str | None = None,
    ) -> dict:
        pass
