import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime
from app.adapters.agent.agentcore_client import AgentCoreClient
from app.adapters.agent.agentcore_cv_analyzer import AgentCoreCVAnalyzer
from app.domain.entities.cv_analysis import CVAnalysisResult
from app.shared.config import CVAnalyzerConfig, get_cv_analyzer_config, reset_config


class TestAgentCoreClient:
    """Test suite for AgentCoreClient."""

    def test_client_init_mock_mode(self):
        """Test that client initializes in mock mode when no runtime configured."""
        client = AgentCoreClient()
        assert client.is_mock_mode is True
        assert client.runtime_id is None
        assert client.runtime_arn is None

    def test_client_init_production_mode_with_runtime_id(self):
        """Test that client initializes in production mode with runtime_id."""
        client = AgentCoreClient(runtime_id="runtime-xyz123")
        assert client.is_mock_mode is False
        assert client.runtime_id == "runtime-xyz123"

    def test_client_invoke_mock_returns_valid_structure(self):
        """Test that mock invocation returns properly structured response."""
        client = AgentCoreClient()
        response = client.invoke_cv_analysis(
            cv_text="Python developer with 5 years experience",
            job_description="Looking for Python and FastAPI developer"
        )

        assert isinstance(response, dict)
        assert "skills" in response
        assert "experience_summary" in response
        assert "score" in response
        assert "summary" in response

        assert isinstance(response["skills"], list)
        assert isinstance(response["experience_summary"], str)
        assert isinstance(response["score"], int)
        assert 0 <= response["score"] <= 100
        assert isinstance(response["summary"], str)

    def test_client_real_invoke_not_implemented(self):
        """Test that real invocation raises NotImplementedError."""
        client = AgentCoreClient(runtime_id="runtime-xyz")
        
        with pytest.raises(NotImplementedError):
            client.invoke_cv_analysis(
                cv_text="Some CV",
                job_description="Some job"
            )


class TestAgentCoreCVAnalyzer:
    """Test suite for AgentCoreCVAnalyzer adapter."""

    def test_analyzer_init_default(self):
        """Test analyzer initialization with defaults."""
        analyzer = AgentCoreCVAnalyzer()
        assert analyzer.client.is_mock_mode is True

    def test_analyzer_successful_analysis(self):
        """Test successful CV analysis with mock client."""
        analyzer = AgentCoreCVAnalyzer()
        
        result = analyzer.analyze(
            cv_text="Python FastAPI PostgreSQL Docker AWS",
            job_description="Looking for Python developer with FastAPI and Docker"
        )

        assert isinstance(result, CVAnalysisResult)
        assert isinstance(result.skills, list)
        assert isinstance(result.experience_summary, str)
        assert isinstance(result.score, int)
        assert 0 <= result.score <= 100
        assert isinstance(result.summary, str)
        assert isinstance(result.analyzed_at, datetime)

    def test_analyzer_validates_response_missing_skills(self):
        """Test that analyzer validates missing 'skills' field."""
        analyzer = AgentCoreCVAnalyzer()
        
        with patch.object(
            analyzer.client,
            "invoke_cv_analysis",
            return_value={"experience_summary": "test", "score": 50, "summary": "test"}
        ):
            with pytest.raises(ValueError, match="missing required fields"):
                analyzer.analyze("cv", "job")

    def test_analyzer_validates_response_invalid_score(self):
        """Test that analyzer validates score is 0-100."""
        analyzer = AgentCoreCVAnalyzer()
        
        with patch.object(
            analyzer.client,
            "invoke_cv_analysis",
            return_value={
                "skills": ["python"],
                "experience_summary": "test",
                "score": 150,  # Invalid: > 100
                "summary": "test"
            }
        ):
            with pytest.raises(ValueError, match="must be an integer between 0-100"):
                analyzer.analyze("cv", "job")

    def test_analyzer_validates_response_invalid_skills_type(self):
        """Test that analyzer validates skills is list of strings."""
        analyzer = AgentCoreCVAnalyzer()
        
        with patch.object(
            analyzer.client,
            "invoke_cv_analysis",
            return_value={
                "skills": "python",  # Invalid: should be list
                "experience_summary": "test",
                "score": 50,
                "summary": "test"
            }
        ):
            with pytest.raises(ValueError, match="must be a list"):
                analyzer.analyze("cv", "job")

    def test_analyzer_transforms_response_correctly(self):
        """Test that analyzer correctly transforms AgentCore response to domain model."""
        analyzer = AgentCoreCVAnalyzer()
        
        mock_response = {
            "skills": ["python", "fastapi", "docker"],
            "experience_summary": "5 years as senior developer",
            "score": 85,
            "summary": "Excellent match for the position"
        }
        
        with patch.object(analyzer.client, "invoke_cv_analysis", return_value=mock_response):
            result = analyzer.analyze("cv", "job")
        
        assert result.skills == ["python", "fastapi", "docker"]
        assert result.experience_summary == "5 years as senior developer"
        assert result.score == 85
        assert result.summary == "Excellent match for the position"

    def test_analyzer_handles_client_errors(self):
        """Test that analyzer handles errors from client gracefully."""
        analyzer = AgentCoreCVAnalyzer()
        
        with patch.object(
            analyzer.client,
            "invoke_cv_analysis",
            side_effect=ValueError("Client error")
        ):
            with pytest.raises(ValueError):
                analyzer.analyze("cv", "job")


class TestCVAnalyzerConfig:
    """Test suite for CV Analyzer configuration."""

    def teardown_method(self):
        """Reset configuration after each test."""
        reset_config()
        # Clear environment variables
        for key in ["CV_ANALYZER_PROVIDER", "AWS_REGION", "AGENTCORE_RUNTIME_ID", 
                    "AGENTCORE_RUNTIME_ARN", "AGENTCORE_AGENT_ID", "BEDROCK_MODEL_ID"]:
            os.environ.pop(key, None)

    def test_config_defaults(self):
        """Test that configuration uses sensible defaults."""
        config = CVAnalyzerConfig()
        
        assert config.provider.value == "simple"
        assert config.aws_region == "eu-west-1"
        assert config.bedrock_model_id == "eu.anthropic.claude-sonnet-4-20250514-v1:0"
        assert config.agentcore_agent_id == "cv-analyzer-agent"

    def test_config_read_provider_simple(self):
        """Test reading CV_ANALYZER_PROVIDER=simple."""
        os.environ["CV_ANALYZER_PROVIDER"] = "simple"
        config = CVAnalyzerConfig()
        
        assert config.is_simple_analyzer() is True
        assert config.is_agentcore_enabled() is False

    def test_config_read_provider_agentcore(self):
        """Test reading CV_ANALYZER_PROVIDER=agentcore."""
        os.environ["CV_ANALYZER_PROVIDER"] = "agentcore"
        config = CVAnalyzerConfig()
        
        assert config.is_agentcore_enabled() is True
        assert config.is_simple_analyzer() is False

    def test_config_read_provider_invalid(self):
        """Test that invalid provider raises error."""
        os.environ["CV_ANALYZER_PROVIDER"] = "invalid"
        
        with pytest.raises(ValueError, match="Invalid CV_ANALYZER_PROVIDER"):
            CVAnalyzerConfig()

    def test_config_read_aws_region(self):
        """Test reading AWS_REGION from environment."""
        os.environ["AWS_REGION"] = "us-east-1"
        config = CVAnalyzerConfig()
        
        assert config.aws_region == "us-east-1"

    def test_config_read_agentcore_settings(self):
        """Test reading AgentCore-specific settings."""
        os.environ["CV_ANALYZER_PROVIDER"] = "agentcore"
        os.environ["AGENTCORE_RUNTIME_ID"] = "runtime-test-123"
        os.environ["AGENTCORE_AGENT_ID"] = "custom-agent"
        os.environ["BEDROCK_MODEL_ID"] = "custom.model.id"
        
        config = CVAnalyzerConfig()
        
        assert config.agentcore_runtime_id == "runtime-test-123"
        assert config.agentcore_agent_id == "custom-agent"
        assert config.bedrock_model_id == "custom.model.id"

    def test_config_singleton_behavior(self):
        """Test that get_cv_analyzer_config returns same instance."""
        reset_config()
        
        config1 = get_cv_analyzer_config()
        config2 = get_cv_analyzer_config()
        
        assert config1 is config2

    def test_config_reset(self):
        """Test that reset_config clears the singleton."""
        reset_config()
        config1 = get_cv_analyzer_config()
        
        reset_config()
        config2 = get_cv_analyzer_config()
        
        # Different instances after reset
        assert config1 is not config2


class TestDependenciesIntegration:
    """Integration tests for dependencies and provider selection."""

    def teardown_method(self):
        """Reset configuration after each test."""
        reset_config()
        os.environ.pop("CV_ANALYZER_PROVIDER", None)

    def test_simple_analyzer_by_default(self):
        """Test that dependencies use SimpleCVAnalyzer by default."""
        from app.shared.dependencies import _get_cv_analyzer
        
        analyzer = _get_cv_analyzer()
        
        from app.adapters.ai.simple_cv_analyzer import SimpleCVAnalyzer
        assert isinstance(analyzer, SimpleCVAnalyzer)

    def test_agentcore_analyzer_when_configured(self):
        """Test that dependencies use AgentCoreCVAnalyzer when provider is set."""
        os.environ["CV_ANALYZER_PROVIDER"] = "agentcore"
        reset_config()
        
        from app.shared.dependencies import _get_cv_analyzer
        
        analyzer = _get_cv_analyzer()
        assert isinstance(analyzer, AgentCoreCVAnalyzer)
