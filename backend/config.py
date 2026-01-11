"""
Configuration Management
========================
Centralized application settings using Pydantic Settings.

Key Benefits:
- Type-safe configuration with validation
- Auto-loads from .env file
- Fails fast if required variables are missing
- Easy to test (can override settings in tests)

Usage:
    from config import settings
    api_key = settings.gemini_api_key
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings - Single Source of Truth

    All settings are loaded from environment variables or .env file.
    Pydantic validates types and ensures required values exist.
    """

    # LLM Configuration (Phase 1)
    gemini_api_key: str  # Required - will raise error if missing
    use_llm_extractor: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30

    # Database Configuration (Phase 3)
    database_url: str = "postgresql://dev:devpass@localhost:5432/insightgraph"

    # Redis Configuration (Phase 2)
    redis_url: str = "redis://localhost:6379"

    # Model configuration
    model_config = SettingsConfigDict(
        env_file="../.env",  # Load from project root (parent directory)
        env_file_encoding="utf-8",
        case_sensitive=False,  # GEMINI_API_KEY == gemini_api_key
        extra="ignore",  # Ignore extra environment variables
    )


# Singleton instance - import this throughout the app
settings = Settings()


# Example usage and validation
if __name__ == "__main__":
    """Run this to test your configuration"""
    print("Configuration loaded successfully!")
    print(f"[OK] LLM Extractor: {'Enabled' if settings.use_llm_extractor else 'Disabled'}")
    print(f"[OK] Max Retries: {settings.max_retries}")
    print(f"[OK] Timeout: {settings.timeout_seconds}s")

    # Check if API key is set (don't print actual key for security)
    if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
        print(f"[OK] Gemini API Key: Set (length: {len(settings.gemini_api_key)})")
    else:
        print("[WARNING] Gemini API Key: Not set or using default placeholder")
