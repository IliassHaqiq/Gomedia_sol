import json
import requests
import re
import os
import time
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

# NVIDIA NIM Configuration
NIM_API_URL = os.getenv("NIM_API_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NIM_API_KEY")
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3-70b-instruct")

# Rate limiting - NVIDIA NIM has 40 requests per minute limit
LAST_REQUEST_TIME = None
MIN_REQUEST_INTERVAL = 1.5  # Respect API limits


def rate_limit():
    """Simple rate limiter to respect API limits"""
    global LAST_REQUEST_TIME
    if LAST_REQUEST_TIME is not None:
        elapsed = time.time() - LAST_REQUEST_TIME
        if elapsed < MIN_REQUEST_INTERVAL:
            sleep_time = MIN_REQUEST_INTERVAL - elapsed
            time.sleep(sleep_time)
    LAST_REQUEST_TIME = time.time()


def _post_to_nim(prompt: str, max_tokens: int = 2000, max_retries: int = 3) -> str:
    """Send prompt to NVIDIA NIM API and return the response text with retry logic."""
    if not NIM_API_KEY:
        raise RuntimeError("NIM_API_KEY not set in environment. Get one from https://build.nvidia.com")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NIM_API_KEY}"
    }

    payload = {
        "model": NIM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens
    }

    for attempt in range(max_retries):
        try:
            rate_limit()

            response = requests.post(
                f"{NIM_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=300  # Increased timeout to 5 minutes
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                if not content:
                    raise RuntimeError("Empty response content from NIM")
                return content
            else:
                raise RuntimeError(f"Unexpected response format from NIM: {result}")

        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                print(f"Timeout occurred, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            raise RuntimeError(f"NIM API timeout after {max_retries} retries: {str(e)}")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RuntimeError("NIM rate limit exceeded. Try again in a minute.")
            elif e.response.status_code == 401:
                raise RuntimeError("Invalid NIM_API_KEY. Check your API key from https://build.nvidia.com")
            else:
                try:
                    error_json = e.response.json()
                    if "error" in error_json:
                        raise RuntimeError(f"NIM API error: {error_json['error'].get('message', str(e))}")
                except:
                    pass
                raise RuntimeError(f"NIM API HTTP error {e.response.status_code}: {e.response.text}")

        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            raise RuntimeError("Cannot connect to NIM API. Check internet connection.")

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"Error occurred, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            raise RuntimeError(f"NIM API error: {str(e)}")

    raise RuntimeError(f"NIM API failed after {max_retries} retries")


def _extract_json(raw_text: str) -> Dict[str, Any]:
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"JSON introuvable dans la réponse du modèle: {raw_text[:500]}")


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

    raw = _post_to_nim(fallback_prompt, max_tokens=500)
    translated = _extract_json(raw)

    desc = str(translated.get("description_en", "")).strip()
    data["description_en"] = desc if desc else "N/A"
    return data


def generate_spec(text: str, filename: str, description_length: str = "medium") -> Dict[str, Any]:
    # Determine description length guidelines
    if description_length == "short":
        desc_guidelines = "Courte (200-500 mots)"
        max_words = "200-500 mots"
        max_tokens = 3000
    elif description_length == "long":
        desc_guidelines = "Longue (détaillée, 800-1300 mots)"
        max_words = "800-1300 mots"
        max_tokens = 5000
    else:  # medium
        desc_guidelines = "Moyenne (500-800 mots)"
        max_words = "500-800 mots"
        max_tokens = 4000

    prompt = f"""
Tu es un expert en fiches techniques industrielles et électroniques.

Analyse le contenu suivant provenant du fichier "{filename}".

Ta mission:
1. Extraire les informations importantes.
2. Générer une description claire en français ({desc_guidelines}).
3. Générer une description claire en anglais ({desc_guidelines}).
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
- Les descriptions doivent faire environ {max_words}.
- "specifications" doit toujours être un objet JSON.
- Uniformiser les unités quand possible: V, VAC, VDC, A, mA, W, kW, Hz.
- Utiliser des noms de clés propres et lisibles dans "specifications".
- Répondre uniquement avec du JSON valide.

Contenu:
{text}
""".strip()

    raw = _post_to_nim(prompt, max_tokens=max_tokens)
    data = _extract_json(raw)
    data = _ensure_required_fields(data)
    data = _translate_to_english_if_missing(data)

    return data


def generate_specs_multi(text: str, filename: str, description_length: str = "medium") -> list[Dict[str, Any]]:
    """
    Extract multiple products from a single document.
    Returns a list of product data dictionaries.
    """
    # Determine description length guidelines
    if description_length == "short":
        desc_guidelines = "Courte (200-500 mots)"
        max_words = "200-500 mots"
        max_tokens = 4000
    elif description_length == "long":
        desc_guidelines = "Longue (détaillée, 800-1300 mots)"
        max_words = "800-1300 mots"
        max_tokens = 8000
    else:  # medium
        desc_guidelines = "Moyenne (500-800 mots)"
        max_words = "500-800 mots"
        max_tokens = 6000

    prompt = f"""
Tu es un expert en fi   ches techniques industrielles et électroniques.

Analyse le contenu suivant provenant du fichier "{filename}".

Ta mission:
1. Détecter si ce document contient UNE ou PLUSIEURS fiches techniques de produits.
2. Pour chaque produit, extraire les informations importantes.
3. Générer une description claire en français ({desc_guidelines}) pour chaque produit.
4. Générer une description claire en anglais ({desc_guidelines}) pour chaque produit.
5. Retourner STRICTEMENT un JSON valide.
6. Ne rien écrire avant ou après le JSON.
7. Si une information est introuvable, mettre "N/A".

Le JSON doit respecter EXACTEMENT cette structure :
{{
    "products": [
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
    ]
}}

Règles importantes:
- "description_en" est obligatoire pour chaque produit.
- Les descriptions doivent faire environ {max_words} pour chaque produit.
- "specifications" doit toujours être un objet JSON pour chaque produit.
- Uniformiser les unités quand possible: V, VAC, VDC, A, mA, W, kW, Hz.
- Utiliser des noms de clés propres et lisibles dans "specifications".
- Répondre uniquement avec du JSON valide.
- Si le document ne contient qu'un seul produit, retourner un tableau avec un seul élément.

Contenu:
{text}
""".strip()

    raw = _post_to_nim(prompt, max_tokens=max_tokens)
    data = _extract_json(raw)

    # Extract products array
    products = data.get("products", [])
    if not isinstance(products, list):
        # If the LLM returned a single product instead of an array, wrap it
        products = [data]

    # Ensure required fields for each product
    processed_products = []
    for product in products:
        product = _ensure_required_fields(product)
        product = _translate_to_english_if_missing(product)
        processed_products.append(product)

    return processed_products


# For backward compatibility
def generate_spec_basic(text: str, filename: str) -> Dict[str, Any]:
    return generate_spec(text, filename, "medium")
