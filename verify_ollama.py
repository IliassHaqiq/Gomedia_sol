#!/usr/bin/env python3
"""
Verification script for Ollama integration.
Tests connectivity and extracts a sample.
"""

import os
import sys
from dotenv import load_dotenv

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

load_dotenv()


def check_env():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

    print(f"✅ OLLAMA_BASE_URL: {ollama_base_url}")
    print(f"✅ OLLAMA_MODEL: {ollama_model}")
    return True


def test_api_connection():
    """Test basic Ollama connectivity."""
    import requests

    print("\n🌐 Testing Ollama connectivity...")

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
        response.raise_for_status()

        result = response.json()
        models = result.get("models", [])
        print("✅ Ollama connection successful!")
        print(f"✅ Status: {response.status_code}")
        print(f"Available models: {len(models)}")
        for model in models[:5]:
            print(f"  - {model.get('name', 'unknown')}")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {ollama_base_url}")
        print("📖 Start Ollama with: ollama serve")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    return False


def test_generation():
    """Test text generation with a simple prompt."""
    print("\n🤖 Testing text generation...")

    try:
        from app.services.llm import _post_to_ollama

        test_prompt = """
You are a technical expert. Generate a JSON response.

Return only JSON, nothing else.
{
  "test": "success",
  "message": "LLM integration working"
}
""".strip()

        print("📤 Sending test prompt to Ollama...")
        response = _post_to_ollama(test_prompt, max_tokens=100)
        print(f"📥 Response received: {len(response)} characters")
        print(f"📄 Response preview: {response[:200]}...")

        from app.services.llm import _extract_json

        data = _extract_json(response)
        if data:
            print(f"✅ JSON extraction successful: {data}")
            return True
        print("❌ Could not extract JSON structure")
        return False

    except Exception as e:
        print(f"❌ Generation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_document_extraction():
    """Test document extraction flow."""
    print("\n📄 Testing document extraction flow...")

    try:
        test_content = """
This is a test document for a relay component.
Model: G6A-434P-ST-US
Manufacturer: Panasonic
Voltage: 24VDC
Current: 10A
        """.strip()

        from app.services.llm import generate_spec

        print("📤 Processing test document...")
        result = generate_spec(test_content, "test_relay.pdf", "short")

        print("✅ Document processing successful!")
        print(f"✅ Generated fields: {list(result.keys())}")

        if result.get("designation"):
            print(f"✅ Designation: {result['designation']}")
        if result.get("fabricant"):
            print(f"✅ Manufacturer: {result['fabricant']}")
        if result.get("specifications"):
            print(f"✅ Specs count: {len(result['specifications'])}")

        return True

    except Exception as e:
        print(f"❌ Document extraction test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("🚀 Ollama Integration Verification")
    print("=" * 60)

    if not check_env():
        sys.exit(1)

    if not test_api_connection():
        sys.exit(1)

    if not test_generation():
        print("⚠️  Generation test failed - check that the model is pulled:")
        print(f"   ollama pull {os.getenv('OLLAMA_MODEL', 'llama3.2:latest')}")

    if not test_document_extraction():
        print("⚠️  Document extraction test failed")
        print("📖 Check the error above and consult OLLAMA_SETUP.md")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ All tests passed! Your Ollama integration is ready.")
    print("=" * 60)
    print("\n🎉 You can now run your application:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n📖 Full setup guide: OLLAMA_SETUP.md")


if __name__ == "__main__":
    main()
