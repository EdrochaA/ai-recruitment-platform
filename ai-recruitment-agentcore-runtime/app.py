import json
import os
import re
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

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


def _build_prompt(cv_text: str, job_offer: str | None) -> str:
    offer_text = job_offer or "No job offer provided."
    return (
        "You are a recruitment assistant. Analyze the CV against the job offer and respond with ONLY a JSON object.\n\n"
        "Return JSON with exactly these fields:\n"
        "{\"score\": 0, \"summary\": \"\", \"skills\": [], \"experience\": \"\"}\n\n"
        "Rules:\n"
        "- score is an integer from 0 to 100\n"
        "- summary is 1-2 concise sentences\n"
        "- skills is a list of detected technical/professional skills\n"
        "- experience is a short summary of relevant experience\n"
        "- Output ONLY JSON, no extra text\n\n"
        "CV:\n"
        "---\n"
        f"{cv_text}\n"
        "---\n\n"
        "JOB OFFER:\n"
        "---\n"
        f"{offer_text}\n"
        "---"
    )


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    code_block = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block:
        return json.loads(code_block.group(1))

    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return json.loads(text[brace_start:brace_end + 1])

    raise ValueError("No valid JSON found in LLM response")


def _normalize_response(payload: dict) -> dict:
    score = payload.get("score")
    if isinstance(score, str):
        match = re.search(r"\d+", score)
        score = int(match.group(0)) if match else 50
    score = int(score) if score is not None else 50
    score = max(0, min(100, score))

    summary = str(payload.get("summary", "")).strip() or "No summary provided."
    experience = str(payload.get("experience", "")).strip() or "No experience summary provided."

    skills = payload.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if not isinstance(skills, list):
        skills = []
    skills = [str(s).strip() for s in skills if str(s).strip()]

    return {
        "score": score,
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "experience_summary": experience,
    }


def _bedrock_analyze(cv_text: str, job_offer: str | None) -> dict:
    region = os.getenv("AWS_REGION")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not region or not model_id:
        raise ValueError("AWS_REGION and BEDROCK_MODEL_ID must be set for Bedrock")

    prompt = _build_prompt(cv_text, job_offer)
    max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS", "700"))

    client = boto3.client("bedrock-runtime", region_name=region)

    try:
        if "anthropic" in model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}],
                    }
                ],
            }
        else:
            raise ValueError("Unsupported model for this minimal runtime")

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body).encode("utf-8"),
            contentType="application/json",
            accept="application/json",
        )

        raw_body = response.get("body")
        if not raw_body:
            raise ValueError("Empty response body from Bedrock")
        response_text = raw_body.read().decode("utf-8")

        parsed = json.loads(response_text)
        if "content" in parsed and isinstance(parsed["content"], list):
            text_parts = [p.get("text", "") for p in parsed["content"] if isinstance(p, dict)]
            llm_text = "".join(text_parts).strip()
        else:
            llm_text = response_text.strip()

        extracted = _extract_json(llm_text)
        return _normalize_response(extracted)

    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Bedrock error: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from Bedrock: {exc}") from exc


def analyze_cv(payload: dict) -> dict:
    validated = _validate_payload(payload)
    cv_text = validated["cv_text"]
    job_offer = validated["job_offer"]

    use_bedrock = os.getenv("USE_BEDROCK", "false").lower() == "true"
    if use_bedrock:
        try:
            return _bedrock_analyze(cv_text, job_offer)
        except Exception:
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
