# Análisis de Integración Arquitectónica: AI Recruitment Platform + AgentCore

*Análisis realizado: Mayo 2, 2026*

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis Arquitectónico Comparative](#análisis-arquitectónico-comparative)
3. [Evaluación de Compatibilidad](#evaluación-de-compatibilidad)
4. [Componentes Reutilizables](#componentes-reutilizables)
5. [Estrategia de Integración](#estrategia-de-integración)
6. [Diseño de Estructura](#diseño-de-estructura)
7. [Caso de Uso: CV Analysis](#caso-de-uso-cv-analysis)
8. [Guía de Implementación](#guía-de-implementación)
9. [Recomendaciones Finales](#recomendaciones-finales)

---

## 1. Resumen Ejecutivo

### 1.1 Viabilidad: ✅ SÍ, ES VIABLE

**Conclusión:** La integración es **completamente viable** manteniendo la arquitectura hexagonal. El código de AgentCore debe vivir en la capa de **infrastructura**, exactamente donde vive `FileStorage` hoy.

### 1.2 Puntos Clave

| Aspecto | Evaluación | Nota |
|---------|-----------|------|
| **Compatibilidad arquitectónica** | ✅ Alta | AgentCore es agnóstico a la arquitectura del host |
| **Desacoplamiento de dominio** | ✅ Posible | El dominio NO depende de AgentCore |
| **Reutilización de código** | ✅ 60-70% | Memory, Gateway patterns son reutilizables |
| **Integración con FFastAPI** | ✅ Sí | Ya tiene entrypoint compatible |
| **Dependencias AWS** | ⚠️ Centralizadas | Todas en infrastructure/ai/ |
| **Escalabilidad** | ✅ Excelente | Por patrón de ports |

---

## 2. Análisis Arquitectónico Comparativo

### 2.1 Tu Arquitectura: AI Recruitment Platform

```
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   HTTP Layer (FastAPI)              │   │
│  │  ├─ job_offer_router.py                             │   │
│  │  └─ application_router.py                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PERSISTENCE Layer (In-Memory)          │   │
│  │  ├─ InMemoryJobOfferRepository                      │   │
│  │  └─ InMemoryJobApplicationRepository                │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                STORAGE Layer                        │   │
│  │  └─ LocalFileStorage                                │   │
│  │     (Abstraction: implements FileStorage port)      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
              ↑                           ↑
              │                           │
┌──────────────┴───────────┐ ┌──────────┴──────────────┐
│    APPLICATION LAYER     │ │    DOMAIN LAYER        │
│  ├─ CreateApplication    │ │  ├─ Entities:          │
│  ├─ ListApplications     │ │  │  ├─ JobOffer        │
│  ├─ UploadApplicationCV  │ │  │  └─ JobApplication  │
│  └─ CreateJobOffer       │ │  ├─ Ports:             │
│                          │ │  │  ├─ Repository      │
│                          │ │  │  └─ FileStorage     │
└──────────────────────────┘ └────────────────────────┘
```

**Características:**
- Clean Architecture (Hexagonal)
- Independencia de framework
- Abstracción de I/O mediante Ports
- Fácil de testear
- Sin acoplamiento a tecnología específica

### 2.2 AgentCore Blueprint

```
┌─────────────────────────────────────────────────────────────┐
│           AWS BEDROCK AGENTCORE RUNTIME                      │
│     (Serverless, Managed by AWS, Deployed via Terraform)     │
└─────────────────────────────────────────────────────────────┘
                          ↑
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼─────┐   ┌──────▼─────┐   ┌──────▼─────┐
   │  AGENT    │   │   MEMORY   │   │  GATEWAY   │
   │           │   │            │   │            │
   │ ├─ model  │   │ ├─ STM     │   │ ├─ MCP     │
   │ ├─ hooks  │   │ ├─ LTM     │   │ └─ Tools   │
   │ ├─ tools  │   │ └─ llm.py  │   └────────────┘
   │ └─ system │   └────────────┘
   │   prompt  │
   └───────────┘
        ↑
  ┌─────┴────────────────┐
  │  STRANDS Library     │
  │  (Agent Framework)   │
  └──────────────────────┘
```

**Características:**
- Runtime serverless (AWS managed)
- Agente con memoria dual (STM + LTM)
- Integración con Gateway para herramientas estándar
- Bedrock Guardrails para content policy
- Prompt Management via SSM + Bedrock
- Autenticación vía JWT (Cognito)

### 2.3 Comparación de Patrones

| Aspecto | AI Recruitment | AgentCore | Compatibilidad |
|---------|-----------------|-----------|-----------------|
| **Pattern** | Hexagonal | Layers | ✅ Complementarios |
| **Framework** | FastAPI | Strands + Bedrock | ⚠️ Diferentes |
| **I/O Abstraction** | Via Ports | Via Hooks + Tools | ✅ Similar concepto |
| **Memory** | Application State | Dual STM/LTM | ✅ Complementarios |
| **Testing** | Unit → In-Memory Repos | Via Strands mock | ✅ Ambos mockeables |
| **Deployment** | FastAPI app | AWS Runtime | ⚠️ Integración necesaria |
| **State Management** | In-Memory/Persistence | Bedrock Memory | ✅ Separable |

---

## 3. Evaluación de Compatibilidad

### 3.1 ¿QUÉ ENCAJA DIRECTAMENTE? ✅

#### 1. **Memory Hook Pattern**
```python
# AgentCore MemoryHook es como un "UseCase Hook"
# Patrón similar a tu CreateApplication → repository.save()
# 
# En AgentCore: on_message_added → memory_session.add_turns()
# En tu app: execute() → repository.save()
#
# DECISIÓN: Reutilizar MemoryHook con minor adaptations
```

**Mapeo:**
- `MemoryHook.__init__()` → se puede usar tal cual
- `on_agent_initialized()` → STM loading pattern es reusable
- `on_message_added()` → LTM injection pattern es reusable
- `save_interaction()` → compatible con tu infrastructure

#### 2. **Gateway Tool Discovery Pattern**
```python
# AgentCore Gateway:
# - Lee MCP tools desde múltiples fuentes (Lambda, API Gateway, OpenAPI)
# - Expone dinámicamente las herramientas al agente
#
# Tu app puede:
# - Exponer endpoints existentes como MCP tools
# - O usar Gateway para descubrir herramientas externas
#
# DECISIÓN: Adaptar Gateway client pero mantener lógica core
```

#### 3. **Configuration DTO Pattern**
Tu app ya usa este patrón (que verás cuando agregues):
```python
# AgentCore:
@dataclass
class AgentLLMConfig:
    llm: LLMConfig
    agent: AgentMetadata
    gateway: GatewayConfig
    memory: MemoryConfig

# TU APP: Similar structure para AI features
@dataclass
class AIConfig:
    llm: LLMConfig
    agent: AgentMetadata
    memory: MemoryConfig
```

**DECISIÓN: Copiar estructura DTO tal cual**

### 3.2 ¿QUÉ NO ENCAJA DIRECTAMENTE? ⚠️

#### 1. **Bedrock AgentCore Runtime**
```
⚠️ NO ENCAJA COMO ESTÁ

Razón:
- AgentCore Runtime es serverless AWS managed
- Desplegado vía Terraform
- Tu app es FastAPI (no usa Terraform)

SOLUCIÓN:
- Copiar lógica del agent (strands Agent creation)
- Descartar deployment infrastructure
- Usar el runtime localmente en tu FastAPI handler
```

#### 2. **Bedrock Prompt Management + SSM**
```
⚠️ PARCIALMENTE APLICABLE

Razón:
- Requiere SSM Parameter Store (AWS service)
- Requiere Bedrock Prompt Management

SOLUCIONES (elige una):
A) Simple: prompts en archivos JSON en tu repo (dev)
B) AWS: Usar SSM solo en prod (con feature flag)
C) Híbrida: File-based por defecto, SSM si disponible
```

#### 3. **Bedrock Guardrails**
```
⚠️ OPCIONAL, SEPARABLE

Razón:
- Es una capa de content policy de AWS
- Puede usarse o no según requirements

SOLUCIÓN:
- Implementar como un Hook separado
- Opcional en configuración
- Costo adicional en AWS
```

#### 4. **JWT Authorization via Cognito**
```
⚠️ DEPENDE DE TU SETUP

En AgentCore:
- Cognito JWT es validado en el runtime authorizer

En tu app:
- ¿Ya tienes auth? → integrar en application_router
- ¿No tienes? → puede venir después

SOLUCIÓN:
- Usar middleware FastAPI para validar JWT
- El agente asume que la identidad ya fue validada
```

### 3.3 Matriz de Compatibilidad

```
┌──────────────────────┬─────────────┬─────────────────────────────┐
│ Componente           │ Compatibilidad │ Acción                   │
├──────────────────────┼─────────────┼─────────────────────────────┤
│ Agent Creation       │ ✅ 100%     │ Copiar agent.py tal cual    │
│ MemoryHook           │ ✅ 95%      │ Minor: simplificar loggers  │
│ Gateway Client       │ ✅ 85%      │ Adaptar endpoint handling   │
│ Config DTOs          │ ✅ 90%      │ Copiar, expandir según need │
│ Strands Integration  │ ✅ 100%     │ Copiar, preservar          │
│ BedrockModel         │ ✅ 90%      │ Copiar, agregar fallback   │
├──────────────────────┼─────────────┼─────────────────────────────┤
│ Bedrock Guardrails   │ ⚠️ 70%      │ Adaptar, hacer opcional     │
│ SSM + PM Integration │ ⚠️ 60%      │ Fallback a archivos         │
│ Runtime Deployment   │ ❌ 0%       │ Reintegrar en FastAPI       │
│ Cognito Auth         │ ⚠️ 50%      │ Usar middleware             │
│ Terraform IaC        │ ❌ 0%       │ Descartar, usar docker      │
└──────────────────────┴─────────────┴─────────────────────────────┘
```

---

## 4. Componentes Reutilizables

### 4.1 Nivel de Reutilización

#### 🟢 COPIAR TAL CUAL (100% Reutilizable)

Estos archivos pueden copiarse sin cambios:
```python
# Origen: agent/agent.py → Tu app: app/infrastructure/ai/agent/agent.py
# ✅ Cambios: NINGUNO (excepto imports relativos)
#
# Reutiliza:
# - create_agent()
# - resolve_system_prompt() (pero adaptado a tu config)
# - Config loading pattern

# Origen: agent/memory.py → Tu app: app/infrastructure/ai/memory/memory_hook.py
# ✅ Cambios: MÍNIMOS (adaptar loggers, imports)
#
# Reutiliza:
# - MemoryHook clase completa
# - on_agent_initialized()
# - on_message_added()
# - save_interaction()

# Origen: agent/config/config_dto.py → Tu app: app/infrastructure/ai/config/config_dto.py
# ✅ Cambios: NINGUNO (copiar tal cual)
#
# Reutiliza:
# - Todos los dataclasses
# - Patrón de configuración

# Origen: agent/config/read_config.py → Tu app: app/infrastructure/ai/config/read_config.py
# ✅ Cambios: MÍNIMOS (adaptar paths)
#
# Reutiliza:
# - Patrón de carga de configuración
# - Validación de configuración
```

#### 🟡 ADAPTAR (50-80% Reutilizable)

Estos archivos necesitan adaptaciones:
```python
# Origen: agent/main.py → Tu app: app/infrastructure/ai/runtime/agent_runtime.py
# ⚠️ Cambios necesarios:
# 
# 1. Quitar decorador @app.entrypoint (es específico de BedrockAgentCoreApp)
#    Reemplazar por: función async que puedas llamar desde tu router
#
# 2. Adaptaciones:
#    - Pasar context como parámetro normal (no vía decorator)
#    - Extraer lógica de invoke_agent() → reutilizable
#    - Crear wrapper para FastAPI
#
# 3. Qué copiar:
#    - Lógica de _run_agent()
#    - Patrón de inicialización de config
#    - Tool loading pattern
#
# Ejemplo adaptación:
#
# ORIGINAL:
# @app.entrypoint
# async def invoke_agent(payload, context=None):
#     ...
#
# ADAPTADO:
# async def run_agent_runtime(
#     user_input: str,
#     actor_id: str,
#     session_id: str,
#     context: BedrockcContext = None,  # Optional, puede ser None
# ) -> str:
#     """FastAPI-compatible wrapper"""
#     ...
```

#### 🔴 DESCARTAR (No Reutilizable)

Estos archivos están específicamente acoplados a AWS y pueden descartarse:
```python
# Descartar completamente:
# - deploy.py → Usa bedrock_agentcore_starter_toolkit (AWS specific)
# - buildspec.yml → Infraestructura de AWS CodeBuild
# - Dockerfile → AWS ECR specific (puedes reutilizar pero adaptado)
# - terraform/ → IaC específico de AWS
# - requirements.txt → Reemplazar por tu pyproject.toml

# Adaptar levemente:
# - Guardrails configuration (opcional, separable)
# - SSM parameter resolution (hacer fallback-friendly)
```

### 4.2 Estrategia por Componente

#### **1. Memory Component**

```python
# COPIAR COMO ESTÁ:
# - MemoryHook class
# - on_agent_initialized() logic
# - on_message_added() logic
#
# ADAPTAR:
# - Logger configuration (usar tu logging setup)
# - Namespace resolution (tu formato de namespaces)
# - Contexto de integración con MemorySession
#
# CÓDIGO:
class CVAnalysisMemoryHook(MemoryHook):
    """Adaptación specializada para CV analysis"""
    
    def __init__(
        self,
        actor_id: str,
        memory_session: MemorySession,
        # ... rest of params
    ):
        super().__init__(actor_id, memory_session, ...)
        # Tu customization aquí
```

#### **2. Agent Creation Component**

```python
# COPIAR COMO ESTÁ:
# - create_agent() estructura
# - Model initialization patterns
# - Tool passing mechanism
#
# ADAPTAR:
# - BedrockModel implementation (¿cambiar modelo? ¿region?)
# - System prompt injection (usar tu prompt storage)
# - Tool filtering (ajustar a tu caso de uso)
#
# DECISIÓN:
# - Crear CVAnalysisAgent (specialized agent para CV)
# - Heredar de Agent pero con lógica customizada
```

#### **3. Gateway Component**

```python
# COPIAR PARCIALMENTE:
# - MCP client initialization
# - Tool discovery pattern
# - Tool invocation pattern
#
# ADAPTAR:
# - Gateway URL resolution (¿dónde vive tu gateway?)
# - MCP endpoint handling (¿local, remoto?)
# - Error handling (¿qué haces sin gateway?)
#
# DECISIÓN IMPORTANTE:
# Opción A) Usar Gateway remoto (produce herramientas externas)
# Opción B) Usar solo herramientas locales (sin gateway)
# Opción C) Gateway híbrido (local + remoto) - MÁS POTENTE
```

#### **4. Configuration Component**

```python
# COPIAR COMPLETAMENTE:
# - DTOs (dataclasses)
# - read_config() pattern
# - Configuration validation
#
# EXPANDIR TU pyproject.toml:
# 
# [project]
# dependencies = [
#     "fastapi>=0.110.0",
#     "uvicorn[standard]>=0.29.0",
#     "pydantic>=2.0.0",
#     ...
#     # AGREGAR:
#     "strands-agents>=0.8.0",
#     "bedrock-agentcore",
#     "boto3",
# ]
```

---

## 5. Estrategia de Integración

### 5.1 Principios de Integración Hexagonal

```
REGLA FUNDAMENTAL:

El DOMINIO nunca debe depender de AgentCore
↓
AgentCore vive en INFRASTRUCTURE
↓
Los USE CASES orquestan la integración
↓
PUERTOS exponen las capacidades del agente
```

### 5.2 Crear Puertos en el Dominio

```python
# Archivo: app/domain/ports/cv_analyzer.py
# Este puerto ABSTRAE el agente

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class CVAnalysisResult:
    """Resultado del análisis de CV - ENTIDAD DE DOMINIO"""
    summary: str
    candidate_score: float  # 0.0 - 1.0
    skills_extracted: list[str]
    experience_years: float
    education_level: str
    recommendations: list[str]
    raw_analysis: dict  # Para auditoría

class CVAnalyzer(ABC):
    """
    Puerto: Define cómo analizar un CV
    
    La IMPLEMENTACIÓN específica con AgentCore
    va en infrastructure/ai/
    """
    
    @abstractmethod
    async def analyze(
        self,
        cv_text: str,
        job_description: str,
        candidate_id: str,
    ) -> CVAnalysisResult:
        """
        Analiza un CV comparándolo con una descripción de puesto.
        
        Args:
            cv_text: Texto extraído del CV
            job_description: Descripción de la posición
            candidate_id: ID para scoping de memoria
        
        Returns:
            Resultado estructurado del análisis
        """
        pass

    @abstractmethod
    async def batch_analyze(
        self,
        analyses: list[tuple[str, str, str]],  # (cv_text, job_desc, candidate_id)
    ) -> list[CVAnalysisResult]:
        """Análisis en lote (optimización)"""
        pass
```

**IMPORTANTE:** Este puerto NO menciona:
- AWS Bedrock
- AgentCore
- Strands
- Memory details
- LTM/STM

Es **100% independiente de la implementación**.

### 5.3 Implementación en Infrastructure

```python
# Archivo: app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py

from app.domain.ports.cv_analyzer import CVAnalyzer, CVAnalysisResult
from app.infrastructure.ai.agent.agent import create_agent
from app.infrastructure.ai.memory.memory_hook import MemoryHook
from bedrock_agentcore.memory.session import MemorySession

class BedrockCVAnalyzer(CVAnalyzer):
    """
    Implementación concreta usando AWS Bedrock + AgentCore
    
    Encapsulación:
    - Toda la complejidad de AgentCore aquí
    - El dominio no sabe que esto existe
    """
    
    def __init__(
        self,
        config: AIConfig,
        memory_session: MemorySession,
    ):
        self.config = config
        self.memory_session = memory_session
        self.agent = None
    
    async def analyze(
        self,
        cv_text: str,
        job_description: str,
        candidate_id: str,
    ) -> CVAnalysisResult:
        """
        1. Crear agente (o reutilizar del pool)
        2. Preparar prompt specializado
        3. Invocar agente
        4. Parsear respuesta
        5. Mapear a CVAnalysisResult
        """
        
        # Crear prompt especializado
        system_prompt = f"""
        Eres un experto en análisis de CVs y selección de talento.
        Tu tarea es analizar el CV del candidato y evaluarlo contra la posición.
        
        PUESTO:
        {job_description}
        
        Devuelve un análisis JSON con:
        - summary: resumen ejecutivo
        - candidate_score: puntuación 0-1
        - skills_extracted: lista de skills
        - experience_years: años de experiencia
        - education_level: nivel educativo
        - recommendations: recomendaciones
        """
        
        # Invocar agente
        user_message = f"Analiza este CV:\n{cv_text}"
        
        response = await self._run_agent(
            system_prompt=system_prompt,
            user_input=user_message,
            actor_id=candidate_id,
        )
        
        # Parsear respuesta (JSON)
        result_dict = json.loads(response)
        
        # Mapear a CVAnalysisResult
        return CVAnalysisResult(
            summary=result_dict["summary"],
            candidate_score=float(result_dict["candidate_score"]),
            skills_extracted=result_dict["skills_extracted"],
            experience_years=float(result_dict["experience_years"]),
            education_level=result_dict["education_level"],
            recommendations=result_dict["recommendations"],
            raw_analysis=result_dict,
        )
    
    async def _run_agent(self, system_prompt, user_input, actor_id):
        """Wrapper sobre strands agent - OCULTO DEL DOMINIO"""
        # Implementación con AgentCore aquí
        pass
```

### 5.4 Orquestación desde Use Cases

```python
# Archivo: app/application/use_cases/analyze_cv_for_job_match.py

from app.domain.entities.job_application import JobApplication
from app.domain.ports.cv_analyzer import CVAnalyzer
from app.domain.ports.job_application_repository import JobApplicationRepository
from app.domain.ports.file_storage import FileStorage

class AnalyzeCVForJobMatch:
    """
    Use case que integra TodoS los puertos
    """
    
    def __init__(
        self,
        cv_analyzer: CVAnalyzer,  # ← Puerto hacia agente
        app_repository: JobApplicationRepository,  # ← Ya existía
        file_storage: FileStorage,  # ← Ya existía
        job_offer_repository,  # ← Ya existía
    ):
        self.cv_analyzer = cv_analyzer
        self.app_repository = app_repository
        self.file_storage = file_storage
        self.job_offer_repository = job_offer_repository
    
    async def execute(
        self,
        application_id: str,
        job_offer_id: str,
    ) -> dict:
        """
        Flujo:
        1. Recuperar application
        2. Obtener CV text
        3. Recuperar job offer description
        4. Analizar con agente (via puerto)
        5. Guardar resultado
        6. Devolver a cliente
        """
        
        # 1. Recuperar candidatura
        application = self.app_repository.find_by_id(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # 2. Verificar que tiene CV
        if not application.cv_text:
            raise ValueError("Application has no CV text")
        
        # 3. Recuperar oferta
        job_offer = self.job_offer_repository.find_by_id(job_offer_id)
        if not job_offer:
            raise ValueError(f"Job offer {job_offer_id} not found")
        
        # 4. LLAMAR AL AGENTE VÍA PUERTO
        analysis_result = await self.cv_analyzer.analyze(
            cv_text=application.cv_text,
            job_description=job_offer.description,
            candidate_id=application.id,
        )
        
        # 5. Guardar resultado en application
        application.analysis_result = asdict(analysis_result)
        application.analysis_timestamp = datetime.utcnow()
        self.app_repository.update(application)
        
        # 6. Devolver
        return {
            "application_id": application.id,
            "analysis": asdict(analysis_result),
        }
```

### 5.5 Inyección de Dependencias

```python
# Archivo: app/shared/dependencies.py
# (Actualizado para incluir agente)

from app.domain.ports.cv_analyzer import CVAnalyzer
from app.infrastructure.ai.cv_analyzer.bedrock_cv_analyzer import BedrockCVAnalyzer
from app.infrastructure.ai.config.read_config import read_config

# Config compartida
ai_config = read_config("app/infrastructure/ai/config/config.json")

# MemorySession (requiere setup AWS)
from bedrock_agentcore.memory.session import MemorySessionManager
memory_manager = MemorySessionManager(resource_id=ai_config.memory.memory_id)

# Implementación del puerto (inyectada)
cv_analyzer: CVAnalyzer = BedrockCVAnalyzer(ai_config, memory_manager)

# Use cases que usan el analizador
from app.application.use_cases.analyze_cv_for_job_match import AnalyzeCVForJobMatch

def get_analyze_cv_use_case() -> AnalyzeCVForJobMatch:
    return AnalyzeCVForJobMatch(
        cv_analyzer=cv_analyzer,
        app_repository=application_repository,
        file_storage=file_storage,
        job_offer_repository=job_offer_repository,
    )
```

---

## 6. Diseño de Estructura

### 6.1 Estructura Completa Propuesta

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                              # FastAPI app
│   │
│   ├── domain/                              # ← SIN cambios principales
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── job_offer.py
│   │   │   └── job_application.py
│   │   └── ports/
│   │       ├── __init__.py
│   │       ├── job_application_repository.py
│   │       ├── job_offer_repository.py
│   │       ├── file_storage.py
│   │       └── cv_analyzer.py                # ← NUEVO: Puerto hacia agente
│   │
│   ├── application/                          # ← Crecimiento aquí
│   │   ├── __init__.py
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       ├── create_job_offer.py
│   │       ├── list_job_offers.py
│   │       ├── create_application.py
│   │       ├── list_applications_by_job_offer.py
│   │       ├── upload_application_cv.py
│   │       └── analyze_cv_for_job_match.py   # ← NUEVO: Use case con agente
│   │
│   ├── infrastructure/                       # ← Expansión principal aquí
│   │   ├── __init__.py
│   │   ├── http/                             # ← Ya existe
│   │   │   ├── __init__.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── job_offer_router.py
│   │   │   │   ├── application_router.py
│   │   │   │   └── cv_analysis_router.py     # ← NUEVO: Endpoint para análisis
│   │   │   └── schemas/
│   │   │       ├── __init__.py
│   │   │       ├── job_offer_schema.py
│   │   │       ├── application_schema.py
│   │   │       └── cv_analysis_schema.py     # ← NUEVO: DTOs HTTP
│   │   │
│   │   ├── persistence/                      # ← Ya existe
│   │   │   ├── __init__.py
│   │   │   └── in_memory/
│   │   │       ├── __init__.py
│   │   │       ├── in_memory_job_offer_repository.py
│   │   │       └── in_memory_job_application_repository.py
│   │   │
│   │   ├── storage/                          # ← Ya existe
│   │   │   ├── __init__.py
│   │   │   └── local_file_storage.py
│   │   │
│   │   └── ai/                               # ← NUEVA CARPETA: Toda la IA
│   │       ├── __init__.py
│   │       │
│   │       ├── config/                       # Configuración del agente
│   │       │   ├── __init__.py
│   │       │   ├── config.json               # ← Config de Bedrock (copiar de AgentCore)
│   │       │   ├── config_dto.py             # ← Copiar de AgentCore
│   │       │   ├── read_config.py            # ← Copiar + adaptar de AgentCore
│   │       │   ├── prompt_management.json    # ← Copiar de AgentCore (opcional)
│   │       │   ├── prompt_management_dto.py  # ← Copiar de AgentCore
│   │       │   ├── read_prompt_management.py # ← Copiar + adaptar
│   │       │   ├── guardrails.json           # ← Copiar de AgentCore (opcional)
│   │       │   ├── guardrails_dto.py         # ← Copiar de AgentCore
│   │       │   └── read_guardrails.py        # ← Copiar + adaptar
│   │       │
│   │       ├── agent/                        # Core del agente
│   │       │   ├── __init__.py
│   │       │   ├── agent.py                  # ← Copiar de AgentCore (sin cambios)
│   │       │   └── agent_factory.py          # ← NUEVO: Factory parecido a agent.py pero simplificado
│   │       │
│   │       ├── memory/                       # Gestión de memoria
│   │       │   ├── __init__.py
│   │       │   ├── memory_hook.py            # ← Copiar de AgentCore (minor changes)
│   │       │   └── memory_manager.py         # ← NUEVO: Wrapper de MemorySession
│   │       │
│   │       ├── gateway/                      # Gateway para herramientas MCP
│   │       │   ├── __init__.py
│   │       │   ├── gateway_client.py         # ← Copiar + adaptar de AgentCore
│   │       │   └── mcp_tools_loader.py       # ← NUEVO: Load tools desde Gateway
│   │       │
│   │       ├── cv_analyzer/                  # Implementación específica para análisis de CV
│   │       │   ├── __init__.py
│   │       │   ├── bedrock_cv_analyzer.py    # ← NUEVO: Implementor del puerto CVAnalyzer
│   │       │   └── cv_analysis_prompts.py    # ← NUEVO: Prompts especializados
│   │       │
│   │       └── runtime/                      # Runtime del agente
│   │           ├── __init__.py
│   │           └── agent_runtime.py          # ← Adaptado de main.py de AgentCore
│   │
│   └── shared/
│       ├── __init__.py
│       └── dependencies.py                   # ← Actualizar con inyecciones de AI
│
├── pyproject.toml                            # ← Actualizar dependencias
└── README.md
```

### 6.2 Comparación: Antes vs Después

```
ANTES (Solo recruitment):
├── domain/
│   ├── entities: JobOffer, JobApplication
│   └── ports: Repository, FileStorage
├── application/
│   └── use_cases: Create*, List*, Upload*
└── infrastructure/
    ├── http: routers, schemas
    ├── persistence: in-memory repos
    └── storage: local files

DESPUÉS (Con AI):
├── domain/
│   ├── entities: + ninguna nueva
│   └── ports: + CVAnalyzer (puerto hacia agente)
├── application/
│   └── use_cases: + AnalyzeCVForJobMatch, + ScoreCandidates
└── infrastructure/
    ├── http: + cv_analysis_router
    ├── persistence: sin cambios
    ├── storage: sin cambios
    └── ai/                     ← NUEVA
        ├── config/
        ├── agent/
        ├── memory/
        ├── gateway/
        ├── cv_analyzer/
        └── runtime/
```

**Cambios en dominio: MÍNIMOS** (solo 1 puerto nuevo)
**Cambios en application: MODERADOS** (1-2 use cases nuevos)
**Cambios en infrastructure: SIGNIFICATIVOS** (carpeta ai/ completa)

---

## 7. Caso de Uso: CV Analysis

### 7.1 Flujo Completo

```
USER REQUEST (HTTP POST)
↓
app/infrastructure/http/routers/cv_analysis_router.py
├─ POST /applications/{app_id}/analyze
├─ parse CreateApplicationRequest
│
↓
dependency injection
├─ get_analyze_cv_use_case()
│
↓
app/application/use_cases/analyze_cv_for_job_match.py
├─ AnalyzeCVForJobMatch.execute(app_id, job_offer_id)
├─ 1. Fetch application from repository
├─ 2. Load CV text
├─ 3. Fetch job offer
├─ 4. CALL PORT: cv_analyzer.analyze(cv_text, job_desc, candidate_id)
│
├─ THIS CROSSES THE BOUNDARY (Hexagon border)
│
↓
app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py
├─ BedrockCVAnalyzer.analyze()
├─ 1. Create system prompt (specialized)
├─ 2. Create agent via agent_factory
├─ 3. Load memory (STM + LTM)
├─ 4. Invoke strands Agent
│
↓
AWS BEDROCK RUNTIME
├─ Model: Claude (via BedrockModel)
├─ Tools: Via Gateway (MCP)
├─ Memory: Via MemorySession
├─ Safety: Via Guardrails
│
↓
RESPONSE (JSON with analysis)
{
  "summary": "...",
  "candidate_score": 0.85,
  "skills": [...],
  ...
}

↓
app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py
├─ Parse response JSON
├─ Map to CVAnalysisResult entity

↓
app/application/use_cases/analyze_cv_for_job_match.py
├─ Save result to repository
├─ Return CVAnalysisResult

↓
app/infrastructure/http/routers/cv_analysis_router.py
├─ Convert CVAnalysisResult → CVAnalysisResponse (Pydantic)
├─ HTTP 200 OK
↓
CLIENT
```

### 7.2 Código Completo: Router

```python
# app/infrastructure/http/routers/cv_analysis_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.application.use_cases.analyze_cv_for_job_match import AnalyzeCVForJobMatch
from app.infrastructure.http.schemas.cv_analysis_schema import (
    CVAnalysisRequest,
    CVAnalysisResponse,
)
from app.shared.dependencies import get_analyze_cv_use_case

router = APIRouter(prefix="/applications", tags=["CV Analysis"])


@router.post(
    "/{application_id}/analyze",
    response_model=CVAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_application(
    application_id: str,
    request: CVAnalysisRequest,
    use_case: AnalyzeCVForJobMatch = Depends(get_analyze_cv_use_case),
):
    """
    Analiza el CV de una candidatura contra la oferta de empleo.
    
    - Obtiene el CV de la candidatura
    - Obtiene la descripción de la oferta
    - Ejecuta el agente de análisis
    - Retorna puntuación y recomendaciones
    """
    try:
        result = await use_case.execute(
            application_id=application_id,
            job_offer_id=request.job_offer_id,
        )
        
        return CVAnalysisResponse(
            application_id=result["application_id"],
            analysis=result["analysis"],
            timestamp=datetime.utcnow(),
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"CV analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing CV. Check logs for details.",
        )
```

### 7.3 Schemas HTTP

```python
# app/infrastructure/http/schemas/cv_analysis_schema.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CVAnalysisRequest(BaseModel):
    job_offer_id: str = Field(..., description="ID of the job offer to compare against")

class CVAnalysisResponse(BaseModel):
    application_id: str
    analysis: dict = Field(..., description="Full analysis result from agent")
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "app-123",
                "analysis": {
                    "summary": "Strong candidate with relevant experience",
                    "candidate_score": 0.85,
                    "skills_extracted": ["Python", "FastAPI", "AWS"],
                    "experience_years": 5.0,
                    "education_level": "Master's",
                    "recommendations": ["Schedule interview", "Discuss project experience"]
                },
                "timestamp": "2026-05-02T10:30:00"
            }
        }
```

### 7.4 Memory Hook Integration

```python
# app/infrastructure/ai/memory/memory_manager.py

from bedrock_agentcore.memory.session import MemorySession

class CVAnalysisMemoryContext:
    """
    Scoped memory para análisis de CVs.
    
    Cada candidatura tiene su propio namespace:
    asa/recruitment/{application_id}/analysis/
    """
    
    def __init__(self, memory_session: MemorySession):
        self.memory_session = memory_session
    
    def get_namespace(self, application_id: str) -> str:
        return f"asa/recruitment/{application_id}/analysis/"
    
    async def save_analysis(
        self,
        application_id: str,
        analysis_result: dict,
    ):
        """Guardar resultado en memoria a largo plazo"""
        namespace = self.get_namespace(application_id)
        
        await self.memory_session.add_turns(
            [
                {
                    "role": "system",
                    "content": f"CV Analysis Result: {analysis_result['summary']}"
                }
            ],
            namespace=namespace,
        )
    
    async def get_previous_analyses(
        self,
        application_id: str,
    ) -> list:
        """Recuperar análisis previos del mismo candidato"""
        # Usar LTM search
        namespace = self.get_namespace(application_id)
        return await self.memory_session.search(
            query="previous analysis",
            namespace=namespace,
            top_k=5,
        )
```

---

## 8. Guía de Implementación

### 8.1 Fases de Implementación

#### Fase 1: Setup Base (1-2 semanas)

```
[ ] 1. Actualizar pyproject.toml con dependencias de strands + bedrock
    - Agregar: strands-agents, bedrock-agentcore, boto3
    - Run: uv sync

[ ] 2. Copiar archivos de configuración de AgentCore
    - Copiar agent/config/ completo
    - Adaptar paths en read_config.py
    - Verificar que config.json tiene valores válidos

[ ] 3. Copiar agent.py, memory.py tal cual
    - app/infrastructure/ai/agent/agent.py
    - app/infrastructure/ai/memory/memory_hook.py
    - Cambiar solo imports relativos

[ ] 4. Adaptar main.py → agent_runtime.py
    - Quitar @app.entrypoint decorator
    - Crear función async reutilizable
    - Test con unit tests
```

#### Fase 2: Puertos y Abstracción (1 semana)

```
[ ] 5. Crear puerto CVAnalyzer en dominio
    - app/domain/ports/cv_analyzer.py
    - Define interface abstracta
    - NO menciona AWS/Bedrock

[ ] 6. Crear entidad CVAnalysisResult en dominio
    - app/domain/entities/cv_analysis_result.py
    - Dataclass con campo de análisis

[ ] 7. Implementación BedrockCVAnalyzer
    - app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py
    - Implementa CVAnalyzer interface
    - Usa runtime del paso 4
```

#### Fase 3: Use Cases e Integración (1 semana)

```
[ ] 8. Crear use case AnalyzeCVForJobMatch
    - app/application/use_cases/analyze_cv_for_job_match.py
    - Inyecta puerto CVAnalyzer
    - Orquesta con repositorios existentes

[ ] 9. Actualizar dependencies.py
    - Inyectar config AI
    - Inyectar implementación BedrockCVAnalyzer
    - Inyectar use case

[ ] 10. Crear router con endpoint
    - app/infrastructure/http/routers/cv_analysis_router.py
    - POST /applications/{app_id}/analyze
    - Usa use case inyectado
```

#### Fase 4: Testing & Refinement (1 semana)

```
[ ] 11. Unit tests para cada componente
    - Mock CVAnalyzer para testing sin AWS
    - Test use cases con mocks
    - Test router con test client

[ ] 12. Integration tests
    - Test con MemorySession real (require AWS setup)
    - Test con Bedrock real si credentials disponibles
    
[ ] 13. Local testing con prompt examples
    - Usar prompt_example_stm_ltm.py como referencia
    - Test local con strands mock

[ ] 14. Documentation
    - README en ai/
    - API docs actualizados
    - Guía de configuración AWS
```

### 8.2 Orden de Tareas Específicas

```
DÍA 1-2: COPY FILES
├─ Copiar config_dto.py, config.json
├─ Copiar agent.py
├─ Copiar memory.py
└─ Copiar prompt_management_*.py, guardrails_*

DÍA 3-4: ADAPT CORE
├─ Adaptar main.py → agent_runtime.py
├─ Crear agent_factory más simple
├─ Test imports y basic invocation

DÍA 5: PORTS
├─ Crear CVAnalyzer puerto
├─ Crear CVAnalysisResult entity
├─ Revisar que no hay coupling

DÍA 6-7: IMPLEMENTATION
├─ Crear BedrockCVAnalyzer implementation
├─ Wire con strands Agent
├─ Test con simple prompt

DÍA 8-9: USE CASES
├─ Crear AnalyzeCVForJobMatch use case
├─ Wire con router
├─ End-to-end test

DÍA 10: TESTING
├─ Unit tests everywhere
├─ Mock Bedrock si necesario
├─ API test client
```

### 8.3 Checklist de Desacoplamiento

Antes de deployar, verificar:

```
DOMAIN (app/domain/)
[ ] CVAnalyzer es abstracto (ABC)
[ ] CVAnalyzer NO importa nada de infrastructure/ai/
[ ] CVAnalyzer NO importa bedrock, strands, boto3
[ ] CVAnalysisResult es dataclass puro (sin lógica de agente)
[ ] Cero referencias a AWS en entities o ports

APPLICATION (app/application/)
[ ] Use cases reciben CVAnalyzer como parámetro (inyección)
[ ] Use cases NO crean instancias de BedrockCVAnalyzer directamente
[ ] Use cases NO conocen detalles de memory_session o agentes
[ ] Cero imports de infrastructure/ai en use cases

INFRASTRUCTURE (app/infrastructure/ai/)
[ ] BedrockCVAnalyzer implementa CVAnalyzer (interface)
[ ] BedrockCVAnalyzer puede cambiar sin afectar domain
[ ] Agent creation es privado (_run_agent)
[ ] Config es inyectada (no hardcoded)
[ ] AWS credentials son obtenidas via boto3 (no hardcoded)

ROUTER (app/infrastructure/http/)
[ ] Router usa Use Case (no invoca agente directamente)
[ ] Router NO conoce BedrockCVAnalyzer
[ ] Response es Pydantic schema (dejan DTO de dominio)

TESTING
[ ] CVAnalyzer puede ser mockeado fácilmente
[ ] Domain tests NO requieren AWS credentials
[ ] Use case tests usan mock de CVAnalyzer
[ ] Integration tests separan domain de infrastructure
```

---

## 9. Recomendaciones Finales

### 9.1 Lo que SÍ Deberías Hacer

✅ **COPIAR DIRECTO** (Sin cambios):
1. `agent/config/config_dto.py`
2. `agent/memory.py` (solo minor imports)
3. `agent/config/read_config.py` pattern
4. `agent/agent.py` (estructura, solo adaptar prompts)

✅ **ADAPTAR Y REUTILIZAR** (Minor changes):
1. `agent/main.py` → Descargar entrypoint, reutilizar lógica
2. `agent/config/config.json` → Copiar estructura, cambiar valores
3. Strands imports → Mantener los mismos

✅ **CREAR NUEVO** (Específico para tu app):
1. `CVAnalyzer` puerto (FUNDAMENTAL)
2. `BedrockCVAnalyzer` implementador (FUNDAMENTAL)
3. `AnalyzeCVForJobMatch` use case (dominio)
4. Prompts especializados para CV analysis

### 9.2 Lo que NO Deberías Hacer

❌ **NO COPIAR**:
1. `deploy.py` → Usa bedrock-agentcore toolkit (específico)
2. `buildspec.yml` → Infraestructura AWS CodeBuild
3. Terraform → Reemplazar con Docker si es app de FastAPI
4. Toda la setup.sh → Usar pyproject.toml + uv

❌ **NO ACOPLAR**:
1. Dominio a AWS services
2. Dominio a Bedrock specifics
3. Use cases a BedrockCVAnalyzer concreto
4. Routers a detalles internos de agente

❌ **NO IGNORAR**:
1. Testing con mocks
2. Error handling robusto
3. Logging estructurado
4. Configuration management

### 9.3 Decisiones Arquitectónicas Clave

#### Decisión 1: ¿Usar Gateway Remoto?

```
OPCIÓN A: Sin Gateway (Recomendado para MVP)
├─ Solo herramientas locales (si las necesitas)
├─ Más simple
├─ No requiere infraestructura adicional
└─ Limitado a what you define

OPCIÓN B: Con Gateway Local (si tienes herramientas internas)
├─ MCP server local en tu infraestructura
├─ Expone herramientas via Gateway
├─ Escalable a múltiples backends
└─ Complejidad moderada: +setup, +testing

OPCIÓN C: Con Gateway Remoto (Full Enterprise)
├─ AWS AgentCore Gateway en otra cuenta
├─ Múltiples targets (APIs, Lambda, etc)
├─ Maximum flexibility
└─ Requires AWS setup + Terraform (out of scope aquí)

RECOMENDACIÓN: Empezar con OPCIÓN A (sin gateway)
- Agente con tools estándar (web search, file ops, etc)
- Si necesitas herramientas especiales después, agregar Gateway
```

#### Decisión 2: ¿Memory STM + LTM?

```
OPCIÓN A: STM Solo (Recomendado para inicios)
├─ Memoria de sesión
├─ Conversación coherente
├─ Más barato (menos storage)
└─ Suficiente para análisis de CV

OPCIÓN B: STM + LTM (Cuando escales)
├─ Memoria a largo plazo
├─ Recordar preferencias de candidatos
├─ Más caro (más storage + semantic search)
└─ Requiere MemorySession + LTMStrategy setup

RECOMENDACIÓN: Empezar STM, agregar LTM cuando:
- Tengas múltiples CVs del mismo candidato
- Quieras recordar decisiones previas
- Necesites auditoría de análisis previos
```

#### Decisión 3: ¿Local vs AWS Deployment?

```
OPCIÓN A: Local (Desarrollo)
├─ FastAPI local en tu máquina
├─ Bedrock credentials vía AWS_PROFILE
├─ No requiere Terraform
├─ Testing rápido
└─ Perfecto para MVP

OPCIÓN B: Docker Local (Testing en isolation)
├─ Containerizar FastAPI
├─ Mismo setup que producción
├─ Mejor para CI/CD testing
└─ Aún local, pero más real

OPCIÓN C: AWS ECS/Lambda (Producción)
├─ FastAPI en ECS Fargate
├─ Bedrock calls desde AWS
├─ Costs optimizados
└─ Requiere Terraform + deployment pipeline

RECOMENDACIÓN: MVP en A, luego B, finalmente C
```

#### Decisión 4: ¿Mock o Real Bedrock Tests?

```
OPCIÓN A: Mock Tests (Recomendado)
├─ Mock CVAnalyzer en unit tests
├─ Fast, repeatable
├─ No cuesta dinero
├─ Perfect para CI/CD
└─ Ejemplo:
   def test_analyze_cv_match():
       mock_analyzer = MagicMock(spec=CVAnalyzer)
       mock_analyzer.analyze.return_value = CVAnalysisResult(...)
       use_case = AnalyzeCVForJobMatch(mock_analyzer, ...)
       result = use_case.execute(...)
       assert result.candidate_score > 0.5

OPCIÓN B: Real Bedrock Tests (Para approval)
├─ Test contra Bedrock real
├─ Cuesta dinero (small amount)
├─ Valida configuración AWS
├─ Haz después de mock tests
└─ Maybe en PR final

RECOMENDACIÓN: 95% mock tests, 5% real tests
```

### 9.4 Roadmap de Evolución

```
MVP (Mes 1):
├─ CVAnalyzer simple (básico scoring)
├─ STM solo
├─ Sin Gateway
├─ Local testing
└─ DELIVERABLE: Agente analiza CVs básicamente

V1 (Mes 2-3):
├─ LTM para recordar decisiones
├─ Mejor prompt engineering
├─ Multiple job offer types
├─ Guardrails para safety
├─ DELIVERABLE: Agente entiende contexto histórico

V2 (Mes 4-5):
├─ Gateway para herramientas externas
├─ Integration con HR system
├─ Batch analysis
├─ Advanced memory search
├─ DELIVERABLE: Agente hace más cosas (lookup, verify, etc)

V3+ (Futuro):
├─ Múltiples agentes especializados
├─ Herramientas personalizadas
├─ Deployment en AWS
├─ Advanced analytics
├─ DELIVERABLE: Platform completamente integrada
```

### 9.5 Checklist Final de Integración

```
PRE-INTEGRACIÓN
[ ] Tienes AWS credentials configurados (AWS_PROFILE o env vars)
[ ] Tienes Bedrock access en tu region
[ ] Terraform/CDK setup para Memory resource (si usas LTM)
[ ] pyproject.toml actualizado con strands + bedrock dependencies
[ ] uv sync ejecutado y sin errores

DURANTE-INTEGRACIÓN
[ ] Porta CVAnalyzer creado (100% independiente)
[ ] BedrockCVAnalyzer implementa CVAnalyzer
[ ] Agent creation funciona sin errors
[ ] Use case orquesta correctamente
[ ] Router endpoint funciona (end-to-end)

POST-INTEGRACIÓN
[ ] Tests corren sin errores (mocks)
[ ] API endpoint devuelve respuestas válidas
[ ] Configuration file tiene valores correctos
[ ] Logging muestra ejecución correcta
[ ] Documentation actualizada
[ ] Legacy code sigue funcionando (backward compat)

PRODUCTION-READY
[ ] Error handling robusto (timeouts, retries, fallbacks)
[ ] Monitoring y observability (logs, metrics, traces)
[ ] Secrets management (no hardcoded credentials)
[ ] Cost monitoring (set up AWS budgets)
[ ] Disaster recovery plan
```

---

## 10. Conclusión

### 10.1 Resumen Ejecutivo Final

| Elemento | Evaluación | Impacto |
|----------|-----------|--------|
| **Viabilidad** | ✅ Alta | Integración completamente posible |
| **Complejidad** | 🟡 Moderada | 2-4 semanas con equipo experiementado |
| **Riesgo del Dominio** | ✅ Bajo | Arquitectura hex protege bien |
| **Costo AWS** | 🟡 Moderado | ~$200-500/mes para smallscale |
| **Mantenibilidad** | ✅ Alta | Patrón de puertos es testeable |
| **Escalabilidad** | ✅ Alta | Fácil agregar más agentes/features |

### 10.2 Decisión Recomendada

```
RECOMENDACIÓN FINAL:

1. Usar AgentCore Blueprint como reference
2. Copiar ~70% del código (agent, memory, config patterns)
3. Crear puerto CVAnalyzer (abstracción crítica)
4. Implementar BedrockCVAnalyzer (en infrastructure)
5. Mantener dominio 100% independiente
6. Testear con mocks durante desarrollo
7. Deployer como FastAPI app (no serverless Bedrock runtime)
8. Escalable a múltiples agentes después

TIMELINE:
- Semana 1-2: Setup + copy files
- Semana 3: Ports + abstraction
- Semana 4: Use cases + integration
- Semana 5: Testing + documentation

RIESGO: BAJO (hexagonal pattern te protege)
VALOR: ALTO (agentes + memoria = powerful)
RECOMENDACIÓN: PROCEDE CON CONFIANZA
```

---

## 11. Apéndice: Recursos

### 11.1 Archivos a Copiar de AgentCore

```python
# Lista con líneas de código aproximadas

agent/config/config_dto.py                  # ~50 líneas
agent/config/config.json                    # ~30 líneas
agent/config/read_config.py                 # ~40 líneas
agent/config/prompt_management_dto.py       # ~40 líneas
agent/config/read_prompt_management.py      # ~60 líneas
agent/config/guardrails_dto.py              # ~30 líneas
agent/config/read_guardrails.py             # ~40 líneas
agent/agent.py                              # ~219 líneas
agent/memory.py                             # ~225 líneas
---
TOTAL: ~780 líneas de código reutilizable
```

### 11.2 Archivos Nuevos a Crear

```python
# En tu backend

app/domain/ports/cv_analyzer.py             # ~60 líneas (nuevo)
app/domain/entities/cv_analysis.py          # ~40 líneas (nuevo)
app/application/use_cases/analyze_cv_*.py   # ~100 líneas (nuevo)
app/infrastructure/ai/cv_analyzer/*.py      # ~150 líneas (nuevo)
app/infrastructure/ai/config/custom_*.py    # ~100 líneas (adapt)
app/infrastructure/http/routers/analysis.py # ~80 líneas (nuevo)
app/infrastructure/http/schemas/analysis.py # ~50 líneas (nuevo)
tests/infrastructure/ai/test_*.py           # ~200 líneas (nuevo)
---
TOTAL: ~780 líneas de nuevo código
```

### 11.3 Referencias de Código

Ver `Agent creation` patterns en:
- agent/agent.py líneas 10-50 (create_agent)
- agent/main.py líneas 60-90 (_run_agent)

Ver `Memory patterns` en:
- agent/memory.py líneas 60-100 (STM loading)
- agent/memory.py líneas 110-160 (LTM injection)

Ver `Config patterns` en:
- agent/config/config.json (estructura)
- agent/config/read_config.py (loaders)

---

**Documento preparado para arquitectos y tech leads**
*Formato: Technical Architecture Review + Integration Roadmap*
*Aprobado para: Feature Planning, Sprint Estimation, Resource Allocation*
