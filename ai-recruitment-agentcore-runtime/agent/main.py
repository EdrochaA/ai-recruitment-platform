import logging
import os
import uuid
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent.agent import analyze_cv, normalize_job_offer


logging.basicConfig(
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("agentcore-runtime")
logger.setLevel(logging.INFO)

app = BedrockAgentCoreApp()

REGION = os.getenv("AWS_REGION", "eu-west-1")


def _get_session_id(context) -> str:
    session_id = getattr(context, "session_id", None)
    return session_id or f"sandbox-session-{uuid.uuid4().hex}"


def _validate_request(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    cv_text = payload.get("cv_text")
    if not isinstance(cv_text, str) or not cv_text.strip():
        raise ValueError("'cv_text' is required and must be a non-empty string")

    job_offer = payload.get("job_offer")
    if job_offer is None:
        job_offer = payload.get("job_description")

    job_offer_text = normalize_job_offer(job_offer)
    if job_offer is not None and job_offer_text is None:
        raise ValueError(
            "'job_offer' must include at least one of: title, description, requirements"
        )

    return {
        "cv_text": cv_text.strip(),
        "job_offer": job_offer,
    }


@app.entrypoint
async def invoke_agent(payload, context=None):
    """
    Main entrypoint for the CV Analysis Runtime.

    Expected payload:
        {
            "cv_text": "...",
            "job_offer": "..."  # or object with title/description/requirements
        }
    """
    logger.info("Received payload: %s", payload)
    session_id = _get_session_id(context)
    logger.info("Context session_id: %s", session_id)

    try:
        validated = _validate_request(payload)
        result = analyze_cv(validated["cv_text"], validated["job_offer"])
        return result
    except Exception as exc:
        error_msg = f"Runtime error: {exc}"
        logger.error(error_msg)
        return {"error": {"message": error_msg, "status": 400}}


if __name__ == "__main__":
    app.run()
