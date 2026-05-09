import json
import os
from typing import Any

try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
except Exception:
    BedrockAgentCoreApp = None


def _error(message: str, status: int = 400) -> dict:
    return {
        "error": {
            "message": message,
            "status": status,
        }
    }


def _job_offer_to_text(job_offer: Any) -> str | None:
    if job_offer is None:
        return None

    if isinstance(job_offer, str):
        return job_offer.strip() or None

    if isinstance(job_offer, dict):
        parts = []
        title = job_offer.get("title")
        description = job_offer.get("description")
        requirements = job_offer.get("requirements")

        if isinstance(title, str) and title.strip():
            parts.append(f"Title: {title.strip()}")
        if isinstance(description, str) and description.strip():
            parts.append(f"Description: {description.strip()}")

        if isinstance(requirements, list):
            req_list = [str(item).strip() for item in requirements if str(item).strip()]
            if req_list:
                parts.append(f"Requirements: {', '.join(req_list)}")
        elif isinstance(requirements, str) and requirements.strip():
            parts.append(f"Requirements: {requirements.strip()}")

        if parts:
            return "\n".join(parts)
        return None

    raise ValueError("'job_offer' must be a string or object when provided")


def _validate_payload(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    cv_text = payload.get("cv_text")
    if not isinstance(cv_text, str) or not cv_text.strip():
        raise ValueError("'cv_text' is required and must be a non-empty string")

    job_offer = payload.get("job_offer")
    if job_offer is None:
        job_offer = payload.get("job_description")

    job_offer_text = _job_offer_to_text(job_offer)
    if job_offer is not None and job_offer_text is None:
        raise ValueError(
            "'job_offer' must include at least one of: title, description, requirements"
        )

    return {
        "cv_text": cv_text.strip(),
        "job_offer": job_offer_text,
    }


def _mock_analyze(cv_text: str, job_offer: str | None) -> dict:
    skills_pool = [
        "python",
        "fastapi",
        "sql",
        "postgresql",
        "docker",
        "aws",
        "java",
        "javascript",
        "react",
        "machine learning",
        "nlp",
        "git",
    ]

    cv_lower = cv_text.lower()
    job_lower = job_offer.lower() if job_offer else ""

    detected_skills = [s for s in skills_pool if s in cv_lower]
    required_skills = [s for s in skills_pool if s in job_lower]

    if required_skills:
        matched = set(detected_skills) & set(required_skills)
        score = int((len(matched) / len(required_skills)) * 100)
    else:
        score = min(50, len(detected_skills) * 5)

    experience = "Mock analysis: relevant experience detected"
    summary = "Mock analysis completed for CV" \
        + (" against job offer" if job_offer else "")

    return {
        "score": min(100, score + 10),
        "summary": summary,
        "skills": detected_skills,
        "experience": experience,
        # Keep compatibility with backend expectations
        "experience_summary": experience,
    }


def analyze_cv(payload: dict) -> dict:
    validated = _validate_payload(payload)
    cv_text = validated["cv_text"]
    job_offer = validated["job_offer"]

    use_bedrock = os.getenv("USE_BEDROCK", "false").lower() == "true"
    if use_bedrock:
        # Placeholder for real Bedrock call
        # Replace _mock_analyze with a real implementation when ready
        return _mock_analyze(cv_text, job_offer)

    return _mock_analyze(cv_text, job_offer)


app = BedrockAgentCoreApp() if BedrockAgentCoreApp else None


if app:
    @app.entrypoint
    async def invoke(payload, context=None):
        try:
            return analyze_cv(payload)
        except Exception as exc:
            return _error(str(exc))


def _local_test() -> None:
    sample_payload = {
        "cv_text": "Senior backend engineer with Python, FastAPI, AWS, Docker.",
        "job_offer": {
            "title": "Senior Python Developer",
            "description": "Backend role focused on APIs and data systems.",
            "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        },
    }
    result = analyze_cv(sample_payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if app is not None and os.getenv("LOCAL_TEST", "false").lower() != "true":
        app.run()
    else:
        _local_test()
