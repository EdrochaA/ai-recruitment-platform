# Guía Práctica: Integración AgentCore en AI Recruitment Platform

*Documento complementario con código ejecutable*

---

## 1. Diagrama de Arquitectura Integrada

### 1.1 Vista General (Capas)

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNA: CLIENTE HTTP                         │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                  APPLICATION: EXPOSED SERVICE LAYER              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  POST /applications/{id}/analyze                           │ │
│  │  ├─ Router: cv_analysis_router                            │ │
│  │  └─ Converts HTTP → UseCase                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│              HEREXAGONAL BOUNDARY: PORTS & USE CASES              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  AnalyzeCVForJobMatch (Use Case)                           │ │
│  │  ├─ INPUT: app_id, job_offer_id                           │ │
│  │  │                                                         │ │
│  │  ├─ Uses → CVAnalyzer PORT (abstraction)                 │ │
│  │  ├─ Uses → JobApplicationRepository PORT                 │ │
│  │  ├─ Uses → JobOfferRepository PORT                       │ │
│  │  │                                                         │ │
│  │  └─ OUTPUT: CVAnalysisResult                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│              DOMAIN: ENTITIES (Pure, no logic)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  JobApplication                                             │ │
│  │  JobOffer                                                   │ │
│  │  CVAnalysisResult (NEW)                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│              DOMAIN: PORTS (Interfaces)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ABC CVAnalyzer (NEW)                                      │ │
│  │  ABC JobApplicationRepository                              │ │
│  │  ABC JobOfferRepository                                    │ │
│  │  ABC FileStorage                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│   ↑ CONOCE:                   ↓ DESCONOCE:                       │
│   · Domain entities           · FastAPI                         │
│   · Abstract ports            · AWS Bedrock                     │
│   · Use case orchestration    · MemorySession                   │
│                               · Strands library                 │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│               INFRASTRUCTURE: IMPLEMENTATIONS                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AI SUBSYSTEM (NEW)                                      │   │
│  │  ├─ BedrockCVAnalyzer                                   │   │
│  │  │  ├─ Implements: CVAnalyzer PORT                      │   │
│  │  │  ├─ Uses: agent_runtime                              │   │
│  │  │  └─ Uses: memory_hook                                │   │
│  │  │                                                       │   │
│  │  ├─ agent_runtime (Agent Orchestrator)                 │   │
│  │  │  ├─ create_agent() ← from AgentCore                 │   │
│  │  │  ├─ invoke agent with prompt                        │   │
│  │  │  └─ handle response                                 │   │
│  │  │                                                       │   │
│  │  ├─ memory_hook (Memory Management)                    │   │
│  │  │  ├─ STM: on_agent_initialized()                     │   │
│  │  │  ├─ LTM: on_message_added()                         │   │
│  │  │  └─ Persistence: save_interaction()                 │   │
│  │  │                                                       │   │
│  │  └─ config/ (Configuration)                            │   │
│  │     ├─ config.json ← from AgentCore                    │   │
│  │     ├─ config_dto.py ← from AgentCore                  │   │
│  │     └─ read_config.py ← from AgentCore                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PERSISTENCE SUBSYSTEM (EXISTING)                        │   │
│  │  ├─ InMemoryJobApplicationRepository                    │   │
│  │  ├─ InMemoryJobOfferRepository                          │   │
│  │  └─ LocalFileStorage                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  HTTP SUBSYSTEM (EXISTING + NEW ROUTER)                 │   │
│  │  ├─ job_offer_router                                   │   │
│  │  ├─ application_router                                 │   │
│  │  └─ cv_analysis_router (NEW)                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│            EXTERNAL SERVICES: AWS BEDROCK & MEMORY               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AWS Bedrock Runtime (Claude LLM)                        │   │
│  │  ├─ Model: EU.anthropic.claude-sonnet-4-6              │   │
│  │  ├─ Tools: Via Gateway MCP                              │   │
│  │  └─ Guardrails: Content policy                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AWS Bedrock Memory Resource                            │   │
│  │  ├─ STM: Session-scoped conversation                   │   │
│  │  ├─ LTM: Vector search for semantic recall             │   │
│  │  └─ Namespaces: Per-candidate scoping                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AWS Bedrock Gateway (Optional)                         │   │
│  │  ├─ Discovers MCP tools                                 │   │
│  │  ├─ Lambda targets                                      │   │
│  │  └─ API Gateway targets                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Código Ejecutable: Paso a Paso

### Paso 1: Crear el Puerto (Dominio)

**Archivo:** `app/domain/ports/cv_analyzer.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class CVAnalysisResult:
    """
    Resultado del análisis de CV.
    
    Esta entidad NO depende de:
    - AWS Bedrock
    - Strands Agent
    - MemorySession
    - Nada de infrastructure
    
    Es 100% independiente.
    """
    summary: str
    candidate_score: float  # 0.0 - 1.0
    skills_extracted: list[str]
    experience_years: float
    education_level: str
    recommendations: list[str]
    raw_analysis: dict


class CVAnalyzer(ABC):
    """
    Puerto hacia el subsistema de análisis de IA.
    
    Define QUÉ hace, no CÓMO lo hace.
    """
    
    @abstractmethod
    async def analyze(
        self,
        cv_text: str,
        job_description: str,
        candidate_id: str,
    ) -> CVAnalysisResult:
        """
        Analiza un CV contra una descripción de puesto.
        
        Args:
            cv_text: Texto extraído del CV
            job_description: Descripción completa de la posición
            candidate_id: ID del candidato (para scoping de memoria)
        
        Returns:
            Resultado estructurado del análisis
        
        Raises:
            ValueError: Si los inputs son inválidos
            RuntimeError: Si el análisis falla
        """
        pass
```

### Paso 2: Crear la Entidad en Dominio

**Archivo:** `app/domain/entities/cv_analysis.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.domain.ports.cv_analyzer import CVAnalysisResult


@dataclass
class CVAnalysis:
    """
    Análisis de CV que pertenece a una candidatura.
    
    Se relaciona con JobApplication pero es separado
    por responsabilidad única.
    """
    id: str
    application_id: str
    job_offer_id: str
    
    # Resultado del análisis
    result: CVAnalysisResult
    
    # Metadata
    analyzed_at: datetime
    version: str = "1.0"
    
    # Auditoría
    analysis_model: str = "Claude Sonnet 4.0"
    analysis_prompt_version: str = "1.0"
    
    # Para estadísticas
    processing_time_ms: Optional[int] = None
```

### Paso 3: Actualizar Entity JobApplication

**Archivo:** `app/domain/entities/job_application.py`

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class JobApplication:
    id: str
    job_offer_id: str
    candidate_name: str
    candidate_email: str

    cv_original_filename: Optional[str] = None
    cv_storage_key: Optional[str] = None
    cv_content_type: Optional[str] = None
    cv_size_bytes: Optional[int] = None
    cv_uploaded_at: Optional[datetime] = None
    cv_text: Optional[str] = None
    
    # NEW: Análisis de CV
    cv_analysis_id: Optional[str] = None  # ← Referencia a CVAnalysis
    cv_analysis_score: Optional[float] = None  # ← Caché para queries rápidas
    cv_analysis_timestamp: Optional[datetime] = None  # ← Cuándo se analizó
    
    created_at: datetime = None  # type: ignore


# Si necesitas buscar por score:
# def get_analysis_summary(application: JobApplication) -> dict:
#     return {
#         "score": application.cv_analysis_score,
#         "analyzed_at": application.cv_analysis_timestamp,
#     }
```

### Paso 4: Crear Repository para CVAnalysis

**Archivo:** `app/domain/ports/cv_analysis_repository.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.cv_analysis import CVAnalysis


class CVAnalysisRepository(ABC):
    """Puerto para persistencia de análisis"""
    
    @abstractmethod
    def save(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Guardar un nuevo análisis"""
        pass

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Optional[CVAnalysis]:
        """Buscar análisis por ID"""
        pass

    @abstractmethod
    def find_by_application(self, application_id: str) -> List[CVAnalysis]:
        """Obtener histórico de análisis de una candidatura"""
        pass

    @abstractmethod
    def update(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Actualizar análisis existente"""
        pass
```

### Paso 5: Implementación del Analizador

**Archivo:** `app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py`

```python
import json
import logging
from datetime import datetime
from uuid import uuid4

from app.domain.ports.cv_analyzer import CVAnalyzer, CVAnalysisResult
from app.infrastructure.ai.config.read_config import AIConfig
from app.infrastructure.ai.agent.agent import create_agent
from app.infrastructure.ai.memory.memory_hook import MemoryHook

logger = logging.getLogger("cv-analyzer")


class BedrockCVAnalyzer(CVAnalyzer):
    """
    Implementación de CVAnalyzer usando AWS Bedrock + Strands Agent.
    
    Esta clase contiene TODA la complejidad de AWS y Agent.
    El dominio nunca la ve.
    """
    
    def __init__(
        self,
        config: AIConfig,
        memory_manager=None,  # MemorySessionManager
    ):
        self.config = config
        self.memory_manager = memory_manager
        self.agent = None
    
    async def analyze(
        self,
        cv_text: str,
        job_description: str,
        candidate_id: str,
    ) -> CVAnalysisResult:
        """
        Analyze CV using Bedrock Agent
        """
        logger.info(f"Starting CV analysis for candidate {candidate_id}")
        
        try:
            # 1. Crear prompt especializado
            system_prompt = self._create_system_prompt(job_description)
            user_message = self._create_user_message(cv_text)
            
            # 2. Invocar agente
            response_text = await self._run_agent(
                system_prompt=system_prompt,
                user_input=user_message,
                actor_id=candidate_id,
            )
            
            # 3. Parsear respuesta JSON
            analysis_dict = json.loads(response_text)
            
            # 4. Validar y mapear a CVAnalysisResult
            result = self._parse_analysis_response(analysis_dict)
            
            logger.info(f"CV analysis completed. Score: {result.candidate_score}")
            return result
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response: {e}")
            raise ValueError(f"Invalid analysis response format: {e}")
        
        except Exception as e:
            logger.error(f"CV analysis failed: {e}", exc_info=True)
            raise RuntimeError(f"Analysis service unavailable: {e}")
    
    def _create_system_prompt(self, job_description: str) -> str:
        """Crear prompt del sistema especializado para análisis de CV"""
        return f"""
Eres un experto en análisis de CVs y selección de talento con 20 años de experiencia.

Tu tarea es analizar el CV del candidato y evaluarlo contra la siguiente posición:

---
DESCRIPCIÓN DEL PUESTO:
{job_description}
---

INSTRUCCIONES CRÍTICAS:
1. Analiza profundamente la alineación entre CV y puesto
2. Extrae y lista todas las skills relevantes
3. Calcula una puntuación numérica (0-1) de match
4. Proporciona recomendaciones accionables
5. Devuelve SOLAMENTE un JSON válido (sin texto adicional)

FORMATO DE RESPUESTA (JSON ONLY):
{{
    "summary": "Resumen ejecutivo de máximo 200 palabras",
    "candidate_score": 0.85,
    "skills_extracted": ["Python", "FastAPI", "AWS", ...],
    "experience_years": 5.5,
    "education_level": "Master's in Computer Science",
    "recommendations": [
        "Strong technical fit",
        "Consider cultural fit interview",
        ...
    ]
}}
"""
    
    def _create_user_message(self, cv_text: str) -> str:
        """Preparar mensaje del usuario"""
        return f"""
Por favor, analiza este CV del candidato:

---
CV DEL CANDIDATO:
{cv_text}
---

Devuelve el análisis en JSON.
"""
    
    async def _run_agent(
        self,
        system_prompt: str,
        user_input: str,
        actor_id: str,
    ) -> str:
        """
        Ejecutar el agente de Strands.
        
        Esta es la parte que integra con AgentCore.
        """
        # 1. Crear memoria o reutilizar
        memory_session = None
        if self.memory_manager:
            memory_session = self.memory_manager.get_session(actor_id)
        
        # 2. Crear agente (del módulo copiado de AgentCore)
        agent = create_agent(
            all_mcp_tools=[],  # Por ahora sin herramientas
            actor_id=actor_id,
            session_id=f"analysis-{uuid4().hex[:8]}",
            agent_llm_config=self.config.agent,
            prompt_management_config=self.config.prompt_management,
            guardrails_config=self.config.guardrails,
        )
        
        if not agent:
            raise RuntimeError("Failed to create agent")
        
        # 3. Override del prompt del sistema
        agent.system_prompt = system_prompt
        
        # 4. Invocar agente
        response = await agent.invoke_async(user_input)
        
        # 5. Extraer texto de respuesta
        try:
            response_text = response.message["content"][0]["text"]
            # Limpiar markdown si es necesario
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]  # Remove ```json y ```
            return response_text.strip()
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Failed to extract response: {e}")
            raise RuntimeError(f"Invalid agent response structure: {e}")
    
    def _parse_analysis_response(self, analysis_dict: dict) -> CVAnalysisResult:
        """
        Validar y convertir respuesta del agente a CVAnalysisResult
        """
        # Validar campos requeridos
        required = ["summary", "candidate_score", "skills_extracted", 
                    "experience_years", "education_level", "recommendations"]
        
        missing = [f for f in required if f not in analysis_dict]
        if missing:
            raise ValueError(f"Missing fields in response: {missing}")
        
        # Validar tipos
        if not isinstance(analysis_dict["candidate_score"], (int, float)):
            raise ValueError("candidate_score must be numeric")
        
        if not 0.0 <= analysis_dict["candidate_score"] <= 1.0:
            raise ValueError("candidate_score must be between 0.0 and 1.0")
        
        # Crear resultado
        return CVAnalysisResult(
            summary=str(analysis_dict["summary"])[:500],  # Max 500 chars
            candidate_score=float(analysis_dict["candidate_score"]),
            skills_extracted=[str(s) for s in analysis_dict["skills_extracted"]],
            experience_years=float(analysis_dict["experience_years"]),
            education_level=str(analysis_dict["education_level"]),
            recommendations=[str(r) for r in analysis_dict["recommendations"]],
            raw_analysis=analysis_dict,
        )
```

### Paso 6: Use Case Que Orquesta

**Archivo:** `app/application/use_cases/analyze_cv_for_job_match.py`

```python
import logging
from datetime import datetime
from uuid import uuid4

from app.domain.entities.cv_analysis import CVAnalysis
from app.domain.ports.cv_analyzer import CVAnalyzer
from app.domain.ports.cv_analysis_repository import CVAnalysisRepository
from app.domain.ports.job_application_repository import JobApplicationRepository
from app.domain.ports.job_offer_repository import JobOfferRepository

logger = logging.getLogger("use-cases")


class AnalyzeCVForJobMatch:
    """
    Use case que integra TODOS los puertos hexagonales.
    
    Responsabilidades:
    1. Validar inputs
    2. Orquestar repositorios
    3. Llamar al analizador (vía puerto)
    4. Guardar resultado
    5. Actualizar candidatura
    6. Mantener consistencia
    """
    
    def __init__(
        self,
        cv_analyzer: CVAnalyzer,
        cv_analysis_repo: CVAnalysisRepository,
        job_app_repo: JobApplicationRepository,
        job_offer_repo: JobOfferRepository,
    ):
        self.cv_analyzer = cv_analyzer
        self.cv_analysis_repo = cv_analysis_repo
        self.job_app_repo = job_app_repo
        self.job_offer_repo = job_offer_repo
    
    async def execute(
        self,
        application_id: str,
        job_offer_id: str,
    ) -> CVAnalysis:
        """
        Analizar candidatura contra oferta de empleo.
        
        Flujo orquestado:
        1. Validar que la candidatura existe
        2. Validar que tiene CV
        3. Validar que la oferta existe
        4. Invocar analizador
        5. Guardar resultado
        6. Actualizar candidatura
        7. Retornar resultado
        """
        
        logger.info(f"Analyzing CV for application {application_id} vs job {job_offer_id}")
        
        # 1. Recuperar y validar candidatura
        job_application = self.job_app_repo.find_by_id(application_id)
        if not job_application:
            raise ValueError(f"Application {application_id} not found")
        
        if not job_application.cv_text:
            raise ValueError(
                f"Application {application_id} has no CV text. "
                "Upload CV first via /applications/{id}/cv"
            )
        
        # 2. Recuperar y validar oferta
        job_offer = self.job_offer_repo.find_by_id(job_offer_id)
        if not job_offer:
            raise ValueError(f"Job offer {job_offer_id} not found")
        
        # 3. LLAMAR AL ANALIZADOR VÍA PUERTO
        # Este es el único punto donde el dominio se conecta con IA
        try:
            analysis_result = await self.cv_analyzer.analyze(
                cv_text=job_application.cv_text,
                job_description=job_offer.description,
                candidate_id=application_id,  # Para scoping de memoria
            )
        except RuntimeError as e:
            logger.error(f"Analysis failed: {e}")
            raise
        
        # 4. Crear entidad CVAnalysis con el resultado
        cv_analysis = CVAnalysis(
            id=str(uuid4()),
            application_id=application_id,
            job_offer_id=job_offer_id,
            result=analysis_result,
            analyzed_at=datetime.utcnow(),
        )
        
        # 5. Guardar en repositorio de análisis
        saved_analysis = self.cv_analysis_repo.save(cv_analysis)
        
        # 6. Actualizar la candidatura con referencia al análisis
        job_application.cv_analysis_id = saved_analysis.id
        job_application.cv_analysis_score = analysis_result.candidate_score
        job_application.cv_analysis_timestamp = saved_analysis.analyzed_at
        
        updated_app = self.job_app_repo.update(job_application)
        
        logger.info(
            f"Analysis saved. "
            f"Application {application_id} score: {analysis_result.candidate_score}"
        )
        
        return saved_analysis
```

### Paso 7: Router HTTP

**Archivo:** `app/infrastructure/http/routers/cv_analysis_router.py`

```python
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.application.use_cases.analyze_cv_for_job_match import AnalyzeCVForJobMatch
from app.shared.dependencies import get_analyze_cv_use_case

logger = logging.getLogger("routers")

router = APIRouter(prefix="/applications", tags=["CV Analysis"])


# DTOs for HTTP layer
class AnalyzeRequest(BaseModel):
    job_offer_id: str = Field(..., description="ID of the job offer to analyze against")


class AnalysisMetadata(BaseModel):
    summary: str
    candidate_score: float
    skills_extracted: list[str]
    experience_years: float
    education_level: str
    recommendations: list[str]


class AnalyzeResponse(BaseModel):
    analysis_id: str
    application_id: str
    job_offer_id: str
    analysis: AnalysisMetadata
    analyzed_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_id": "analysis-abc123",
                "application_id": "app-123",
                "job_offer_id": "job-456",
                "analysis": {
                    "summary": "Strong technical match with relevant Python experience",
                    "candidate_score": 0.87,
                    "skills_extracted": ["Python", "FastAPI", "AWS", "Docker"],
                    "experience_years": 5.5,
                    "education_level": "Master's in Computer Science",
                    "recommendations": [
                        "Schedule technical interview",
                        "Verify AWS certifications",
                    ]
                },
                "analyzed_at": "2026-05-02T15:30:00"
            }
        }


@router.post(
    "/{application_id}/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze CV against job offer",
    description="Run CV analysis with AI agent, scoring candidate match",
)
async def analyze_application(
    application_id: str,
    request: AnalyzeRequest,
    use_case: AnalyzeCVForJobMatch = Depends(get_analyze_cv_use_case),
):
    """
    Analiza el CV de una candidatura contra una oferta de empleo.
    
    Flujo:
    1. Obtiene CV de la candidatura
    2. Obtiene descripción de la oferta
    3. Ejecuta agente de análisis
    4. Persiste resultado
    5. Retorna análisis
    
    Requiere:
    - Application con CV cargado (via POST /applications/{id}/cv)
    - JobOffer válida
    - AWS credentials configuradas
    """
    try:
        # Ejecutar use case
        cv_analysis = await use_case.execute(
            application_id=application_id,
            job_offer_id=request.job_offer_id,
        )
        
        # Convertir entidad a respuesta HTTP
        return AnalyzeResponse(
            analysis_id=cv_analysis.id,
            application_id=cv_analysis.application_id,
            job_offer_id=cv_analysis.job_offer_id,
            analysis=AnalysisMetadata(
                summary=cv_analysis.result.summary,
                candidate_score=cv_analysis.result.candidate_score,
                skills_extracted=cv_analysis.result.skills_extracted,
                experience_years=cv_analysis.result.experience_years,
                education_level=cv_analysis.result.education_level,
                recommendations=cv_analysis.result.recommendations,
            ),
            analyzed_at=cv_analysis.analyzed_at,
        )
    
    except ValueError as e:
        logger.warning(f"Validation error in CV analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    except RuntimeError as e:
        logger.error(f"Analysis service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI analysis service temporarily unavailable",
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during CV analysis",
        )
```

### Paso 8: Repositorio In-Memory para CVAnalysis

**Archivo:** `app/infrastructure/persistence/in_memory/in_memory_cv_analysis_repository.py`

```python
from typing import List, Optional
from app.domain.entities.cv_analysis import CVAnalysis
from app.domain.ports.cv_analysis_repository import CVAnalysisRepository


class InMemoryCVAnalysisRepository(CVAnalysisRepository):
    """
    Implementación en memoria del repositorio de análisis de CV.
    
    Para MVP. Después puedes reemplazar con base de datos real.
    """
    
    def __init__(self):
        self._analyses: List[CVAnalysis] = []
    
    def save(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Guardar nuevo análisis"""
        self._analyses.append(cv_analysis)
        return cv_analysis
    
    def find_by_id(self, analysis_id: str) -> Optional[CVAnalysis]:
        """Buscar por ID"""
        for analysis in self._analyses:
            if analysis.id == analysis_id:
                return analysis
        return None
    
    def find_by_application(self, application_id: str) -> List[CVAnalysis]:
        """Obtener todos los análisis de una aplicación"""
        return [
            a for a in self._analyses
            if a.application_id == application_id
        ]
    
    def update(self, cv_analysis: CVAnalysis) -> CVAnalysis:
        """Actualizar análisis existente"""
        for idx, existing in enumerate(self._analyses):
            if existing.id == cv_analysis.id:
                self._analyses[idx] = cv_analysis
                return cv_analysis
        raise ValueError(f"Analysis {cv_analysis.id} not found")
```

### Paso 9: Actualizar Dependencies

**Archivo:** `app/shared/dependencies.py` (Actualizado)

```python
import logging

from app.application.use_cases.create_job_offer import CreateJobOffer
from app.application.use_cases.list_job_offers import ListJobOffers
from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import ListApplicationsByJobOffer
from app.application.use_cases.upload_application_cv import UploadApplicationCV
from app.application.use_cases.analyze_cv_for_job_match import AnalyzeCVForJobMatch  # NEW

# Repositorios existentes
from app.infrastructure.persistence.in_memory.in_memory_job_offer_repository import InMemoryJobOfferRepository
from app.infrastructure.persistence.in_memory.in_memory_job_application_repository import InMemoryJobApplicationRepository
from app.infrastructure.persistence.in_memory.in_memory_cv_analysis_repository import InMemoryCVAnalysisRepository  # NEW

# Storage
from app.infrastructure.storage.local_file_storage import LocalFileStorage

# AI NEW
from app.domain.ports.cv_analyzer import CVAnalyzer
from app.infrastructure.ai.cv_analyzer.bedrock_cv_analyzer import BedrockCVAnalyzer
from app.infrastructure.ai.config.read_config import read_config

logger = logging.getLogger("dependencies")

# ==================== EXISTING REPOSITORIES ====================
job_offer_repository = InMemoryJobOfferRepository()
job_application_repository = InMemoryJobApplicationRepository()
file_storage = LocalFileStorage()

# ==================== NEW: CV ANALYSIS ====================
cv_analysis_repository = InMemoryCVAnalysisRepository()

# AI Configuration
try:
    ai_config = read_config("app/infrastructure/ai/config/config.json")
    logger.info("AI config loaded successfully")
except Exception as e:
    logger.warning(f"AI config failed to load: {e}. AI features disabled.")
    ai_config = None

# Memory Manager (opcional, requiere AWS setup)
memory_manager = None
if ai_config:
    try:
        from bedrock_agentcore.memory.session import MemorySessionManager
        memory_manager = MemorySessionManager(
            resource_id=ai_config.memory.memory_id,
        )
        logger.info("Memory manager initialized")
    except Exception as e:
        logger.warning(f"Memory manager failed: {e}. Using without LTM/STM.")

# CV Analyzer implementation
cv_analyzer: CVAnalyzer | None = None
if ai_config:
    try:
        cv_analyzer = BedrockCVAnalyzer(ai_config, memory_manager)
        logger.info("CV Analyzer initialized")
    except Exception as e:
        logger.error(f"CV Analyzer initialization failed: {e}")

# ==================== DEPENDENCY GETTERS ====================
# Existing getters (unchanged)
def get_create_job_offer_use_case() -> CreateJobOffer:
    return CreateJobOffer(job_offer_repository)

def get_list_job_offers_use_case() -> ListJobOffers:
    return ListJobOffers(job_offer_repository)

def get_create_application_use_case() -> CreateApplication:
    return CreateApplication(job_application_repository)

def get_list_applications_use_case() -> ListApplicationsByJobOffer:
    return ListApplicationsByJobOffer(job_application_repository)

def get_upload_application_cv_use_case() -> UploadApplicationCV:
    return UploadApplicationCV(job_application_repository, file_storage)

# NEW: CV Analysis use case with dependency checking
def get_analyze_cv_use_case() -> AnalyzeCVForJobMatch:
    """
    Get CV analysis use case.
    
    Raises ValueError if AI is not properly configured.
    """
    if not cv_analyzer:
        raise ValueError(
            "CV analysis is not available. "
            "Check AI configuration and AWS credentials."
        )
    
    return AnalyzeCVForJobMatch(
        cv_analyzer=cv_analyzer,
        cv_analysis_repo=cv_analysis_repository,
        job_app_repo=job_application_repository,
        job_offer_repo=job_offer_repository,
    )
```

---

## 3. Test Examples

### Unit Test: CVAnalyzer Mock

**Archivo:** `tests/application/use_cases/test_analyze_cv.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4

from app.domain.ports.cv_analyzer import CVAnalyzer, CVAnalysisResult
from app.domain.ports.cv_analysis_repository import CVAnalysisRepository
from app.domain.ports.job_application_repository import JobApplicationRepository
from app.domain.ports.job_offer_repository import JobOfferRepository

from app.domain.entities.job_application import JobApplication
from app.domain.entities.job_offer import JobOffer

from app.application.use_cases.analyze_cv_for_job_match import AnalyzeCVForJobMatch


@pytest.fixture
def mock_cv_analyzer():
    """Mock de CVAnalyzer para testing sin AWS"""
    mock = AsyncMock(spec=CVAnalyzer)
    
    # Resultado esperado
    mock.analyze.return_value = CVAnalysisResult(
        summary="Strong candidate with relevant skills",
        candidate_score=0.85,
        skills_extracted=["Python", "FastAPI", "AWS"],
        experience_years=5.0,
        education_level="Master's",
        recommendations=["Schedule interview", "Verify certifications"],
        raw_analysis={"mock": True},
    )
    
    return mock


@pytest.fixture
def mock_repositories():
    """Mock de todos los repositorios"""
    
    job_app_repo = MagicMock(spec=JobApplicationRepository)
    job_offer_repo = MagicMock(spec=JobOfferRepository)
    cv_analysis_repo = MagicMock(spec=CVAnalysisRepository)
    
    # Setup default returns
    app_id = str(uuid4())
    job_id = str(uuid4())
    
    job_application = JobApplication(
        id=app_id,
        job_offer_id=job_id,
        candidate_name="John Doe",
        candidate_email="john@example.com",
        cv_text="Python developer with 5 years experience...",
        created_at=datetime.utcnow(),
    )
    
    job_offer = JobOffer(
        id=job_id,
        title="Senior Python Developer",
        description="We are looking for a Python expert...",
        created_at=datetime.utcnow(),
    )
    
    job_app_repo.find_by_id.return_value = job_application
    job_offer_repo.find_by_id.return_value = job_offer
    cv_analysis_repo.save.return_value = MagicMock()  # Simplificado
    job_app_repo.update.return_value = job_application
    
    return {
        "job_app_repo": job_app_repo,
        "job_offer_repo": job_offer_repo,
        "cv_analysis_repo": cv_analysis_repo,
    }


@pytest.mark.asyncio
async def test_analyze_cv_for_new_application(mock_cv_analyzer, mock_repositories):
    """Test del flujo completo de análisis"""
    
    use_case = AnalyzeCVForJobMatch(
        cv_analyzer=mock_cv_analyzer,
        cv_analysis_repo=mock_repositories["cv_analysis_repo"],
        job_app_repo=mock_repositories["job_app_repo"],
        job_offer_repo=mock_repositories["job_offer_repo"],
    )
    
    # Ejecutar
    result = await use_case.execute(
        application_id="app-123",
        job_offer_id="job-456",
    )
    
    # Verificaciones
    assert result is not None
    assert result.result.candidate_score == 0.85
    assert "Python" in result.result.skills_extracted
    
    # Verificar que el mock fue llamado
    mock_cv_analyzer.analyze.assert_called_once()
    call_args = mock_cv_analyzer.analyze.call_args
    assert call_args[1]["candidate_id"] == "app-123"


@pytest.mark.asyncio
async def test_analyze_cv_without_text_fails(mock_cv_analyzer, mock_repositories):
    """Test: error si no hay CV"""
    
    # Setup
    mock_repositories["job_app_repo"].find_by_id.return_value = JobApplication(
        id="app-no-cv",
        job_offer_id="job-456",
        candidate_name="No CV",
        candidate_email="nocv@example.com",
        cv_text=None,  # ← No tiene texto
        created_at=datetime.utcnow(),
    )
    
    use_case = AnalyzeCVForJobMatch(
        cv_analyzer=mock_cv_analyzer,
        cv_analysis_repo=mock_repositories["cv_analysis_repo"],
        job_app_repo=mock_repositories["job_app_repo"],
        job_offer_repo=mock_repositories["job_offer_repo"],
    )
    
    # Debería fallar
    with pytest.raises(ValueError, match="has no CV text"):
        await use_case.execute(
            application_id="app-no-cv",
            job_offer_id="job-456",
        )
```

---

## 4. Configuración Pyproject.toml

**Archivo:** `pyproject.toml` (Actualizado)

```toml
[project]
name = "ai-recruitment-platform"
version = "0.2.0"
description = "AI-powered recruitment platform with AgentCore integration"
readme = "README.md"
requires-python = ">=3.10"

dependencies = [
    # HTTP/Web
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.0.0",
    "email-validator>=2.3.0",
    "python-multipart>=0.0.9",
    
    # AI/AgentCore (NEW)
    "strands-agents>=0.8.0",
    "bedrock-agentcore",
    "boto3>=1.28.0",
    
    # Utilities
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[tool.uv]
index-url = "https://pypi.org/simple"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"

[tool.black]
line-length = 100

[tool.ruff]
line-length = 100
select = ["E", "F", "W"]
```

---

## 5. Checklist de Integración

```
[ ] 1. Copiar archivos de AgentCore a app/infrastructure/ai/
    [ ] agent.py
    [ ] memory.py
    [ ] config/config.json
    [ ] config/config_dto.py
    [ ] config/read_config.py

[ ] 2. Crear puertos en dominio
    [ ] app/domain/ports/cv_analyzer.py
    [ ] app/domain/ports/cv_analysis_repository.py

[ ] 3. Crear entidades en dominio
    [ ] app/domain/entities/cv_analysis.py
    [ ] Actualizar app/domain/entities/job_application.py

[ ] 4. Crear implementación en infrastructure
    [ ] app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py
    [ ] app/infrastructure/persistence/in_memory/in_memory_cv_analysis_repository.py

[ ] 5. Crear use case
    [ ] app/application/use_cases/analyze_cv_for_job_match.py

[ ] 6. Crear router
    [ ] app/infrastructure/http/routers/cv_analysis_router.py
    [ ] Actualizar app/main.py para incluir router

[ ] 7. Actualizar dependencias
    [ ] app/shared/dependencies.py
    [ ] pyproject.toml

[ ] 8. Tests
    [ ] tests/application/use_cases/test_analyze_cv.py
    [ ] tests/infrastructure/ai/ tests

[ ] 9. Configuración AWS
    [ ] AWS_PROFILE configurado
    [ ] Bedrock access verificado
    [ ] Memory resource creado (si usas LTM)

[ ] 10. Testing End-to-End
    [ ] curl POST /applications/{id}/analyze
    [ ] Verificar respuesta JSON
    [ ] Verificar persistencia en repositorio
```

---

**Documento complementario preparado para desarrollo**
*Código ejecutable, tests, configuración lista para copiar/pegar*
