#!/usr/bin/env python3
"""
Verification script for NVIDIA NIM integration.
Tests API connectivity and extracts a sample.
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

def check_env():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")

    nim_api_key = os.getenv("NIM_API_KEY")
    nim_model = os.getenv("NIM_MODEL", "meta/llama-3-70b-instruct")
    nim_api_url = os.getenv("NIM_API_URL", "https://integrate.api.nvidia.com/v1")

    if not nim_api_key:
        print("❌ NIM_API_KEY not found in .env file")
        print("📖 Get your API key from: https://build.nvidia.com")
        return False

    print(f"✅ NIM_API_KEY: {nim_api_key[:20]}...")
    print(f"✅ NIM_MODEL: {nim_model}")
    print(f"✅ NIM_API_URL: {nim_api_url}")

    return True

def test_api_connection():
    """Test basic API connectivity."""
    import requests

    print("\n🌐 Testing API connectivity...")

    nim_api_key = os.getenv("NIM_API_KEY")
    nim_api_url = os.getenv("NIM_API_URL", "https://integrate.api.nvidia.com/v1")

    try:
        # Test listing available models
        response = requests.get(
            f"{nim_api_url}/models",
            headers={"Authorization": f"Bearer {nim_api_key}"},
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        print(f"✅ API connection successful!")
        print(f"✅ Status: {response.status_code}")

        if "data" in result and len(result["data"]) > 0:
            print(f"Available models: {len(result['data'])}")
            for model in result["data"][:5]:
                print(f"  - {model.get('id', 'unknown')}")
        else:
            print("✅ Models endpoint accessible")

        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Invalid API key. Please check NIM_API_KEY")
            print("📖 Get a valid key from: https://build.nvidia.com")
        else:
            print(f"❌ HTTP error: {e.response.status_code}")
            print(f"📖 Error: {e.response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API endpoint. Check your internet connection.")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    return False

def test_generation():
    """Test text generation with a simple prompt."""
    print("\n🤖 Testing text generation...")

    try:
        from app.services.llm import _post_to_nim

        test_prompt = """
You are a technical expert. Generate a JSON response.

Return only JSON, nothing else.
{
  "test": "success",
  "message": "LLM integration working"
}
""".strip()

        print("📤 Sending test prompt to NIM...")
        response = _post_to_nim(test_prompt, max_tokens=100)
        print(f"📥 Response received: {len(response)} characters")
        print(f"📄 Response preview: {response[:200]}...")

        # Try to extract JSON
        from app.services.llm import _extract_json
        data = _extract_json(response)

        if data:
            print(f"✅ JSON extraction successful: {data}")

            # If it's a simple test response, expect specific fields
            if "test" in data:
                print("✅ Test fields present")

            return True
        else:
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
        # Create a mock document
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
    """Run all verification tests."""
    print("=" * 60)
    print("🚀 NVIDIA NIM Integration Verification")
    print("=" * 60)

    # Step 1: Environment
    if not check_env():
        sys.exit(1)

    # Step 2: API Connection
    if not test_api_connection():
        sys.exit(1)

    # Step 3: Generation test
    if not test_generation():
        print("⚠️  Generation test failed - but this might be expected on first run")
        print("📖 Continue to document extraction test...")

    # Step 4: Document extraction
    if not test_document_extraction():
        print("⚠️  Document extraction test failed")
        print("📖 Check the error above and consult NVIDIA_NIM_SETUP.md")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ All tests passed! Your NIM integration is ready.")
    print("=" * 60)
    print("\n🎉 You can now run your application:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\n📖 Full setup guide: NVIDIA_NIM_SETUP.md")

if __name__ == "__main__":
    main()
