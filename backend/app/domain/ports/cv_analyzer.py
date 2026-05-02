from abc import ABC, abstractmethod
from app.domain.entities.cv_analysis import CVAnalysisResult


class CVAnalyzer(ABC):
    """Puerto para análisis inteligente de CVs.
    
    Define el contrato que debe implementar cualquier analizador de CVs,
    permitiendo múltiples estrategias de análisis desacopladas del dominio.
    
    El puerto habilita tanto análisis heurísticos simples como integraciones
    con servicios externos de IA, manteniendo la arquitectura hexagonal:
    
    Implementaciones posibles:
    - SimpleCVAnalyzer: Análisis heurístico basado en patrones (actual)
    - BedrockCVAnalyzer: LLM directo mediante AWS Bedrock
    - AgentCoreCVAnalyzer: Agente inteligente mediante AWS AgentCore
      (que puede usar Bedrock como modelo subyacente)
    
    El dominio solo conoce la interfaz; AWS, AgentCore y Bedrock quedan
    aislados en adapters/, permitiendo cambios sin modificar domain ni application.
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
