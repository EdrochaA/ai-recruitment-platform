import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from app.application.use_cases.analyze_application_cv import AnalyzeApplicationCV
from app.domain.entities.job_application import JobApplication
from app.domain.entities.job_offer import JobOffer
from app.domain.entities.cv_analysis import CVAnalysisResult


def test_analyze_application_cv_successful():
    """Test que AnalyzeApplicationCV completa exitosamente."""
    # Setup mocks
    mock_app_repo = Mock()
    mock_job_repo = Mock()
    mock_analyzer = Mock()
    
    # Create test data
    application = JobApplication(
        id="app_1",
        job_offer_id="job_1",
        candidate_name="John Doe",
        candidate_email="john@example.com",
        cv_text="Python FastAPI Docker",
        cv_processing_status="processed",
        created_at=datetime.now(),
    )
    
    job_offer = JobOffer(
        id="job_1",
        title="Python Developer",
        description="Looking for Python FastAPI Docker developer",
        location="Remote",
        status="active",
        created_at=datetime.now(),
    )
    
    analysis_result = CVAnalysisResult(
        skills=["python", "fastapi", "docker"],
        experience_summary="5 years experience",
        score=85,
        summary="Good match",
        analyzed_at=datetime.now(),
    )
    
    # Configure mocks
    mock_app_repo.find_by_id.return_value = application
    mock_job_repo.find_by_id.return_value = job_offer
    mock_analyzer.analyze.return_value = analysis_result
    
    # Execute
    use_case = AnalyzeApplicationCV(mock_app_repo, mock_job_repo, mock_analyzer)
    result = use_case.execute("app_1")
    
    # Assertions
    assert result.cv_analysis_status == "completed"
    assert result.cv_analysis_score == 85
    assert result.cv_analysis_summary == "Good match"
    assert result.cv_analysis_skills == ["python", "fastapi", "docker"]
    assert result.cv_analysis_experience == "5 years experience"
    assert result.cv_analysis_error is None
    
    # Verify mocks were called
    mock_app_repo.find_by_id.assert_called_once_with("app_1")
    mock_job_repo.find_by_id.assert_called_once_with("job_1")
    mock_analyzer.analyze.assert_called_once()
    mock_app_repo.update.assert_called_once()


def test_analyze_application_cv_not_found():
    """Test que falla cuando la aplicación no existe."""
    mock_app_repo = Mock()
    mock_job_repo = Mock()
    mock_analyzer = Mock()
    
    mock_app_repo.find_by_id.return_value = None
    
    use_case = AnalyzeApplicationCV(mock_app_repo, mock_job_repo, mock_analyzer)
    
    with pytest.raises(ValueError, match="not found"):
        use_case.execute("nonexistent_app")


def test_analyze_application_cv_no_cv_text():
    """Test que falla cuando el CV no tiene texto procesado."""
    mock_app_repo = Mock()
    mock_job_repo = Mock()
    mock_analyzer = Mock()
    
    application = JobApplication(
        id="app_1",
        job_offer_id="job_1",
        candidate_name="John Doe",
        candidate_email="john@example.com",
        cv_text=None,  # No CV text
        cv_processing_status="pending",
        created_at=datetime.now(),
    )
    
    mock_app_repo.find_by_id.return_value = application
    
    use_case = AnalyzeApplicationCV(mock_app_repo, mock_job_repo, mock_analyzer)
    
    with pytest.raises(ValueError, match="does not have processed CV text"):
        use_case.execute("app_1")


def test_analyze_application_cv_job_offer_not_found():
    """Test que falla cuando la oferta no existe."""
    mock_app_repo = Mock()
    mock_job_repo = Mock()
    mock_analyzer = Mock()
    
    application = JobApplication(
        id="app_1",
        job_offer_id="job_1",
        candidate_name="John Doe",
        candidate_email="john@example.com",
        cv_text="Some CV text",
        cv_processing_status="processed",
        created_at=datetime.now(),
    )
    
    mock_app_repo.find_by_id.return_value = application
    mock_job_repo.find_by_id.return_value = None
    
    use_case = AnalyzeApplicationCV(mock_app_repo, mock_job_repo, mock_analyzer)
    
    with pytest.raises(ValueError, match="JobOffer not found"):
        use_case.execute("app_1")


def test_analyze_application_cv_analyzer_error():
    """Test que marca como fallido si el analizador falla."""
    mock_app_repo = Mock()
    mock_job_repo = Mock()
    mock_analyzer = Mock()
    
    application = JobApplication(
        id="app_1",
        job_offer_id="job_1",
        candidate_name="John Doe",
        candidate_email="john@example.com",
        cv_text="Some CV text",
        cv_processing_status="processed",
        created_at=datetime.now(),
    )
    
    job_offer = JobOffer(
        id="job_1",
        title="Developer",
        description="Job description",
        location="Remote",
        status="active",
        created_at=datetime.now(),
    )
    
    mock_app_repo.find_by_id.return_value = application
    mock_job_repo.find_by_id.return_value = job_offer
    mock_analyzer.analyze.side_effect = RuntimeError("Analysis failed")
    
    use_case = AnalyzeApplicationCV(mock_app_repo, mock_job_repo, mock_analyzer)
    
    with pytest.raises(RuntimeError):
        use_case.execute("app_1")
    
    # Verify that the update was called with failed status
    updated_app = mock_app_repo.update.call_args[0][0]
    assert updated_app.cv_analysis_status == "failed"
    assert "Analysis failed" in updated_app.cv_analysis_error
