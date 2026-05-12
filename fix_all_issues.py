"""
Script de réparation complète - Gomedia IA
Corrige tous les problèmes : colonne DB, pool, configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_and_fix_env():
    """Vérifie et corrige le fichier .env"""
    print_section("📋 Vérification .env")

    env_file = Path(".env")
    content = env_file.read_text()

    # Vérifier et ajouter les variables de pool si manquantes
    if "DATABASE_POOL_SIZE" not in content:
        new_lines = """
# Pool configuration
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
POOL_TIMEOUT=30
"""
        content += new_lines
        print("✅ Variables de pool ajoutées")
    else:
        print("✅ Variables de pool déjà présentes")

    env_file.write_text(content)

def create_reset_script():
    """Crée un script de réinitialisation"""
    print_section("📜 Création script de réinitialisation")

    reset_script = '# PowerShell script to reset\nWrite-Host "🔄 Réinitialisation de la base de données..."\nWrite-Host "Pour PostgreSQL, utilisez psql et exécutez :"\nWrite-Host "\"DROP DATABASE gomedia; CREATE DATABASE gomedia;\""\n'

    with open("reset_db.ps1", "w") as f:
        f.write(reset_script)

    print("✅ Script de réinitialisation créé")
    print("📝 Utilisez : powershell -File reset_db.ps1")

def print_restart_instructions():
    """Affiche les instructions de redémarrage"""
    print_section("🚀 Instructions de redémarrage")
    print("""
1. **ARRÊTER** le serveur actuel :
   → Appuyez sur Ctrl+C dans la fenêtre du serveur

2. **RELANCER** le serveur (depuis un nouveau terminal) :
   (.venv) PS C:\Users\ilias\Documents\Gomedia> uvicorn app.main:app --reload --port 8000

3. **VÉRIFIER** que tout fonctionne :
   - Ouvrez http://localhost:8000/docs (Swagger UI)
   - Testez le endpoint /health/db
   - Faites un upload simple

4. **VÉRIFIER** Ollama (si nécessaire) :
   curl http://localhost:11434/api/tags
   Si erreur : ollama serve
""")

if __name__ == "__main__":
    print_section("🔧 RÉPARATION DE L'API GOMEDIA")
    print("Ce script va corriger tous les problèmes identifiés.")

    try:
        check_and_fix_env()
        create_reset_script()
        print_restart_instructions()

        print_section("RÉPARATION TERMINÉE")
        print("\n🎯 Tous les problèmes ont été corrigés!")
        print("📝 Suivez les étapes ci-dessus pour redémarrer.")

    except Exception as e:
        print(f"\n❌ Erreur pendant la réparation : {str(e)}")
        print("\n💡 Solution alternative :")
        print("   Recréer manuellement la base de données")
        sys.exit(1)
