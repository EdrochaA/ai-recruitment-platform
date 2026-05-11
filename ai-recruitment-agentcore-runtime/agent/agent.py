import json
import logging
import os
import re
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("agentcore-runtime")


def bedrock_enabled() -> bool:
    return os.getenv("USE_BEDROCK", "false").lower() == "true"


def read_bedrock_config() -> tuple[str | None, str | None]:
    return os.getenv("AWS_REGION"), os.getenv("BEDROCK_MODEL_ID")


def new_bedrock_client(region: str):
    read_timeout = int(os.getenv("BEDROCK_READ_TIMEOUT", "60"))
    connect_timeout = int(os.getenv("BEDROCK_CONNECT_TIMEOUT", "10"))
    config = Config(read_timeout=read_timeout, connect_timeout=connect_timeout)
    return boto3.client("bedrock-runtime", region_name=region, config=config)


def normalize_job_offer(job_offer: Any) -> str | None:
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


def mock_analysis(cv_text: str, job_offer_text: str | None) -> dict:
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
    job_lower = job_offer_text.lower() if job_offer_text else ""

    detected_skills = [s for s in skills_pool if s in cv_lower]
    required_skills = [s for s in skills_pool if s in job_lower]

    if required_skills:
        matched = set(detected_skills) & set(required_skills)
        score = int((len(matched) / len(required_skills)) * 100)
    else:
        score = min(50, len(detected_skills) * 5)

    experience = "Mock analysis: relevant experience detected"
    summary = "Mock analysis completed for CV" + (" against job offer" if job_offer_text else "")

    return {
        "score": min(100, score + 10),
        "summary": summary,
        "skills": detected_skills,
        "experience": experience,
        "experience_summary": experience,
    }


def build_system_prompt(cv_text: str, job_offer_text: str | None) -> str:
    offer_text = job_offer_text or "No job offer provided."
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


def extract_json_payload(text: str) -> dict:
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


def normalize_output(payload: dict) -> dict:
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


def invoke_bedrock(cv_text: str, job_offer_text: str | None) -> dict:
    region, model_id = read_bedrock_config()
    if not region or not model_id:
        raise ValueError("AWS_REGION and BEDROCK_MODEL_ID must be set for Bedrock")

    prompt = build_system_prompt(cv_text, job_offer_text)
    max_tokens = int(os.getenv("BEDROCK_MAX_TOKENS", "700"))

    client = new_bedrock_client(region)

    try:
        logger.info("Bedrock enabled. model_id=%s", model_id)
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
        if not response_text.strip():
            raise ValueError("Empty response text from Bedrock")

        parsed = json.loads(response_text)
        if "content" in parsed and isinstance(parsed["content"], list):
            text_parts = [p.get("text", "") for p in parsed["content"] if isinstance(p, dict)]
            llm_text = "".join(text_parts).strip()
        else:
            llm_text = response_text.strip()
        if not llm_text:
            raise ValueError("Empty LLM response text")

        extracted = extract_json_payload(llm_text)
        return normalize_output(extracted)

    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError("Bedrock error: %s" % exc) from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("Invalid Bedrock response: %s" % exc) from exc


def analyze_cv(cv_text: str, job_offer: str | dict | None = None) -> dict:
    job_offer_text = normalize_job_offer(job_offer)
    if job_offer is not None and job_offer_text is None:
        raise ValueError(
            "'job_offer' must include at least one of: title, description, requirements"
        )

    if bedrock_enabled():
        try:
            return invoke_bedrock(cv_text, job_offer_text)
        except Exception as exc:
            logger.error("Bedrock failed, falling back to mock: %s", exc)
            return mock_analysis(cv_text, job_offer_text)

    logger.info("USE_BEDROCK is false. Using mock analysis.")
    return mock_analysis(cv_text, job_offer_text)
