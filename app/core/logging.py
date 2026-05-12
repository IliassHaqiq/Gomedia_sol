"""
Configuration centralisée du logging pour l'application Gomedia
"""
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging():
    """
    Configure le logging pour toute l'application
    - Console: INFO et plus
    - Fichier: DEBUG et plus avec rotation
    - Format structuré avec timestamps et niveaux
    """

    # Créer le dossier logs s'il n'existe pas
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configuration du format
    log_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)

    # Handler pour le fichier avec rotation
    log_file = os.path.join(log_dir, f"gomedia_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)

    # Configuration du logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Loggers spécifiques (réduire le bruit des bibliothèques)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('pdfplumber').setLevel(logging.INFO)

    return root_logger


# Logger pour ce module
core_logger = logging.getLogger(__name__)
