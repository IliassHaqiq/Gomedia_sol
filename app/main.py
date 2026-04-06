from fastapi import FastAPI
from app.api import documents, specifications
from app.db.session import engine
from app.db.base import Base
from app.models import document, specification

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gomedia IA Specs", version="0.1.0")

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(specifications.router, prefix="/specifications", tags=["Specifications"])

@app.get("/")
def root():
    return {"message": "Gomedia IA Specs API is running"}