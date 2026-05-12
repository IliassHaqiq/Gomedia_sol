from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.db.base import Base

class Specification(Base):
    __tablename__ = "specifications"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    numero_de_piece = Column(String)
    designation = Column(String)
    fabricant = Column(String)
    description_fr = Column(String)
    description_en = Column(String)
    structured_data = Column(JSON)
    validation_status = Column(String, default="pending")
    prompt_version = Column(String, default="v1")
    description_length = Column(String, default="medium")  # short, medium, long