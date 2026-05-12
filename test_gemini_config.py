#!/usr/bin/env python3
"""
Simple test script to verify NVIDIA NIM integration is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_nim_api_key():
    """Test if NVIDIA NIM API key is accessible"""
    api_key = os.getenv("NIM_API_KEY")

    print("Testing NVIDIA NIM Integration")
    print("=" * 50)

    if not api_key:
        print("ERROR: NIM_API_KEY not found in .env")
        return False

    if api_key == "your_api_key_here":
        print("ERROR: NIM_API_KEY is set to default value")
        print("   Please update .env with your real NVIDIA NIM API key")
        return False

    print(f"[OK] NIM_API_KEY found: {api_key[:20]}...")

    # Test import and configuration
    try:
        from app.services.llm import NIM_API_KEY, NIM_MODEL
        print(f"[OK] LLM service imports successfully")
        print(f"[OK] MODEL: {NIM_MODEL}")
        print(f"[OK] API Key configured: {bool(NIM_API_KEY)}")

        # Test basic function
        from app.services.llm import generate_spec
        print("[OK] generate_spec function loaded")

        return True
    except Exception as e:
        print(f"ERROR: Error importing LLM service: {e}")
        return False

def test_output():
    """Generate a simple test to verify functionality"""
    # Skip actual API call for now - just verify setup
    print("\nNVIDIA NIM integration is configured!")
    print("Next step: Run the actual application and test with real documents")

if __name__ == "__main__":
    success = test_nim_api_key()
    if success:
        test_output()
        sys.exit(0)
    else:
        print("\nERROR: Configuration incomplete. Please fix the issues above.")
        sys.exit(1)
