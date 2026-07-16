import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.adapters.chatbot.rule_based_chatbot_service import RuleBasedChatbotService
from app.domain.ports.chatbot_service import ChatbotService

logger = logging.getLogger("agentcore-chatbot")


class AgentCoreChatbotService(ChatbotService):
    def __init__(
        self,
        runtime_arn: str,
        region: str,
        timeout_seconds: int = 20,
        fallback_service: ChatbotService | None = None,
    ):
        self.runtime_arn = runtime_arn
        self.region = region
        self.timeout_seconds = timeout_seconds
        self.fallback_service = fallback_service or RuleBasedChatbotService()
        logger.info(
            "AgentCoreChatbotService initialized. runtime_arn=%s region=%s timeout=%s",
            self.runtime_arn,
            self.region,
            self.timeout_seconds,
        )

    def send_message(
        self,
        message: str,
        actor_id: str | None = None,
    ) -> dict:
        safe_actor_id = actor_id or "user"

        try:
            response = self._invoke_runtime(
                prompt=message,
                actor_id=safe_actor_id,
            )
            return self._parse_runtime_response(response)
        except Exception as exc:
            logger.exception(
                "AgentCore chatbot invocation failed for runtime=%s",
                self.runtime_arn,
            )
            if os.getenv("CHATBOT_AGENTCORE_FALLBACK", "true").lower() == "true":
                logger.warning("Falling back to RuleBasedChatbotService after AgentCore failure")
                return self.fallback_service.send_message(
                    message=message,
                    actor_id=safe_actor_id,
                )
            error_detail = str(exc).strip() or exc.__class__.__name__
            raise RuntimeError(
                f"Chatbot provider error: AgentCore runtime is unavailable ({error_detail})"
            ) from exc

    def _invoke_runtime(self, prompt: str, actor_id: str) -> dict[str, Any]:
        config = Config(read_timeout=self.timeout_seconds, connect_timeout=10)
        client = boto3.client(
            "bedrock-agentcore",
            region_name=self.region,
            config=config,
        )

        payload = {
            "prompt": prompt,
            "actor_id": actor_id,
        }

        logger.info(
            "Invoking AgentCore chatbot runtime role-safe actor_id=%s region=%s",
            actor_id,
            self.region,
        )

        try:
            return client.invoke_agent_runtime(
                agentRuntimeArn=self.runtime_arn,
                runtimeSessionId=self._build_session_id(actor_id),
                payload=json.dumps(payload).encode("utf-8"),
            )
        except (ClientError, BotoCoreError):
            raise

    def _build_session_id(self, actor_id: str) -> str:
        safe_actor = "".join(ch for ch in actor_id if ch.isalnum() or ch in {"-", "_"})
        timestamp = str(int(time.time() * 1000))
        actor_fragment = (safe_actor[:16] or "user").ljust(16, "0")
        return f"chatbot-session-{actor_fragment}-{timestamp}"

    def _parse_runtime_response(self, response: dict[str, Any]) -> dict:
        raw_text = self._extract_text(response).strip()
        if not raw_text:
            return self._safe_response(
                answer="No se pudo obtener respuesta del asistente en este momento.",
                intent="general_help",
                suggestions=[],
            )

        parsed_json = self._try_parse_json(raw_text)
        if isinstance(parsed_json, dict):
            answer_value = parsed_json.get("answer") or raw_text
            if isinstance(answer_value, str):
                try:
                    import json as _json

                    answer_value = _json.loads(answer_value)
                except (ValueError, TypeError):
                    pass
            answer = str(answer_value).strip()
            intent = str(parsed_json.get("intent") or "general_help").strip() or "general_help"
            suggestions = parsed_json.get("suggestions") or []
            if not isinstance(suggestions, list):
                suggestions = []
            suggestions = [str(item).strip() for item in suggestions if str(item).strip()]
            return self._safe_response(answer=answer, intent=intent, suggestions=suggestions)

        clean_answer = parsed_json if isinstance(parsed_json, str) else raw_text
        return self._safe_response(
            answer=clean_answer,
            intent="general_help",
            suggestions=[],
        )

    def _extract_text(self, response: dict[str, Any]) -> str:
        content_type = response.get("contentType", "")
        if "response" in response:
            body = response["response"]
            if hasattr(body, "read"):
                return body.read().decode("utf-8")
            if hasattr(body, "iter_lines"):
                chunks = []
                for line in body.iter_lines(chunk_size=10):
                    if not line:
                        continue
                    text_line = line.decode("utf-8")
                    if text_line.startswith("data: "):
                        text_line = text_line[6:]
                    chunks.append(text_line)
                return "".join(chunks)

        if "application/json" in content_type and "payload" in response:
            payload = response["payload"]
            if isinstance(payload, (bytes, bytearray)):
                return payload.decode("utf-8")

        if "output" in response:
            return str(response["output"])
        if "text" in response:
            return str(response["text"])
        return ""

    def _try_parse_json(self, text: str) -> dict[str, Any] | None:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None

    def _safe_response(self, answer: str, intent: str, suggestions: list[str]) -> dict:
        allowed_intents = {
            "general_help",
            "job_offer_help",
            "application_help",
            "cv_help",
            "hr_help",
            "unknown",
        }
        normalized_intent = intent if intent in allowed_intents else "general_help"
        return {
            "answer": answer or "No se pudo generar una respuesta.",
            "intent": normalized_intent,
            "suggestions": suggestions[:3],
        }
