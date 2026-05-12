from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from app.db.base import Base
from sqlalchemy.sql import func

class ExportConfig(Base):
    __tablename__ = "export_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    format = Column(String, nullable=False)  # json, csv, pdf
    template = Column(String)  # For PDF/CSV formatting
    fields = Column(JSON)  # List of fields to include
    language = Column(String, default="fr")  # fr, en, both
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
