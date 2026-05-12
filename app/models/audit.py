from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.db.base import Base
from sqlalchemy.sql import func

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    specification_id = Column(Integer, ForeignKey("specifications.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., 'created', 'updated', 'validated', 'exported'
    user_id = Column(String, default="system")  # For future authentication
    changes = Column(JSON)  # Store what was changed: {"field": {"old": "val", "new": "val"}}
    created_at = Column(DateTime, default=func.now())
