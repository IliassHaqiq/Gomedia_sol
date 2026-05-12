# 📋 TODO List - Gomedia IA Specifications

## 🔴 URGENT - À FAIRE IMMÉDIATEMENT

### 1. Sécurité
- [ ] **CRITIQUE** : Révoquer la clé API Anthropic exposée dans l'historique git
  - Aller sur https://console.anthropic.com/ et révoquer la clé
  - Nettoyer l'historique git avec `git filter-branch` ou BFG Repo-Cleaner
  - **Action**: `bfg --delete-files '\.env'` ou équivalent

- [ ] **CRITIQUE** : Ajouter `.env` au `.gitignore`
  ```bash
  echo ".env" >> .gitignore
  git rm --cached .env
  git commit -m "Security: Remove .env from version control"
  ```

- [ ] **CRITIQUE** : Créer `.env.example` avec valeurs fictives
  - Copier `.env` vers `.env.example`
  - Remplacer les vraies clés par `your_key_here`

### 2. Code
- [x] **FAIT** : Supprimer `app/services/llm.py.backup` ✓
- [ ] **IMPORTANT** : Ajouter CORS dans `app/main.py`
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "http://localhost:8080"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

## 🟡 PRIORITÉ HAUTE - Cette semaine

### 3. Validation et Sécurité
- [ ] **IMPORTANT** : Ajouter validation de taille de fichiers dans `documents.py`
  ```python
  MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
  
  file.file.seek(0, 2)
  size = file.file.tell()
  file.file.seek(0)
  
  if size > MAX_FILE_SIZE:
      raise HTTPException(413, "File too large")
  ```

- [ ] **IMPORTANT** : Nettoyer les noms de fichiers pour éviter les injections
  ```python
  import re
  
  def sanitize_filename(filename: str) -> str:
      # Retirer les chemins
      filename = os.path.basename(filename)
      # Retirer les caractères spéciaux
      filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
      return filename[:100]  # Limiter la longueur
  ```

- [ ] **IMPORTANCE** : Valider description_length avec enum
  ```python
  from enum import Enum
  
  class DescriptionLength(str, Enum):
      short = "short"
      medium = "medium"
      long = "long"
  
  description_length: DescriptionLength = Query(DescriptionLength.medium)
  ```

### 4. Gestion des Erreurs
- [ ] **IMPORTANT** : Ajouter mécanisme de retry pour appels LLM
  - Installer `tenacity`: `pip install tenacity`
  - Ajouter décorateur retry sur `_post_to_ollama`

- [ ] **IMPORTANT** : Améliorer gestion timeouts
  ```python
  # Timeout configurable via .env
  OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))
  ```

### 5. Logging
- [ ] **IMPORTANT** : Ajouter logging structuré dans tous les services
```python
import logging

logger = logging.getLogger(__name__)

# Dans services/llm.py
logger.info(f"Calling Ollama with prompt length: {len(prompt)}")
logger.error(f"Ollama failed: {e}")

# Dans api/documents.py
logger.info(f"Uploaded file: {filename}")
logger.warning(f"Skipped file: {filename}, reason: {reason}")
```

## 🟢 PRIORITÉ MOYENNE - Ce mois-ci

### 6. Monitoring & Health Checks
- [ ] **UTIL** : Ajouter des endpoints health check
  ```python
  @app.get("/health")
  def health():
      return {"status": "healthy", "timestamp": datetime.now()}
  
  @app.get("/health/db")
  def health_db(db: Session = Depends(get_db)):
      db.execute("SELECT 1")
      return {"status": "healthy"}
  
  @app.get("/health/ollama")
  def health_ollama():
      response = requests.get(f"{OLLAMA_URL}/tags", timeout=5)
      return {"status": "healthy" if response.status_code == 200 else "unhealthy"}
  ```

### 7. Authentification (Optionnel pour dev, Obligatoire pour prod)
- [ ] **API Key simple** pour commencer
  ```python
  from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
  
  security = HTTPBearer()
  
  def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
      if credentials.credentials != os.getenv("API_KEY"):
          raise HTTPException(403, "Invalid API key")
  ```

### 8. Tests de base
- [ ] **CRITIQUE** : Créer structure de tests
```bash
mkdir -p tests/fixtures
cp test_upload.py tests/  # Déplacer le fichier de test
```

- [ ] **Implémenter** tests unitaires pour les services
- [ ] **Implémenter** tests d'intégration pour l'API
- [ ] **Ajouter** GitHub Actions pour CI/CD

### 9. Configuration multi-environnement
- [ ] Créer `config/` avec:
  - `development.py`
  - `staging.py`
  - `production.py`
- [ ] Utiliser `pydantic-settings` pour validation

### 10. Documentation API
- [ ] **AMÉLIORER** les descriptions des endpoints
- [ ] **AJOUTER** des examples dans les docstrings
- [ ] **GÉNÉRER** documentation OpenAPI complète

## 🔵 PRIORITÉ BASSE - À long terme

### 11. Export des données
- [ ] Endpoint pour exporter en Excel
- [ ] Endpoint pour exporter en PDF
- [ ] Export par lot avec filtres

### 12. Features avancées
- [ ] **Historique des versions** des spécifications
- [ ] **Recherche plein-texte** dans les spécifications
- [ ] **Score de confiance** pour les extractions LLM
- [ ] **Feedback utilisateur** pour améliorer les prompts

### 13. Scaling
- [ ] **File d'attente Redis** pour les extractions lourdes
- [ ] **Workers Celery** pour traitement asynchrone
- [ ] **Cache Redis** pour les réponses LLM
- [ ] **Monitoring** avec Prometheus/Grafana

### 14. Frontend (Optionnel)
- [ ] Interface web pour upload et validation
- [ ] Dashboard de suivi des extractions
- [ ] Éditeur pour corrections manuelles

## 📦 Dépendances à ajouter

```bash
# Sécurité & Validation
pip install tenacity          # Retry mechanism
pip install python-jose       # JWT tokens
pip install passlib[bcrypt]   # Password hashing

# Testing
pip install pytest
pip install pytest-cov
pip install pytest-asyncio
pip install httpx             # Async test client

# Monitoring
pip install prometheus-client
pip install structlog         # Structured logging

# Documentation
pip install pdoc3             # API documentation

# Async processing (pour plus tard)
pip install celery
pip install redis
```

## 📊 Metrics & Monitoring

### Autres métriques à ajouter
- [ ] Temps moyen d'extraction par taille de fichier
- [ ] Taux de succès des extractions LLM
- [ ] Nombre d'uploads par jour/semaine
- [ ] Types de fichiers les plus utilisés
- [ ] Temps de validation manuelle
- [ ] Erreurs les plus fréquentes

## 🎛️ Configuration à enrichir

### Variables d'environnement manquantes
Ajouter dans `.env.example`:

```env
# API Configuration
API_KEY=your_api_key_here
MAX_FILE_SIZE=10485760
ALLOWED_FILE_TYPES=pdf,xlsx

# LLM Configuration
OLLAMA_TIMEOUT=180
OLLAMA_MAX_RETRIES=3

# Application
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
MAX_WORKERS=4

# Database
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

## 📝 Scripts utiles à créer

### 1. Script d'initialisation
```bash
#!/bin/bash
# scripts/init.sh
# Initialise l'application pour la première fois
```

### 2. Script de backup
```bash
#!/bin/bash
# scripts/backup.sh
# Backup de la base de données et uploads
```

### 3. Script health check
```bash
#!/bin/bash
# scripts/health.sh
# Vérifie que tous les services tournent
```

---

## 🎯 Objectifs pour Production-Ready

### Critères de production
- [ ] Tests unitaires : >80% coverage
- [ ] Tests d'intégration : tous les endpoints
- [ ] Monitoring : logs + metrics
- [ ] Sécurité : authentification + validation
- [ ] Documentation : API + README
- [ ] Performance : tests de charge effectués
- [ ] Backup : procédures documentées

### Estimation effort total
- **Urgent** (1 jour) : Sécurité + Fixes critiques
- **Haute priorité** (1 semaine) : Validation + Logging
- **Moyenne priorité** (2 semaines) : Tests + Monitoring
- **Basse priorité** (1 mois) : Features avancées

**Total estimé** : ~1.5 mois pour version production robuste

---

## 🔄 Process de développement

### Workflow Git
```bash
# 1. Créer une branche feature
git checkout -b feature/add-validation

# 2. Faire les changements
# 3. Créer des tests
# 4. Lancer les tests
pytest tests/

# 5. Commit et push
git commit -m "Add: file size validation"
git push origin feature/add-validation

# 6. Créer Pull Request
```

### Code Review Checklist
- [ ] Le code compile sans erreurs
- [ ] Les tests passent
- [ ] La documentation est à jour
- [ ] Les secrets ne sont pas exposés
- [ ] Les validations sont en place
- [ ] Les erreurs sont loggées

---

*Dernière mise à jour: 13 avril 2026*
*Prochaine review: 20 avril 2026*
