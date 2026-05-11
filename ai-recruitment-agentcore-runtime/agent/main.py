import logging
import os
from typing import Any

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except Exception:
    BedrockAgentCoreApp = None

from agent.agent import analyze_cv, _normalize_job_offer


logging.basicConfig(
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("agentcore-runtime")
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))


def _error(message: str, status: int = 400) -> dict:
    return {
        "error": {
            "message": message,
            "status": status,
        }
    }


def _validate_request(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    cv_text = payload.get("cv_text")
    if not isinstance(cv_text, str) or not cv_text.strip():
        raise ValueError("'cv_text' is required and must be a non-empty string")

    job_offer = payload.get("job_offer")
    if job_offer is None:
        job_offer = payload.get("job_description")

    job_offer_text = _normalize_job_offer(job_offer)
    if job_offer is not None and job_offer_text is None:
        raise ValueError(
            "'job_offer' must include at least one of: title, description, requirements"
        )

    return {
        "cv_text": cv_text.strip(),
        "job_offer": job_offer,
    }


app = BedrockAgentCoreApp() if BedrockAgentCoreApp else None


if app:
    @app.entrypoint
    async def invoke_agent(payload, context=None):
        try:
            logger.info("Invoking runtime entrypoint")
            validated = _validate_request(payload)
            result = analyze_cv(validated["cv_text"], validated["job_offer"])
            return result
        except Exception as exc:
            logger.error("Runtime error: %s", exc)
            return _error(str(exc))


def main() -> None:
    if app is None:
        logger.error("BedrockAgentCoreApp is not available. Runtime cannot start.")
        return

    logger.info("Starting Bedrock AgentCore runtime")
    app.run()


if __name__ == "__main__":
    main()
