from pydantic import BaseModel
from datetime import datetime

class DocumentOut(BaseModel):
    id: int
    filename: str
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}