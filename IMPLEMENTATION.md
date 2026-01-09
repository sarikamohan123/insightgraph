# InsightGraph - Implementation Plan & Progress Tracker

**Project Goal:** Build a Knowledge Graph system that extracts entities and relationships from unstructured text using LLM-powered NER.

**Core Requirements (Industry Best Practices):**
- LLM-based NER (Gemini 2.0)
- Structured JSON outputs (Pydantic)
- Graph database (PostgreSQL + JSONB)
- Visualization (React + TypeScript + react-force-graph)
- Rate limiting (Redis)
- Semantic search (pgvector - Advanced)

**Development Principles:**
- ✅ SOLID, DRY, YAGNI
- ✅ 100-line module limit (readability)
- ✅ Test-driven development
- ✅ Type safety (Pydantic + TypeScript)
- ✅ Dependency injection
- ✅ Modern tooling (Docker, Poetry/UV)

---

## Current Status: Phase 1.5 - Testing & Infrastructure ✅ COMPLETED!

**Last Updated:** 2026-01-08 (Evening)

### ✅ Completed (Phase 1.5 - Testing & Infrastructure)
**Completion Date:** 2026-01-08

Phase 1.5 focused on establishing a solid testing foundation and verifying infrastructure, following modern 2025/2026 best practices.

**Infrastructure Verification:**
- [x] Docker containers started and verified (Redis + PostgreSQL)
- [x] Redis connectivity tested (PING, SET/GET, TTL)
- [x] PostgreSQL connectivity tested (queries, table operations)
- [x] Health checks passing for all services
- [x] Fixed docker-compose.yml (removed obsolete version attribute)

**Test Suite Implementation:**
- [x] Test dependencies installed (pytest-asyncio, pytest-cov, pytest-mock, httpx)
- [x] Infrastructure tests (7 tests - Redis & PostgreSQL connectivity)
- [x] LLM extractor unit tests (14 tests - with mocked Gemini service)
- [x] API integration tests (23 tests - FastAPI endpoints)
- [x] Rule-based extractor tests (6 tests - existing)
- [x] **Total: 50 tests passing** ✅

**Test Coverage:**
- [x] **81% overall coverage** (exceeds 80% target)
- [x] extractors/llm_based.py: **100% coverage**
- [x] extractors/rule_based.py: **98% coverage**
- [x] extractor.py: **98% coverage**
- [x] tests/test_api.py: **99% coverage**
- [x] tests/test_llm_extractor.py: **100% coverage**
- [x] tests/test_extractor.py: **100% coverage**
- [x] HTML coverage report generated (htmlcov/)

**Testing Best Practices Applied:**
- [x] Mocking for LLM service (no real API calls in tests)
- [x] Fast test execution (< 20 seconds for all 50 tests)
- [x] Deterministic tests (no flakiness)
- [x] Cost-free testing (no API charges)
- [x] Offline capability (tests work without internet)
- [x] pytest.ini configured with asyncio settings
- [x] Coverage reporting with HTML output

**Quality Metrics:**
- Test execution time: ~20 seconds (all 50 tests)
- No warnings (asyncio deprecation fixed)
- All assertions passing
- Ready for CI/CD pipeline integration

---

## Previous Status: Phase 1 - LLM Integration ✅ COMPLETED!

**Completion Date:** 2026-01-06 (Evening)

### ✅ Completed (Foundation)
- [x] FastAPI backend with `/health` and `/extract` endpoints
- [x] Pydantic schemas (Node, Edge, ExtractResponse)
- [x] Rule-based extraction engine
- [x] Pytest suite (6 passing tests)
- [x] API documentation (Swagger)

### ✅ Completed (Phase 1 - LLM Integration)
- [x] Environment configuration (.env, docker-compose.yml)
- [x] Dependencies installed (google-generativeai, pydantic-settings, etc.)
- [x] Configuration management (config.py with Pydantic Settings)
- [x] LLM service layer (services/llm_service.py with Gemini 2.5 Flash)
- [x] Abstract extractor interface (extractors/base.py - SOLID principles)
- [x] Refactored rule-based extractor (extractors/rule_based.py)
- [x] LLM-based extractor (extractors/llm_based.py)
- [x] Prompt engineering templates (prompts/extraction.py)
- [x] Updated main.py with dependency injection
- [x] Better error handling for rate limits
- [x] API testing (successfully extracting with LLM!)
- [x] Docker containers running (Redis + PostgreSQL)

### 📊 Test Results
**LLM Extraction Test:**
- Input: "FastAPI is a Python framework used for building APIs"
- Nodes extracted: 4 (FastAPI, Python, framework, APIs)
- Edges extracted: 3 (written_in, is_a, used_for_building)
- Model: gemini-2.5-flash
- Status: ✅ Working perfectly!

### 📋 Next Phase

**Phase 2: Rate Limiting & Request Queuing** (Ready to Start)

**Prerequisites:** ✅ All Complete
- [x] Phase 1: LLM Integration complete
- [x] Phase 1.5: Testing & Infrastructure verified
- [x] Docker containers running (Redis + PostgreSQL)
- [x] 81% test coverage achieved
- [x] 50 tests passing

**Objectives:**
- Implement Redis-based request queue
- Per-user and global rate limiting (sliding window algorithm)
- Background job processing (FastAPI BackgroundTasks)
- Result caching (reduce API costs)
- Monitoring dashboard for quota tracking
- Job status tracking (queued/processing/completed)
- Prevent API quota exhaustion during high traffic

**Estimated Timeline:** 2-3 days

**Implementation Files:**
- `backend/middleware/rate_limiter.py` - Rate limiting logic
- `backend/services/redis_service.py` - Redis connection manager
- `backend/services/queue_service.py` - Job queue management
- `backend/services/cache_service.py` - Result caching
- `backend/workers/extraction_worker.py` - Background processing
- `backend/routers/monitoring.py` - Usage stats API

### 📋 Future Phases
- [ ] Phase 3: Database Persistence (PostgreSQL + JSONB)
- [ ] Phase 4: Frontend Visualization (React + TypeScript)
- [ ] Phase 5: Semantic Search (pgvector - Advanced)

---

## Phase 1: LLM-Powered NER - Detailed Plan

### Architecture Design (SOLID Principles)

#### 1. **Single Responsibility Principle (SRP)**
Each module has ONE job:

```
backend/
├── config.py              # Settings & environment (1 job: configuration)
├── services/
│   ├── llm_service.py     # LLM client wrapper (1 job: API communication)
│   └── extraction_service.py  # Orchestrates extraction logic (1 job: coordination)
├── extractors/
│   ├── base.py            # Abstract extractor interface (1 job: contract)
│   ├── rule_based.py      # Rule-based extraction (1 job: pattern matching)
│   └── llm_based.py       # LLM extraction (1 job: prompt + parse)
├── schemas.py             # Data models (1 job: validation)
├── main.py                # API routes (1 job: HTTP handling)
└── tests/
```

#### 2. **Open/Closed Principle (OCP)**
Open for extension, closed for modification:

```python
# base.py - Abstract interface
from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """Extractor contract - add new extractors without changing existing code"""

    @abstractmethod
    def extract(self, text: str) -> ExtractResponse:
        """Extract nodes and edges from text"""
        pass
```

```python
# Can add new extractors (LLM, hybrid, ML-based) without modifying base
class LLMExtractor(BaseExtractor):
    def extract(self, text: str) -> ExtractResponse:
        # Implementation
        pass
```

#### 3. **Dependency Inversion Principle (DIP)**
Depend on abstractions, not concretions:

```python
# main.py - Inject dependency
from fastapi import Depends

def get_extractor() -> BaseExtractor:
    """Dependency injection - can swap extractors easily"""
    use_llm = os.getenv("USE_LLM_EXTRACTOR", "true") == "true"
    if use_llm:
        return LLMExtractor()
    return RuleBasedExtractor()

@app.post("/extract")
async def extract(
    request: ExtractRequest,
    extractor: BaseExtractor = Depends(get_extractor)
):
    return extractor.extract(request.text)
```

#### 4. **DRY (Don't Repeat Yourself)**
- Shared utilities in `utils/`
- Reusable prompt templates
- Common validation logic in base classes

#### 5. **YAGNI (You Aren't Gonna Need It)**
- No premature optimization
- No unused abstraction layers
- Build features when needed, not "just in case"

---

## Implementation Steps - Phase 1

### Step 1: Environment Setup ⚙️

**Files to Create:**
- `.env` - Environment variables
- `docker-compose.yml` - Redis & PostgreSQL
- `pyproject.toml` - Modern Python dependency management (Poetry)

**Dependencies:**
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.128.0"
pydantic = "^2.12.5"
pydantic-settings = "^2.0.0"  # Settings management
google-generativeai = "^0.8.0"  # Gemini SDK
python-dotenv = "^1.0.0"
uvicorn = "^0.27.0"
redis = "^5.0.0"  # For Phase 2

[tool.poetry.group.dev.dependencies]
pytest = "^9.0.2"
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: insightgraph
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**.env:**
```bash
# LLM
GEMINI_API_KEY=your_key_here
USE_LLM_EXTRACTOR=true

# Database (Phase 3)
DATABASE_URL=postgresql://dev:devpass@localhost:5432/insightgraph

# Redis (Phase 2)
REDIS_URL=redis://localhost:6379
```

---

### Step 2: Configuration Module 📋

**File:** `backend/config.py` (< 100 lines)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings - single source of truth"""

    # LLM
    gemini_api_key: str
    use_llm_extractor: bool = True
    max_retries: int = 3

    # Future settings
    database_url: str | None = None
    redis_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# Singleton pattern
settings = Settings()
```

**Why?**
- ✅ Type-safe settings
- ✅ Auto-loads from .env
- ✅ Validation at startup
- ✅ Easy to test (mock settings)

---

### Step 3: LLM Service Layer 🤖

**File:** `backend/services/llm_service.py` (< 100 lines)

**Responsibilities:**
- Initialize Gemini client
- Send prompts
- Handle rate limiting errors
- Retry logic
- Parse JSON responses

**Key Methods:**
```python
class GeminiService:
    def __init__(self, api_key: str):
        """Initialize Gemini client"""

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[BaseModel]
    ) -> BaseModel:
        """Generate structured output matching Pydantic schema"""

    async def _retry_with_backoff(self, func):
        """Exponential backoff for rate limits"""
```

**Why Separate Service?**
- ✅ Can swap LLM providers (OpenAI, Claude, local models)
- ✅ Easy to mock for testing
- ✅ Single place to handle API changes

---

### Step 4: Extractor Abstraction 🏗️

**File:** `backend/extractors/base.py` (< 50 lines)

```python
from abc import ABC, abstractmethod
from schemas import ExtractResponse

class BaseExtractor(ABC):
    """Contract for all extractors"""

    @abstractmethod
    async def extract(self, text: str) -> ExtractResponse:
        """Extract entities and relationships"""
        pass
```

**File:** `backend/extractors/rule_based.py`
- Move existing `extractor.py` logic here
- Refactor into class implementing `BaseExtractor`
- Keep under 100 lines (split helpers if needed)

**File:** `backend/extractors/llm_based.py` (< 100 lines)

```python
class LLMExtractor(BaseExtractor):
    def __init__(self, llm_service: GeminiService):
        self.llm = llm_service

    async def extract(self, text: str) -> ExtractResponse:
        prompt = self._build_prompt(text)
        return await self.llm.generate_structured(prompt, ExtractResponse)

    def _build_prompt(self, text: str) -> str:
        """Create NER extraction prompt"""
        return f"""
        Extract entities and relationships from this text:
        {text}

        Return JSON with:
        - nodes: array of {{id, label, type, confidence}}
        - edges: array of {{source, target, relation}}

        Types: Tech, Concept, Person
        """
```

---

### Step 5: Prompt Engineering 📝

**File:** `backend/prompts/extraction.py` (< 100 lines)

```python
from string import Template

NER_SYSTEM_PROMPT = """You are an expert at Named Entity Recognition and Relationship Extraction.
Extract entities (People, Technologies, Concepts) and their relationships from text.
Be precise and only extract meaningful connections."""

NER_USER_TEMPLATE = Template("""
Text to analyze:
\"\"\"
$text
\"\"\"

Extract:
1. Entities (nodes):
   - id: lowercase alphanumeric identifier
   - label: Display name
   - type: "Tech" | "Concept" | "Person"
   - confidence: 0.0-1.0 based on clarity

2. Relationships (edges):
   - source: node id
   - target: node id
   - relation: verb phrase (e.g., "used_for", "implements", "created_by")

Return valid JSON matching this schema:
{
  "nodes": [...],
  "edges": [...]
}
""")
```

**Why separate prompts?**
- ✅ Easy to iterate and improve
- ✅ Version control for prompt changes
- ✅ A/B testing different prompts
- ✅ Reusable across extractors

---

### Step 6: Update API Layer 🌐

**File:** `backend/main.py` (< 100 lines)

```python
from fastapi import FastAPI, Depends, HTTPException
from extractors.base import BaseExtractor
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from services.llm_service import GeminiService
from config import settings

app = FastAPI(title="InsightGraph API")

# Dependency injection
def get_extractor() -> BaseExtractor:
    if settings.use_llm_extractor:
        llm_service = GeminiService(settings.gemini_api_key)
        return LLMExtractor(llm_service)
    return RuleBasedExtractor()

@app.post("/extract", response_model=ExtractResponse)
async def extract_graph(
    request: ExtractRequest,
    extractor: BaseExtractor = Depends(get_extractor)
):
    try:
        return await extractor.extract(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Step 7: Testing Strategy 🧪

**File:** `backend/tests/test_llm_extractor.py` (< 100 lines)

```python
import pytest
from unittest.mock import AsyncMock
from extractors.llm_based import LLMExtractor
from schemas import ExtractResponse, Node, Edge

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    # Mock response
    service.generate_structured.return_value = ExtractResponse(
        nodes=[Node(id="python", label="Python", type="Tech", confidence=0.9)],
        edges=[Edge(source="python", target="data-science", relation="used_for")]
    )
    return service

@pytest.mark.asyncio
async def test_llm_extractor_success(mock_llm_service):
    extractor = LLMExtractor(mock_llm_service)
    result = await extractor.extract("Python is used for data science")

    assert len(result.nodes) == 1
    assert result.nodes[0].id == "python"
    assert mock_llm_service.generate_structured.called

@pytest.mark.asyncio
async def test_llm_extractor_handles_errors(mock_llm_service):
    mock_llm_service.generate_structured.side_effect = Exception("API Error")
    extractor = LLMExtractor(mock_llm_service)

    with pytest.raises(Exception):
        await extractor.extract("test text")
```

**Test Coverage:**
- ✅ Successful extraction
- ✅ API errors
- ✅ Malformed responses
- ✅ Rate limiting
- ✅ Fallback to rule-based

---

## Step 8: Hybrid Fallback Strategy 🔄

**File:** `backend/extractors/hybrid.py` (< 100 lines)

```python
class HybridExtractor(BaseExtractor):
    """Falls back to rule-based if LLM fails"""

    def __init__(self, llm: LLMExtractor, rule_based: RuleBasedExtractor):
        self.llm = llm
        self.fallback = rule_based

    async def extract(self, text: str) -> ExtractResponse:
        try:
            return await self.llm.extract(text)
        except (RateLimitError, APIError) as e:
            logger.warning(f"LLM failed: {e}. Using rule-based fallback.")
            return self.fallback.extract(text)
```

---

## Quality Checklist ✅

Before marking Phase 1 complete:

**Code Quality:**
- [ ] All modules under 100 lines
- [ ] Type hints on all functions
- [ ] Docstrings (Google style)
- [ ] No duplicate code (DRY)
- [ ] SOLID principles followed

**Testing:**
- [ ] All tests pass
- [ ] >80% code coverage
- [ ] Edge cases covered
- [ ] Mocks used properly

**Documentation:**
- [ ] README updated
- [ ] API docs accurate
- [ ] Comments explain "why", not "what"

**Performance:**
- [ ] No blocking operations in async routes
- [ ] Proper error handling
- [ ] Logging for debugging

---

## Next Steps After Phase 1

1. **Phase 2:** Rate limiting with Redis (prevent API exhaustion)
2. **Phase 3:** PostgreSQL persistence (store extracted graphs)
3. **Phase 4:** React frontend (visualize knowledge graph)
4. **Phase 5:** Semantic search with pgvector (advanced)

---

## Decisions Log 📝

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-06 (AM) | Use Pydantic for settings | Type safety, auto-validation, modern |
| 2026-01-06 (AM) | Abstract extractor interface | Easy to swap/test implementations |
| 2026-01-06 (AM) | Separate LLM service layer | Can change providers, easier mocking |
| 2026-01-06 (AM) | Docker for dev environment | Consistent, modern, production-like |
| 2026-01-06 (PM) | Use gemini-2.5-flash over experimental models | Better free-tier quotas, more stable |
| 2026-01-06 (PM) | Add detailed rate limit error handling | Helps users troubleshoot quota issues |
| 2026-01-06 (PM) | Dependency injection in FastAPI | Easy testing, swappable extractors |
| 2026-01-06 (PM) | Separate prompt templates in prompts/ | Version control, easy iteration, reusability |

---

## Questions & Blockers 🚧

**Current:**
- None! Phase 1 completed successfully!

**Resolved:**
- [x] Obtain Gemini API key ✅ (Working, 39 chars, access to 34 models)
- [x] Install Docker Desktop ✅ (Redis + PostgreSQL running)
- [x] Rate limit issues with experimental models ✅ (Switched to gemini-2.5-flash)

---

## Resources 📚

- [Gemini API Docs](https://ai.google.dev/docs)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SOLID Principles in Python](https://realpython.com/solid-principles-python/)
