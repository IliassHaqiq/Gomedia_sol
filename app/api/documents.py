# Standard library imports
import os
import shutil
import re
import logging
from typing import List
import hashlib

# Third-party imports
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session

# Local imports
from app.db.session import get_db
from app.models.document import Document
from app.models.product import Product, ProductDescription, ProductFile, TechnicalSpec, ProductEmbedding
from app.services.extractor import extract_text_from_file
from app.services.llm import generate_spec, generate_specs_multi

# Configuration
router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Configuration validation fichiers
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB par défaut
ALLOWED_EXTENSIONS = (".pdf", ".xlsx")
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream"  # Pour certains navigateurs
]

# Logger
logger = logging.getLogger(__name__)
logger.info("📂 Document API module chargé")


def is_allowed_file(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def sanitize_filename(filename: str) -> str:
    """Nettoie le nom de fichier pour éviter les injections de chemin"""
    if not filename:
        return "unnamed_file"

    # Garder seulement le basename pour éviter les chemins
    filename = os.path.basename(filename)

    # Retirer les caractères spéciaux sauf . _ - et alphanumériques
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Limiter la longueur à 200 caractères
    if len(filename) > 200:
        base, ext = os.path.splitext(filename)
        filename = base[:195] + ext

    # Si le nom est vide après nettoyage, donner un nom par défaut
    if not filename or filename == '.':
        return "uploaded_file.dat"

    return filename


def validate_uploaded_file(file: UploadFile) -> None:
    """Valide le fichier uploadé"""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    # Validation type MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            400,
            f"Invalid MIME type: {file.content_type}. "
            f"Allowed: {', '.join(ALLOWED_MIME_TYPES[:-1])}"
        )

    # Validation extension
    if not is_allowed_file(file.filename):
        raise HTTPException(
            400,
            "Invalid file extension. Only PDF and XLSX files are allowed"
        )

    # Validation taille (doit se faire après lecture du fichier)
    # La taille sera vérifiée dans la fonction save_uploaded_file


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file for deduplication"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def save_uploaded_file(file: UploadFile) -> str:
    """
    Sauvegarde un fichier uploadé dans le dossier uploads/.
    Si le nom existe déjà, ajoute un suffixe numérique.
    Valide aussi la taille du fichier.
    """
    validate_uploaded_file(file)

    original_filename = sanitize_filename(file.filename or "uploaded_file")
    base_name, ext = os.path.splitext(original_filename)
    safe_filename = original_filename
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Lecture en chunks pour vérifier la taille
    chunk_size = 8192
    total_size = 0
    chunks = []

    while True:
        chunk = file.file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        chunks.append(chunk)

        if total_size > MAX_FILE_SIZE:
            raise HTTPException(413, f"File exceeds maximum size of {MAX_FILE_SIZE} bytes")

    # Sauvegarder le fichier
    with open(file_path, "wb") as buffer:
        for chunk in chunks:
            buffer.write(chunk)

    # Vérifier les doublons et ajouter suffixe si nécessaire
    counter = 1
    while os.path.exists(file_path):
        safe_filename = f"{base_name}_{counter}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        counter += 1

    # Renommer si nécessaire
    if counter > 1:
        os.rename(os.path.join(UPLOAD_DIR, original_filename), file_path)

    logger.info(f"File saved: {safe_filename} ({total_size} bytes)")
    return file_path


def extract_reference_from_filename(filename: str) -> str:
    """
    Extract product reference from filename.
    Examples:
        - 60-1493-21.pdf → 60-1493-21
        - UM121.pdf → UM121
        - TCS_DAT_71.98.2005_uniCOS_PRO-T_FR.pdf → 71.98.2005
        - TCS_DAT_71.98.0502_ConfideaF-DV_en-US (2).pdf → 71.98.0502
    """
    # Remove extension
    base_name = os.path.splitext(filename)[0]

    # Handle TCS_DAT_ prefix pattern
    if base_name.startswith("TCS_DAT_"):
        # Extract the numeric part after TCS_DAT_
        # Pattern: TCS_DAT_XX.XX.XXXX_rest
        match = re.match(r"TCS_DAT_(\d+\.\d+\.\d+)", base_name)
        if match:
            return match.group(1)

    # For other files, return the base name without extension
    return base_name


def create_product_from_document(
    doc: Document,
    db: Session,
    description_length: str = "medium"
) -> List[Product]:
    """
    Extrait le texte du document, génère les données via NVIDIA NIM,
    et crée un ou plusieurs produits avec leurs descriptions, specs et embeddings.
    Retourne une liste de produits créés/mis à jour.
    """
    text = extract_text_from_file(doc.file_path)

    # Use NVIDIA NIM to extract structured data (may return multiple products)
    products_data = generate_specs_multi(text, doc.filename, description_length)

    created_products = []
    file_hash = calculate_file_hash(doc.file_path)

    for idx, product_data in enumerate(products_data):
        # Generate a unique reference for each product in multi-product documents
        # Use the LLM's numero_de_piece if available, otherwise generate one
        ref_produit = product_data.get("numero_de_piece", "N/A")

        # If the reference is N/A or generic, create a unique one based on filename and index
        if ref_produit == "N/A" or not ref_produit:
            base_ref = extract_reference_from_filename(doc.filename)
            if len(products_data) > 1:
                ref_produit = f"{base_ref}-{idx + 1}"
            else:
                ref_produit = base_ref

        existing_product = db.query(Product).filter(Product.ref_produit == ref_produit).first()

        if existing_product:
            logger.info(f"Product already exists: {ref_produit}, updating...")
            product = existing_product
            # Update product info
            product.marque = product_data.get("fabricant", "N/A")
            product.designation = product_data.get("designation", "N/A")
        else:
            # Create new product
            product = Product(
                ref_produit=ref_produit,
                marque=product_data.get("fabricant", "N/A"),
                designation=product_data.get("designation", "N/A")
            )
            db.add(product)
            db.flush()  # Get the product ID

        # Add file to product_files (link document to product)
        existing_file = db.query(ProductFile).filter(
            ProductFile.product_id == product.id,
            ProductFile.file_hash == file_hash
        ).first()

        if not existing_file:
            product_file = ProductFile(
                product_id=product.id,
                file_name=doc.filename,
                file_path=doc.file_path,
                file_hash=file_hash
            )
            db.add(product_file)
            logger.info(f"Added file to product_files: {doc.filename} -> {ref_produit}")

        # Update or create product descriptions
        existing_desc = db.query(ProductDescription).filter(
            ProductDescription.product_id == product.id
        ).first()

        if existing_desc:
            existing_desc.descriptif_fr = product_data.get("description_fr", "N/A")
            existing_desc.descriptif_en_specs = product_data.get("description_en", "N/A")
            logger.info(f"Updated product descriptions for: {ref_produit}")
        else:
            product_description = ProductDescription(
                product_id=product.id,
                descriptif_fr=product_data.get("description_fr", "N/A"),
                descriptif_en_specs=product_data.get("description_en", "N/A")
            )
            db.add(product_description)
            logger.info(f"Created product descriptions for: {ref_produit}")

        # Add technical specs
        specs = product_data.get("specifications", {})
        if isinstance(specs, dict):
            # Clear existing specs for this product
            db.query(TechnicalSpec).filter(TechnicalSpec.product_id == product.id).delete()

            for attr_name, attr_value in specs.items():
                # Parse value if it's a dict with value and unit
                if isinstance(attr_value, dict):
                    valeur = attr_value.get("value", str(attr_value))
                    unite = attr_value.get("unit", "")
                else:
                    valeur = str(attr_value)
                    unite = ""

                tech_spec = TechnicalSpec(
                    product_id=product.id,
                    attribut=attr_name,
                    valeur=valeur,
                    unite=unite
                )
                db.add(tech_spec)

            logger.info(f"Added {len(specs)} technical specs for: {ref_produit}")

        # Generate and add embeddings (placeholder for now)
        try:
            # Combine description and specs for embedding
            combined_text = f"{product_data.get('description_fr', '')} {product_data.get('description_en', '')}"
            for spec_name, spec_value in specs.items():
                if isinstance(spec_value, dict):
                    combined_text += f" {spec_name}: {spec_value.get('value', spec_value)}"
                else:
                    combined_text += f" {spec_name}: {spec_value}"

            # For now, we'll create a simple hash-based embedding as placeholder
            # In production, you would use a proper embedding model
            import hashlib
            text_hash = hashlib.md5(combined_text.encode()).hexdigest()
            # Create a simple 1536-dimensional embedding based on hash
            embedding_vector = [float(int(text_hash[i % len(text_hash)], 16)) / 15.0 for i in range(1536)]

            # Clear existing embeddings
            db.query(ProductEmbedding).filter(ProductEmbedding.product_id == product.id).delete()

            product_embedding = ProductEmbedding(
                product_id=product.id,
                embedding=str(embedding_vector),  # Store as string
                embedding_type="combined",
                model_name="placeholder-hash"
            )
            db.add(product_embedding)
            logger.info(f"Generated placeholder embedding for: {ref_produit}")

        except Exception as e:
            logger.warning(f"Failed to generate embedding for {ref_produit}: {str(e)}")

        created_products.append(product)

    # Update document status
    doc.status = "extracted"

    db.commit()

    # Refresh all products
    for product in created_products:
        db.refresh(product)

    logger.info(f"✅ Extraction completed: {len(created_products)} product(s) created/updated from {doc.filename}")

    return created_products


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload d'un seul fichier.
    Swagger affichera un bouton 'Choose File / Parcourir'.
    """
    logger.info(f"📤 Début upload fichier: {file.filename}")

    if not file.filename:
        logger.warning("❌ Upload annulé: aucun nom de fichier")
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    if not is_allowed_file(file.filename):
        logger.warning(f"❌ Format non supporté: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilisez .pdf ou .xlsx"
        )

    try:
        file_path = save_uploaded_file(file)
        logger.info(f"✅ Fichier sauvegardé: {file_path}")

        doc = Document(
            filename=os.path.basename(file_path),
            file_path=file_path,
            status="uploaded"
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"✅ Document enregistré en base: id={doc.id}, filename={doc.filename}")

        return {
            "message": "Fichier uploadé avec succès",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "status": doc.status
            }
        }

    except HTTPException as he:
        logger.error(f"❌ Erreur HTTP lors de l'upload: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de l'upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload de plusieurs fichiers à la fois.
    Swagger affichera un sélecteur multiple selon le navigateur.
    """
    logger.info(f"📤 Début upload multiple: {len(files)} fichiers")

    if not files:
        logger.warning("❌ Upload multiple annulé: aucun fichier")
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    uploaded_documents = []
    skipped_files = []

    for file in files:
        if not file.filename:
            logger.warning("❌ Fichier sans nom ignoré")
            skipped_files.append({
                "filename": None,
                "reason": "Nom de fichier manquant"
            })
            continue

        if not is_allowed_file(file.filename):
            logger.warning(f"❌ Format non supporté: {file.filename}")
            skipped_files.append({
                "filename": file.filename,
                "reason": "Format non supporté"
            })
            continue

        try:
            file_path = save_uploaded_file(file)

            doc = Document(
                filename=os.path.basename(file_path),
                file_path=file_path,
                status="uploaded"
            )

            db.add(doc)
            db.commit()
            db.refresh(doc)

            logger.info(f"✅ Fichier uploadé: {doc.filename} (id: {doc.id})")
            uploaded_documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "status": doc.status
            })

        except Exception as e:
            logger.error(f"❌ Erreur upload fichier {file.filename}: {str(e)}")
            skipped_files.append({
                "filename": file.filename,
                "reason": f"Erreur upload: {str(e)}"
            })

    logger.info(f"📊 Upload multiple terminé: {len(uploaded_documents)} réussis, {len(skipped_files)} ignorés")

    return {
        "message": "Upload multiple terminé",
        "uploaded_count": len(uploaded_documents),
        "skipped_count": len(skipped_files),
        "documents": uploaded_documents,
        "skipped_files": skipped_files
    }


@router.post("/{doc_id}/extract")
def extract_document(doc_id: int, description_length: str = "medium", db: Session = Depends(get_db)):
    """
    Extrait un document déjà uploadé et crée un ou plusieurs produits avec leurs descriptions et specs.
    Param description_length: short, medium, long
    """
    logger.info(f"🔍 Début extraction document id={doc_id}, length={description_length}")

    if description_length not in ["short", "medium", "long"]:
        logger.warning(f"❌ Longueur invalide: {description_length}")
        raise HTTPException(status_code=400, detail="description_length must be 'short', 'medium', or 'long'")

    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        logger.error(f"❌ Document introuvable: id={doc_id}")
        raise HTTPException(status_code=404, detail="Document introuvable")

    logger.info(f"📄 Document trouvé: {doc.filename} (id: {doc.id}, status: {doc.status})")

    try:
        products = create_product_from_document(doc, db, description_length)
        logger.info(f"✅ Extraction réussie: {len(products)} produit(s) créé(s)/mis à jour")

        return {
            "message": f"Extraction réussie: {len(products)} produit(s) trouvé(s)",
            "document_id": doc.id,
            "filename": doc.filename,
            "products": [
                {
                    "id": product.id,
                    "ref_produit": product.ref_produit,
                    "marque": product.marque,
                    "designation": product.designation,
                    "created_at": product.created_at.isoformat() if product.created_at else None
                }
                for product in products
            ]
        }

    except ValueError as e:
        logger.error(f"❌ Erreur extraction (ValueError): {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erreur extraction: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Erreur specification inattendue: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur specification: {str(e)}")


@router.post("/extract-all")
def extract_all_uploaded_documents(description_length: str = "medium", db: Session = Depends(get_db)):
    """
    Extrait tous les documents avec status='uploaded'.
    Param description_length: short, medium, long
    """
    if description_length not in ["short", "medium", "long"]:
        raise HTTPException(status_code=400, detail="description_length must be 'short', 'medium', or 'long'")
    docs = db.query(Document).filter(Document.status == "uploaded").all()

    if not docs:
        return {
            "message": "Aucun document à extraire",
            "processed_count": 0,
            "results": []
        }

    results = []

    for doc in docs:
        try:
            products = create_product_from_document(doc, db, description_length)
            results.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "status": "success",
                "products_count": len(products),
                "products": [
                    {
                        "product_id": product.id,
                        "ref_produit": product.ref_produit
                    }
                    for product in products
                ]
            })
        except Exception as e:
            results.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "status": "error",
                "error": str(e)
            })

    return {
        "message": "Extraction en lot terminée",
        "processed_count": len(results),
        "results": results
    }


@router.get("/")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.id.desc()).all()

    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_path": doc.file_path,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at
        }
        for doc in docs
    ]


@router.get("/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_path": doc.file_path,
        "status": doc.status,
        "uploaded_at": doc.uploaded_at
    }
