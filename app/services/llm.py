import anthropic
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_spec(text: str, filename: str) -> dict:
    prompt = f"""Tu es un expert en fiches techniques de produits électroniques/industriels.
Voici le contenu d'une fiche technique (fichier: {filename}).
Extrait les informations suivantes et réponds UNIQUEMENT en JSON:
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
Si une info est introuvable, mets "N/A".
Contenu de la fiche:
{text}
"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("JSON introuvable dans la réponse")
    except Exception as e:
        raise RuntimeError(f"Erreur LLM: {e}")