# Gomedia IA - Système d'Extraction Intelligente de Spécifications Techniques

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/Licence-MIT-yellow.svg)](LICENSE)

Système d'extraction intelligente automatisée de données techniques à partir de fiches PDF et fichiers Excel (datasheets fournisseurs) avec génération de spécifications structurées en français et anglais, selon des styles rédactionnels personnalisables.

## 🎯 Fonctionnalités Principales

### ✅ Fonctionnalités Implémentées

- **📄 Extraction Multi-format**
  - Support des fichiers PDF et Excel (.xlsx)
  - Détection automatique du type de document
  - Normalisation du texte et nettoyage intelligent

- **🤖 Intelligence Artificielle (LLM)**
  - Intégration avec Ollama (supporte Llama3, Claude, etc.)
  - Extraction intelligente des caractéristiques techniques
  - Génération automatique de descriptions en français et anglais
  - Traduction automatique si description anglaise manquante

- **📊 Qualité des Données**
  - Contrôle qualité avec validation des champs requis
  - Normalisation des clés de spécifications (mapping intelligent)
  - Uniformisation des unités (V, A, W, Hz, etc.)
  - Système de validation manuelle des données extraites

- **🔧 Paramétrage Flexible**
  - Longueur des descriptions configurable (short/medium/long)
  - Style rédactionnel adaptable
  - Query templates personnalisables pour le LLM

- **📚 Gestion des Documents**
  - Upload simple et upload multiple
  - Stockage sécurisé des fichiers
  - Versioning automatique (ajout de suffixes numériques)
  - Statut de traitement (uploaded → extracted → validated)

- **🗄️ Base de Données**
  - PostgreSQL avec SQLAlchemy ORM
  - Schéma relationnel Documents ↔ Specifications
  - Stockage JSON pour les données structurées flexibles
  - Timestamps automatiques

- **🌐 API REST**
  - FastAPI avec documentation interactive (Swagger UI)
  - Endpoints RESTful complets
  - Gestion des erreurs et codes HTTP appropriés
  - Support CORS (à configurer selon besoin)

### 🔍 Extraction Intelligente Supportée

Le système détecte automatiquement :
- **Caractéristiques bobines** : Tension, courant, puissance, résistance
- **Spécifications contacts** : Nombre, type, courant nominal, tension max
- **Performances** : Puissance de coupure, plages de fonctionnement
- **Identification** : Numéro de pièce, désignation, fabricant
- **Propriétés électriques** : Tensions AC/DC, courants, fréquences

## 🏗️ Architecture

```
┌─────────────────┐
│   API Gateway   │
│   (FastAPI)     │
└────────┬────────┘
         │
┌────────▼────────┬──────────────┬──────────────┐
│  Document API   │  Spec API    │  Health      │
│  Management     │  CRUD        │  Monitoring  │
└────────┬────────┴──────┬───────┴──────┬─────┘
         │               │              │
┌────────▼────────┐ ┌───▼────┐   ┌──▼──┐
│  Extraction     │ │  LLM   │   │ DB  │
│  Service        │ │ Service│   │ PG  │
│  (PDF/Excel)    │ │ Ollama │   │     │
└─────────────────┘ └────────┘   └─────┘
```

### Stack Technique

- **Backend**: Python 3.8+ avec FastAPI
- **Base de données**: PostgreSQL 14+ avec SQLAlchemy
- **LLM**: Ollama (support local)/ Anthropic Claude
- **Extraction PDF**: pdfplumber
- **Extraction Excel**: openpyxl
- **Déploiement**: Docker-ready (docker-compose inclus)

## 📋 Prérequis

### Système

- Python 3.8 ou supérieur
- PostgreSQL 14 ou supérieur
- Ollama installé et en cours d'exécution (pour LLM local)
- 4 Go RAM minimum (8 Go recommandé pour le LLM)
- 2 Go d'espace disque pour les uploads

### Dépendances Python

Voir `requirements.txt` pour la liste complète des dépendances.

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/your-org/gomedia-ia-specs.git
cd gomedia-ia-specs
```

### 2. Créer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate   # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer la base de données

Assurez-vous que PostgreSQL est en cours d'exécution et créez la base de données :

```sql
CREATE DATABASE gomedia;
CREATE USER gomedia_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gomedia TO gomedia_user;
```

### 5. Configurer les variables d'environnement

Copiez et modifiez le fichier `.env` :

```bash
cp .env.example .env
```

Modifier `.env` avec vos configurations :

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/gomedia

# Ollama Configuration
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3:latest

# LLM Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...  # Si vous utilisez Claude à la place d'Ollama
```

### 6. Initialiser la base de données

```bash
# Les tables seront créées automatiquement au démarrage
# (voir app/main.py ligne 7)
```

### 7. Installer et démarrer Ollama (pour LLM local)

```bash
# Sur Mac/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Sur Windows (PowerShell Admin)
winget install ollama

# Démarrer Ollama
ollama serve

# Télécharger le modèle Llama3
ollama pull llama3:latest
```

## ▶️ Démarrage

### Développement

```bash
# Lancer le serveur en mode développement
uvicorn app.main:app --reload --port 8000

# Lancer avec workers multiples (production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

L'API sera accessible à l'adresse : http://localhost:8000

### Documentation API

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Utilisation avec Docker

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f

# Arrêter les services
docker-compose down
```

## 📖 Utilisation de l'API

### 1. Upload d'un document

```bash
curl -X 'POST' \
  'http://localhost:8000/documents/upload' \
  -F 'file=@/path/to/document.pdf'
```

**Response** :
```json
{
  "message": "Fichier uploadé avec succès",
  "document": {
    "id": 1,
    "filename": "document.pdf",
    "file_path": "uploads/document.pdf",
    "status": "uploaded"
  }
}
```

### 2. Upload multiple de documents

```bash
curl -X 'POST' \
  'http://localhost:8000/documents/upload-multiple' \
  -F 'files=@/path/to/doc1.pdf' \
  -F 'files=@/path/to/doc2.xlsx'
```

### 3. Extraction et génération de spécification

```bash
curl -X 'POST' \
  'http://localhost:8000/documents/1/extract?description_length=medium'
```

**Paramètres** :
- `description_length` : `short`, `medium`, ou `long`

**Response** :
```json
{
  "message": "Extraction réussie",
  "specification": {
    "id": 1,
    "document_id": 1,
    "numero_de_piece": "RWH SH-204",
    "designation": "Contacteur industriel",
    "fabricant": "ComatReleco",
    "description_fr": "Contacteur industriel monostable 4 contacts...",
    "description_en": "Industrial monostatic contactor with 4 contacts...",
    "structured_data": {
      "Tension nominale bobine": "250 V",
      "Courant bobine nominal": "100 mA",
      "Nombre de contacts": "4",
      "Type de contact": "AgNi 90/10"
    },
    "validation_status": "pending",
    "prompt_version": "v2"
  }
}
```

### 4. Extraction en lot de tous les documents

```bash
curl -X 'POST' \
  'http://localhost:8000/documents/extract-all?description_length=long'
```

### 5. Lister les documents

```bash
curl -X 'GET' \
  'http://localhost:8000/documents/'
```

### 6. Récupérer une spécification

```bash
curl -X 'GET' \
  'http://localhost:8000/specifications/1'
```

### 7. Valider et corriger une spécification

```bash
curl -X 'PUT' \
  'http://localhost:8000/specifications/1' \
  -H 'Content-Type: application/json' \
  -d '{
    "description_en": "Updated description",
    "structured_data": {
      "Tension nominale bobine": "230 V"
    }
  }'
```

## 📁 Structure du Projet

```
.
├── app/
│   ├── api/                      # Routes API
│   │   ├── documents.py         # Endpoints documents
│   │   └── specifications.py    # Endpoints spécifications
│   ├── db/
│   │   ├── base.py              # Base SQLAlchemy
│   │   └── session.py           # Configuration DB session
│   ├── models/                   # Modèles SQLAlchemy
│   │   ├── document.py          # Table Documents
│   │   └── specification.py     # Table Specifications
│   ├── schemas/                  # Schémas Pydantic (validation)
│   │   └── specification.py     # Validation specs
│   ├── services/                 # Logique métier
│   │   ├── extractor.py         # Extraction PDF/Excel
│   │   └── llm.py               # Intégration LLM
│   └── main.py                   # Point d'entrée FastAPI
├── uploads/                      # Dossier des fichiers uploadés
├── .env                         # Variables d'environnement
├── requirements.txt             # Dépendances Python
├── docker-compose.yml          # Configuration Docker
├── README.md                   # Ce fichier
└── test_upload.py              # Script de test
```

## 🐛 Problèmes Connus et Correctifs

### 1. **Erreur : Duplicate llm.py**

**Problème** : Présence d'un fichier `app/services/llm.py.backup` qui contient une version dupliquée du code.

**Solution** :
```bash
rm app/services/llm.py.backup
```

**Statut** : 🔴 **CRITIQUE - À CORRIGER IMMÉDIATEMENT**

### 2. **Validation améliorable**

**Problème** : Manque de validation rigoureuse sur les entrées utilisateur.

**Recommandations** :
- Ajouter des validateurs Pydantic sur tous les champs
- Implémenter des contraintes de taille (max length)
- Ajouter des regex pour les formats (ex: numéro de pièce)

**Statut** : 🟡 **À AMÉLIORER**

### 3. **Gestion des erreurs LLM**

**Problème** : Le LLM peut générer des réponses mal formatées.

**Recommandations** :
- Ajouter un mécanisme de retry avec backoff exponentiel
- Implémenter une validation JSON avec schéma strict
- Ajouter des logs détaillés pour le debugging

**Statut** : 🟡 **À AMÉLIORER**

### 4. **Sécurité des fichiers**

**Problème** : Pas de validation de la taille des fichiers.

**Recommandations** :
- Ajouter `max_file_size` dans la configuration
- Implémenter une validation côté API
- Ajouter une limite de taille globale pour le dossier uploads

**Statut** : 🟡 **À AMÉLIORER**

### 5. **Configuration manquante**

**Problèmes identifiés** :
- Pas de configuration CORS
- Pas de rate limiting
- Pas de configuration HTTPS/TLS
- Pas de monitoring/health checks

**Solutions** : Voir section "Améliorations Futures" ci-dessous

**Statut** : 🟡 **À AJOUTER**

## 🔒 Sécurité

### Recommandations de sécurité actuelles

- ✅ Variable d'environnement pour les secrets (API keys)
- ✅ Séparation des configurations par environnement
- ⚠️ **TODO** : Implémenter CORS pour restreindre les origines
- ⚠️ **TODO** : Ajouter l'authentification (OAuth2/JWT)
- ⚠️ **TODO** : Valider les types MIME des fichiers
- ⚠️ **TODO** : Évaluer les quotas utilisateur

### Variables sensibles (à ne JAMAIS commit)

```env
# NE PAS COMMITER CES VALEURS DANS GIT !
ANTHROPIC_API_KEY=sk-ant-api03-...
DATABASE_URL=postgresql://...
```

## ✅ Améliorations et Roadmap

### Phase 1 : Stabilité et Sécurité (Priorité Haute)

- [ ] **Fix** : Supprimer le fichier `llm.py.backup` en double
- [ ] **Sécurité** : Implémenter CORS et authentication
- [ ] **Validation** : Ajouter des validateurs Pydantic complets
- [ ] **Tests** : Créer une suite de tests unitaires et d'intégration
- [ ] **Monitoring** : Ajouter des endpoints health checks
- [ ] **Logging** : Implémenter des logs structurés avec rotation

### Phase 2 : Expérience Utilisateur (Priorité Moyenne)

- [ ] **Frontend** : Créer une interface web pour l'upload et la validation
- [ ] **Export** : Ajouter l'export des spécifications en PDF/Excel
- [ ] **Recherche** : Implémenter la recherche plein-texte dans les spécifications
- [ ] **Batch** : Créer un système de traitement asynchrone (Celery)
- [ ] **Notifications** : Ajouter des webhooks pour les événements

### Phase 3 : Intelligence Artificielle (Priorité Moyenne)

- [ ] **Confiance** : Scorer la confiance des extractions LLM
- [ ] **Apprentissage** : Feedback utilisateur pour améliorer les prompts
- [ ] **Classification** : Classification automatique des types de composants
- [ ] **Comparaison** : Comparaison de spécifications entre produits
- [ ] **Multi-modal** : Support de l'extraction d'images et tableaux

### Phase 4 : Évolutivité (Priorité Basse)

- [ ] **Cache** : Implémenter Redis pour le cache des réponses LLM
- [ ] **Queue** : Système de file d'attente pour les extractions lourdes
- [ ] **Scaling** : Support du scaling horizontal
- [ ] **Database** : Partitionnement des tables volumineuses
- [ ] **Backup** : Système de backup automatique

## 📊 Exemples de Sortie

### Extraction d'un Contacteur Industriel

**Input** : `contactor.pdf` (fiche technique ComatReleco)

**Output** :
```json
{
  "numero_de_piece": "C4-A40/DC24V",
  "designation": "Contactor industrial",
  "fabricant": "ComatReleco",
  "description_fr": "Contacteur industriel compact avec 4 contacts. Idéal pour applications de commutation de charges résistives et inductives. Conforme aux normes IEC 60947.",
  "description_en": "Compact industrial contactor with 4 contacts. Ideal for switching resistive and inductive loads. Compliant with IEC 60947 standards.",
  "specifications": {
    "Tension nominale bobine": "24 VDC",
    "Courant bobine nominal": "200 mA",
    "Résistance bobine": "120 Ω",
    "Nombre de contacts": "4",
    "Type de contact": "AgNi 90/10",
    "Courant nominal contact": "10 A",
    "Tension max contact (AC)": "250 VAC",
    "Tension max contact (DC)": "30 VDC"
  },
  "validation_status": "pending"
}
```

### Extraction d'un Relais Temporel

**Input** : `timer.xlsx` (tableau Excel)

**Output** :
```json
{
  "numero_de_piece": "C4-A40/DC24V",
  "designation": "Time relay",
  "fabricant": "ComatReleco",
  "description_fr": "Relais temporel électronique multifonctions avec temporisation de 0,1 seconde à 10 jours. Protection IP40 et plage de température étendue.",
  "description_en": "Multi-function electronic time relay with timing from 0.1 second to 10 days. IP40 protection rating and wide temperature range.",
  "specifications": {
    "Tension d'enclenchement (min)": "19.2 VDC",
    "Tension de déclenchement (max)": "4.8 VDC",
    "Plage temporisation": "0,1s à 10j",
    "Précision": "±5%",
    "Température de fonctionnement": "-25°C à +55°C",
    "Degré protection": "IP40"
  },
  "validation_status": "pending"
}
```

## 🔧 Configuration Avancée

### Personnalisation des Prompts LLM

Vous pouvez modifier les prompts dans `app/services/llm.py` pour adapter l'extraction à votre domaine spécifique.

### Ajout de Nouveaux Formats

Pour ajouter un nouveau format de fichier :

1. Modifier `app/services/extractor.py`
2. Ajouter votre fonction d'extraction
3. Mettre à jour `extract_text_from_file()`

### Base de Données

Pour utiliser SQLite au lieu de PostgreSQL (développement uniquement) :

```python
# Dans app/db/session.py
DATABASE_URL = "sqlite:///./gomedia.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
```

## 📈 Monitoring

### Vérifier la santé de l'API

```bash
curl http://localhost:8000/
```

### Vérifier Connexion DB

```bash
# À implémenter - endpoint health check
```

### Vérifier Service Ollama

```bash
curl http://localhost:11434/api/tags
```

## 🐛 Dépannage

### Problème : LLM ne répond pas

**Symptôme**: Timeout ou erreur de connexion LLM

**Solution** :
```bash
# Vérifier si Ollama tourne
systemctl status ollama  # Linux
# ou
ollama serve

# Tester la connexion
curl http://localhost:11434/api/tags
```

### Problème : Database Connection Refused

**Symptôme**: Erreur connexion PostgreSQL

**Solution** :
```bash
# Vérifier PostgreSQL
sudo systemctl status postgresql

# Vérifier les identifiants dans .env
echo $DATABASE_URL
```

### Problème : Fichiers uploadés non trouvés

**Symptôme**: Fichiers manquants après upload

**Solution** :
```bash
# Vérifier les permissions
cd /path/to/project
mkdir -p uploads
chmod 755 uploads
```

### Problème : Memory Error avec gros PDF

**Symptôme**: Plantage extraction PDF volumineux

**Solution** :
```python
# Modifier MAX_TEXT_LENGTH dans app/services/extractor.py
MAX_TEXT_LENGTH = 10000  # Augmenter si nécessaire
```

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add: ma nouvelle feature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

## 📞 Support

- **Documentation** : [Wiki du projet](https://github.com/your-org/gomedia-ia-specs/wiki)
- **Issues** : [GitHub Issues](https://github.com/your-org/gomedia-ia-specs/issues)
- **Email** : support@gomedia.com

## 🙏 Remerciements

- [FastAPI](https://fastapi.tiangolo.com/) pour le framework API
- [Ollama](https://ollama.ai/) pour les LLM locaux
- [SQLAlchemy](https://www.sqlalchemy.org/) pour l'ORM
- [pdfplumber](https://github.com/jsvine/pdfplumber) pour l'extraction PDF
- [ComatReleco](https://www.comatreleco.com/) pour les exemples de datasheets

---

**Développé avec ❤️ par l'équipe Gomedia**

*Dernière mise à jour : 13 avril 2026*
