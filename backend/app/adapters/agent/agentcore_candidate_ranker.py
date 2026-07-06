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

# Max characters per CV sent to the LLM (prevent token overflow)
_CV_TEXT_LIMIT = 2500
# Max total candidates sent in a single prompt
_MAX_CANDIDATES_IN_PROMPT = 20


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
            prompt = self._build_prompt(
                job_offer_title, job_offer_description, required_skills,
                candidates, top_n,
            )
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

    def _build_prompt(
        self,
        title: str,
        description: str,
        required_skills: list[str],
        candidates: list[CandidateInput],
        top_n: int,
    ) -> str:
        skills_str = ", ".join(required_skills) if required_skills else "No especificadas"

        candidates_block = ""
        for i, c in enumerate(candidates[:_MAX_CANDIDATES_IN_PROMPT], start=1):
            cv_snippet = (c.cv_text or "")[:_CV_TEXT_LIMIT]
            if len(c.cv_text or "") > _CV_TEXT_LIMIT:
                cv_snippet += "\n[... CV truncado por longitud ...]"
            candidates_block += (
                f"\n--- CANDIDATO {i} ---\n"
                f"ID: {c.application_id}\n"
                f"Nombre: {c.candidate_name}\n"
                f"CV:\n{cv_snippet}\n"
            )

        prompt = (
            f"Eres un experto en selección de personal. Analiza los siguientes CVs "
            f"y devuelve un ranking de los {top_n} mejores candidatos para la oferta descrita.\n\n"
            f"OFERTA DE TRABAJO:\n"
            f"- Título: {title}\n"
            f"- Descripción: {description[:1500]}\n"
            f"- Skills requeridas: {skills_str}\n\n"
            f"CANDIDATOS (total: {len(candidates)}):\n"
            f"{candidates_block}\n"
            f"INSTRUCCIÓN:\n"
            f"Rankea los {top_n} candidatos más idóneos de mayor a menor puntuación. "
            f"Para cada uno evalúa su ajuste con la oferta y explica el motivo.\n\n"
            f"Devuelve ÚNICAMENTE el siguiente JSON, sin texto adicional antes ni después:\n"
            f"{{\n"
            f'  "ranking": [\n'
            f'    {{"application_id": "...", "candidate_name": "...", "score": 85, "reason": "..."}}\n'
            f"  ],\n"
            f'  "summary": "Resumen breve del proceso de selección"\n'
            f"}}"
        )
        return prompt

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

        # Build lookup by application_id for fast access
        cand_map = {c.application_id: c for c in candidates}

        ranked: list[RankedCandidate] = []
        for i, item in enumerate(data["ranking"][:top_n], start=1):
            app_id = str(item.get("application_id", ""))
            cand = cand_map.get(app_id)
            ranked.append(
                RankedCandidate(
                    rank=i,
                    application_id=app_id,
                    candidate_name=item.get("candidate_name") or (cand.candidate_name if cand else "Desconocido"),
                    candidate_email=cand.candidate_email if cand else "",
                    score=int(item.get("score", 0)),
                    ranking_reason=str(item.get("reason", "")),
                    cv_summary=cand.cv_analysis_summary if cand else None,
                    skills=cand.cv_analysis_technical_skills if cand else [],
                    experience=cand.cv_analysis_experience if cand else None,
                    cv_processing_status="processed",
                    cv_analysis_status=cand.cv_analysis_status if cand else "pending",
                )
            )

        summary = str(data.get("summary", "Ranking generado por el agente IA."))
        return ranked, summary

    def _try_parse_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None
