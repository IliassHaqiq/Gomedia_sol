"""
Script de correction du schéma base de données - Gomedia IA
Ajoute la colonne description_length manquante à la table specifications
"""

from sqlalchemy import create_engine, text
from app.db.session import DATABASE_URL
import os

def fix_database_schema():
    """Ajoute la colonne description_length manquante"""

    print("🔧 Correction du schéma base de données...")
    print(f"🗄️ URL: {DATABASE_URL}")

    # Créer un engine direct pour la modification
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            # Essayer d'ajouter la colonne
            conn.execute(
                text("""
                    ALTER TABLE specifications
                    ADD COLUMN IF NOT EXISTS description_length VARCHAR(20) DEFAULT 'medium'
                """)
            )
            conn.commit()
            print("✅ Colonne 'description_length' ajoutée avec succès!")
            return True

        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            print("\n📝 Veuillez exécuter cette commande SQL manuellement:")
            print("""
            ALTER TABLE specifications
            ADD COLUMN IF NOT EXISTS description_length VARCHAR(20) DEFAULT 'medium';
            """)
            return False

if __name__ == "__main__":
    success = fix_database_schema()
    if success:
        print("\n🎉 La base de données est maintenant à jour!")
        print("\n📝 Prochaine étape: Relancer le serveur")
        print("📋 Commande: uvicorn app.main:app --reload --port 8000")
    else:
        print("\n❌ La correction a échoué.")
        print("💡 Solution alternative: Supprimer et recréer la base de données")
        print("   (si vous utilisez SQLite: rm gomedia.db)")
