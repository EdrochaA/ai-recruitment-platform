import re

from app.domain.ports.chatbot_service import ChatbotService


class RuleBasedChatbotService(ChatbotService):
    def send_message(
        self,
        message: str,
        role: str,
        page: str,
        job_offer_id: str | None = None,
        application_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        message_lower = message.lower()

        if self._is_job_offer_question(message_lower, page):
            return self._job_offer_help(role, job_offer_id)

        if self._is_application_question(message_lower, page):
            return self._application_help(role, application_id)

        if self._is_cv_question(message_lower):
            return self._cv_help(role)

        if self._is_hr_question(message_lower, page):
            return self._hr_help(role)

        if self._is_ai_analysis_question(message_lower):
            return self._ai_analysis_help(role)

        return {
            "answer": (
                "Estoy especializado en la plataforma de reclutamiento. "
                "Puedo ayudarte con ofertas, candidaturas y CV dentro del sistema."
            ),
            "intent": "general_help",
            "suggestions": self._default_suggestions(role),
        }

    def _is_job_offer_question(self, message: str, page: str) -> bool:
        return bool(re.search(r"oferta|vacante|puesto|job", message)) or page in {
            "job_offers",
            "job_detail",
        }

    def _is_application_question(self, message: str, page: str) -> bool:
        return bool(re.search(r"candidatura|postul|aplic", message)) or page in {
            "applications",
        }

    def _is_cv_question(self, message: str) -> bool:
        return bool(re.search(r"\bcv\b|curriculum|resume|hoja de vida", message))

    def _is_hr_question(self, message: str, page: str) -> bool:
        return bool(re.search(r"dashboard|hr|reclutad|admin", message)) or page in {
            "hr_dashboard",
        }

    def _is_ai_analysis_question(self, message: str) -> bool:
        return bool(re.search(r"ia|inteligencia artificial|analysis|analisis", message))

    def _job_offer_help(self, role: str, job_offer_id: str | None) -> dict:
        details_hint = (
            f" Puedes revisar el detalle de la oferta {job_offer_id}."
            if job_offer_id
            else ""
        )
        return {
            "answer": (
                "Puedes consultar las ofertas disponibles desde el listado y abrir el detalle para ver requisitos."
                f"{details_hint}"
            ),
            "intent": "job_offer_help",
            "suggestions": [
                "Ver ofertas disponibles",
                "Abrir detalle de una oferta",
                "Filtrar por ubicación o habilidades",
            ],
        }

    def _application_help(self, role: str, application_id: str | None) -> dict:
        ref_hint = (
            f" Puedes revisar el estado de la candidatura {application_id}."
            if application_id
            else ""
        )
        if role == "candidate":
            answer = (
                "Como candidato, puedes revisar tus candidaturas y su estado desde tu panel."
                f"{ref_hint}"
            )
            suggestions = [
                "Revisar mis candidaturas",
                "Ver estado de una candidatura",
                "Aplicar a una oferta",
            ]
        else:
            answer = (
                "Puedes revisar candidaturas asociadas a cada oferta desde el panel de RRHH."
                f"{ref_hint}"
            )
            suggestions = [
                "Ver candidaturas por oferta",
                "Abrir dashboard de RRHH",
                "Descargar CVs de una oferta",
            ]

        return {
            "answer": answer,
            "intent": "application_help",
            "suggestions": suggestions,
        }

    def _cv_help(self, role: str) -> dict:
        if role == "candidate":
            answer = (
                "Puedes subir tu CV en PDF desde tu candidatura. "
                "Después podrás verificar que quedó asociado correctamente."
            )
            suggestions = [
                "Subir mi CV",
                "Revisar mis candidaturas",
                "Ver ofertas disponibles",
            ]
        else:
            answer = (
                "Puedes visualizar y descargar CVs vinculados a candidaturas desde las vistas de RRHH."
            )
            suggestions = [
                "Ver candidaturas por oferta",
                "Descargar CVs de una oferta",
                "Abrir dashboard de RRHH",
            ]

        return {
            "answer": answer,
            "intent": "cv_help",
            "suggestions": suggestions,
        }

    def _hr_help(self, role: str) -> dict:
        if role == "candidate":
            return {
                "answer": (
                    "El dashboard de RRHH está orientado a usuarios internos. "
                    "Como candidato, puedes usar tu panel de candidaturas y ofertas."
                ),
                "intent": "hr_help",
                "suggestions": [
                    "Ver ofertas disponibles",
                    "Revisar mis candidaturas",
                    "Subir mi CV",
                ],
            }

        if role == "admin":
            answer = (
                "Como admin, puedes gestionar usuarios HR y supervisar la publicación de ofertas."
            )
            suggestions = [
                "Crear usuario HR",
                "Revisar ofertas activas",
                "Abrir dashboard de RRHH",
            ]
        else:
            answer = (
                "Como HR, puedes gestionar ofertas y revisar candidaturas en el dashboard."
            )
            suggestions = [
                "Crear una oferta",
                "Ver candidaturas por oferta",
                "Descargar CVs de una oferta",
            ]

        return {
            "answer": answer,
            "intent": "hr_help",
            "suggestions": suggestions,
        }

    def _ai_analysis_help(self, role: str) -> dict:
        return {
            "answer": (
                "La plataforma contempla análisis asistido de CV, "
                "pero no realiza decisiones automáticas de contratación desde este chatbot."
            ),
            "intent": "cv_help",
            "suggestions": self._default_suggestions(role),
        }

    def _default_suggestions(self, role: str) -> list[str]:
        if role == "candidate":
            return [
                "Ver ofertas disponibles",
                "Revisar mis candidaturas",
                "Subir mi CV",
            ]

        if role == "admin":
            return [
                "Crear usuario HR",
                "Revisar ofertas activas",
                "Ver candidaturas por oferta",
            ]

        return [
            "Abrir dashboard de RRHH",
            "Ver candidaturas por oferta",
            "Descargar CVs de una oferta",
        ]
