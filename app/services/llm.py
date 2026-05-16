import json
import logging
import requests
import re
import os
import time
from typing import Any, Dict, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# NVIDIA NIM Configuration
NIM_API_URL = os.getenv("NIM_API_URL", "https://integrate.api.nvidia.com/v1")
NIM_API_KEY = os.getenv("NIM_API_KEY")
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3-70b-instruct")

# Rate limiting - NVIDIA NIM has 40 requests per minute limit
LAST_REQUEST_TIME = None
MIN_REQUEST_INTERVAL = float(os.getenv("NIM_REQUEST_INTERVAL", "0.4"))

# Longueur des descriptions (mots par langue)
LENGTH_CONFIG = {
    "short": {"min_words": 200, "max_words": 400, "max_tokens": 3000},
    "medium": {"min_words": 400, "max_words": 600, "max_tokens": 5000},
    "long": {"min_words": 700, "max_words": 1000, "max_tokens": 7000},
}

NIM_TIMEOUT = int(os.getenv("NIM_TIMEOUT", "180"))


def _get_length_config(description_length: str) -> Dict[str, int]:
    return LENGTH_CONFIG.get(description_length, LENGTH_CONFIG["medium"])


def _word_count(text: str) -> int:
    if not text or str(text).strip() in ("", "N/A", "PENDING"):
        return 0
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def _description_structure_instructions(description_length: str) -> str:
    cfg = _get_length_config(description_length)
    min_w, max_w = cfg["min_words"], cfg["max_words"]
    return f"""
LONGUEUR OBLIGATOIRE pour description_fr ET description_en (comptez les mots avant de répondre):
- MINIMUM ABSOLU: {min_w} mots par langue — en dessous = réponse refusée
- CIBLE: {min_w} à {max_w} mots par langue

STRUCTURE OBLIGATOIRE (4 paragraphes distincts par langue):
§1 Présentation du produit, fabricant, gamme et usage principal (~{min_w // 4} mots)
§2 Caractéristiques techniques détaillées avec TOUTES les valeurs chiffrées du datasheet (~{min_w // 3} mots)
§3 Applications professionnelles, compatibilité, connectique, intégration système (~{min_w // 4} mots)
§4 Avantages, fiabilité, différenciateurs par rapport aux solutions concurrentes (~{min_w // 4} mots)

INTERDIT: résumé d'un seul paragraphe court, généralités sans chiffres, listes à puces seules.
"""


def _length_prompt_rules(description_length: str) -> str:
    return _description_structure_instructions(description_length)


def rate_limit():
    """Simple rate limiter to respect API limits"""
    global LAST_REQUEST_TIME
    if LAST_REQUEST_TIME is not None:
        elapsed = time.time() - LAST_REQUEST_TIME
        if elapsed < MIN_REQUEST_INTERVAL:
            sleep_time = MIN_REQUEST_INTERVAL - elapsed
            time.sleep(sleep_time)
    LAST_REQUEST_TIME = time.time()


def _post_to_nim(
    prompt: str,
    max_tokens: int = 2000,
    max_retries: int = 3,
    temperature: float = 0.1,
) -> str:
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
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    for attempt in range(max_retries):
        try:
            rate_limit()

            t0 = time.perf_counter()
            logger.info(
                "🌐 Appel NIM (tentative %s/%s, max_tokens=%s, timeout=%ss)...",
                attempt + 1,
                max_retries,
                max_tokens,
                NIM_TIMEOUT,
            )

            response = requests.post(
                f"{NIM_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=NIM_TIMEOUT,
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                elapsed = time.perf_counter() - t0
                usage = result.get("usage", {})
                logger.info(
                    "✅ NIM répondu en %.1fs (%s caractères, tokens: %s)",
                    elapsed,
                    len(content),
                    usage.get("total_tokens", "?"),
                )
                if not content:
                    raise RuntimeError("Empty response content from NIM")
                return content
            else:
                raise RuntimeError(f"Unexpected response format from NIM: {result}")

        except requests.exceptions.Timeout as e:
            logger.warning("⏱️ Timeout NIM après %ss (tentative %s/%s)", NIM_TIMEOUT, attempt + 1, max_retries)
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff: 5s, 10s, 15s
                time.sleep(wait_time)
                continue
            raise RuntimeError(
                f"NIM API timeout après {NIM_TIMEOUT}s × {max_retries} tentatives. "
                "Essayez 'short' ou vérifiez https://build.nvidia.com"
            )

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status == 429:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10
                    logger.warning("Rate limit 429, retry in %ss...", wait_time)
                    time.sleep(wait_time)
                    continue
                raise RuntimeError(
                    "Limite NVIDIA NIM atteinte (429). Réessayez dans 1 minute."
                )
            if status == 401:
                raise RuntimeError(
                    "Clé NIM invalide (401). Vérifiez NIM_API_KEY sur https://build.nvidia.com"
                )
            if status in (502, 503, 504):
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 8
                    logger.warning(
                        "NIM indisponible (%s), nouvelle tentative dans %ss...",
                        status,
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue
                raise RuntimeError(
                    f"Service NVIDIA NIM temporairement indisponible ({status}). "
                    "Réessayez dans quelques minutes ou utilisez le mode « Court »."
                )
            try:
                error_json = e.response.json()
                if "error" in error_json:
                    msg = error_json["error"].get("message", str(e))
                    raise RuntimeError(f"Erreur NVIDIA NIM: {msg}")
            except RuntimeError:
                raise
            except Exception:
                pass
            raise RuntimeError(
                f"Erreur NVIDIA NIM (HTTP {status}). "
                "Vérifiez le modèle NIM_MODEL dans .env."
            )

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


def _extract_products_structure(text: str, filename: str) -> list[Dict[str, Any]]:
    """Étape 1 : extraction multi-produits (sans descriptions longues)."""
    prompt = f"""
Tu es un expert en fiches techniques industrielles et électroniques.

Analyse le contenu suivant provenant du fichier "{filename}".

Ta mission:
1. Détecter si ce document contient UNE ou PLUSIEURS fiches techniques de produits.
2. Pour chaque produit, extraire référence, désignation, fabricant et spécifications.
3. NE PAS rédiger de descriptions — laisse description_fr et description_en à "PENDING".
4. Retourner STRICTEMENT un JSON valide.
5. Si une information est introuvable, mettre "N/A".

Le JSON doit respecter EXACTEMENT cette structure :
{{
    "products": [
        {{
            "numero_de_piece": "...",
            "designation": "...",
            "description_fr": "PENDING",
            "description_en": "PENDING",
            "fabricant": "...",
            "specifications": {{
                "Nom caractéristique 1": "Valeur 1"
            }}
        }}
    ]
}}

Règles importantes:
- Extraire le MAXIMUM de caractéristiques techniques par produit.
- Si le document ne contient qu'un seul produit, retourner un tableau avec un seul élément.
- Répondre uniquement avec du JSON valide.

Contenu:
{text}
""".strip()

    raw = _post_to_nim(prompt, max_tokens=5000, temperature=0.1)
    data = _extract_json(raw)

    products = data.get("products", [])
    if not isinstance(products, list):
        products = [data]
    return products


def _generate_descriptions_batch(
    products: List[Dict[str, Any]],
    source_text: str,
    filename: str,
    description_length: str = "medium",
) -> List[Dict[str, str]]:
    """Un seul appel API pour les descriptions de tous les produits."""
    if not products:
        return []

    if len(products) == 1:
        return [_generate_descriptions_single_product(products[0], source_text, filename, description_length)]

    cfg = _get_length_config(description_length)
    structure = _description_structure_instructions(description_length)

    products_payload = []
    for idx, product in enumerate(products):
        specs = product.get("specifications", {})
        if not isinstance(specs, dict):
            specs = {}
        products_payload.append({
            "index": idx,
            "numero_de_piece": product.get("numero_de_piece", "N/A"),
            "designation": product.get("designation", "N/A"),
            "fabricant": product.get("fabricant", "N/A"),
            "specifications": specs,
        })

    batch_max_tokens = min(cfg["max_tokens"] * len(products), 16000)

    prompt = f"""
Tu es rédacteur technique senior. Document: "{filename}".

Pour CHAQUE produit, rédige description_fr et description_en LONGUES.
{structure}

Produits:
{json.dumps(products_payload, ensure_ascii=False, indent=2)}

Contexte source:
{source_text[:6000]}

Retourne STRICTEMENT ce JSON (un élément par produit, même index):
{{
    "products": [
        {{"index": 0, "description_fr": "...", "description_en": "..."}}
    ]
}}
""".strip()

    raw = _post_to_nim(prompt, max_tokens=batch_max_tokens, temperature=0.35)
    data = _extract_json(raw)
    items = data.get("products", [])
    if not isinstance(items, list):
        items = []

    by_index: Dict[int, Dict[str, str]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        idx = item.get("index", len(by_index))
        by_index[int(idx)] = {
            "description_fr": str(item.get("description_fr", "")).strip() or "N/A",
            "description_en": str(item.get("description_en", "")).strip() or "N/A",
        }

    results = []
    for idx, product in enumerate(products):
        desc = by_index.get(idx, {"description_fr": "N/A", "description_en": "N/A"})
        desc = _expand_descriptions_if_short(
            desc, product, source_text, filename, description_length
        )
        results.append(desc)
    return results


def _expand_descriptions_if_short(
    descriptions: Dict[str, str],
    product: Dict[str, Any],
    source_text: str,
    filename: str,
    description_length: str,
) -> Dict[str, str]:
    """Relance une expansion si le modèle a généré un texte trop court."""
    cfg = _get_length_config(description_length)
    min_words = cfg["min_words"]
    fr = str(descriptions.get("description_fr", "")).strip()
    en = str(descriptions.get("description_en", "")).strip()
    fr_w, en_w = _word_count(fr), _word_count(en)

    if fr_w >= min_words * 0.85 and en_w >= min_words * 0.85:
        logger.info("✅ Descriptions: FR=%s mots, EN=%s mots (cible min=%s)", fr_w, en_w, min_words)
        return descriptions

    logger.warning(
        "⚠️ Descriptions trop courtes (FR=%s, EN=%s mots, min=%s) — expansion...",
        fr_w, en_w, min_words,
    )

    specs = product.get("specifications", {})
    if not isinstance(specs, dict):
        specs = {}

    prompt = f"""
Tu es rédacteur technique senior. Le texte ci-dessous est TROP COURT.

Document: "{filename}"
Référence: {product.get("numero_de_piece", "N/A")}
Spécifications: {json.dumps(specs, ensure_ascii=False, indent=2)[:3000]}

Texte actuel FR ({fr_w} mots):
{fr[:2000]}

{_description_structure_instructions(description_length)}

RALLONGE description_fr ET description_en en conservant les faits techniques.
Chaque langue doit atteindre AU MINIMUM {min_words} mots.

Retourne STRICTEMENT: {{"description_fr": "...", "description_en": "..."}}
""".strip()

    raw = _post_to_nim(prompt, max_tokens=cfg["max_tokens"], temperature=0.4)
    expanded = _extract_json(raw)
    result = {
        "description_fr": str(expanded.get("description_fr", fr)).strip() or fr,
        "description_en": str(expanded.get("description_en", en)).strip() or en,
    }
    logger.info(
        "📏 Après expansion: FR=%s mots, EN=%s mots",
        _word_count(result["description_fr"]),
        _word_count(result["description_en"]),
    )
    return result


def _generate_descriptions_single_product(
    product: Dict[str, Any],
    source_text: str,
    filename: str,
    description_length: str = "medium",
) -> Dict[str, str]:
    """Appel dédié à la rédaction longue FR/EN."""
    cfg = _get_length_config(description_length)
    specs = product.get("specifications", {})
    if not isinstance(specs, dict):
        specs = {}

    structure = _description_structure_instructions(description_length)

    prompt = f"""
Tu es rédacteur technique senior pour catalogues industriels B2B.

Rédige deux descriptions COMPLÈTES et LONGUES pour ce produit.

Document source: "{filename}"
Référence: {product.get("numero_de_piece", "N/A")}
Désignation: {product.get("designation", "N/A")}
Fabricant: {product.get("fabricant", "N/A")}

Spécifications extraites:
{json.dumps(specs, ensure_ascii=False, indent=2)}

Extrait datasheet:
{source_text[:8000]}

{structure}

Retourne STRICTEMENT ce JSON (rien avant/après):
{{"description_fr": "...", "description_en": "..."}}
""".strip()

    raw = _post_to_nim(prompt, max_tokens=cfg["max_tokens"], temperature=0.4)
    descriptions = _extract_json(raw)
    result = {
        "description_fr": str(descriptions.get("description_fr", "")).strip() or "N/A",
        "description_en": str(descriptions.get("description_en", "")).strip() or "N/A",
    }
    return _expand_descriptions_if_short(
        result, product, source_text, filename, description_length
    )


def generate_spec(text: str, filename: str, description_length: str = "medium") -> Dict[str, Any]:
    """Extraction des specs puis rédaction longue (2 appels, qualité medium/long)."""
    products = _extract_products_structure(text, filename)
    if not products:
        raise ValueError("Aucun produit détecté dans le document")

    product = _ensure_required_fields(products[0])
    descriptions = _generate_descriptions_single_product(
        product, text, filename, description_length
    )
    product["description_fr"] = descriptions["description_fr"]
    product["description_en"] = descriptions["description_en"]
    return _translate_to_english_if_missing(product)


def generate_specs_multi(text: str, filename: str, description_length: str = "medium") -> list[Dict[str, Any]]:
    """
    Extract multiple products: 2 appels API max (extraction specs + descriptions groupées).
    """
    products = _extract_products_structure(text, filename)

    if not products:
        return []

    if len(products) == 1:
        product = _ensure_required_fields(products[0])
        descriptions = _generate_descriptions_single_product(
            product, text, filename, description_length
        )
        product["description_fr"] = descriptions["description_fr"]
        product["description_en"] = descriptions["description_en"]
        return [_translate_to_english_if_missing(product)]

    descriptions_list = _generate_descriptions_batch(
        products, text, filename, description_length
    )

    processed_products = []
    for product, descriptions in zip(products, descriptions_list):
        product = _ensure_required_fields(product)
        product["description_fr"] = descriptions["description_fr"]
        product["description_en"] = descriptions["description_en"]
        processed_products.append(_translate_to_english_if_missing(product))

    return processed_products


# For backward compatibility
def generate_spec_basic(text: str, filename: str) -> Dict[str, Any]:
    return generate_spec(text, filename, "medium")
