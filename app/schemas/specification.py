from pydantic import BaseModel
from typing import Optional, Any

class SpecificationOut(BaseModel):
    id: int
    document_id: int
    numero_de_piece: Optional[str] = None
    designation: Optional[str] = None
    fabricant: Optional[str] = None
    description_fr: Optional[str] = None
    description_en: Optional[str] = None
    structured_data: Optional[Any] = None
    validation_status: str
    description_length: Optional[str] = "medium"

    model_config = {"from_attributes": True}


class SpecificationUpdate(BaseModel):
    numero_de_piece: Optional[str] = None
    designation: Optional[str] = None
    fabricant: Optional[str] = None
    description_fr: Optional[str] = None
    description_en: Optional[str] = None
    structured_data: Optional[Any] = None
    validation_status: Optional[str] = None
    description_length: Optional[str] = None