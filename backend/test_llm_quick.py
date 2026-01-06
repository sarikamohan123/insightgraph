"""Quick test for LLM extractor"""
import asyncio
from services.llm_service import GeminiService
from extractors.llm_based import LLMExtractor

async def test_llm_extraction():
    print("[INFO] Initializing Gemini service...")
    service = GeminiService()

    print("[INFO] Creating LLM extractor...")
    extractor = LLMExtractor(service)

    print("[INFO] Testing extraction with: 'Python is used for data science'")
    result = await extractor.extract("Python is used for data science")

    print("\n[SUCCESS] Extraction completed!")
    print(f"\nNodes found: {len(result.nodes)}")
    for node in result.nodes:
        print(f"  - {node.label} ({node.type}) [confidence: {node.confidence}]")

    print(f"\nEdges found: {len(result.edges)}")
    for edge in result.edges:
        print(f"  - {edge.source} --[{edge.relation}]--> {edge.target}")

if __name__ == "__main__":
    asyncio.run(test_llm_extraction())
