"""
Configuration management for CV Analyzer provider selection and AWS settings.

Provides centralized configuration reading from environment variables,
allowing runtime selection between SimpleCVAnalyzer and AgentCoreCVAnalyzer
without modifying code.

Environment variables:
- CV_ANALYZER_PROVIDER: "simple" (default) or "agentcore"
- AWS_REGION: AWS region (default: "eu-west-1")
- AWS_PROFILE: AWS profile name (optional)
- AWS_ACCESS_KEY_ID: AWS access key (optional)
- AWS_SECRET_ACCESS_KEY: AWS secret key (optional)
- AWS_SESSION_TOKEN: AWS session token (optional)
- AGENTCORE_RUNTIME_ID: AgentCore Runtime ID (optional)
- AGENTCORE_RUNTIME_ARN: AgentCore Runtime ARN (optional)
- AGENTCORE_AGENT_ID: Strands Agent ID (optional, default: "cv-analyzer-agent")
- BEDROCK_MODEL_ID: Bedrock model ID (optional, default: Claude Sonnet)
"""

import os
import logging
from enum import Enum

logger = logging.getLogger("config")


class CVAnalyzerProvider(str, Enum):
    """Supported CV Analyzer implementations."""
    SIMPLE = "simple"
    AGENTCORE = "agentcore"


class CVAnalyzerConfig:
    """Configuration for CV Analyzer provider selection and AWS settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Provider selection
        self.provider = self._read_provider()
        
        # AWS configuration
        self.aws_region = os.getenv("AWS_REGION", "eu-west-1")
        self.aws_profile = os.getenv("AWS_PROFILE")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")
        self.bedrock_model_id = os.getenv(
            "BEDROCK_MODEL_ID",
            "eu.anthropic.claude-sonnet-4-20250514-v1:0"
        )
        
        # AgentCore configuration (required if provider is agentcore)
        self.agentcore_runtime_id = os.getenv("AGENTCORE_RUNTIME_ID")
        self.agentcore_runtime_arn = os.getenv("AGENTCORE_RUNTIME_ARN")
        self.agentcore_agent_id = os.getenv("AGENTCORE_AGENT_ID", "cv-analyzer-agent")
        
        self._validate_configuration()

    def _read_provider(self) -> CVAnalyzerProvider:
        """Read and validate CV_ANALYZER_PROVIDER environment variable.
        
        Returns:
            CVAnalyzerProvider.SIMPLE by default
            CVAnalyzerProvider.AGENTCORE if explicitly set
            
        Raises:
            ValueError: If CV_ANALYZER_PROVIDER has an invalid value
        """
        provider_str = os.getenv("CV_ANALYZER_PROVIDER", "simple").lower()
        
        try:
            return CVAnalyzerProvider(provider_str)
        except ValueError:
            raise ValueError(
                f"Invalid CV_ANALYZER_PROVIDER='{provider_str}'. "
                f"Valid values: {', '.join([p.value for p in CVAnalyzerProvider])}"
            )

    def _validate_configuration(self) -> None:
        """Validate that configuration is consistent.
        
        Auto-fallback: If AgentCore is requested but AWS credentials are missing,
        automatically fall back to SimpleCVAnalyzer. This allows:
        - Development without AWS (no credentials needed)
        - Graceful degradation if AWS is unavailable
        - Same code path for development and production
        """
        if self.provider == CVAnalyzerProvider.AGENTCORE:
            # AgentCore mode requires at least runtime_id or runtime_arn
            if not (self.agentcore_runtime_id or self.agentcore_runtime_arn):
                logger.warning(
                    "CV_ANALYZER_PROVIDER=agentcore but no AGENTCORE_RUNTIME_ID or "
                    "AGENTCORE_RUNTIME_ARN provided. Auto-falling back to SimpleCVAnalyzer. "
                    "(Set AGENTCORE_RUNTIME_ID for production AgentCore deployment)"
                )
                # Auto-fallback to SimpleCVAnalyzer
                self.provider = CVAnalyzerProvider.SIMPLE
            else:
                logger.info(
                    f"AgentCore configuration: "
                    f"runtime_id={self.agentcore_runtime_id}, "
                    f"agent_id={self.agentcore_agent_id}, "
                    f"region={self.aws_region}"
                )
        
        if self.provider == CVAnalyzerProvider.SIMPLE:
            logger.info("Using SimpleCVAnalyzer (local, no external dependencies)")

    def is_agentcore_enabled(self) -> bool:
        """Check if AgentCore provider is enabled.
        
        Returns:
            True if provider is agentcore, False otherwise
        """
        return self.provider == CVAnalyzerProvider.AGENTCORE

    def is_simple_analyzer(self) -> bool:
        """Check if SimpleCVAnalyzer is enabled.
        
        Returns:
            True if provider is simple, False otherwise
        """
        return self.provider == CVAnalyzerProvider.SIMPLE

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"CVAnalyzerConfig(provider={self.provider.value}, "
            f"aws_region={self.aws_region}, "
            f"bedrock_model_id={self.bedrock_model_id})"
        )


# Global configuration instance (loaded once at startup)
_config = None


def get_cv_analyzer_config() -> CVAnalyzerConfig:
    """Get or create the global CV Analyzer configuration.
    
    The configuration is loaded once on first access and cached.
    Subsequent calls return the same instance.
    
    Returns:
        CVAnalyzerConfig instance
    """
    global _config
    if _config is None:
        _config = CVAnalyzerConfig()
    return _config


def reset_config() -> None:
    """Reset the global configuration (useful for testing).
    
    This forces the next call to get_cv_analyzer_config() to reload
    environment variables.
    """
    global _config
    _config = None
