"""
Extraction API Endpoints
=========================

Endpoints for extracting knowledge graphs from text.

Endpoints:
- POST /extract - Extract entities and relationships (cached, rate-limited)
"""

from typing import Annotated

from extractors.base import BaseExtractor
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from fastapi import APIRouter, Depends, HTTPException
from middleware.rate_limiter import rate_limit
from pydantic import BaseModel, Field
from schemas import ExtractResponse
from services.cache_service import cache_service
from services.llm_service import GeminiService

from config import settings

# Create router
router = APIRouter(tags=["Extraction"])


# Request model
class ExtractRequest(BaseModel):
    """Request for entity extraction"""

    text: str = Field(
        ...,
        description="Input text to analyze",
        min_length=1,
        max_length=10000,
        examples=["Python is used for data science and web development"],
    )


# Dependency to get extractor
def get_extractor() -> BaseExtractor:
    """
    Dependency injection for extractor.

    Returns:
        LLMExtractor if USE_LLM_EXTRACTOR=true, else RuleBasedExtractor
    """
    if settings.use_llm_extractor:
        llm_service = GeminiService()
        return LLMExtractor(llm_service)
    else:
        return RuleBasedExtractor()


# Main extraction endpoint
@router.post(
    "/extract",
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
        429: {"description": "Rate limit exceeded - too many requests"},
        500: {"description": "Extraction failed (API error, etc.)"},
    },
    dependencies=[Depends(rate_limit)],  # Add rate limiting
)
async def extract(req: ExtractRequest, extractor: Annotated[BaseExtractor, Depends(get_extractor)]):
    """
    Extract entities (nodes) and relationships (edges) from text.

    This endpoint:
    1. Takes unstructured text as input
    2. Checks cache for previous identical requests (saves API costs!)
    3. If not cached, extracts entities (Tech, Concepts, People, etc.)
    4. Identifies relationships between entities
    5. Caches result for 24 hours
    6. Returns a structured knowledge graph

    Note: This endpoint is public (rate-limited) and does not persist to database.
    Use POST /graphs to save the graph to the database.

    Args:
        req: ExtractRequest with text field
        extractor: Injected by FastAPI (LLM or Rule-based)

    Returns:
        ExtractResponse with nodes and edges

    Raises:
        HTTPException(500): If extraction fails
    """
    try:
        # Use cache to avoid redundant API calls
        result = await cache_service.get_or_compute(
            text=req.text, compute_fn=lambda: extractor.extract(req.text)
        )
        return result

    except Exception as e:
        # Log error and return HTTP 500
        print(f"[ERROR] Extraction failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Extraction failed: {str(e)[:200]}"
        ) from e  # Preserve exception chain for better debugging
