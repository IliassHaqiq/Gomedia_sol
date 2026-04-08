#import anthropic
import json
import requests
import re
import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()



#Hadchi zdto as a testing for alloma
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

import json
import os
import re
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")


def _extract_json(raw_text: str) -> Dict[str, Any]:
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        candidate = match.group(0)
        return json.loads(candidate)

    raise ValueError(f"JSON introuvable dans la réponse du modèle: {raw_text[:500]}")


def _post_to_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Ollama a renvoyé {response.status_code}: {response.text}")

    data = response.json()
    raw = data.get("response", "")
    if not raw:
        raise RuntimeError(f"Réponse vide d'Ollama: {data}")

    return raw


def _normalize_spec_keys(specs: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {}

    key_map = {
        "tension nominale bobine": "Tension nominale bobine",
        "courant bobine nominal": "Courant bobine nominal",
        "puissance bobine": "Puissance bobine",
        "résistance bobine": "Résistance bobine",
        "resistance bobine": "Résistance bobine",
        "tension d'enclenchement (min)": "Tension d'enclenchement (min)",
        "tension de déclenchement (max)": "Tension de déclenchement (max)",
        "nombre de contacts": "Nombre de contacts",
        "type de contact": "Type de contact",
        "courant nominal contact": "Courant nominal contact",
        "tension max contact (ac)": "Tension max contact (AC)",
        "tension max contact (dc)": "Tension max contact (DC)",
        "puissance de coupure max": "Puissance de coupure max",
    }

    for key, value in specs.items():
        clean_key = str(key).strip()
        mapped = key_map.get(clean_key.lower(), clean_key)
        normalized[mapped] = value

    return normalized


def _ensure_required_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    required_fields = [
        "numero_de_piece",
        "designation",
        "description_fr",
        "description_en",
        "fabricant",
    ]

    for field in required_fields:
        value = data.get(field)
        if value is None or str(value).strip() == "":
            data[field] = "N/A"

    specs = data.get("specifications")
    if not isinstance(specs, dict):
        data["specifications"] = {}
    else:
        data["specifications"] = _normalize_spec_keys(specs)

    return data


def _translate_to_english_if_missing(data: Dict[str, Any]) -> Dict[str, Any]:
    description_en = str(data.get("description_en", "")).strip()

    if description_en and description_en != "N/A":
        return data

    description_fr = str(data.get("description_fr", "")).strip()
    designation = str(data.get("designation", "")).strip()
    fabricant = str(data.get("fabricant", "")).strip()

    fallback_prompt = f"""
You are a technical translator.

Translate the following product description into professional English.
Return STRICTLY valid JSON and nothing else.

Expected format:
{{
  "description_en": "..."
}}

French description: {description_fr}
Designation: {designation}
Manufacturer: {fabricant}
""".strip()

    raw = _post_to_ollama(fallback_prompt)
    translated = _extract_json(raw)

    desc = str(translated.get("description_en", "")).strip()
    data["description_en"] = desc if desc else "N/A"
    return data


def generate_spec(text: str, filename: str) -> Dict[str, Any]:
    prompt = f"""
Tu es un expert en fiches techniques industrielles et électroniques.

Analyse le contenu suivant provenant du fichier "{filename}".

Ta mission:
1. Extraire les informations importantes.
2. Générer une description claire en français.
3. Générer une description claire en anglais.
4. Retourner STRICTEMENT un JSON valide.
5. Ne rien écrire avant ou après le JSON.
6. Si une information est introuvable, mettre "N/A".

Le JSON doit respecter EXACTEMENT cette structure :
{{
  "numero_de_piece": "...",
  "designation": "...",
  "description_fr": "...",
  "description_en": "...",
  "fabricant": "...",
  "specifications": {{
    "Nom caractéristique 1": "Valeur 1",
    "Nom caractéristique 2": "Valeur 2"
  }}
}}

Règles importantes:
- "description_en" est obligatoire.
- "specifications" doit toujours être un objet JSON.
- Uniformiser les unités quand possible: V, VAC, VDC, A, mA, W, kW, Hz.
- Utiliser des noms de clés propres et lisibles dans "specifications".
- Répondre uniquement avec du JSON valide.

Contenu:
{text}
""".strip()

    raw = _post_to_ollama(prompt)
    data = _extract_json(raw)
    data = _ensure_required_fields(data)
    data = _translate_to_english_if_missing(data)

    return data


#"client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# def generate_spec(text: str, filename: str) -> dict:
#     prompt = f"""Tu es un expert en fiches techniques de produits électroniques/industriels.
# Voici le contenu d'une fiche technique (fichier: {filename}).
# Extrait les informations suivantes et réponds UNIQUEMENT en JSON:
# {{
#   "numero_de_piece": "...",
#   "designation": "...",
#   "description_fr": "...",
#   "description_en": "...",
#   "fabricant": "...",
#   "specifications": {{
#     "spec1": "valeur1",
#     "spec2": "valeur2"
#   }}
# }}
# Si une info est introuvable, mets "N/A".
# Contenu de la fiche:
# {text}
# """
#     try:
#         response = client.messages.create(
#             model="claude-sonnet-4-20250514",
#             max_tokens=1000,
#             messages=[{"role": "user", "content": prompt}]
#         )
#         raw = response.content[0].text
#         match = re.search(r'\{.*\}', raw, re.DOTALL)
#         if match:
#             return json.loads(match.group())
#         raise ValueError("JSON introuvable dans la réponse")
#     except Exception as e:
#         raise RuntimeError(f"Erreur LLM: {e}")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"  # ou llama3, mixtral, etc.

def call_llm(prompt: str):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()
    return result["response"]