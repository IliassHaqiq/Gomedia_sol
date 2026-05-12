"""
Vector Search Service using pgvector

This module provides RAG (Retrieval-Augmented Generation) search capabilities
using PostgreSQL's pgvector extension for semantic similarity search.
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.product import Product, ProductEmbedding
from app.services.deepseek import deepseek_service
import json

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Service for vector similarity search using pgvector

    Provides methods for:
    - Creating and storing embeddings for products
    - Searching for similar products using vector similarity
    - Managing product embeddings
    """

    def __init__(self, db: Session):
        """
        Initialize vector search service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    async def create_product_embedding(
        self,
        product_id: int,
        text: str,
        embedding_type: str = "combined"
    ) -> List[float]:
        """
        Create and store embedding for a product

        Args:
            product_id: Product ID
            text: Text to embed
            embedding_type: Type of embedding ('description', 'specs', 'combined')

        Returns:
            The embedding vector as list of floats

        Raises:
            Exception: If embedding generation or storage fails
        """
        # Generate embedding using DeepSeek
        embedding = await deepseek_service.generate_embedding(text)

        # Store embedding in product_embeddings table
        embedding_record = ProductEmbedding(
            product_id=product_id,
            embedding=json.dumps(embedding),
            embedding_type=embedding_type,
            model_name="deepseek-v4-pro"
        )

        self.db.add(embedding_record)

        # Also update the search_vector column on products table
        vector_str = "[" + ",".join(map(str, embedding)) + "]"
        self.db.execute(
            text(f"""
                UPDATE products
                SET search_vector = '{vector_str}'::vector
                WHERE id = :product_id
            """),
            {"product_id": product_id}
        )

        self.db.commit()

        logger.info(f"✅ Created embedding for product {product_id} (type: {embedding_type})")

        return embedding

    async def search_similar_products(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        embedding_type: str = "combined"
    ) -> List[Dict]:
        """
        Search for similar products using vector similarity

        Args:
            query: Search query text
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            embedding_type: Type of embedding to search against

        Returns:
            List of similar products with similarity scores

        Raises:
            Exception: If search fails
        """
        # Generate embedding for query
        query_embedding = await deepseek_service.generate_embedding(query)
        vector_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Perform vector search using pgvector
        # Using cosine distance (1 - cosine_similarity)
        results = self.db.execute(
            text(f"""
                SELECT
                    p.id,
                    p.ref_produit,
                    p.marque,
                    p.designation,
                    pd.descriptif_fr,
                    pd.descriptif_en_specs,
                    1 - (search_vector <=> '{vector_str}'::vector) as similarity
                FROM products p
                LEFT JOIN product_descriptions pd ON p.id = pd.product_id
                WHERE search_vector IS NOT NULL
                ORDER BY search_vector <=> '{vector_str}'::vector
                LIMIT :limit
            """),
            {"limit": limit}
        ).fetchall()

        # Filter by threshold and format results
        formatted_results = []
        for row in results:
            similarity = float(row.similarity)
            if similarity >= threshold:
                formatted_results.append({
                    "product_id": row.id,
                    "ref_produit": row.ref_produit,
                    "marque": row.marque,
                    "designation": row.designation,
                    "descriptif_fr": row.descriptif_fr,
                    "descriptif_en": row.descriptif_en_specs,
                    "similarity": similarity
                })

        logger.info(f"✅ Found {len(formatted_results)} similar products for query")

        return formatted_results

    def get_product_by_ref(self, ref_produit: str) -> Optional[Product]:
        """
        Get product by reference number

        Args:
            ref_produit: Product reference/part number

        Returns:
            Product object or None if not found
        """
        return self.db.query(Product).filter(
            Product.ref_produit == ref_produit
        ).first()

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get product by ID

        Args:
            product_id: Product ID

        Returns:
            Product object or None if not found
        """
        return self.db.query(Product).filter(
            Product.id == product_id
        ).first()

    def get_all_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Product objects
        """
        return self.db.query(Product).offset(skip).limit(limit).all()

    def get_product_embeddings(self, product_id: int) -> List[ProductEmbedding]:
        """
        Get all embeddings for a product

        Args:
            product_id: Product ID

        Returns:
            List of ProductEmbedding objects
        """
        return self.db.query(ProductEmbedding).filter(
            ProductEmbedding.product_id == product_id
        ).all()

    def delete_product_embeddings(self, product_id: int) -> int:
        """
        Delete all embeddings for a product

        Args:
            product_id: Product ID

        Returns:
            Number of embeddings deleted
        """
        count = self.db.query(ProductEmbedding).filter(
            ProductEmbedding.product_id == product_id
        ).count()

        self.db.query(ProductEmbedding).filter(
            ProductEmbedding.product_id == product_id
        ).delete()

        # Clear search_vector column
        self.db.execute(
            text("""
                UPDATE products
                SET search_vector = NULL
                WHERE id = :product_id
            """),
            {"product_id": product_id}
        )

        self.db.commit()

        logger.info(f"✅ Deleted {count} embeddings for product {product_id}")

        return count

    async def rebuild_all_embeddings(self) -> Dict[str, int]:
        """
        Rebuild embeddings for all products

        This is useful when:
        - Changing the embedding model
        - Updating product descriptions
        - Initial setup

        Returns:
            Dictionary with statistics (total, success, failed)
        """
        products = self.get_all_products(limit=1000)  # Limit to 1000 for safety

        stats = {
            "total": len(products),
            "success": 0,
            "failed": 0
        }

        for product in products:
            try:
                # Combine description text
                text_parts = []
                if product.designation:
                    text_parts.append(product.designation)
                if product.marque:
                    text_parts.append(product.marque)

                # Get descriptions
                descriptions = self.db.execute(
                    text("""
                        SELECT descriptif_fr, descriptif_en_specs
                        FROM product_descriptions
                        WHERE product_id = :product_id
                    """),
                    {"product_id": product.id}
                ).fetchone()

                if descriptions:
                    if descriptions.descriptif_fr:
                        text_parts.append(descriptions.descriptif_fr)
                    if descriptions.descriptif_en_specs:
                        text_parts.append(descriptions.descriptif_en)

                # Get technical specs
                specs = self.db.execute(
                    text("""
                        SELECT attribut, valeur, unite
                        FROM technical_specs
                        WHERE product_id = :product_id
                    """),
                    {"product_id": product.id}
                ).fetchall()

                for spec in specs:
                    text_parts.append(f"{spec.attribut}: {spec.valeur} {spec.unite or ''}")

                if text_parts:
                    combined_text = " ".join(text_parts)
                    await self.create_product_embedding(product.id, combined_text)
                    stats["success"] += 1
                else:
                    stats["failed"] += 1

            except Exception as e:
                logger.error(f"❌ Failed to rebuild embedding for product {product.id}: {e}")
                stats["failed"] += 1

        logger.info(f"✅ Rebuilt embeddings: {stats['success']} success, {stats['failed']} failed")

        return stats
