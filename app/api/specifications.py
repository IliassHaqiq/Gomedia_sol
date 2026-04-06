from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.specification import Specification

router = APIRouter()

@router.get("/")
def get_specifications(db: Session = Depends(get_db)):
    specs = db.query(Specification).all()
    return specs

@router.get("/{spec_id}")
def get_specification(spec_id: int, db: Session = Depends(get_db)):
    spec = db.query(Specification).filter(Specification.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spécification introuvable")
    return spec

@router.put("/{spec_id}")
def update_specification(spec_id: int, updates: dict, db: Session = Depends(get_db)):
    spec = db.query(Specification).filter(Specification.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spécification introuvable")
    for key, value in updates.items():
        setattr(spec, key, value)
    spec.validation_status = "validated"
    db.commit()
    db.refresh(spec)
    return spec