import os
import shutil
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.models.specification import Specification
from app.services.extractor import extract_text_from_file
from app.services.llm import generate_spec

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = (".pdf", ".xlsx")


def is_allowed_file(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def save_uploaded_file(file: UploadFile) -> str:
    """
    Sauvegarde un fichier uploadé dans le dossier uploads/.
    Si le nom existe déjà, ajoute un suffixe numérique.
    """
    original_filename = file.filename or "uploaded_file"
    base_name, ext = os.path.splitext(original_filename)
    safe_filename = original_filename
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    counter = 1
    while os.path.exists(file_path):
        safe_filename = f"{base_name}_{counter}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        counter += 1

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def create_spec_from_document(doc: Document, db: Session) -> Specification:
    """
    Extrait le texte du document, génère la spec via LLM,
    l'insère en base et met à jour le statut du document.
    """
    text = extract_text_from_file(doc.file_path)
    structured = generate_spec(text, doc.filename)

    spec = Specification(
        document_id=doc.id,
        numero_de_piece=structured.get("numero_de_piece", "N/A"),
        designation=structured.get("designation", "N/A"),
        fabricant=structured.get("fabricant", "N/A"),
        description_fr=structured.get("description_fr", "N/A"),
        description_en=structured.get("description_en", "N/A"),
        structured_data=structured.get("specifications", {}),
        validation_status="pending",
        prompt_version="v2"
    )

    db.add(spec)
    doc.status = "extracted"
    db.commit()
    db.refresh(spec)

    return spec


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload d'un seul fichier.
    Swagger affichera un bouton 'Choose File / Parcourir'.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. Utilisez .pdf ou .xlsx"
        )

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

        return {
            "message": "Fichier uploadé avec succès",
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "status": doc.status
            }
        }

    except Exception as e:
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
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    uploaded_documents = []
    skipped_files = []

    for file in files:
        if not file.filename:
            skipped_files.append({
                "filename": None,
                "reason": "Nom de fichier manquant"
            })
            continue

        if not is_allowed_file(file.filename):
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

            uploaded_documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "file_path": doc.file_path,
                "status": doc.status
            })

        except Exception as e:
            skipped_files.append({
                "filename": file.filename,
                "reason": f"Erreur upload: {str(e)}"
            })

    return {
        "message": "Upload multiple terminé",
        "uploaded_count": len(uploaded_documents),
        "skipped_count": len(skipped_files),
        "documents": uploaded_documents,
        "skipped_files": skipped_files
    }


@router.post("/{doc_id}/extract")
def extract_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Extrait un document déjà uploadé et crée une specification.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    try:
        spec = create_spec_from_document(doc, db)

        return {
            "message": "Extraction réussie",
            "specification": {
                "id": spec.id,
                "document_id": spec.document_id,
                "numero_de_piece": spec.numero_de_piece,
                "designation": spec.designation,
                "fabricant": spec.fabricant,
                "description_fr": spec.description_fr,
                "description_en": spec.description_en,
                "structured_data": spec.structured_data,
                "validation_status": spec.validation_status,
                "prompt_version": spec.prompt_version
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Erreur extraction: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur specification: {str(e)}")


@router.post("/extract-all")
def extract_all_uploaded_documents(db: Session = Depends(get_db)):
    """
    Extrait tous les documents avec status='uploaded'.
    """
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
            spec = create_spec_from_document(doc, db)
            results.append({
                "document_id": doc.id,
                "filename": doc.filename,
                "status": "success",
                "specification_id": spec.id
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