from dataclasses import dataclass
from datetime import datetime


@dataclass
class CVAnalysisResult:
    """Resultado del análisis de un CV."""
    
    skills: list[str]
    experience_summary: str
    score: int  # 0-100
    summary: str
    analyzed_at: datetime
