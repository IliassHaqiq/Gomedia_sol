#!/usr/bin/env python3
"""Simple test script to verify Ollama integration is working."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_ollama_config():
    """Test if Ollama is configured and reachable."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

    print("Testing Ollama Integration")
    print("=" * 40)
    print(f"[OK] OLLAMA_BASE_URL: {base_url}")
    print(f"[OK] OLLAMA_MODEL: {model}")

    try:
        from app.services.llm import OLLAMA_BASE_URL, OLLAMA_MODEL

        print(f"[OK] Loaded OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
        print(f"[OK] Loaded OLLAMA_MODEL: {OLLAMA_MODEL}")
    except ImportError as e:
        print(f"[ERROR] Could not import llm module: {e}")
        return False

    import requests

    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        response.raise_for_status()
        print("[OK] Ollama server is reachable")
        return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Ollama. Run: ollama serve")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


if __name__ == "__main__":
    success = test_ollama_config()
    if success:
        print("\nOllama integration is configured!")
    sys.exit(0 if success else 1)
