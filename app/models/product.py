"""
Product Models - Database Schema for Product-Centric Architecture

This module defines the database models for the new product-based schema.
Each product can have descriptions, files, technical specs, and embeddings.
"""
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class Product(Base):
    """
    Main product table representing industrial components.

    Attributes:
        id: Primary key
        ref_produit: Unique product reference/part number
        marque: Manufacturer/brand name
        designation: Product designation/name
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    ref_produit = Column(String(100), unique=True, nullable=False, index=True)
    marque = Column(String(100), index=True)
    designation = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    descriptions = relationship("ProductDescription", back_populates="product", cascade="all, delete-orphan")
    files = relationship("ProductFile", back_populates="product", cascade="all, delete-orphan")
    technical_specs = relationship("TechnicalSpec", back_populates="product", cascade="all, delete-orphan")
    embeddings = relationship("ProductEmbedding", back_populates="product", cascade="all, delete-orphan")


class ProductDescription(Base):
    """
    Product descriptions in French and English.

    Attributes:
        id: Primary key
        product_id: Foreign key to products
        descriptif_fr: French description
        descriptif_en_specs: English specification description
        last_edited_by_human: Whether description was manually edited
    """
    __tablename__ = "product_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True)
    descriptif_fr = Column(Text)
    descriptif_en_specs = Column(Text)
    last_edited_by_human = Column(Boolean, default=False)

    # Relationship
    product = relationship("Product", back_populates="descriptions")


class ProductFile(Base):
    """
    Files associated with a product (PDF, Excel, etc.).

    Attributes:
        id: Primary key
        product_id: Foreign key to products
        file_name: Original filename
        file_path: Storage path
        file_hash: SHA256 hash for deduplication
        created_at: Upload timestamp
    """
    __tablename__ = "product_files"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    file_name = Column(String(255))
    file_path = Column(Text)
    file_hash = Column(String(64))
    created_at = Column(DateTime, default=func.now())

    # Relationship
    product = relationship("Product", back_populates="files")


class TechnicalSpec(Base):
    """
    Technical specifications for a product.

    Attributes:
        id: Primary key
        product_id: Foreign key to products
        attribut: Attribute name (e.g., "Tension nominale")
        valeur: Attribute value
        unite: Unit of measurement (e.g., "V", "A", "W")
    """
    __tablename__ = "technical_specs"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    attribut = Column(String(1000))
    valeur = Column(Text)
    unite = Column(String(50))

    # Relationship
    product = relationship("Product", back_populates="technical_specs")


class ProductEmbedding(Base):
    """
    Vector embeddings for semantic search.

    Attributes:
        id: Primary key
        product_id: Foreign key to products
        embedding: JSON string of the vector
        embedding_type: Type of embedding ('description', 'specs', 'combined')
        model_name: Model used for embedding
        created_at: Creation timestamp
    """
    __tablename__ = "product_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    embedding = Column(Text)  # JSON string of the vector
    embedding_type = Column(String(50))  # 'description', 'specs', 'combined'
    model_name = Column(String(100))  # 'deepseek-v4-pro'
    created_at = Column(DateTime, default=func.now())

    # Relationship
    product = relationship("Product", back_populates="embeddings")
