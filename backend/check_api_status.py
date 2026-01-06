"""
Check Gemini API Key Status
============================
This script checks if your API key is valid and shows available models.
"""

import google.generativeai as genai
from config import settings

def check_api_status():
    """Check API key validity and available models"""
    print("=" * 60)
    print("Gemini API Key Status Check")
    print("=" * 60)

    # Check if API key is set
    api_key = settings.gemini_api_key
    if api_key == "your_gemini_api_key_here":
        print("\n[ERROR] API key not configured!")
        print("Please update your .env file with a valid GEMINI_API_KEY")
        print("\nGet your key at: https://aistudio.google.com/apikey")
        return False

    print(f"\n[OK] API Key found (length: {len(api_key)} characters)")

    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        print("[OK] API Key configured successfully")
    except Exception as e:
        print(f"[ERROR] Failed to configure API: {e}")
        return False

    # List available models
    print("\n" + "=" * 60)
    print("Available Models:")
    print("=" * 60)

    try:
        models = genai.list_models()

        # Filter for generation models
        generation_models = [
            m for m in models
            if 'generateContent' in m.supported_generation_methods
        ]

        if not generation_models:
            print("[WARNING] No generation models available")
            print("This might indicate an API key issue or account restriction")
            return False

        print(f"\nFound {len(generation_models)} generation models:\n")

        for model in generation_models:
            print(f"Model: {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description[:100]}...")

            # Check rate limits
            if hasattr(model, 'rate_limit'):
                print(f"  Rate Limit: {model.rate_limit}")

            print()

        print("\n" + "=" * 60)
        print("Recommended models for this project:")
        print("=" * 60)
        print("1. gemini-1.5-flash (Stable, good free tier)")
        print("2. gemini-1.5-pro (Higher quality, stricter limits)")
        print("3. gemini-2.0-flash-exp (Experimental, limited quota)")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to list models: {e}")
        print("\nPossible causes:")
        print("1. Invalid API key")
        print("2. API key not activated")
        print("3. Network issues")
        print("4. Quota exceeded")
        print("\nActions:")
        print("- Visit: https://aistudio.google.com/apikey")
        print("- Check usage: https://aistudio.google.com/usage")
        return False

if __name__ == "__main__":
    success = check_api_status()

    if success:
        print("\n[SUCCESS] API key is valid and working!")
    else:
        print("\n[FAILED] Please resolve the issues above")
