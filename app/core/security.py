"""
Système d'authentification pour l'API Gomedia
"""
import os
import logging
from typing import Optional
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Vérifie que l'API key fournie est valide.

    Args:
        credentials: Les credentials de l'header Authorization

    Returns:
        L'API key validée

    Raises:
        HTTPException: Si l'API key est invalide ou manquante

    Example:
        >>> from app.core.security import verify_api_key
        >>> async def protected_route(api_key: str = Security(verify_api_key)):
        >>>     return {"message": "Authenticated!"}
    """
    # Récupérer la clé depuis les variables d'environnement
    expected_api_key = os.getenv("API_KEY")

    # Logger une alerte si pas de clé configurée (mode développement)
    if not expected_api_key:
        logger.warning("⚠️  Aucune API_KEY n'est configurée dans les variables d'environnement!")
        logger.warning("⚠️  L'API est ouverte sans authentification!")
        # En développement, on peut laisser passer si pas de clé
        return credentials.credentials

    # Vérifier si la clé fournie correspond
    if credentials.credentials != expected_api_key:
        logger.warning(f"❌ Tentative d'accès avec clé API invalide: {credentials.credentials[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("✅ Accès authentifié avec succès")
    return credentials.credentials


def is_production() -> bool:
    """Vérifie si l'application tourne en mode production"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env == "production"
