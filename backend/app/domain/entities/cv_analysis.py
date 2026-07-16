from dataclasses import dataclass
from datetime import datetime


@dataclass
class CVAnalysisResult:
    """Resultado del análisis de un CV."""

    candidate_name: str
    professional_summary: str
    education: list[str]
    work_experience: list[str]
    technical_skills: list[str]
    soft_skills: list[str]
    languages: list[str]
    certifications: list[str]
    warnings: list[str]
    analyzed_at: datetime
