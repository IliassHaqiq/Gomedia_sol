#import anthropic
import json
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()



#Hadchi zdto as a testing for alloma
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")




def _extract_json(raw_text: str) -> dict:
    """
    Essaie d'extraire un JSON valide depuis la réponse du modèle.
    """
    raw_text = raw_text.strip()

    # Cas simple : la réponse entière est déjà un JSON
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # Cas fréquent : le modèle ajoute du texte autour du JSON
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("JSON introuvable ou invalide dans la réponse du modèle")


def generate_spec(text: str, filename: str) -> dict:
    prompt = f"""
Tu es un expert en fiches techniques de produits électroniques et industriels.

Voici le contenu d'une fiche technique (fichier: {filename}).

Ta tâche :
- Extraire les informations demandées
- Répondre STRICTEMENT en JSON valide
- Ne rien ajouter avant ou après le JSON
- Si une information est introuvable, mettre "N/A"

Format attendu :
{{
  "numero_de_piece": "...",
  "designation": "...",
  "description_fr": "...",
  "description_en": "...",
  "fabricant": "...",
  "specifications": {{
    "spec1": "valeur1",
    "spec2": "valeur2"
  }}
}}

Contenu de la fiche :
{text}
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        raw = data.get("response", "")
        if not raw:
            raise RuntimeError("Réponse vide retournée par Ollama")

        return _extract_json(raw)

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Erreur de connexion à Ollama: {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur LLM: {e}")

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