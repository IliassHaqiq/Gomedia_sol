from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.document import Document
from app.models.specification import Specification
from app.services.extractor import extract_text_from_pdf
from app.services.llm import generate_spec
import shutil, os

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".pdf", ".PDF", ".xlsx", ".cvx")):
        raise HTTPException(status_code=400, detail="Format non supporté")

    file_path = f"{UPLOAD_DIR}/{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(filename=file.filename, file_path=file_path, status="uploaded")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "filename": doc.filename, "status": doc.status}

@router.post("/{doc_id}/extract")
def extract_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    text = extract_text_from_pdf(doc.file_path)
    structured = generate_spec(text, doc.filename)

    spec = Specification(
        document_id=doc.id,
        numero_de_piece=structured.get("numero_de_piece", "N/A"),
        designation=structured.get("designation", "N/A"),
        fabricant=structured.get("fabricant", "N/A"),
        description_fr=structured.get("description_fr", "N/A"),
        description_en=structured.get("description_en", "N/A"),
        structured_data=structured.get("specifications", {}),
        validation_status="pending"
    )
    db.add(spec)
    doc.status = "extracted"
    db.commit()
    db.refresh(spec)
    return spec