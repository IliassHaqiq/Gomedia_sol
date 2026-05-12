"""
Migration Script - Create Product Tables

This script creates the product-based tables while keeping the existing documents table.

Usage:
    python migrations/create_product_tables.py

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
    Execute the migration to create product tables

    Steps:
    1. Create new product tables
    2. Enable pgvector extension
    3. Add vector column to products
    4. Create vector index
    """
    logger.info("🚀 Starting migration to create product tables...")

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
        # Step 1: Create new product tables
        logger.info("📦 Step 1: Creating product tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Product tables created successfully")

        # List created tables
        tables = session.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)).fetchall()
        logger.info(f"📊 Tables in database: {[t[0] for t in tables]}")

        # Step 2: Enable pgvector extension
        logger.info("🔧 Step 2: Enabling pgvector extension...")
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

        # Step 3: Add vector column to products table
        logger.info("🔧 Step 3: Adding vector column to products table...")
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

        # Step 4: Create vector index
        logger.info("🔧 Step 4: Creating vector index...")
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

        # Step 5: Verify migration
        logger.info("🔍 Step 5: Verifying migration...")

        # Check tables
        expected_tables = ['products', 'product_descriptions', 'product_files',
                          'technical_specs', 'product_embeddings', 'documents']
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
        logger.info("  - documents (kept)")
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


if __name__ == "__main__":
    migrate()
