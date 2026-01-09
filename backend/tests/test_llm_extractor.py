"""
LLM Extractor Unit Tests
=========================

Tests for LLMExtractor using mocked Gemini service.

Key Testing Principles:
- Mock external API calls (no real Gemini API usage)
- Test success paths and error handling
- Verify fallback mechanisms
- Fast, deterministic, no API costs
"""

import pytest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from services.llm_service import GeminiService
from schemas import ExtractResponse, Node, Edge


@pytest.fixture
def mock_llm_service():
    """
    Provide a mocked GeminiService for testing.

    This prevents real API calls and makes tests:
    - Fast (no network I/O)
    - Deterministic (same result every time)
    - Cost-free (no API charges)
    - Offline-capable
    """
    service = AsyncMock(spec=GeminiService)

    # Configure mock to return a valid ExtractResponse
    service.generate_structured.return_value = ExtractResponse(
        nodes=[
            Node(id="python", label="Python", type="Tech", confidence=0.95),
            Node(id="data-science", label="Data Science", type="Concept", confidence=0.9)
        ],
        edges=[
            Edge(source="python", target="data-science", relation="used_for")
        ]
    )

    return service


@pytest.fixture
def llm_extractor(mock_llm_service):
    """Provide a LLMExtractor with mocked service"""
    return LLMExtractor(mock_llm_service)


class TestLLMExtractorBasic:
    """Test basic extraction functionality"""

    @pytest.mark.asyncio
    async def test_extract_success(self, llm_extractor, mock_llm_service):
        """Test successful extraction returns nodes and edges"""
        text = "Python is used for data science"
        result = await llm_extractor.extract(text)

        # Verify result structure
        assert isinstance(result, ExtractResponse)
        assert len(result.nodes) >= 1
        assert len(result.edges) >= 1

        # Verify service was called
        assert mock_llm_service.generate_structured.called
        assert mock_llm_service.generate_structured.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_returns_expected_nodes(self, llm_extractor):
        """Test that extracted nodes match expected structure"""
        result = await llm_extractor.extract("Test text")

        # Check first node structure
        node = result.nodes[0]
        assert hasattr(node, 'id')
        assert hasattr(node, 'label')
        assert hasattr(node, 'type')
        assert hasattr(node, 'confidence')

        # Validate types
        assert isinstance(node.id, str)
        assert isinstance(node.label, str)
        assert isinstance(node.type, str)
        assert isinstance(node.confidence, float)

        # Validate confidence range
        assert 0.0 <= node.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_extract_returns_expected_edges(self, llm_extractor):
        """Test that extracted edges match expected structure"""
        result = await llm_extractor.extract("Test text")

        # Check first edge structure
        edge = result.edges[0]
        assert hasattr(edge, 'source')
        assert hasattr(edge, 'target')
        assert hasattr(edge, 'relation')

        # Validate types
        assert isinstance(edge.source, str)
        assert isinstance(edge.target, str)
        assert isinstance(edge.relation, str)

    @pytest.mark.asyncio
    async def test_extract_with_empty_text(self, mock_llm_service):
        """Test extraction with empty text"""
        # Configure mock to return empty result
        mock_llm_service.generate_structured.return_value = ExtractResponse(
            nodes=[],
            edges=[]
        )

        extractor = LLMExtractor(mock_llm_service)
        result = await extractor.extract("")

        assert len(result.nodes) == 0
        assert len(result.edges) == 0


class TestLLMExtractorErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_extract_handles_validation_error(self, mock_llm_service):
        """Test that ValidationError is raised for malformed responses"""
        # Mock service to raise ValidationError
        mock_llm_service.generate_structured.side_effect = ValidationError.from_exception_data(
            "test",
            [{"type": "missing", "loc": ("nodes",), "msg": "Field required"}]
        )

        extractor = LLMExtractor(mock_llm_service)

        with pytest.raises(ValidationError):
            await extractor.extract("Test text")

    @pytest.mark.asyncio
    async def test_extract_handles_api_error(self, mock_llm_service):
        """Test that API errors are propagated"""
        # Mock service to raise generic exception
        mock_llm_service.generate_structured.side_effect = Exception("API Error")

        extractor = LLMExtractor(mock_llm_service)

        with pytest.raises(Exception) as exc_info:
            await extractor.extract("Test text")

        assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_handles_rate_limit_error(self, mock_llm_service):
        """Test handling of rate limit errors"""
        from google.api_core import exceptions as google_exceptions

        # Mock rate limit error
        mock_llm_service.generate_structured.side_effect = google_exceptions.ResourceExhausted(
            "Quota exceeded"
        )

        extractor = LLMExtractor(mock_llm_service)

        with pytest.raises(google_exceptions.ResourceExhausted):
            await extractor.extract("Test text")


class TestLLMExtractorFallback:
    """Test fallback mechanism to rule-based extraction"""

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self, mock_llm_service):
        """Test automatic fallback to rule-based extractor on LLM failure"""
        # Mock LLM to fail
        mock_llm_service.generate_structured.side_effect = Exception("LLM failed")

        llm_extractor = LLMExtractor(mock_llm_service)
        rule_extractor = RuleBasedExtractor()

        # Should fallback without raising exception
        result = await llm_extractor.extract_with_fallback(
            "Python is used for data science",
            rule_extractor
        )

        # Should return valid result from rule-based extractor
        assert isinstance(result, ExtractResponse)
        # Rule-based should extract at least Python
        assert len(result.nodes) >= 1

    @pytest.mark.asyncio
    async def test_fallback_not_used_on_success(self, mock_llm_service):
        """Test that fallback is not called when LLM succeeds"""
        llm_extractor = LLMExtractor(mock_llm_service)
        rule_extractor = RuleBasedExtractor()

        result = await llm_extractor.extract_with_fallback(
            "Python is great",
            rule_extractor
        )

        # Verify LLM was called
        assert mock_llm_service.generate_structured.called

        # Result should be from LLM (has 2 nodes from our mock)
        assert len(result.nodes) == 2

    @pytest.mark.asyncio
    async def test_fallback_with_rate_limit(self, mock_llm_service):
        """Test fallback specifically for rate limit errors"""
        from google.api_core import exceptions as google_exceptions

        mock_llm_service.generate_structured.side_effect = google_exceptions.ResourceExhausted(
            "Rate limit exceeded"
        )

        llm_extractor = LLMExtractor(mock_llm_service)
        rule_extractor = RuleBasedExtractor()

        # Should fallback gracefully
        result = await llm_extractor.extract_with_fallback(
            "Python is used for AI",
            rule_extractor
        )

        assert isinstance(result, ExtractResponse)
        assert len(result.nodes) >= 1  # At least "python"


class TestLLMExtractorIntegration:
    """Integration-style tests (still mocked, but more realistic scenarios)"""

    @pytest.mark.asyncio
    async def test_extract_complex_text(self, mock_llm_service):
        """Test extraction from complex technical text"""
        # Mock more realistic response
        mock_llm_service.generate_structured.return_value = ExtractResponse(
            nodes=[
                Node(id="react", label="React", type="Tech", confidence=0.95),
                Node(id="javascript", label="JavaScript", type="Tech", confidence=0.9),
                Node(id="facebook", label="Facebook", type="Organization", confidence=0.85),
                Node(id="ui", label="User Interfaces", type="Concept", confidence=0.8)
            ],
            edges=[
                Edge(source="react", target="javascript", relation="written_in"),
                Edge(source="facebook", target="react", relation="created"),
                Edge(source="react", target="ui", relation="used_for")
            ]
        )

        extractor = LLMExtractor(mock_llm_service)
        text = "React is a JavaScript library created by Facebook for building user interfaces"
        result = await extractor.extract(text)

        # Verify comprehensive extraction
        assert len(result.nodes) == 4
        assert len(result.edges) == 3

        # Verify specific entities
        node_ids = [n.id for n in result.nodes]
        assert "react" in node_ids
        assert "javascript" in node_ids
        assert "facebook" in node_ids

    @pytest.mark.asyncio
    async def test_extract_multiple_calls_independent(self, mock_llm_service):
        """Test that multiple extraction calls are independent"""
        extractor = LLMExtractor(mock_llm_service)

        # First call
        result1 = await extractor.extract("Python is great")
        assert mock_llm_service.generate_structured.call_count == 1

        # Second call
        result2 = await extractor.extract("JavaScript is awesome")
        assert mock_llm_service.generate_structured.call_count == 2

        # Both should succeed independently
        assert isinstance(result1, ExtractResponse)
        assert isinstance(result2, ExtractResponse)


class TestLLMExtractorDependencyInjection:
    """Test that dependency injection works correctly"""

    @pytest.mark.asyncio
    async def test_extractor_uses_injected_service(self):
        """Test that extractor uses the service provided at initialization"""
        mock_service = AsyncMock(spec=GeminiService)
        mock_service.generate_structured.return_value = ExtractResponse(nodes=[], edges=[])

        extractor = LLMExtractor(mock_service)
        await extractor.extract("test")

        # Verify the injected service was used
        assert mock_service.generate_structured.called

    @pytest.mark.asyncio
    async def test_can_swap_llm_service(self):
        """Test that we can easily swap LLM services (key benefit of DI)"""
        # Create extractor with first service
        service1 = AsyncMock(spec=GeminiService)
        service1.generate_structured.return_value = ExtractResponse(nodes=[], edges=[])

        # We could create another extractor with different service
        service2 = AsyncMock(spec=GeminiService)
        service2.generate_structured.return_value = ExtractResponse(
            nodes=[Node(id="test", label="Test", type="Tech", confidence=1.0)],
            edges=[]
        )

        extractor1 = LLMExtractor(service1)
        extractor2 = LLMExtractor(service2)

        result1 = await extractor1.extract("text")
        result2 = await extractor2.extract("text")

        # Different services produce different results
        assert len(result1.nodes) == 0
        assert len(result2.nodes) == 1
