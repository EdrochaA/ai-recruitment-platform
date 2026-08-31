import pytest
from datetime import datetime
from app.adapters.ai.simple_cv_analyzer import SimpleCVAnalyzer
from app.domain.entities.cv_analysis import CVAnalysisResult


def test_simple_cv_analyzer_detects_skills():
    """Test que SimpleCVAnalyzer detecta skills correctamente."""
    analyzer = SimpleCVAnalyzer()
    
    cv_text = """
    Senior Python Developer with 5 years experience.
    Skills: Python, FastAPI, PostgreSQL, Docker, AWS
    Worked with REST APIs and microservices.
    Git and CI/CD experienced.
    """
    
    job_description = """
    We are looking for a Python developer with FastAPI experience.
    Required: Python, FastAPI, SQL, PostgreSQL, Docker
    Nice to have: AWS, Kubernetes
    """
    
    result = analyzer.analyze(cv_text, job_description)
    
    assert isinstance(result, CVAnalysisResult)
    assert "python" in result.skills
    assert "fastapi" in result.skills
    assert "postgresql" in result.skills
    assert "docker" in result.skills
    assert result.score >= 60  # Should have good score


def test_simple_cv_analyzer_calculates_score():
    """Test que el score se calcula correctamente."""
    analyzer = SimpleCVAnalyzer()
    
    cv_with_all_skills = """
    Python FastAPI PostgreSQL Docker AWS
    """
    
    job_requiring_all = """
    Python FastAPI PostgreSQL Docker AWS
    """
    
    result = analyzer.analyze(cv_with_all_skills, job_requiring_all)
    
    # Should have high score since all skills match
    assert result.score >= 90


def test_simple_cv_analyzer_low_score_missing_skills():
    """Test que calcula score bajo cuando faltan skills."""
    analyzer = SimpleCVAnalyzer()
    
    cv_with_one_skill = """
    JavaScript developer
    """
    
    job_requiring_many = """
    Python FastAPI PostgreSQL Docker AWS Kubernetes
    """
    
    result = analyzer.analyze(cv_with_one_skill, job_requiring_many)
    
    # Should have low score since missing most skills
    assert result.score < 40


def test_simple_cv_analyzer_generates_summary():
    """Test que genera un resumen coherente."""
    analyzer = SimpleCVAnalyzer()
    
    cv_text = """
    Software Engineer with Python and Docker experience.
    """
    
    job_description = """
    Senior position requiring Python, Docker and Kubernetes.
    """
    
    result = analyzer.analyze(cv_text, job_description)
    
    assert result.summary  # Should have a summary
    assert len(result.summary) > 0
    assert isinstance(result.analyzed_at, datetime)


def test_simple_cv_analyzer_extracts_experience():
    """Test que extrae información de experiencia."""
    analyzer = SimpleCVAnalyzer()
    
    cv_text = """
    EXPERIENCE
    Senior Developer at Tech Company
    Worked on REST APIs and microservices for 3 years
    
    Python developer at StartUp
    Built web applications with Django
    """
    
    job_description = """
    Looking for experienced developer
    """
    
    result = analyzer.analyze(cv_text, job_description)
    
    assert result.experience_summary
    assert len(result.experience_summary) > 0


def test_simple_cv_analyzer_case_insensitive():
    """Test que la búsqueda de skills es insensible a mayúsculas."""
    analyzer = SimpleCVAnalyzer()
    
    cv_upper = "PYTHON FASTAPI POSTGRESQL"
    cv_lower = "python fastapi postgresql"
    cv_mixed = "Python FastAPI PostgreSQL"
    
    job_description = "python fastapi postgresql"
    
    result_upper = analyzer.analyze(cv_upper, job_description)
    result_lower = analyzer.analyze(cv_lower, job_description)
    result_mixed = analyzer.analyze(cv_mixed, job_description)
    
    # All should detect the same skills
    assert set(result_upper.skills) == set(result_lower.skills) == set(result_mixed.skills)
    assert result_upper.score == result_lower.score == result_mixed.score
