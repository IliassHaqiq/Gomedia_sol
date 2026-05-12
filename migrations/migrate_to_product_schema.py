"""
Migration Script - Product-Based Schema with pgvector

This script migrates the database from a document-based schema to a product-centric
schema with vector search capabilities using pgvector.

Usage:
    python migrations/migrate_to_product_schema.py

Requirements:
    - PostgreSQL with pgvector extension installed
    - Database connection configured in .env
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.product import Product, ProductDescription, ProductFile, TechnicalSpec, ProductEmbedding
from app.models.document import Document
from app.models.specification import Specification
from app.db.base import Base
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)


def migrate():
    """
    Execute the migration to product-based schema

    Steps:
    1. Drop old tables (documents, specifications)
    2. Create new tables
    3. Enable pgvector extension
    4. Add vector column to products
    5. Create vector index
    """
    logger.info("🚀 Starting migration to product-based schema...")

    # Get database connection from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:admin@localhost:5433/postgres"
    )

    logger.info(f"📦 Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1: Drop old tables if they exist
        logger.info("📦 Step 1: Dropping old tables...")
        try:
            session.execute(text("DROP TABLE IF EXISTS specifications CASCADE"))
            session.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
            session.commit()
            logger.info("✅ Old tables dropped successfully")
        except Exception as e:
            logger.warning(f"⚠️  Warning dropping old tables: {e}")
            session.rollback()

        # Step 2: Create new tables
        logger.info("📦 Step 2: Creating new tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ New tables created successfully")

        # List created tables
        tables = session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)).fetchall()
        logger.info(f"📊 Tables created: {[t[0] for t in tables]}")

        # Step 3: Enable pgvector extension
        logger.info("🔧 Step 3: Enabling pgvector extension...")
        try:
            session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            session.commit()

            # Verify pgvector is installed
            result = session.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).fetchone()

            if result:
                logger.info(f"✅ pgvector extension enabled (version {result[0]})")
            else:
                logger.warning("⚠️  pgvector extension not found after creation")
        except Exception as e:
            logger.error(f"❌ Error enabling pgvector: {e}")
            logger.error("⚠️  Please install pgvector manually:")
            logger.error("   - Ubuntu/Debian: sudo apt-get install postgresql-14-pgvector")
            logger.error("   - macOS: brew install pgvector")
            logger.error("   - Or compile from source: https://github.com/pgvector/pgvector")
            raise

        # Step 4: Add vector column to products table
        logger.info("🔧 Step 4: Adding vector column to products table...")
        try:
            # Check if column already exists
            column_exists = session.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'search_vector'
            """)).fetchone()

            if not column_exists:
                session.execute(text("""
                    ALTER TABLE products
                    ADD COLUMN search_vector vector(1536)
                """))
                session.commit()
                logger.info("✅ Vector column added to products table")
            else:
                logger.info("ℹ️  Vector column already exists in products table")
        except Exception as e:
            logger.error(f"❌ Error adding vector column: {e}")
            session.rollback()
            raise

        # Step 5: Create vector index
        logger.info("🔧 Step 5: Creating vector index...")
        try:
            # Check if index already exists
            index_exists = session.execute(text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'products' AND indexname = 'idx_products_search_vector'
            """)).fetchone()

            if not index_exists:
                session.execute(text("""
                    CREATE INDEX idx_products_search_vector
                    ON products USING ivfflat (search_vector vector_cosine_ops)
                    WITH (lists = 100)
                """))
                session.commit()
                logger.info("✅ Vector index created successfully")
            else:
                logger.info("ℹ️  Vector index already exists")
        except Exception as e:
            logger.error(f"❌ Error creating vector index: {e}")
            session.rollback()
            raise

        # Step 6: Verify migration
        logger.info("🔍 Step 6: Verifying migration...")

        # Check tables
        expected_tables = ['products', 'product_descriptions', 'product_files',
                          'technical_specs', 'product_embeddings']
        existing_tables = [t[0] for t in tables]

        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.warning(f"⚠️  Table '{table}' not found")

        # Check pgvector extension
        pgvector_version = session.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()

        if pgvector_version:
            logger.info(f"✅ pgvector extension version: {pgvector_version[0]}")
        else:
            logger.warning("⚠️  pgvector extension not found")

        # Check vector column
        vector_column = session.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'search_vector'
        """)).fetchone()

        if vector_column:
            logger.info(f"✅ Vector column exists: {vector_column[0]} ({vector_column[1]})")
        else:
            logger.warning("⚠️  Vector column not found")

        # Check vector index
        vector_index = session.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'products' AND indexname = 'idx_products_search_vector'
        """)).fetchone()

        if vector_index:
            logger.info(f"✅ Vector index exists: {vector_index[0]}")
        else:
            logger.warning("⚠️  Vector index not found")

        logger.info("\n" + "="*60)
        logger.info("✅ Migration completed successfully!")
        logger.info("="*60)
        logger.info("\n📊 New schema:")
        logger.info("  - products")
        logger.info("  - product_descriptions")
        logger.info("  - product_files")
        logger.info("  - technical_specs")
        logger.info("  - product_embeddings")
        logger.info("\n🔧 Extensions:")
        logger.info("  - pgvector (enabled)")
        logger.info("\n📈 Indexes:")
        logger.info("  - idx_products_search_vector (ivfflat)")

    except Exception as e:
        logger.error(f"\n❌ Migration failed: {str(e)}")
        session.rollback()
        raise

    finally:
        session.close()


def rollback():
    """
    Rollback the migration by dropping new tables

    WARNING: This will delete all data in the new tables!
    """
    logger.warning("⚠️  Starting rollback...")
    logger.warning("⚠️  This will delete all data in the new tables!")

    confirm = input("Are you sure you want to rollback? (yes/no): ")

    if confirm.lower() != 'yes':
        logger.info("Rollback cancelled")
        return

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5433/postgres"
    )

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Drop new tables
        session.execute(text("DROP TABLE IF EXISTS product_embeddings CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS technical_specs CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS product_files CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS product_descriptions CASCADE"))
        session.execute(text("DROP TABLE IF EXISTS products CASCADE"))
        session.commit()

        logger.info("✅ Rollback completed successfully")

    except Exception as e:
        logger.error(f"❌ Rollback failed: {str(e)}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate database to product-based schema with pgvector"
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the migration (WARNING: deletes all data)'
    )

    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
