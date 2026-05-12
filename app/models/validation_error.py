from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from app.db.base import Base
from sqlalchemy.sql import func

class ValidationError(Base):
    __tablename__ = "validation_errors"

    id = Column(Integer, primary_key=True, index=True)
    specification_id = Column(Integer, ForeignKey("specifications.id"), nullable=False)
    field_name = Column(String, nullable=False)
    error_type = Column(String, nullable=False)  # e.g., 'missing', 'invalid_format', 'low_confidence'
    error_message = Column(String, nullable=False)
    suggested_value = Column(String)
    severity = Column(String, default="warning")  # warning, error
    status = Column(String, default="open")  # open, resolved, ignored
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)
    resolved_by = Column(String)
