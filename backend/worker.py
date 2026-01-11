"""
Background Worker - Job Processor
===================================

Processes extraction jobs from the Redis queue.

Architecture:
- Long-running process that polls the job queue
- Fetches jobs from Redis, processes them, updates status
- Graceful shutdown on SIGTERM/SIGINT

Usage:
    python worker.py  # Run in separate terminal

Deployment:
    - Run as systemd service on Linux
    - Run as background process with supervisor/pm2
    - Run in separate Docker container
"""

import asyncio
import signal
import sys

from config import settings
from extractors.llm_based import LLMExtractor
from extractors.rule_based import RuleBasedExtractor
from models.job import JobStatus
from services.cache_service import cache_service
from services.job_service import job_service
from services.llm_service import GeminiService
from services.redis_service import redis_service


class Worker:
    """Background worker for processing extraction jobs."""

    def __init__(self):
        """Initialize worker with extractor based on config."""
        self.running = False
        self.extractor = None

    async def start(self):
        """Start the worker loop."""
        print("\n" + "=" * 60)
        print("InsightGraph Worker Starting...")
        print("=" * 60)

        # Connect to Redis
        await redis_service.connect()
        redis_healthy = await redis_service.ping()
        print(f"Redis: {'Connected' if redis_healthy else 'Not connected'}")

        if not redis_healthy:
            print("[ERROR] Redis not available. Exiting.")
            sys.exit(1)

        # Initialize extractor
        if settings.use_llm_extractor:
            print("Extractor: LLM (Gemini)")
            llm_service = GeminiService()
            self.extractor = LLMExtractor(llm_service)
        else:
            print("Extractor: Rule-based")
            self.extractor = RuleBasedExtractor()

        print("Worker ready! Waiting for jobs...")
        print("=" * 60 + "\n")

        # Start processing loop
        self.running = True
        await self.process_loop()

    async def process_loop(self):
        """Main processing loop - poll queue and process jobs."""
        while self.running:
            try:
                # Get next job from queue (blocking with 5s timeout)
                job_id = await job_service.get_next_job(timeout=5)

                if not job_id:
                    # No job available, continue polling
                    continue

                # Process the job
                await self.process_job(job_id)

            except KeyboardInterrupt:
                print("\n[INFO] Received shutdown signal")
                break
            except Exception as e:
                print(f"[ERROR] Worker error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying

    async def process_job(self, job_id: str):
        """
        Process a single extraction job.

        Args:
            job_id: Job identifier to process
        """
        print(f"[Worker] Processing job {job_id}")

        # Get job data
        job = await job_service.get_job(job_id)
        if not job:
            print(f"[ERROR] Job {job_id} not found")
            return

        try:
            # Update status to PROCESSING
            await job_service.update_job_status(job_id, JobStatus.PROCESSING)

            # Run extraction (with caching to save API costs)
            result = await cache_service.get_or_compute(
                text=job.text, compute_fn=lambda: self.extractor.extract(job.text)
            )

            # Convert result to dict
            result_dict = result.model_dump()

            # Update job with result
            await job_service.update_job_status(
                job_id, JobStatus.COMPLETED, result=result_dict
            )

            print(f"[Worker] Job {job_id} completed successfully")

        except Exception as e:
            # Update job with error
            error_msg = str(e)[:500]  # Limit error message length
            await job_service.update_job_status(job_id, JobStatus.FAILED, error=error_msg)

            print(f"[ERROR] Job {job_id} failed: {error_msg}")

    async def stop(self):
        """Stop the worker gracefully."""
        print("\n[INFO] Stopping worker...")
        self.running = False
        await redis_service.disconnect()
        print("[INFO] Worker stopped")


# Global worker instance
worker = Worker()


def signal_handler(signum, frame):
    """Handle shutdown signals (SIGTERM, SIGINT)."""
    print(f"\n[INFO] Received signal {signum}")
    asyncio.create_task(worker.stop())


# Main entry point
async def main():
    """Run the worker."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await worker.start()
    except KeyboardInterrupt:
        pass
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
