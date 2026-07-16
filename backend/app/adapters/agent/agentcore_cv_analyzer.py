"""
AgentCore-based CV Analyzer adapter.

Implements the CVAnalyzer port using AWS Bedrock AgentCore runtime.

This adapter demonstrates how to integrate an external LLM-powered service
while maintaining clean architecture separation:
- Domain: CVAnalyzer port (interface only, no AWS dependencies)
- Application: AnalyzeApplicationCV (orchestration, no AWS dependencies)
- Adapter: AgentCoreCVAnalyzer (AWS-specific implementation)
"""

from datetime import datetime
import logging
from typing import Optional

from app.adapters.agent.agentcore_client import AgentCoreClient
from app.domain.entities.cv_analysis import CVAnalysisResult
from app.domain.ports.cv_analyzer import CVAnalyzer

logger = logging.getLogger("agentcore-analyzer")


class AgentCoreCVAnalyzer(CVAnalyzer):
    """CV Analyzer implementation using AWS Bedrock AgentCore.

    Delegates CV analysis to an AgentCore-hosted Strands agent powered by
    a Bedrock LLM (Claude Sonnet or similar).

    This adapter:
    - Remains a black-box "CVAnalyzer" to the domain and application layers
    - Handles all AWS-specific communication via AgentCoreClient
    - Transforms AgentCore responses into CVAnalysisResult domain objects
    - Validates response structure and handles errors gracefully

    Configuration is injected at construction, making the adapter testable
    and swappable without modifying domain or application code.

    Examples:
        # Development (mock mode, no AWS credentials needed)
        analyzer = AgentCoreCVAnalyzer()
        result = analyzer.analyze(cv_text, job_description)

        # Production (with AgentCore credentials)
        analyzer = AgentCoreCVAnalyzer(
            runtime_id="cv-analyzer-xyz",
            agent_id="cv-analyzer-agent-v1",
            region="eu-west-1",
        )
        result = analyzer.analyze(cv_text, job_description, session_id="sess_123")
    """

    # Required fields in AgentCore response
    REQUIRED_RESPONSE_FIELDS = {
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

    def __init__(
        self,
        runtime_id: Optional[str] = None,
        runtime_arn: Optional[str] = None,
        agent_id: str = "cv-analyzer-agent",
        region: str = "eu-west-1",
        model_id: str = "eu.anthropic.claude-sonnet-4-20250514-v1:0",
    ):
        """Initialize AgentCore-based CV analyzer.

        Args:
            runtime_id: AgentCore Runtime ID (optional, mock mode if absent)
            runtime_arn: AgentCore Runtime ARN (optional, mock mode if absent)
            agent_id: Strands Agent ID within the runtime
            region: AWS region for AgentCore deployment
            model_id: Bedrock model ID (Claude Sonnet recommended for analysis)

        Note:
            If neither runtime_id nor runtime_arn is provided, the analyzer
            operates in mock mode using simulated analysis for development.
        """
        self.client = AgentCoreClient(
            runtime_id=runtime_id,
            runtime_arn=runtime_arn,
            agent_id=agent_id,
            region=region,
            model_id=model_id,
        )
        self.region = region
        self.agent_id = agent_id

        logger.info(
            "AgentCoreCVAnalyzer initialized. Mode: %s",
            "mock" if self.client.is_mock_mode else "production",
        )

    def analyze(
        self,
        cv_text: str,
        job_description: str,
        application_id: str,
        job_offer_id: str,
        prompt: str,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> CVAnalysisResult:
        """Analyze CV using AgentCore.

        Sends the CV text and job description to AgentCore runtime,
        which uses a Bedrock LLM to perform intelligent analysis.

        Args:
            cv_text: Extracted text from candidate's CV
            job_description: Description of the job opening
            session_id: Optional session ID for conversation continuity
                       (useful if AgentCore memory is enabled)
            actor_id: Optional actor/user ID for authorization

        Returns:
            CVAnalysisResult with skills, score, summary and analyzed timestamp

        Raises:
            ValueError: If AgentCore response is invalid or missing required fields
        """
        try:
            logger.info("Invoking AgentCore analysis for CV (%s chars)", len(cv_text))

            # Call AgentCore via the client
            response = self.client.invoke_cv_analysis(
                cv_text=cv_text,
                job_description=job_description,
                application_id=application_id,
                job_offer_id=job_offer_id,
                prompt=prompt,
                session_id=session_id,
                actor_id=actor_id,
            )

            # Validate response structure
            self._validate_response(response)

            # Transform to domain model
            result = self._transform_response(response)

            logger.info(
                "AgentCore analysis complete: warnings=%s",
                len(result.warnings),
            )

            return result

        except ValueError as e:
            # Validation or transformation error
            logger.error("AgentCore response validation failed: %s", e)
            raise

        except Exception as e:
            # Unexpected error
            logger.error("Unexpected error during AgentCore analysis: %s", e)
            raise ValueError(f"AgentCore analysis failed: {e}")

    def _validate_response(self, response: dict) -> None:
        """Validate that AgentCore response contains required fields.

        Args:
            response: Response dict from AgentCore

        Raises:
            ValueError: If response is missing required fields or has invalid types
        """
        if not isinstance(response, dict):
            raise ValueError(f"Expected dict response, got {type(response).__name__}")

        # Check required fields
        missing_fields = self.REQUIRED_RESPONSE_FIELDS - set(response.keys())
        if missing_fields:
            raise ValueError(
                f"AgentCore response missing required fields: {missing_fields}"
            )
        
        if not isinstance(response["candidate_name"], str):
            raise ValueError("'candidate_name' must be a string")
        if not isinstance(response["professional_summary"], str):
            raise ValueError("'professional_summary' must be a string")

        list_fields = [
            "education",
            "work_experience",
            "technical_skills",
            "soft_skills",
            "languages",
            "certifications",
            "warnings",
        ]
        for field in list_fields:
            if not isinstance(response[field], list):
                raise ValueError(f"'{field}' must be a list")
            if not all(isinstance(item, str) for item in response[field]):
                raise ValueError(f"'{field}' must be a list of strings")

    def _transform_response(self, response: dict) -> CVAnalysisResult:
        """Transform AgentCore response to domain model.

        Args:
            response: Validated AgentCore response dict

        Returns:
            CVAnalysisResult domain object
        """
        return CVAnalysisResult(
            candidate_name=response["candidate_name"],
            professional_summary=response["professional_summary"],
            education=response["education"],
            work_experience=response["work_experience"],
            technical_skills=response["technical_skills"],
            soft_skills=response["soft_skills"],
            languages=response["languages"],
            certifications=response["certifications"],
            warnings=response["warnings"],
            analyzed_at=datetime.now(),
        )
