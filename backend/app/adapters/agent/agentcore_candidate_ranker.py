"""
Adapter: AgentCoreCandidateRanker

Delegates candidate ranking to the AgentCore LLM runtime.

Flow:
  1. Build a structured prompt with the job offer + all CV texts.
  2. Call the AgentCore runtime (same mechanism as AgentCoreChatbotService).
  3. Parse the JSON response produced by the LLM.
  4. Return RankedCandidate list.

Falls back to KeywordCandidateRanker on any failure when fallback is provided.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.domain.ports.candidate_ranker import (
    CandidateInput,
    CandidateRankerPort,
    RankedCandidate,
)

logger = logging.getLogger("agentcore-candidate-ranker")


class AgentCoreCandidateRanker(CandidateRankerPort):
    """Ranks candidates using the AgentCore LLM runtime."""

    def __init__(
        self,
        runtime_arn: str,
        region: str,
        timeout_seconds: int = 60,
        fallback: CandidateRankerPort | None = None,
    ) -> None:
        self.runtime_arn = runtime_arn
        self.region = region
        self.timeout_seconds = timeout_seconds
        self.fallback = fallback
        logger.info(
            "AgentCoreCandidateRanker ready — runtime_arn=%s region=%s",
            runtime_arn,
            region,
        )

    # ── Port implementation ────────────────────────────────────────────────

    def rank(
        self,
        job_offer_title: str,
        job_offer_description: str,
        required_skills: list[str],
        candidates: list[CandidateInput],
        top_n: int,
    ) -> tuple[list[RankedCandidate], str]:
        try:
            prompt = self._build_prompt(job_offer_title, top_n)
            raw_response = self._invoke_runtime(prompt)
            ranked, summary = self._parse_response(raw_response, candidates, top_n)
            logger.info(
                "AgentCore ranking complete — offer='%s' candidates=%d top=%d",
                job_offer_title, len(candidates), len(ranked),
            )
            return ranked, summary

        except Exception as exc:
            logger.exception(
                "AgentCore ranking failed for offer='%s': %s", job_offer_title, exc
            )
            if self.fallback:
                logger.warning("Falling back to KeywordCandidateRanker")
                return self.fallback.rank(
                    job_offer_title, job_offer_description, required_skills,
                    candidates, top_n,
                )
            raise RuntimeError(
                f"AgentCore ranking unavailable: {exc}"
            ) from exc

    # ── Prompt builder ─────────────────────────────────────────────────────

    def _build_prompt(self, title: str, top_n: int) -> str:
        """Build a short delegation prompt so the agent uses its own tools."""
        return (
            f"Usa tus tools para obtener los detalles de la oferta '{title}' y todas sus "
            f"candidaturas. Considera evaluable únicamente una candidatura cuyo campo "
            f"cv_text contenga texto no vacío. No puntúes ni incluyas en el ranking a "
            f"candidatos sin CV subido o cuyo CV no tenga texto extraíble.\n\n"
            f"Cuenta primero el total de candidaturas y cuántas son evaluables. Después "
            f"rankea únicamente las evaluables según el ajuste de su CV con los requisitos "
            f"de la oferta. Devuelve hasta min({top_n}, evaluable_candidates) resultados. "
            f"Si existen al menos {top_n} candidatos evaluables, devuelve exactamente "
            f"{top_n}. Los candidatos no evaluables no deben consumir plazas del top.\n\n"
            f"Devuelve ÚNICAMENTE el siguiente JSON, sin texto adicional antes ni después:\n"
            f'{{"total_candidates": 0, "evaluable_candidates": 0, '
            f'"ranking": [{{"application_id": "...", "candidate_name": "...", '
            f'"score": 85, "reason": "Motivo detallado"}}], '
            f'"summary": "Resumen breve del proceso de selección"}}'
        )

    # ── Runtime call ───────────────────────────────────────────────────────

    def _invoke_runtime(self, prompt: str) -> str:
        config = Config(
            read_timeout=self.timeout_seconds,
            connect_timeout=10,
        )
        client = boto3.client(
            "bedrock-agentcore",
            region_name=self.region,
            config=config,
        )
        session_id = self._build_session_id()
        payload = json.dumps({"prompt": prompt, "actor_id": "ranking-system"})

        logger.info(
            "Invoking AgentCore ranking — session=%s prompt_len=%d",
            session_id, len(prompt),
        )

        response = client.invoke_agent_runtime(
            agentRuntimeArn=self.runtime_arn,
            runtimeSessionId=session_id,
            payload=payload.encode("utf-8"),
        )
        return self._extract_text(response)

    def _extract_text(self, response: dict[str, Any]) -> str:
        if "response" in response:
            body = response["response"]
            if hasattr(body, "read"):
                return body.read().decode("utf-8")
            if hasattr(body, "iter_lines"):
                chunks = []
                for line in body.iter_lines(chunk_size=10):
                    if not line:
                        continue
                    text = line.decode("utf-8")
                    if text.startswith("data: "):
                        text = text[6:]
                    chunks.append(text)
                return "".join(chunks)
        for key in ("output", "text"):
            if key in response:
                return str(response[key])
        return ""

    def _build_session_id(self) -> str:
        ts = str(int(time.time() * 1000))
        return f"ranking-session-system00000000-{ts}"

    # ── Response parser ────────────────────────────────────────────────────

    def _parse_response(
        self,
        raw: str,
        candidates: list[CandidateInput],
        top_n: int,
    ) -> tuple[list[RankedCandidate], str]:
        """Parse LLM JSON response into RankedCandidate list."""
        raw = raw.strip()
        data = self._try_parse_json(raw)

        if not isinstance(data, dict) or "ranking" not in data:
            logger.warning(
                "Unexpected LLM response format, raw preview: %s", raw[:300]
            )
            raise ValueError("LLM response did not contain expected 'ranking' key")

        # CandidateInput is the backend-authoritative set with usable CV text.
        cand_map = {c.application_id: c for c in candidates}

        ranking_items = data["ranking"]
        if not isinstance(ranking_items, list):
            raise ValueError("LLM response 'ranking' value was not a list")

        ranked: list[RankedCandidate] = []
        seen_application_ids: set[str] = set()
        for item in ranking_items:
            if len(ranked) >= top_n:
                break
            if not isinstance(item, dict):
                logger.warning("Ignoring non-object LLM ranking item: %r", item)
                continue

            app_id = str(item.get("application_id", ""))
            cand = cand_map.get(app_id)
            if not cand:
                logger.warning(
                    "Ignoring non-evaluable or unknown candidate returned by LLM: %r",
                    app_id,
                )
                continue
            if app_id in seen_application_ids:
                logger.warning("Ignoring duplicate candidate returned by LLM: %r", app_id)
                continue

            seen_application_ids.add(app_id)
            ranked.append(
                RankedCandidate(
                    rank=len(ranked) + 1,
                    application_id=app_id,
                    candidate_name=cand.candidate_name,
                    candidate_email=cand.candidate_email,
                    score=int(item.get("score", 0)),
                    ranking_reason=str(item.get("reason", "")),
                    cv_summary=cand.cv_analysis_summary,
                    skills=cand.cv_analysis_technical_skills,
                    experience=cand.cv_analysis_experience,
                    cv_processing_status="processed",
                    cv_analysis_status=cand.cv_analysis_status,
                )
            )

        summary = str(data.get("summary", "Ranking generado por el agente IA."))
        return ranked, summary

    def _try_parse_json(self, text: str) -> Any:
        candidate = text.strip()

        if candidate.startswith("```") and candidate.endswith("```"):
            opening_line_end = candidate.find("\n")
            if opening_line_end != -1:
                fence_language = candidate[3:opening_line_end].strip().lower()
                if fence_language in {"", "json"}:
                    candidate = candidate[opening_line_end + 1:-3].strip()

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Could not parse complete LLM response as JSON: %s",
                exc,
            )

        start, end = candidate.find("{"), candidate.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(candidate[start:end + 1])
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Could not parse extracted LLM JSON object: %s",
                    exc,
                )

        return None
