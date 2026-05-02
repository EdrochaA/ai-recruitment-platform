from abc import ABC, abstractmethod
from app.domain.entities.cv_analysis import CVAnalysisResult


class CVAnalyzer(ABC):
    """Puerto para análisis de CVs.
    
    Define la interfaz que debe implementar cualquier analizador de CVs,
    permitiendo futuras integraciones con servicios externos como AWS Bedrock.
    """

    @abstractmethod
    def analyze(self, cv_text: str, job_description: str) -> CVAnalysisResult:
        """Analiza un CV contra una descripción de puesto.
        
        Args:
            cv_text: Texto extraído del CV del candidato
            job_description: Descripción del puesto de trabajo
            
        Returns:
            CVAnalysisResult con skills detectadas, score y resumen
        """
        pass
