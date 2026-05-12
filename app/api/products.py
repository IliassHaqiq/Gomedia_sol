"""
Product API Endpoints

This module provides REST API endpoints for product management including:
- Product CRUD operations
- File upload and specification extraction
- Vector similarity search
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.db.session import get_db
from app.models.product import Product, ProductDescription, ProductFile, TechnicalSpec
from app.services.extractor import extract_text_from_file
from app.services.deepseek import deepseek_service
from app.services.vector_search import VectorSearchService
from app.services.description_generator import DescriptionGeneratorService, DescriptionLength
import os
import shutil
import hashlib

router = APIRouter()


# Pydantic schemas for request/response validation
class ProductBase(BaseModel):
    """Base product schema"""
    ref_produit: str = Field(..., description="Product reference/part number", max_length=100)
    marque: Optional[str] = Field(None, description="Manufacturer/brand", max_length=100)
    designation: Optional[str] = Field(None, description="Product designation", max_length=255)


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    marque: Optional[str] = Field(None, max_length=100)
    designation: Optional[str] = Field(None, max_length=255)


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: int
    ref_produit: str
    marque: Optional[str] = None
    designation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductDescriptionResponse(BaseModel):
    """Schema for product description"""
    id: int
    product_id: int
    descriptif_fr: Optional[str] = None
    descriptif_en_specs: Optional[str] = None
    last_edited_by_human: bool

    class Config:
        from_attributes = True


class TechnicalSpecResponse(BaseModel):
    """Schema for technical specification"""
    id: int
    product_id: int
    attribut: str
    valeur: Optional[str] = None
    unite: Optional[str] = None

    class Config:
        from_attributes = True


class ProductFileResponse(BaseModel):
    """Schema for product file"""
    id: int
    product_id: int
    file_name: str
    file_path: str
    file_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProductDetailResponse(ProductResponse):
    """Schema for detailed product response"""
    descriptions: Optional[ProductDescriptionResponse] = None
    files: List[ProductFileResponse] = []
    technical_specs: List[TechnicalSpecResponse] = []


class SimilarProductResult(BaseModel):
    """Schema for similar product search result"""
    product_id: int
    ref_produit: str
    marque: Optional[str] = None
    designation: Optional[str] = None
    descriptif_fr: Optional[str] = None
    descriptif_en: Optional[str] = None
    similarity: float


class SimilarProductsResponse(BaseModel):
    """Schema for similar products search response"""
    results: List[SimilarProductResult]
    query: str
    count: int


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product

    Args:
        product: Product data
        db: Database session

    Returns:
        Created product

    Raises:
        HTTPException: If product reference already exists
    """
    # Check if reference already exists
    existing = db.query(Product).filter(
        Product.ref_produit == product.ref_produit
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product with reference '{product.ref_produit}' already exists"
        )

    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    List all products with pagination

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of products
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Get product details by ID

    Args:
        product_id: Product ID
        db: Database session

    Returns:
        Product details with descriptions, files, and specs

    Raises:
        HTTPException: If product not found
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Build response manually to handle SQLAlchemy relationships
    response_data = {
        "id": product.id,
        "ref_produit": product.ref_produit,
        "marque": product.marque,
        "designation": product.designation,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "descriptions": None,
        "files": [],
        "technical_specs": []
    }

    # Get descriptions
    if product.descriptions:
        desc = product.descriptions[0] if isinstance(product.descriptions, list) else product.descriptions
        response_data["descriptions"] = {
            "id": desc.id,
            "product_id": desc.product_id,
            "descriptif_fr": desc.descriptif_fr,
            "descriptif_en_specs": desc.descriptif_en_specs,
            "last_edited_by_human": desc.last_edited_by_human
        }

    # Get files
    if product.files:
        files_list = product.files if isinstance(product.files, list) else [product.files]
        response_data["files"] = [
            {
                "id": f.id,
                "product_id": f.product_id,
                "file_name": f.file_name,
                "file_path": f.file_path,
                "file_hash": f.file_hash,
                "created_at": f.created_at
            }
            for f in files_list
        ]

    # Get technical specs
    if product.technical_specs:
        specs_list = product.technical_specs if isinstance(product.technical_specs, list) else [product.technical_specs]
        response_data["technical_specs"] = [
            {
                "id": s.id,
                "product_id": s.product_id,
                "attribut": s.attribut,
                "valeur": s.valeur,
                "unite": s.unite
            }
            for s in specs_list
        ]

    return response_data


@router.get("/ref/{ref_produit}", response_model=ProductDetailResponse)
def get_product_by_ref(ref_produit: str, db: Session = Depends(get_db)):
    """
    Get product details by reference number

    Args:
        ref_produit: Product reference/part number
        db: Database session

    Returns:
        Product details with descriptions, files, and specs

    Raises:
        HTTPException: If product not found
    """
    product = db.query(Product).filter(Product.ref_produit == ref_produit).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Build response manually to handle SQLAlchemy relationships
    response_data = {
        "id": product.id,
        "ref_produit": product.ref_produit,
        "marque": product.marque,
        "designation": product.designation,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "descriptions": None,
        "files": [],
        "technical_specs": []
    }

    # Get descriptions
    if product.descriptions:
        desc = product.descriptions[0] if isinstance(product.descriptions, list) else product.descriptions
        response_data["descriptions"] = {
            "id": desc.id,
            "product_id": desc.product_id,
            "descriptif_fr": desc.descriptif_fr,
            "descriptif_en_specs": desc.descriptif_en_specs,
            "last_edited_by_human": desc.last_edited_by_human
        }

    # Get files
    if product.files:
        files_list = product.files if isinstance(product.files, list) else [product.files]
        response_data["files"] = [
            {
                "id": f.id,
                "product_id": f.product_id,
                "file_name": f.file_name,
                "file_path": f.file_path,
                "file_hash": f.file_hash,
                "created_at": f.created_at
            }
            for f in files_list
        ]

    # Get technical specs
    if product.technical_specs:
        specs_list = product.technical_specs if isinstance(product.technical_specs, list) else [product.technical_specs]
        response_data["technical_specs"] = [
            {
                "id": s.id,
                "product_id": s.product_id,
                "attribut": s.attribut,
                "valeur": s.valeur,
                "unite": s.unite
            }
            for s in specs_list
        ]

    return response_data


@router.post("/{product_id}/upload", status_code=201)
async def upload_product_file(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for a product and extract specifications

    This endpoint:
    1. Uploads the file (PDF or Excel)
    2. Extracts text from the file
    3. Uses DeepSeek to extract structured product data
    4. Updates product information
    5. Creates technical specifications
    6. Generates vector embeddings for search

    Args:
        product_id: Product ID
        file: Uploaded file (PDF or Excel)
        db: Database session

    Returns:
        Upload result with extracted data

    Raises:
        HTTPException: If product not found or processing fails
    """
    # Check product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate file type
    allowed_extensions = {'.pdf', '.xlsx', '.xls'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Create uploads directory
    upload_dir = "uploads/products"
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    safe_filename = f"{product_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Calculate file hash
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    # Store file record
    product_file = ProductFile(
        product_id=product_id,
        file_name=file.filename,
        file_path=file_path,
        file_hash=file_hash
    )
    db.add(product_file)

    # Extract text from file
    try:
        extracted_text = extract_text_from_file(file_path)

        # Use DeepSeek to extract structured data
        product_data = await deepseek_service.extract_product_data(extracted_text)

        # Update product if data extracted
        if product_data.get("designation"):
            product.designation = product_data["designation"]
        if product_data.get("marque"):
            product.marque = product_data["marque"]

        # Create/update description
        description = db.query(ProductDescription).filter(
            ProductDescription.product_id == product_id
        ).first()

        if not description:
            description = ProductDescription(product_id=product_id)
            db.add(description)

        description.descriptif_fr = product_data.get("descriptif_fr")
        description.descriptif_en_specs = product_data.get("descriptif_en")

        # Create technical specs
        for attr_name, spec_data in product_data.get("technical_specs", {}).items():
            if isinstance(spec_data, dict):
                value = spec_data.get("value")
                unit = spec_data.get("unit")
            else:
                value = str(spec_data)
                unit = None

            tech_spec = TechnicalSpec(
                product_id=product_id,
                attribut=attr_name,
                valeur=value,
                unite=unit
            )
            db.add(tech_spec)

        # Create embedding for search
        vector_service = VectorSearchService(db)
        combined_text = f"{product_data.get('descriptif_fr', '')} {product_data.get('descriptif_en', '')}"
        await vector_service.create_product_embedding(product_id, combined_text)

        db.commit()
        db.refresh(product)

        return {
            "message": "File uploaded and processed successfully",
            "product": ProductResponse.model_validate(product),
            "extracted_data": product_data
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/search/similar", response_model=SimilarProductsResponse)
async def search_similar_products(
    query: str = Query(..., description="Search query text", min_length=2),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    threshold: float = Query(0.7, ge=0, le=1, description="Minimum similarity threshold"),
    db: Session = Depends(get_db)
):
    """
    Search for similar products using vector similarity

    This endpoint uses pgvector to find semantically similar products
    based on the search query.

    Args:
        query: Search query text
        limit: Maximum number of results
        threshold: Minimum similarity threshold (0-1)
        db: Database session

    Returns:
        List of similar products with similarity scores
    """
    vector_service = VectorSearchService(db)
    results = await vector_service.search_similar_products(
        query=query,
        limit=limit,
        threshold=threshold
    )

    return SimilarProductsResponse(
        results=[SimilarProductResult(**r) for r in results],
        query=query,
        count=len(results)
    )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updates: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update product information

    Args:
        product_id: Product ID
        updates: Product data to update
        db: Database session

    Returns:
        Updated product

    Raises:
        HTTPException: If product not found
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=200)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Delete a product

    This will also delete all related:
    - Descriptions
    - Files
    - Technical specifications
    - Embeddings

    Args:
        product_id: Product ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If product not found
    """
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


# Description Generation Endpoints

class DescriptionGenerateRequest(BaseModel):
    """Schema for description generation request"""
    length: str = Field(default="medium", description="Description length: short, medium, or long")


class DescriptionGenerateResponse(BaseModel):
    """Schema for description generation response"""
    product_id: int
    descriptif_fr: str
    descriptif_en: str
    length: str
    success: bool


class TechnicalSpecCreate(BaseModel):
    """Schema for creating a technical specification"""
    attribut: str = Field(..., description="Attribute name", max_length=1000)
    valeur: str = Field(..., description="Attribute value")
    unite: Optional[str] = Field(None, description="Unit of measurement", max_length=50)


@router.post("/{product_id}/specs", status_code=201)
def add_technical_spec(
    product_id: int,
    spec: TechnicalSpecCreate,
    db: Session = Depends(get_db)
):
    """
    Add a technical specification to a product

    Args:
        product_id: Product ID
        spec: Technical specification data
        db: Database session

    Returns:
        Created specification

    Raises:
        HTTPException: If product not found
    """
    # Check product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Create technical spec
    tech_spec = TechnicalSpec(
        product_id=product_id,
        attribut=spec.attribut,
        valeur=spec.valeur,
        unite=spec.unite
    )
    db.add(tech_spec)
    db.commit()
    db.refresh(tech_spec)

    return TechnicalSpecResponse.model_validate(tech_spec)


@router.get("/{product_id}/specs", response_model=List[TechnicalSpecResponse])
def get_technical_specs(product_id: int, db: Session = Depends(get_db)):
    """
    Get all technical specifications for a product

    Args:
        product_id: Product ID
        db: Database session

    Returns:
        List of technical specifications

    Raises:
        HTTPException: If product not found
    """
    # Check product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    specs = db.query(TechnicalSpec).filter(
        TechnicalSpec.product_id == product_id
    ).all()

    return [TechnicalSpecResponse.model_validate(spec) for spec in specs]


@router.post("/{product_id}/description/generate", response_model=DescriptionGenerateResponse)
async def generate_description(
    product_id: int,
    request: DescriptionGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate product description from technical specifications

    This endpoint uses DeepSeek to generate professional descriptions
    based on the technical specifications stored in the database.

    Args:
        product_id: Product ID
        request: Generation request with length parameter
        db: Database session

    Returns:
        Generated descriptions in French and English

    Raises:
        HTTPException: If product not found or generation fails
    """
    # Check product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate length parameter
    valid_lengths = [DescriptionLength.SHORT, DescriptionLength.MEDIUM, DescriptionLength.LONG]
    if request.length not in valid_lengths:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid length. Must be one of: {', '.join(valid_lengths)}"
        )

    # Generate description
    description_service = DescriptionGeneratorService(db)
    result = await description_service.generate_and_save_description(
        product_id=product_id,
        length=request.length
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Description generation failed: {result.get('error', 'Unknown error')}"
        )

    return DescriptionGenerateResponse(
        product_id=product_id,
        descriptif_fr=result["descriptif_fr"],
        descriptif_en=result["descriptif_en"],
        length=request.length,
        success=True
    )


@router.put("/{product_id}/description")
def update_description(
    product_id: int,
    descriptif_fr: Optional[str] = None,
    descriptif_en: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update product description manually

    Args:
        product_id: Product ID
        descriptif_fr: French description
        descriptif_en: English description
        db: Database session

    Returns:
        Updated description

    Raises:
        HTTPException: If product not found
    """
    # Check product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get or create description
    description = db.query(ProductDescription).filter(
        ProductDescription.product_id == product_id
    ).first()

    if not description:
        description = ProductDescription(product_id=product_id)
        db.add(description)

    # Update fields
    if descriptif_fr is not None:
        description.descriptif_fr = descriptif_fr
    if descriptif_en is not None:
        description.descriptif_en_specs = descriptif_en

    description.last_edited_by_human = True
    db.commit()
    db.refresh(description)

    return ProductDescriptionResponse.model_validate(description)
