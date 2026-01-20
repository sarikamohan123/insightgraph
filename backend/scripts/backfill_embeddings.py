"""
Backfill Embeddings Script
==========================

Generate embeddings for existing graphs that don't have them.

Usage:
    cd backend
    python scripts/backfill_embeddings.py

Features:
- Resumable: Only processes graphs without embeddings
- Rate-limited: Delays between batches to avoid API limits
- Progress tracking: Shows progress as it runs
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from models.database import Graph
from repositories.graph_repository import GraphRepository
from services.db_service import get_db_session
from services.embedding_service import EmbeddingService


async def backfill_embeddings(
    batch_size: int = 10,
    delay_between_batches: float = 1.0,
) -> dict:
    """
    Backfill embeddings for all graphs without them.

    Args:
        batch_size: Number of graphs to process per batch
        delay_between_batches: Seconds to wait between batches

    Returns:
        Dict with processing statistics
    """
    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "errors": [],
    }

    embedding_service = EmbeddingService()

    print(f"Starting embedding backfill...")
    print(f"  Batch size: {batch_size}")
    print(f"  Delay between batches: {delay_between_batches}s")
    print()

    async with get_db_session() as session:
        repo = GraphRepository(session)

        while True:
            # Get next batch of graphs without embeddings
            graphs = await repo.get_graphs_without_embeddings(limit=batch_size)

            if not graphs:
                print("No more graphs to process.")
                break

            print(f"Processing batch of {len(graphs)} graphs...")

            for graph in graphs:
                stats["total_processed"] += 1

                try:
                    # Generate embedding from source text
                    embedding = await embedding_service.generate_embedding(
                        graph.source_text
                    )

                    # Update graph with embedding
                    success = await repo.update_embedding(graph.id, embedding)

                    if success:
                        stats["successful"] += 1
                        print(f"  [OK] Graph {graph.id} - embedded successfully")
                    else:
                        stats["failed"] += 1
                        error_msg = f"Graph {graph.id} - update failed"
                        stats["errors"].append(error_msg)
                        print(f"  [FAIL] {error_msg}")

                except Exception as e:
                    stats["failed"] += 1
                    error_msg = f"Graph {graph.id} - {str(e)[:100]}"
                    stats["errors"].append(error_msg)
                    print(f"  [FAIL] {error_msg}")

            # Delay between batches to avoid rate limiting
            if len(graphs) == batch_size:
                print(f"  Waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)

    return stats


async def main():
    """Main entry point for backfill script."""
    print("=" * 60)
    print("InsightGraph Embedding Backfill")
    print("=" * 60)
    print()

    # Check for API key
    if not settings.gemini_api_key:
        print("ERROR: GEMINI_API_KEY not set in environment")
        sys.exit(1)

    try:
        stats = await backfill_embeddings()

        print()
        print("=" * 60)
        print("Backfill Complete")
        print("=" * 60)
        print(f"  Total processed: {stats['total_processed']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")

        if stats["errors"]:
            print()
            print("Errors:")
            for error in stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats["errors"]) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")

        sys.exit(0 if stats["failed"] == 0 else 1)

    except KeyboardInterrupt:
        print("\nBackfill interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
