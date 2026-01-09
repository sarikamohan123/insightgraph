"""
InsightGraph API
================
FastAPI backend for knowledge graph extraction.

Endpoints:
- GET  /health: Health check
- POST /extract: Extract entities and relationships from text

Architecture:
- Uses dependency injection to swap extractors (LLM vs Rule-based)
- Async endpoints for non-blocking I/O
- Type-safe with Pydantic models
"""

from typing import Annotated

from config import settings
from extractors.base import BaseExtractor
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from schemas import ExtractResponse
from services.llm_service import GeminiService

# Initialize FastAPI app
app = FastAPI(
    title="InsightGraph API",
    description="Transform unstructured text into knowledge graphs using LLMs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Request/Response models
class ExtractRequest(BaseModel):
    """Request for entity extraction"""

    text: str = Field(
        ...,
        description="Input text to analyze",
        min_length=1,
        max_length=10000,
        examples=["Python is used for data science and web development"],
    )


# Dependency Injection: Provide extractor based on configuration
def get_extractor() -> BaseExtractor:
    """
    Dependency injection for extractor.

    Learning Note - Dependency Injection:
    FastAPI calls this function to create the extractor.
    We can easily swap implementations by changing settings
    or for testing by overriding this dependency.

    Returns:
        LLMExtractor if USE_LLM_EXTRACTOR=true, else RuleBasedExtractor

    Example override for testing:
        app.dependency_overrides[get_extractor] = lambda: MockExtractor()
    """
    if settings.use_llm_extractor:
        print("[INFO] Using LLM-based extraction")
        llm_service = GeminiService()
        return LLMExtractor(llm_service)
    else:
        print("[INFO] Using rule-based extraction")
        return RuleBasedExtractor()


# Health check endpoint
@app.get("/health", tags=["System"], summary="Health check", response_model=dict)
async def health():
    """
    Check if the API is running.

    Returns:
        Simple status message
    """
    return {"status": "ok", "extractor": "LLM" if settings.use_llm_extractor else "Rule-based"}


# Main extraction endpoint
@app.post(
    "/extract",
    tags=["Extraction"],
    summary="Extract knowledge graph from text",
    response_model=ExtractResponse,
    responses={
        200: {
            "description": "Successfully extracted entities and relationships",
            "content": {
                "application/json": {
                    "example": {
                        "nodes": [
                            {"id": "python", "label": "Python", "type": "Tech", "confidence": 0.95},
                            {
                                "id": "data-science",
                                "label": "Data Science",
                                "type": "Concept",
                                "confidence": 0.9,
                            },
                        ],
                        "edges": [
                            {"source": "python", "target": "data-science", "relation": "used_for"}
                        ],
                    }
                }
            },
        },
        500: {"description": "Extraction failed (rate limit, API error, etc.)"},
    },
)
async def extract(req: ExtractRequest, extractor: Annotated[BaseExtractor, Depends(get_extractor)]):
    """
    Extract entities (nodes) and relationships (edges) from text.

    This endpoint:
    1. Takes unstructured text as input
    2. Extracts entities (Tech, Concepts, People, etc.)
    3. Identifies relationships between entities
    4. Returns a structured knowledge graph

    Learning Note - Dependency Injection:
    The `extractor` parameter is automatically provided by FastAPI
    via the `Depends(get_extractor)` annotation. This means:
    - We don't create the extractor inside this function
    - Easy to swap extractors (LLM vs Rule-based)
    - Easy to test (can inject mock extractor)

    Args:
        req: ExtractRequest with text field
        extractor: Injected by FastAPI (LLM or Rule-based)

    Returns:
        ExtractResponse with nodes and edges

    Raises:
        HTTPException(500): If extraction fails
    """
    try:
        # Call the extractor (async)
        result = await extractor.extract(req.text)
        return result

    except Exception as e:
        # Log error and return HTTP 500
        print(f"[ERROR] Extraction failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Extraction failed: {str(e)[:200]}"
        ) from e  # Preserve exception chain for better debugging


# Startup event
@app.on_event("startup")
async def startup_event():
    """Print startup information"""
    print("\n" + "=" * 60)
    print("InsightGraph API Starting...")
    print("=" * 60)
    print(f"Extractor: {'LLM (Gemini)' if settings.use_llm_extractor else 'Rule-based'}")
    print("Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
