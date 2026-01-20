"""
Embedding Service - Gemini Text Embeddings
==========================================

Generates semantic embeddings for text using Google Gemini API.

Key Features:
- Uses models/embedding-001 (768 dimensions)
- Async support via asyncio.to_thread
- Batch embedding for backfill operations
- Configurable task types for queries vs documents
"""

import asyncio

import google.generativeai as genai
from config import settings

# Embedding model configuration
EMBEDDING_MODEL = "models/embedding-001"
EMBEDDING_DIMENSIONS = 768


class EmbeddingService:
    """
    Service for generating text embeddings using Gemini.

    Usage:
        service = EmbeddingService()
        embedding = await service.generate_embedding("Python is great for ML")
    """

    def __init__(self, api_key: str | None = None):
        """Initialize with Gemini API key."""
        self.api_key = api_key or settings.gemini_api_key
        genai.configure(api_key=self.api_key)
        self.model = EMBEDDING_MODEL
        self.dimensions = EMBEDDING_DIMENSIONS

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text (document).

        Uses task_type="retrieval_document" for optimal document indexing.

        Args:
            text: Text to embed (will be truncated if too long)

        Returns:
            768-dimensional embedding vector as list of floats

        Raises:
            Exception: If API call fails
        """
        # Truncate text if too long (Gemini has token limits)
        max_chars = 25000
        if len(text) > max_chars:
            text = text[:max_chars]

        # Run embedding in thread pool (SDK is synchronous)
        result = await asyncio.to_thread(
            genai.embed_content,
            model=self.model,
            content=text,
            task_type="retrieval_document",
        )

        return result["embedding"]

    async def generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Uses task_type="retrieval_query" for optimal query matching.
        This produces embeddings optimized for finding relevant documents.

        Args:
            query: Search query text

        Returns:
            768-dimensional embedding vector
        """
        result = await asyncio.to_thread(
            genai.embed_content,
            model=self.model,
            content=query,
            task_type="retrieval_query",
        )

        return result["embedding"]

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 10,
        delay_between_batches: float = 0.5,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts with batching.

        Useful for backfilling existing data. Includes rate limiting
        to avoid API quota exhaustion.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            delay_between_batches: Seconds to wait between batches

        Returns:
            List of embedding vectors (same order as input texts)
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Process batch concurrently
            batch_embeddings = await asyncio.gather(
                *[self.generate_embedding(text) for text in batch]
            )
            embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(delay_between_batches)

        return embeddings


# Singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get or create singleton embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
