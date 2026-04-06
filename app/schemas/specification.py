from pydantic import BaseModel
from typing import Optional, dict

class SpecificationOut(BaseModel):
    id: int
    document_id: int
    numero_de_piece: Optional[str]
    designation: Optional[str]
    fabricant: Optional[str]
    description_fr: Optional[str]
    description_en: Optional[str]
    structured_data: Optional[dict]
    validation_status: str

    model_config = {"from_attributes": True}