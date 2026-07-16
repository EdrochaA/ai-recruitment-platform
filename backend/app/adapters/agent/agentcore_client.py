"""
AgentCore Client module.

Encapsulates communication with AWS Bedrock AgentCore for CV analysis.
This module provides the integration point between the domain (CVAnalyzer port)
and the external AWS AgentCore runtime.

Currently implements a stub/mock to facilitate local development.
The stub will be replaced with actual AgentCore API calls in production.
"""

import json
import logging
import os
import re
import time
import uuid
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger("agentcore-client")


class AgentCoreClient:
    """Client for invoking AgentCore runtime for CV analysis.

    Encapsulates the communication logic with AWS Bedrock AgentCore.
    Provides a single integration point for AgentCore-specific functionality,
    keeping the adapter (AgentCoreCVAnalyzer) clean and focused on transforming
    requests/responses.

    The actual implementation depends on deployment mode:
    - Development/Local: Mock implementation (current)
    - Production: Real AgentCore runtime invocation via boto3

    Structure follows the pattern from cc-swp-blueprint-agent-memory:
    - runtime_id: AgentCore Runtime identifier
    - agent_id: Strands Agent identifier within the runtime
    - model integration: Bedrock model configuration
    """

    def __init__(
        self,
        runtime_id: Optional[str] = None,
        runtime_arn: Optional[str] = None,
        agent_id: Optional[str] = None,
        region: str = "eu-west-1",
        model_id: str = "eu.anthropic.claude-sonnet-4-20250514-v1:0",
    ):
        """Initialize AgentCore client.

        Args:
            runtime_id: AgentCore Runtime ID (format: alphanumeric dash, e.g., "cv-analyzer-xyz")
            runtime_arn: Full ARN of AgentCore Runtime (alternative to runtime_id)
            agent_id: Strands Agent ID within the runtime (e.g., "cv-analyzer-agent-v1")
            region: AWS region where AgentCore is deployed
            model_id: Bedrock model ID (e.g., Claude Sonnet)

        Note:
            Either runtime_id or runtime_arn must be provided (not both).
            If neither is provided, client assumes local/mock mode.
        """
        self.runtime_id = runtime_id
        self.runtime_arn = runtime_arn
        self.agent_id = agent_id or "cv-analyzer-agent"
        self.region = region
        self.model_id = model_id

        # Track if client is in mock mode (no real AgentCore configured)
        self.is_mock_mode = not (runtime_id or runtime_arn)

        if self.is_mock_mode:
            logger.warning(
                "AgentCoreClient initialized in MOCK mode (no runtime_id or runtime_arn provided). "
                "This is suitable for development only. CV analysis will use simulated results."
            )
        else:
            logger.info(
                "AgentCoreClient initialized for AgentCore runtime. "
                "Region: %s, Agent: %s, Model: %s",
                self.region,
                self.agent_id,
                self.model_id,
            )

    def invoke_cv_analysis(
        self,
        cv_text: str,
        job_description: str,
        application_id: str,
        job_offer_id: str,
        prompt: str,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> dict:
        """Invoke CV analysis via AgentCore.

        Calls the AgentCore runtime with CV text and job description,
        returning structured analysis results.

        Args:
            cv_text: Extracted text from candidate's CV
            job_description: Description of the job opening
            session_id: Optional session identifier for conversation continuity
            actor_id: Optional actor/user identifier for authorization

        Returns:
            Dictionary with normalized structure:
            {
                "candidate_name": str,
                "professional_summary": str,
                "education": list[str],
                "work_experience": list[str],
                "technical_skills": list[str],
                "soft_skills": list[str],
                "languages": list[str],
                "certifications": list[str],
                "warnings": list[str]
            }

        Raises:
            ValueError: If response is invalid or missing required fields
        """
        try:
            if self.is_mock_mode:
                logger.info("AgentCore provider is mock. Using mock analyzer.")
                return self._mock_invoke(cv_text)
            else:
                # Production: Call real AgentCore runtime
                # This will be implemented in the next iteration
                return self._real_invoke(
                    cv_text=cv_text,
                    job_description=job_description,
                    application_id=application_id,
                    job_offer_id=job_offer_id,
                    prompt=prompt,
                    session_id=session_id,
                    actor_id=actor_id,
                )

        except Exception as e:
            logger.error("Failed to invoke AgentCore CV analysis: %s", e)
            raise ValueError(f"AgentCore invocation failed: {e}")

    def _mock_invoke(self, cv_text: str) -> dict:
        """Mock/stub implementation for local development.

        This serves as a placeholder showing the expected response structure,
        allowing integration testing without AWS AgentCore infrastructure.

        In production, this will be replaced by actual AgentCore runtime calls
        using the bedrock_agentcore SDK and AWS credentials.
        """
        logger.info("Using mock AgentCore implementation for CV analysis")

        return {
            "candidate_name": "",
            "professional_summary": "",
            "education": [],
            "work_experience": [],
            "technical_skills": [],
            "soft_skills": [],
            "languages": [],
            "certifications": [],
            "warnings": ["Mock response; no structured extraction performed"],
        }

    def _real_invoke(
        self,
        cv_text: str,
        job_description: str,
        application_id: str,
        job_offer_id: str,
        prompt: str,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> dict:
        """Real invocation against AgentCore runtime using boto3.

        This implements actual communication with AWS Bedrock AgentCore runtime.
        Follows the AWS InvokeAgentRuntime flow:

        Flow:
        1. Build system prompt asking for CV analysis
        2. Create session ID if not provided
        3. Invoke AgentCore runtime via boto3 (bedrock-agentcore)
        4. Parse and extract JSON from LLM response
        5. Validate and normalize response structure
        6. Return structured analysis data

        Args:
            cv_text: Extracted CV text
            job_description: Job description
            session_id: Session identifier (optional, generated if not provided)
            actor_id: Actor/user identifier (optional, defaults to "analyzer")

        Returns:
            Normalized response dict:
            {
                "candidate_name": str,
                "professional_summary": str,
                "education": list[str],
                "work_experience": list[str],
                "technical_skills": list[str],
                "soft_skills": list[str],
                "languages": list[str],
                "certifications": list[str],
                "warnings": list[str]
            }

        Raises:
            ValueError: If response validation fails or AgentCore returns error
            BotoCoreError: If AWS API call fails
        """
        # Use provided values or generate defaults
        session_id = session_id or self._generate_session_id()
        actor_id = actor_id or "cv-analyzer"

        start_time = time.time()

        try:
            logger.info(
                "Invoking AgentCore runtime. session_id=%s, actor_id=%s, cv_text_len=%s, job_desc_len=%s",
                session_id,
                actor_id,
                len(cv_text),
                len(job_description),
            )

            # Prepare payload for AgentCore
            payload = {
                "prompt": prompt,
                "application_id": application_id,
                "job_offer_id": job_offer_id,
                "cv_text": cv_text,
            }

            # Invoke AgentCore runtime
            response_data = self._invoke_agentcore_runtime(
                payload=payload,
                session_id=session_id,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info("AgentCore runtime responded in %sms", elapsed_ms)

            # Extract and parse the agent's response
            agent_response = self._extract_agent_response(response_data)

            # Parse JSON from response
            parsed_json = self._parse_json_response(agent_response)

            # Validate and normalize
            normalized = self._validate_and_normalize_response(parsed_json)

            logger.info(
                "AgentCore analysis completed successfully. warnings=%s",
                len(normalized["warnings"]),
            )

            return normalized

        except ValueError as e:
            logger.error("AgentCore response validation failed: %s", e)
            raise

        except (ClientError, BotoCoreError) as e:
            logger.error("AWS API error during AgentCore invocation: %s", e)
            raise ValueError(f"AgentCore API call failed: {e}") from e

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "Unexpected error during AgentCore invocation (%sms): %s",
                elapsed_ms,
                e,
            )
            raise ValueError(f"AgentCore invocation failed: {e}") from e

    def _generate_session_id(self) -> str:
        """Generate a session ID for AgentCore invocation."""
        timestamp = int(time.time() * 1000)
        unique_id = uuid.uuid4().hex[:8]
        return f"cv-analysis-{timestamp}-{unique_id}"

    def _invoke_agentcore_runtime(self, payload: dict, session_id: str) -> dict:
        """Invoke the AgentCore runtime via boto3.

        Uses the bedrock-agentcore service to send the payload
        to the configured runtime.

        Args:
            payload: Request payload (prompt, actor_id)
            session_id: Session identifier

        Returns:
            Response from AgentCore runtime

        Raises:
            ValueError: If runtime_id or runtime_arn not configured
            ClientError: If AWS API call fails
        """
        if not self.runtime_arn and not self.runtime_id:
            raise ValueError(
                "AgentCore runtime not configured. "
                "Provide either runtime_arn or runtime_id."
            )

        # Use runtime_arn if available, otherwise fall back to runtime_id
        runtime_identifier = self.runtime_arn or self.runtime_id
        if not runtime_identifier or not str(runtime_identifier).startswith("arn:"):
            raise ValueError(
                "InvokeAgentRuntime requires an Agent Runtime ARN. "
                "Set AGENTCORE_RUNTIME_ARN (or provide an ARN in runtime_id)."
            )

        try:
            timeout_seconds = int(
                os.getenv("AGENTCORE_RUNTIME_TIMEOUT_SECONDS", "30")
            )
            config = Config(read_timeout=timeout_seconds, connect_timeout=10)
            # Initialize bedrock-agentcore client (InvokeAgentRuntime)
            client = boto3.client(
                "bedrock-agentcore",
                region_name=self.region,
                config=config,
            )

            logger.info(
                "Invoking bedrock-agentcore. runtime_arn=%s, session_id=%s",
                runtime_identifier,
                session_id,
            )

            # Build the request payload (binary)
            payload_bytes = json.dumps(payload).encode("utf-8")

            # Send request to AgentCore runtime
            response = client.invoke_agent_runtime(
                agentRuntimeArn=runtime_identifier,
                runtimeSessionId=session_id,
                payload=payload_bytes,
            )

            logger.debug(
                "AgentCore runtime response status: %s",
                response.get("ResponseMetadata", {}).get("HTTPStatusCode"),
            )
            if not response:
                raise ValueError("Empty response from AgentCore runtime")

            return response

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error("AWS ClientError [%s]: %s", error_code, error_msg)
            raise

        except BotoCoreError as e:
            logger.error("AWS BotoCoreError: %s", e)
            raise

    def _extract_agent_response(self, response_data: dict) -> str:
        """Extract the text response from AgentCore runtime response.

        AgentCore may return response in different formats depending on streaming
        and response structure. This method extracts the actual agent output text.

        Args:
            response_data: Response from bedrock-agentcore InvokeAgentRuntime call

        Returns:
            The agent's response text

        Raises:
            ValueError: If response structure is unexpected
        """
        try:
            # InvokeAgentRuntime returns contentType and a streaming body in "response"
            content_type = response_data.get("contentType", "")
            if "response" in response_data:
                body = response_data["response"]
                content = None

                if hasattr(body, "iter_lines"):
                    # Handle event stream responses
                    chunks = []
                    for line in body.iter_lines(chunk_size=10):
                        if not line:
                            continue
                        text_line = line.decode("utf-8")
                        if text_line.startswith("data: "):
                            text_line = text_line[6:]
                        chunks.append(text_line)
                    content = "".join(chunks)
                elif hasattr(body, "read"):
                    content = body.read().decode("utf-8")

                if content is not None:
                    content = content.strip()
                    if "application/json" in content_type:
                        return content
                    if content.startswith("{"):
                        return content
                    return content

            # Legacy/alternate response shapes
            if "output" in response_data:
                return response_data["output"]

            if "text" in response_data:
                return response_data["text"]

            if "messages" in response_data and isinstance(
                response_data["messages"],
                list,
            ):
                if response_data["messages"]:
                    msg = response_data["messages"][-1]
                    if isinstance(msg, dict) and "content" in msg:
                        return msg["content"]

            logger.error(
                "Unexpected AgentCore response structure: %s",
                list(response_data.keys()),
            )
            raise ValueError(
                "AgentCore response has unexpected structure. "
                "Cannot extract agent output."
            )

        except Exception as e:
            logger.error("Error extracting agent response: %s", e)
            raise ValueError(f"Failed to extract agent response: {e}") from e

    def _parse_json_response(self, response_text: str) -> dict:
        """Extract and parse JSON from agent response.

        The LLM may return:
        - Pure JSON object
        - JSON wrapped in markdown code blocks
        - JSON embedded in text

        This method attempts to robustly extract and parse the JSON.

        Args:
            response_text: Raw response text from agent

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If no valid JSON can be extracted or parsed
        """
        if not response_text or not isinstance(response_text, str):
            raise ValueError("Response text is empty or not a string")

        response_text = response_text.strip()

        # Try direct JSON parse first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.debug("Direct JSON parse failed, attempting extraction...")

        # Try to extract JSON from markdown code blocks
        markdown_patterns = [
            r"```json\s*(\{.*?\})\s*```",
            r"```\s*(\{.*?\})\s*```",
        ]

        for pattern in markdown_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                json_str = match.group(1)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.debug(
                        "Failed to parse extracted JSON: %s",
                        json_str[:100],
                    )

        # Try to find JSON object in text using braces
        brace_start = response_text.find("{")
        brace_end = response_text.rfind("}")

        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            json_candidate = response_text[brace_start : brace_end + 1]
            try:
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                logger.debug(
                    "Failed to parse JSON from braces: %s",
                    json_candidate[:100],
                )

        # If all else fails, raise error with context
        logger.error("Could not parse JSON from response: %s", response_text[:200])
        raise ValueError(
            f"AgentCore response does not contain valid JSON. "
            f"Response start: {response_text[:100]}"
        )

    def _validate_and_normalize_response(self, parsed_json: dict) -> dict:
        """Validate that response contains required fields and normalize format.

        Ensures the response has all required fields with correct types
        and reasonable values.

        Args:
            parsed_json: Parsed JSON response from agent

        Returns:
            Normalized response dict with validated fields

        Raises:
            ValueError: If required fields missing or invalid
        """
        required_fields = {
            "candidate_name",
            "professional_summary",
            "education",
            "work_experience",
            "technical_skills",
            "soft_skills",
            "languages",
            "certifications",
            "warnings",
        }

        # Check for required fields
        missing_fields = required_fields - set(parsed_json.keys())
        if missing_fields:
            raise ValueError(
                f"AgentCore response missing required fields: {missing_fields}. "
                f"Response: {parsed_json}"
            )

        # Normalize and validate each field
        try:
            candidate_name = str(parsed_json.get("candidate_name", "")).strip()
            professional_summary = str(
                parsed_json.get("professional_summary", "")
            ).strip()

            list_fields = [
                "education",
                "work_experience",
                "technical_skills",
                "soft_skills",
                "languages",
                "certifications",
                "warnings",
            ]
            normalized_lists = {}
            for field in list_fields:
                value = parsed_json.get(field, [])
                if isinstance(value, str):
                    value = [v.strip() for v in value.split(",") if v.strip()]
                if not isinstance(value, list):
                    raise ValueError(f"{field} must be list, got {type(value)}")
                normalized_lists[field] = [
                    str(v).strip()
                    for v in value
                    if str(v).strip()
                ]

            normalized = {
                "candidate_name": candidate_name,
                "professional_summary": professional_summary,
                **normalized_lists,
            }

            logger.debug("Normalized response: %s", normalized)
            return normalized

        except Exception as e:
            logger.error("Error normalizing response: %s", e)
            raise ValueError(f"Failed to normalize AgentCore response: {e}") from e
