from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api import documents, specifications, products, documents_generation
from app.db.session import engine, get_db
from app.models import document, specification
from app.models.product import Product, ProductDescription, ProductFile, TechnicalSpec, ProductEmbedding
from app.db.base import Base
from app.core.logging import setup_logging
from app.services.deepseek import deepseek_service
from app.services.llm import OLLAMA_BASE_URL, OLLAMA_MODEL
import os
import logging
import requests

# Configuration du logging
logger = setup_logging()
logger.info(" Initialisation de l'application Gomedia IA Specs API")

# Create all tables
Base.metadata.create_all(bind=engine)
logger.info(" Modèles de base de données créés avec succès")

# Enable pgvector extension
try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    logger.info(" Extension pgvector activée")
except Exception as e:
    logger.warning(f"  Impossible d'activer pgvector: {e}")

app = FastAPI(
    title="Gomedia IA Specifications API",
    description="Extraction intelligente de fiches techniques industrielles avec RAG",
    version="2.0.0"
)

# Configuration CORS
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f" CORS configuré avec les origines: {allowed_origins}")

# Routes principales
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(specifications.router, prefix="/specifications", tags=["Specifications"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(documents_generation.router, prefix="/documents-generation", tags=["Documents Generation"])
logger.info("📡 Routes API incluses: /documents, /specifications, /products, /documents-generation")

@app.get("/")
def root():
    logger.info(" GET / - Health check")
    return {
        "message": "Gomedia IA Specs API is running",
        "version": "2.0.0",
        "features": ["RAG Search", "Ollama LLM", "DeepSeek V4 Pro", "pgvector"],
        "status": "healthy"
    }

@app.get("/health")
def health_check():
    """Health check simple"""
    return {"status": "healthy", "service": "api", "version": "2.0.0"}

@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    """Vérifie la connexion à la base de données"""
    try:
        db.execute(text("SELECT 1"))
        logger.info("✅ Health check DB: OK")
        return {"status": "healthy", "service": "database", "version": "2.0.0"}
    except Exception as e:
        logger.error(f" Health check DB FAILED: {str(e)}")
        raise HTTPException(503, f"Database health check failed: {str(e)}")

@app.get("/health/deepseek")
def health_deepseek():
    """Vérifie le service DeepSeek"""
    return deepseek_service.health_check()


@app.get("/health/ollama")
def health_ollama():
    """Vérifie le service Ollama (LLM local)"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        model_available = any(
            name == OLLAMA_MODEL or name.startswith(f"{OLLAMA_MODEL}:")
            for name in model_names
        )
        if not model_available and model_names:
            logger.warning(
                "Modèle %s non trouvé dans Ollama. Disponibles: %s",
                OLLAMA_MODEL,
                ", ".join(model_names[:5]),
            )
        return {
            "status": "healthy",
            "service": "ollama",
            "version": "local",
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
            "model_available": model_available,
            "models_count": len(model_names),
        }
    except requests.exceptions.ConnectionError:
        logger.error("Health check Ollama FAILED: service not running")
        raise HTTPException(
            503,
            f"Ollama inaccessible à {OLLAMA_BASE_URL}. Démarrez avec: ollama serve",
        )
    except Exception as e:
        logger.error(f"Health check Ollama FAILED: {str(e)}")
        raise HTTPException(503, f"Ollama health check failed: {str(e)}")

@app.get("/health/pgvector")
def health_pgvector(db: Session = Depends(get_db)):
    """Vérifie l'extension pgvector"""
    try:
        result = db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if result:
            logger.info(f" Health check pgvector: OK (version {result[0]})")
            return {"status": "healthy", "service": "pgvector", "version": result[0]}
        else:
            logger.warning("  pgvector extension not found")
            return {"status": "unhealthy", "service": "pgvector", "error": "Extension not installed"}
    except Exception as e:
        logger.error(f" Health check pgvector FAILED: {str(e)}")
        return {"status": "unhealthy", "service": "pgvector", "error": str(e)}
