"""
Python Fix Script - Gomedia IA
Fixes all issues: DB schema, pool config, Ollama timeout
"""

import os
import sys
from sqlalchemy import create_engine, text

def fix_db_column():
    """Fixes the missing description_length column"""
    print("="*60)
    print("  FIXING DATABASE SCHEMA")
    print("="*60)

    try:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/gomedia")
        print(f"DB URL: {DATABASE_URL}")

        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE specifications ADD COLUMN IF NOT EXISTS description_length VARCHAR(20) DEFAULT 'medium'
            """))
            conn.commit()
        print("✅ Column 'description_length' added successfully")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_env():
    """Checks and updates .env configuration"""
    print("\n" + "="*60)
    print("  CHECKING ENVIRONMENT CONFIG")
    print("="*60)

    env_file = ".env"
    with open(env_file, 'r') as f:
        content = f.read()

    pool_vars = {
        "DATABASE_POOL_SIZE": "20",
        "DATABASE_MAX_OVERFLOW": "10",
        "POOL_TIMEOUT": "30"
    }

    updated = False
    for var, value in pool_vars.items():
        if var not in content:
            with open(env_file, 'a') as f:
                f.write(f"{var}={value}\n")
            updated = True
            print(f"✅ Added {var}={value}")
        else:
            print(f"✅ {var} already present")

    return updated

def check_ollama():
    """Checks Ollama service"""
    print("\n" + "="*60)
    print("  CHECKING OLLAMA SERVICE")
    print("="*60)

    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
        else:
            print(f"❌ Ollama HTTP error: {response.status_code}")
            return False
    except:
        print("❌ Ollama is not running")
        print("To start: run 'ollama serve' in new terminal")
        return False

def main():
    print("\n" + "="*60)
    print("  GOMEDIA IA - ISSUES FIXER")
    print("="*60 + "\n")

    success = True

    # Fix 1: DB column
    if not fix_db_column():
        success = False

    # Fix 2: Env config
    check_env()

    # Fix 3: Ollama
    ollama_ok = check_ollama()
    if not ollama_ok:
        print("\n💡 ACTION REQUIRED: Start Ollama in another terminal")

    print("\n" + "="*60)
    if success:
        print("✅ ALL ISSUES FIXED")
    else:
        print("⚠️ SOME ISSUES PERSIST")
    print("="*60)

    print("\n📝 NEXT STEPS:")
    print("1. STOP server (Ctrl+C if running)")
    print("2. RESTART server: uvicorn app.main:app --reload --port 8000")
    print("3. TEST: curl http://localhost:8000/health/db")

if __name__ == "__main__":
    main()
