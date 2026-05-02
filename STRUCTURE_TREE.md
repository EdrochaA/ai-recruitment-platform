# 📁 Estructura Final Integrada: Árbol Completo

*Vista completa de cómo quedará tu backend con AgentCore integrado*

---

## 1. Estructura Completa con Colores y Explicaciones

```
backend/
│
├── 📄 pyproject.toml                    ← ACTUALIZAR: agregar strands, bedrock
│   │   ├─ strands-agents>=0.8.0
│   │   ├─ bedrock-agentcore
│   │   └─ boto3
│
├── 📄 README.md                         ← ACTUALIZAR: documentar cambios
│
├── 📂 app/
│
│   ├── 🐍 __init__.py
│   ├── 🐍 main.py                       ← ACTUALIZAR: incluye cv_analysis_router
│   │   └─ Ahora incluye:
│   │       └─ app.include_router(cv_analysis_router)
│   │
│   ├── 📂 domain/                       ← CAMBIOS MÍNIMOS (solo +1 puerto)
│   │   ├── 🐍 __init__.py
│   │   │
│   │   ├── 📂 entities/                 ← Entidades puras (sin lógica)
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 job_offer.py          [SIN CAMBIOS]
│   │   │   ├── 🐍 job_application.py    [ACTUALIZADO +3 campos]
│   │   │   │   └─ NEW: cv_analysis_id
│   │   │   │   └─ NEW: cv_analysis_score
│   │   │   │   └─ NEW: cv_analysis_timestamp
│   │   │   │
│   │   │   └── 🐍 cv_analysis.py        [NUEVO]
│   │   │       └─ @dataclass
│   │   │           ├─ id
│   │   │           ├─ application_id
│   │   │           ├─ result: CVAnalysisResult
│   │   │           ├─ analyzed_at
│   │   │           └─ processing_time_ms
│   │   │
│   │   └── 📂 ports/                    ← Interfaces (abstracciones)
│   │       ├── 🐍 __init__.py
│   │       ├── 🐍 job_application_repository.py    [SIN CAMBIOS]
│   │       ├── 🐍 job_offer_repository.py          [SIN CAMBIOS]
│   │       ├── 🐍 file_storage.py                   [SIN CAMBIOS]
│   │       │
│   │       ├── 🐍 cv_analyzer.py                    [NUEVO - CRÍTICO]
│   │       │   ├─ @dataclass CVAnalysisResult
│   │       │   └─ ABC CVAnalyzer
│   │       │       ├─ async analyze()
│   │       │       └─ async batch_analyze()
│   │       │
│   │       └── 🐍 cv_analysis_repository.py         [NUEVO]
│   │           ├─ save()
│   │           ├─ find_by_id()
│   │           ├─ find_by_application()
│   │           └─ update()
│   │
│   ├── 📂 application/                  ← CAMBIOS MÍNIMOS (solo +1 use case)
│   │   ├── 🐍 __init__.py
│   │   │
│   │   └── 📂 use_cases/                ← Orquestradores
│   │       ├── 🐍 __init__.py
│   │       ├── 🐍 create_job_offer.py              [SIN CAMBIOS]
│   │       ├── 🐍 list_job_offers.py               [SIN CAMBIOS]
│   │       ├── 🐍 create_application.py            [SIN CAMBIOS]
│   │       ├── 🐍 list_applications_by_job_offer.py [SIN CAMBIOS]
│   │       ├── 🐍 upload_application_cv.py         [SIN CAMBIOS]
│   │       │
│   │       └── 🐍 analyze_cv_for_job_match.py      [NUEVO]
│   │           └─ class AnalyzeCVForJobMatch
│   │               ├─ __init__(cv_analyzer, cv_analysis_repo, ...)
│   │               └─ execute(application_id, job_offer_id) → CVAnalysis
│   │
│   ├── 📂 infrastructure/               ← CAMBIOS SIGNIFICATIVOS (carpeta ai/ nueva)
│   │   ├── 🐍 __init__.py
│   │   │
│   │   ├── 📂 http/                     ← CAMBIOS LEVES (+1 router)
│   │   │   ├── 🐍 __init__.py
│   │   │   │
│   │   │   ├── 📂 routers/
│   │   │   │   ├── 🐍 __init__.py
│   │   │   │   ├── 🐍 job_offer_router.py          [SIN CAMBIOS]
│   │   │   │   ├── 🐍 application_router.py        [SIN CAMBIOS]
│   │   │   │   │
│   │   │   │   └── 🐍 cv_analysis_router.py        [NUEVO]
│   │   │   │       ├─ router = APIRouter(prefix="/applications")
│   │   │   │       └─ @router.post("/{app_id}/analyze")
│   │   │   │           async def analyze_application(...)
│   │   │   │
│   │   │   └── 📂 schemas/
│   │   │       ├── 🐍 __init__.py
│   │   │       ├── 🐍 job_offer_schema.py          [SIN CAMBIOS]
│   │   │       ├── 🐍 application_schema.py        [SIN CAMBIOS]
│   │   │       │
│   │   │       └── 🐍 cv_analysis_schema.py        [NUEVO]
│   │   │           ├─ class AnalyzeRequest
│   │   │           ├─ class AnalysisMetadata
│   │   │           └─ class AnalyzeResponse
│   │   │
│   │   ├── 📂 persistence/              ← CAMBIOS LEVES (+1 repo)
│   │   │   ├── 🐍 __init__.py
│   │   │   │
│   │   │   └── 📂 in_memory/
│   │   │       ├── 🐍 __init__.py
│   │   │       ├── 🐍 in_memory_job_offer_repository.py           [SIN CAMBIOS]
│   │   │       ├── 🐍 in_memory_job_application_repository.py     [SIN CAMBIOS]
│   │   │       │
│   │   │       └── 🐍 in_memory_cv_analysis_repository.py         [NUEVO]
│   │   │           └─ class InMemoryCVAnalysisRepository
│   │   │               ├─ save()
│   │   │               ├─ find_by_id()
│   │   │               ├─ find_by_application()
│   │   │               └─ update()
│   │   │
│   │   ├── 📂 storage/                  ← SIN CAMBIOS
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 local_file_storage.py            [SIN CAMBIOS]
│   │   │
│   │   └── 📂 ai/                       ← 🆕 NUEVA CARPETA COMPLETA
│   │       ├── 🐍 __init__.py
│   │       │
│   │       ├── 📂 config/               ← Configuración (from AgentCore)
│   │       │   ├── 🐍 __init__.py
│   │       │   │
│   │       │   ├── 📄 config.json                  [COPIAR de AgentCore]
│   │       │   │   └─ Contiene:
│   │       │   │       ├─ llm (modelo, región, parámetros)
│   │       │   │       ├─ agent (metadata)
│   │       │   │       ├─ gateway (opcional)
│   │       │   │       └─ memory (STM/LTM config)
│   │       │   │
│   │       │   ├── 🐍 config_dto.py                [COPIAR de AgentCore]
│   │       │   │   ├─ @dataclass LLMConfig
│   │       │   │   ├─ @dataclass AgentConfig
│   │       │   │   ├─ @dataclass MemoryConfig
│   │       │   │   └─ @dataclass AIConfig
│   │       │   │
│   │       │   ├── 🐍 read_config.py               [COPIAR de AgentCore + adaptar]
│   │       │   │   └─ def read_config() → AIConfig
│   │       │   │
│   │       │   ├── 📄 prompt_management.json       [COPIAR de AgentCore]
│   │       │   ├── 🐍 prompt_management_dto.py     [COPIAR de AgentCore]
│   │       │   ├── 🐍 read_prompt_management.py    [COPIAR + adaptar]
│   │       │   │
│   │       │   ├── 📄 guardrails.json              [COPIAR de AgentCore]
│   │       │   ├── 🐍 guardrails_dto.py            [COPIAR de AgentCore]
│   │       │   └── 🐍 read_guardrails.py           [COPIAR + adaptar]
│   │       │
│   │       ├── 📂 agent/                ← Núcleo del agente (from AgentCore)
│   │       │   ├── 🐍 __init__.py
│   │       │   │
│   │       │   ├── 🐍 agent.py                     [COPIAR de AgentCore]
│   │       │   │   ├─ def create_agent()
│   │       │   │   ├─ def resolve_system_prompt()
│   │       │   │   └─ def get_prompt_management()
│   │       │   │
│   │       │   └── 🐍 agent_factory.py             [NUEVO - simplificado]
│   │       │       └─ class AgentFactory
│   │       │           └─ create_analysis_agent()
│   │       │
│   │       ├── 📂 memory/               ← Gestión de memoria (from AgentCore)
│   │       │   ├── 🐍 __init__.py
│   │       │   │
│   │       │   ├── 🐍 memory_hook.py               [COPIAR de AgentCore]
│   │       │   │   ├─ class MemoryHook(HookProvider)
│   │       │   │   ├─ on_agent_initialized()       (STM: carga histórico)
│   │       │   │   ├─ on_message_added()           (LTM: inyecta contexto)
│   │       │   │   └─ save_interaction()           (persiste conversación)
│   │       │   │
│   │       │   └── 🐍 memory_manager.py            [NUEVO - wrapper]
│   │       │       ├─ class MemorySessionManager
│   │       │       ├─ get_session(actor_id)
│   │       │       └─ ensure_namespace()
│   │       │
│   │       ├── 📂 gateway/              ← Herramientas MCP (from AgentCore)
│   │       │   ├── 🐍 __init__.py
│   │       │   │
│   │       │   ├── 🐍 gateway_client.py            [COPIAR + adaptar de AgentCore]
│   │       │   │   ├─ class GatewayClient
│   │       │   │   ├─ resolve_gateway_url()
│   │       │   │   └─ load_mcp_tools()
│   │       │   │
│   │       │   └── 🐍 mcp_tools_loader.py          [NUEVO - opcional]
│   │       │       └─ def load_available_tools()
│   │       │
│   │       ├── 📂 runtime/              ← Ejecución del agente (from AgentCore)
│   │       │   ├── 🐍 __init__.py
│   │       │   │
│   │       │   └── 🐍 agent_runtime.py             [ADAPTADO de main.py]
│   │       │       ├─ class AgentRuntime
│   │       │       ├─ async _run_agent()
│   │       │       └─ parse_response()
│   │       │
│   │       └── 📂 cv_analyzer/          ← Implementación para análisis de CV
│   │           ├── 🐍 __init__.py
│   │           │
│   │           ├── 🐍 bedrock_cv_analyzer.py       [NUEVO - CRÍTICO]
│   │           │   └─ class BedrockCVAnalyzer(CVAnalyzer)
│   │           │       ├─ __init__(config, memory_manager)
│   │           │       ├─ async analyze(cv_text, job_desc, candidate_id)
│   │           │       ├─ _create_system_prompt()
│   │           │       ├─ _create_user_message()
│   │           │       ├─ async _run_agent()
│   │           │       └─ _parse_analysis_response()
│   │           │
│   │           └── 🐍 cv_analysis_prompts.py       [NUEVO - opcional]
│   │               ├─ SYSTEM_PROMPT_TEMPLATE
│   │               ├─ USER_MESSAGE_TEMPLATE
│   │               └─ def get_prompt_for_job_type()
│   │
│   └── 📂 shared/                       ← CAMBIOS MODERADOS (inyecciones nuevas)
│       ├── 🐍 __init__.py
│       │
│       └── 🐍 dependencies.py            [ACTUALIZAR - +5 nuevas inyecciones]
│           ├─ # Existing (sin cambios)
│           ├─ job_offer_repository = InMemoryJobOfferRepository()
│           ├─ job_application_repository = InMemoryJobApplicationRepository()
│           ├─ file_storage = LocalFileStorage()
│           │
│           ├─ # NEW: AI Configuration
│           ├─ ai_config = read_config(...)
│           ├─ memory_manager = MemorySessionManager(...)
│           ├─ cv_analysis_repository = InMemoryCVAnalysisRepository()
│           ├─ cv_analyzer: CVAnalyzer = BedrockCVAnalyzer(...)
│           │
│           ├─ # Existing getters (sin cambios)
│           ├─ def get_create_job_offer_use_case()
│           ├─ def get_list_job_offers_use_case()
│           ├─ def get_create_application_use_case()
│           ├─ def get_list_applications_use_case()
│           ├─ def get_upload_application_cv_use_case()
│           │
│           └─ # NEW getter
│               └─ def get_analyze_cv_use_case() → AnalyzeCVForJobMatch
│
├── 📂 tests/                            ← ESTRUCTURA DE TESTS (Optional pero recomendado)
│   ├── 🐍 __init__.py
│   │
│   ├── 📂 domain/
│   │   ├── 🐍 __init__.py
│   │   └── 📂 entities/
│   │       └── test_cv_analysis.py       [NUEVO]
│   │
│   ├── 📂 application/
│   │   ├── 🐍 __init__.py
│   │   └── 📂 use_cases/
│   │       ├── test_create_job_offer.py  [EXISTENTE]
│   │       ├── test_create_application.py [EXISTENTE]
│   │       └── test_analyze_cv.py        [NUEVO]
│   │
│   └── 📂 infrastructure/
│       ├── 🐍 __init__.py
│       │
│       ├── 📂 http/
│       │   └── test_cv_analysis_router.py [NUEVO]
│       │
│       └── 📂 ai/
│           ├── 🐍 __init__.py
│           ├── test_bedrock_cv_analyzer.py [NUEVO]
│           └── test_config_loading.py     [NUEVO]
│
└── 📂 scripts/                          ← UTILIDADES (Optional)
    ├── setup_bedrock.sh                 [NUEVO]
    │   └─ Script para verificar Bedrock access
    │
    ├── test_local_agent.py              [NUEVO]
    │   └─ Script para testing local sin endpoint
    │
    └── check_config.py                  [NUEVO]
        └─ Script para validar configuration
```

---

## 2. Cambios por Carpeta: Resumen Ejecutivo

```
┌─────────────────────────────────────────────────────────┐
│              CAMBIOS POR LAYER                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ DOMAIN (app/domain/)                                    │
│ ├─ Entities: +1 nuevo (CVAnalysis)                     │
│ ├─ Ports: +2 nuevos (CVAnalyzer, CVAnalysisRepository) │
│ └─ Cambio total: +3 archivos (180 LOC)                 │
│    ✅ Desacoplamiento perfecto                         │
│                                                         │
│ APPLICATION (app/application/)                          │
│ ├─ Use Cases: +1 nuevo (AnalyzeCVForJobMatch)          │
│ ├─ Cambio total: +1 archivo (120 LOC)                  │
│    ✅ Orquestación limpia                              │
│                                                         │
│ INFRASTRUCTURE (app/infrastructure/)                    │
│ ├─ HTTP:          +1 router + 1 schema (150 LOC)       │
│ ├─ Persistence:   +1 repository (80 LOC)               │
│ ├─ Storage:       SIN CAMBIOS ✅                        │
│ ├─ AI (NEW):      CARPETA COMPLETA (1000+ LOC)         │
│ │   ├─ config/    (400 LOC from AgentCore)             │
│ │   ├─ agent/     (300 LOC from AgentCore)             │
│ │   ├─ memory/    (250 LOC from AgentCore)             │
│ │   ├─ gateway/   (150 LOC optional)                   │
│ │   ├─ runtime/   (200 LOC adapted)                    │
│ │   └─ cv_analyzer/ (150 LOC custom)                   │
│ └─ Cambio total: +1,450 LOC nuevas                     │
│    ✅ Aisladas en carpeta ai/                          │
│                                                         │
│ SHARED (app/shared/)                                    │
│ ├─ Dependencies: +5 inyecciones nuevas                  │
│ ├─ Cambio total: ~50 LOC adicionales                   │
│    ✅ Inyección de dependencias limpia                 │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ TOTAL CAMBIOS: ~1,800 LOC nuevas                        │
├─────────────────────────────────────────────────────────┤
│ ARCHIVOS MODIFICADOS: 7                                 │
│ ARCHIVOS NUEVOS: 25+                                     │
│ ARCHIVOS SIN CAMBIOS: 10+                                │
│                                                         │
│ IMPACTO ARQUITECTURA: MÍNIMO ✅                         │
│ DESACOPLAMIENTO: PERFECTO ✅                            │
│ ESCALABILIDAD: MEJORADA ✅                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Flujo de Datos: Entrada → Salida

```
CLIENT REQUEST (HTTP)
│
│ POST /applications/app-123/analyze
│ {
│   "job_offer_id": "job-456"
│ }
│
└──→ app/infrastructure/http/routers/cv_analysis_router.py
     ├─ Parse request to AnalyzeRequest
     │
     └──→ Dependency Injection
          └─ get_analyze_cv_use_case()
             │
             └──→ app/shared/dependencies.py
                  └─ Returns AnalyzeCVForJobMatch instance
                     - Injected: cv_analyzer (BedrockCVAnalyzer)
                     - Injected: cv_analysis_repository
                     - Injected: job_application_repository
                     - Injected: job_offer_repository
│
└──→ app/application/use_cases/analyze_cv_for_job_match.py
     │
     ├─ VALIDATION LAYER
     │  ├─ job_app_repo.find_by_id(app_id)
     │  ├─ job_offer_repo.find_by_id(job_offer_id)
     │  └─ Assert: application.cv_text exists
     │
     └──→ HEXAGONAL BOUNDARY ⬤ (crosses into infrastructure/ai)
          │
          └─ cv_analyzer.analyze(cv_text, job_desc, candidate_id)
             │
             └──→ app/infrastructure/ai/cv_analyzer/bedrock_cv_analyzer.py
                  │
                  ├─ Create system prompt
                  ├─ Create user message
                  │
                  └──→ INVOKE AGENT
                       │
                       └──→ app/infrastructure/ai/agent/agent.py
                            ├─ create_agent()
                            ├─ Set tools from gateway (optional)
                            ├─ Load memory (STM/LTM)
                            │
                            └──→ AWS BEDROCK RUNTIME
                                 ├─ Model: Claude
                                 ├─ Tools: MCP (optional)
                                 ├─ Safety: Guardrails (optional)
                                 └─ Returns: JSON response
                       │
                       └─ Parse JSON response
                       └─ Validate response
                       └─ Map to CVAnalysisResult
                  │
                  └──→ Return CVAnalysisResult
                       └─ No AWS dependencies visible to domain
│
└──→ Back to use_case.execute()
     │
     ├─ Create CVAnalysis entity
     ├─ cv_analysis_repo.save(cv_analysis)
     ├─ Update job_application with analysis_id
     ├─ job_app_repo.update(application)
     │
     └──→ Return CVAnalysis
│
└──→ Back to router
     │
     ├─ Convert entity to AnalyzeResponse (Pydantic)
     │
     └──→ HTTP 200 OK
          {
            "analysis_id": "analysis-xyz",
            "application_id": "app-123",
            "job_offer_id": "job-456",
            "analysis": {
              "summary": "...",
              "candidate_score": 0.85,
              "skills_extracted": [...],
              "experience_years": 5.0,
              "education_level": "...",
              "recommendations": [...]
            },
            "analyzed_at": "2026-05-02T..."
          }
│
└──→ CLIENT receives response
```

---

## 4. Dependencias Visualizadas

### 4.1 Dependency Graph: Sin Ciclos

```
🔴 DOMAIN (Pure)
├─ app.domain.entities.*
├─ app.domain.ports.*
└─ Cero dependencias a infrastructure ✅

       ↑ (used by)
       │
       │
🟠 APPLICATION (Orchestration)
├─ app.application.use_cases.*
└─ Solo conoce: domain.ports, domain.entities ✅
   No conoce: infrastructure, AWS, Bedrock ✅

       ↑ (used by)
       │
       │
🟡 INFRASTRUCTURE
├─ HTTP Layer (routers, schemas)
├─ Persistence Layer (repositories)
├─ Storage Layer (file storage)
└─ AI Layer (NEW)
   
   ├─ app.infrastructure.ai.cv_analyzer
   │  └─ Implementa: domain.ports.CVAnalyzer ✅
   │     Usa: strands, bedrock, boto3 ✅
   │
   └─ app.infrastructure.ai.config
      └─ Configura: agent, memoria, gateway ✅

       ↑ (used by)
       │
       │
🔵 SHARED
├─ Dependency Injection
└─ Config Management

       ↑ (used by)
       │
       │
🟢 ENTRY POINT
├─ app.main (FastAPI)
└─ Main orchestrator
```

### 4.2 Import Rules

```
✅ ALLOWED:

domain/ imports:
└─ dataclasses, typing, abc (stdlib only)

application/ imports:
├─ domain/
├─ typing, dataclasses (stdlib only)
└─ No third-party libs ✅

infrastructure/ imports:
├─ domain/
├─ application/
├─ strands, bedrock, boto3, fastapi
└─ Any third-party library ✅

shared/ imports:
├─ domain/
├─ application/
├─ infrastructure/
├─ All third-party libs
└─ Setup point ✅


❌ FORBIDDEN:

domain/ includes:
├─ AWS/Bedrock imports ❌
├─ FastAPI imports ❌
└─ strands imports ❌

application/ includes:
├─ FastAPI imports ❌
├─ AWS imports ❌
└─ strands imports ❌

infrastructure/http/ includes:
├─ Bedrock direct imports ❌
└─ Should use ai/ subsystem ❌
```

---

## 5. Migration Checklist: Step by Step

```
PHASE 1: COPY FILES (Day 1-2)
─────────────────────────────

Copiar de AgentCore blueprint:
├─ agent/config/config_dto.py → app/infrastructure/ai/config/config_dto.py
├─ agent/config/config.json → app/infrastructure/ai/config/config.json
├─ agent/config/read_config.py → app/infrastructure/ai/config/read_config.py
├─ agent/agent.py → app/infrastructure/ai/agent/agent.py
├─ agent/memory.py → app/infrastructure/ai/memory/memory_hook.py
├─ agent/config/prompt_management_* → app/infrastructure/ai/config/
├─ agent/config/guardrails_* → app/infrastructure/ai/config/

Actualizar en tus archivos:
├─ pyproject.toml: agregar strands, bedrock, boto3
├─ app/main.py: verificar configuración


PHASE 2: CREATE PORTS (Day 3)
─────────────────────────────

Crear en domain/ports/:
├─ cv_analyzer.py
│  ├─ @dataclass CVAnalysisResult
│  ├─ @abstractmethod analyze()
│  └─ @abstractmethod batch_analyze()
│
└─ cv_analysis_repository.py
   ├─ @abstractmethod save()
   ├─ @abstractmethod find_by_id()
   ├─ @abstractmethod find_by_application()
   └─ @abstractmethod update()

Crear en domain/entities/:
└─ cv_analysis.py
   └─ @dataclass CVAnalysis


PHASE 3: CREATE IMPLEMENTATION (Day 4-5)
─────────────────────────────────────────

Crear en infrastructure/ai/cv_analyzer/:
└─ bedrock_cv_analyzer.py
   └─ class BedrockCVAnalyzer(CVAnalyzer)
      ├─ Implementa: analyze()
      ├─ Usa: create_agent() de agent/
      ├─ Usa: MemoryHook de memory/
      └─ Usa: config de config/

Crear en infrastructure/ai/runtime/:
└─ agent_runtime.py
   └─ class AgentRuntime
      ├─ _run_agent()
      └─ parse_response()

Crear en infrastructure/persistence/in_memory/:
└─ in_memory_cv_analysis_repository.py
   └─ class InMemoryCVAnalysisRepository(CVAnalysisRepository)


PHASE 4: WIRE USE CASES (Day 6)
────────────────────────────────

Crear use case:
└─ app/application/use_cases/analyze_cv_for_job_match.py
   └─ class AnalyzeCVForJobMatch
      ├─ __init__(cv_analyzer, repos)
      └─ execute(application_id, job_offer_id)

Actualizar dependencies:
└─ app/shared/dependencies.py
   ├─ cv_analyzer = BedrockCVAnalyzer(...)
   ├─ cv_analysis_repository = InMemoryCVAnalysisRepository()
   └─ def get_analyze_cv_use_case()

Actualizar main.py:
└─ include cv_analysis_router


PHASE 5: CREATE HTTP LAYER (Day 6-7)
─────────────────────────────────────

Crear router:
└─ app/infrastructure/http/routers/cv_analysis_router.py
   └─ @router.post("/applications/{app_id}/analyze")
      └─ async def analyze_application()

Crear schemas:
└─ app/infrastructure/http/schemas/cv_analysis_schema.py
   ├─ class AnalyzeRequest
   ├─ class AnalysisMetadata
   └─ class AnalyzeResponse


PHASE 6: TESTING (Day 8)
─────────────────────────

Tests unitarios:
├─ tests/application/use_cases/test_analyze_cv.py
├─ tests/infrastructure/ai/test_bedrock_cv_analyzer.py
└─ tests/infrastructure/http/test_cv_analysis_router.py

Run tests:
├─ pytest -v tests/
├─ pytest --cov (coverage check)
└─ curl tests


PHASE 7: DOCUMENTATION (Day 9-10)
──────────────────────────────────

Actualizar:
├─ README.md: nuevo endpoint documentado
├─ API docs: Swagger auto-generado por FastAPI
├─ ARCHITECTURE_INTEGRATION_ANALYSIS.md: ya creado ✅
├─ INTEGRATION_IMPLEMENTATION_GUIDE.md: ya creado ✅
└─ EXECUTIVE_SUMMARY.md: ya creado ✅
```

---

## 6. Comparativa: Antes vs. Después de Integración

```
┌──────────────────────────────────────────────────────────────────┐
│                          BEFORE                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Endpoints:
│ POST   /job-offers
│ GET    /job-offers
│ POST   /applications
│ GET    /applications/job-offer/{id}
│ POST   /applications/{id}/cv
│
│ Capabilities:
│ - Job offer management
│ - Application management
│ - CV upload (storage)
│ - No AI/Analysis ❌
│
│ Architecture:
│ - Clean Hexagonal ✅
│ - Testable ✅
│ - No AWS dependencies ✅
│
│ Total LOC: ~2,000
│
└──────────────────────────────────────────────────────────────────┘

                            ║
                            ║ Integration
                            ▼

┌──────────────────────────────────────────────────────────────────┐
│                          AFTER                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Endpoints:
│ POST   /job-offers
│ GET    /job-offers
│ POST   /applications
│ GET    /applications/job-offer/{id}
│ POST   /applications/{id}/cv
│ POST   /applications/{id}/analyze            ← NEW ✅
│ GET    /applications/{id}/analysis           ← Future
│
│ Capabilities:
│ - Job offer management ✅
│ - Application management ✅
│ - CV upload (storage) ✅
│ - CV Analysis with AI ✅ NEW
│ - Memory management (STM/LTM) ✅ NEW
│ - Semantic search ✅ NEW (future)
│
│ Architecture:
│ - Clean Hexagonal ✅ (MORE CLEAN)
│ - Testable ✅ (MORE TESTABLE)
│ - Scalable ✅ (NEW)
│ - AWS dependencies isolated ✅ (in /ai/)
│
│ Total LOC: ~3,800 (+1,800 nuevas)
│
└──────────────────────────────────────────────────────────────────┘
```

---

**Estructura final lista para implementar**
*Copiar/pega directamente en tu proyecto*
