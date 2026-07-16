import re

from app.domain.ports.chatbot_service import ChatbotService


class RuleBasedChatbotService(ChatbotService):
    def send_message(
        self,
        message: str,
        actor_id: str | None = None,
    ) -> dict:
        message_lower = message.lower()

        if self._is_job_offer_question(message_lower):
            return self._job_offer_help()

        if self._is_application_question(message_lower):
            return self._application_help()

        if self._is_cv_question(message_lower):
            return self._cv_help()

        if self._is_hr_question(message_lower):
            return self._hr_help()

        if self._is_ai_analysis_question(message_lower):
            return self._ai_analysis_help()

        return {
            "answer": (
                "Estoy especializado en la plataforma de reclutamiento. "
                "Puedo ayudarte con ofertas, candidaturas y CV dentro del sistema."
            ),
            "intent": "general_help",
            "suggestions": [
                "Ver ofertas disponibles",
                "Revisar candidaturas",
                "Consultar sobre CV",
            ],
        }

    def _is_job_offer_question(self, message: str) -> bool:
        return bool(re.search(r"oferta|vacante|puesto|job", message))

    def _is_application_question(self, message: str) -> bool:
        return bool(re.search(r"candidatura|postul|aplic", message))

    def _is_cv_question(self, message: str) -> bool:
        return bool(re.search(r"\bcv\b|curriculum|resume|hoja de vida", message))

    def _is_hr_question(self, message: str) -> bool:
        return bool(re.search(r"dashboard|hr|reclutad|admin", message))

    def _is_ai_analysis_question(self, message: str) -> bool:
        return bool(re.search(r"ia|inteligencia artificial|analysis|analisis", message))

    def _job_offer_help(self) -> dict:
        return {
            "answer": "Puedes consultar las ofertas disponibles desde el listado y abrir el detalle para ver requisitos.",
            "intent": "job_offer_help",
            "suggestions": [
                "Ver ofertas disponibles",
                "Abrir detalle de una oferta",
                "Filtrar por habilidades",
            ],
        }

    def _application_help(self) -> dict:
        return {
            "answer": "Puedes revisar candidaturas y su estado desde el panel disponible.",
            "intent": "application_help",
            "suggestions": [
                "Ver candidaturas",
                "Revisar estado",
                "Postular a una oferta",
            ],
        }

    def _cv_help(self) -> dict:
        return {
            "answer": "Puedes gestionar y revisar CV desde la plataforma.",
            "intent": "cv_help",
            "suggestions": [
                "Subir CV",
                "Revisar mis candidaturas",
                "Descargar CVs",
            ],
        }

    def _hr_help(self) -> dict:
        return {
            "answer": "El dashboard de RRHH gestiona ofertas, candidaturas y usuarios.",
            "intent": "hr_help",
            "suggestions": [
                "Crear una oferta",
                "Ver candidaturas",
                "Gestionar usuarios",
            ],
        }

    def _ai_analysis_help(self) -> dict:
        return {
            "answer": "La plataforma ofrece análisis asistido de CV y candidaturas.",
            "intent": "cv_help",
            "suggestions": [
                "Analizar CV",
                "Revisar candidaturas",
                "Ver resultados",
            ],
        }
