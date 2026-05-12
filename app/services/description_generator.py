"""
Description Generation Service

This module provides functionality to generate product descriptions
based on technical specifications stored in the database.
"""
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.deepseek import deepseek_service

logger = logging.getLogger(__name__)


class DescriptionLength:
    """Description length options"""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class DescriptionGeneratorService:
    """
    Service for generating product descriptions from technical specifications

    Provides methods for:
    - Generating descriptions in French and English
    - Controlling description length (short/medium/long)
    - Using technical specs as source data
    """

    def __init__(self, db: Session):
        """
        Initialize description generator service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_technical_specs(self, product_id: int) -> list:
        """
        Get all technical specifications for a product

        Args:
            product_id: Product ID

        Returns:
            List of technical specs as dicts
        """
        specs = self.db.execute(
            text("""
                SELECT attribut, valeur, unite
                FROM technical_specs
                WHERE product_id = :product_id
                ORDER BY attribut
            """),
            {"product_id": product_id}
        ).fetchall()

        return [
            {
                "attribut": spec.attribut,
                "valeur": spec.valeur,
                "unite": spec.unite
            }
            for spec in specs
        ]

    def get_product_info(self, product_id: int) -> Optional[Dict]:
        """
        Get basic product information

        Args:
            product_id: Product ID

        Returns:
            Product info dict or None
        """
        product = self.db.execute(
            text("""
                SELECT id, ref_produit, marque, designation
                FROM products
                WHERE id = :product_id
            """),
            {"product_id": product_id}
        ).fetchone()

        if not product:
            return None

        return {
            "id": product.id,
            "ref_produit": product.ref_produit,
            "marque": product.marque,
            "designation": product.designation
        }

    def format_technical_specs(self, specs: list) -> str:
        """
        Format technical specs for LLM prompt

        Args:
            specs: List of technical specs

        Returns:
            Formatted string
        """
        if not specs:
            return "Aucune spécification technique disponible"

        formatted = []
        for spec in specs:
            value = spec["valeur"] or "N/A"
            unit = spec["unite"] or ""
            formatted.append(f"- {spec['attribut']}: {value} {unit}".strip())

        return "\n".join(formatted)

    def get_length_instructions(self, length: str) -> Dict[str, str]:
        """
        Get length-specific instructions for description generation

        Args:
            length: Description length (short/medium/long)

        Returns:
            Dict with French and English instructions
        """
        instructions = {
            DescriptionLength.SHORT: {
                "fr": "Génère une description courte et concise (2-3 phrases maximum).",
                "en": "Generate a short and concise description (2-3 sentences maximum)."
            },
            DescriptionLength.MEDIUM: {
                "fr": "Génère une description de longueur moyenne (4-6 phrases).",
                "en": "Generate a medium-length description (4-6 sentences)."
            },
            DescriptionLength.LONG: {
                "fr": "Génère une description détaillée et complète (7-10 phrases ou plus).",
                "en": "Generate a detailed and comprehensive description (7-10 sentences or more)."
            }
        }

        return instructions.get(length, instructions[DescriptionLength.MEDIUM])

    async def generate_description(
        self,
        product_id: int,
        length: str = DescriptionLength.MEDIUM,
        language: str = "both"
    ) -> Dict[str, str]:
        """
        Generate product description from technical specifications

        Args:
            product_id: Product ID
            length: Description length (short/medium/long)
            language: Language to generate ('fr', 'en', or 'both')

        Returns:
            Dict with 'descriptif_fr' and/or 'descriptif_en'

        Raises:
            ValueError: If product not found
        """
        # Get product info
        product_info = self.get_product_info(product_id)
        if not product_info:
            raise ValueError(f"Product with ID {product_id} not found")

        # Get technical specs
        specs = self.get_technical_specs(product_id)
        specs_text = self.format_technical_specs(specs)

        # Get length instructions
        length_instructions = self.get_length_instructions(length)

        # Build prompt
        system_prompt = f"""You are an expert technical writer specializing in industrial components.
Your task is to write professional product descriptions based on technical specifications.

Product Information:
- Reference: {product_info['ref_produit']}
- Brand: {product_info['marque'] or 'N/A'}
- Designation: {product_info['designation'] or 'N/A'}

Technical Specifications:
{specs_text}

Instructions:
- Write in a professional, technical style
- Be accurate and precise
- Use appropriate technical terminology
- {length_instructions['fr']}
- {length_instructions['en']}

Return the result as JSON with the following structure:
{{
  "descriptif_fr": "French description here",
  "descriptif_en": "English description here"
}}"""

        user_prompt = f"""Generate a product description for this industrial component.

Reference: {product_info['ref_produit']}
Brand: {product_info['marque'] or 'N/A'}
Designation: {product_info['designation'] or 'N/A'}

Technical Specifications:
{specs_text}

Generate the description in JSON format with 'descriptif_fr' and 'descriptif_en' fields."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            result = await deepseek_service.generate_completion(
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            import json
            data = json.loads(result["content"])

            logger.info(f"✅ Generated description for product {product_id} (length: {length})")

            return {
                "descriptif_fr": data.get("descriptif_fr", ""),
                "descriptif_en": data.get("descriptif_en", "")
            }

        except Exception as e:
            logger.error(f"❌ Failed to generate description for product {product_id}: {e}")
            raise

    def save_description(
        self,
        product_id: int,
        descriptif_fr: str,
        descriptif_en: str,
        edited_by_human: bool = False
    ) -> bool:
        """
        Save or update product description

        Args:
            product_id: Product ID
            descriptif_fr: French description
            descriptif_en: English description
            edited_by_human: Whether description was manually edited

        Returns:
            True if successful
        """
        try:
            # Check if description exists
            existing = self.db.execute(
                text("""
                    SELECT id FROM product_descriptions
                    WHERE product_id = :product_id
                """),
                {"product_id": product_id}
            ).fetchone()

            if existing:
                # Update existing
                self.db.execute(
                    text("""
                        UPDATE product_descriptions
                        SET descriptif_fr = :descriptif_fr,
                            descriptif_en_specs = :descriptif_en,
                            last_edited_by_human = :edited_by_human
                        WHERE product_id = :product_id
                    """),
                    {
                        "product_id": product_id,
                        "descriptif_fr": descriptif_fr,
                        "descriptif_en": descriptif_en,
                        "edited_by_human": edited_by_human
                    }
                )
            else:
                # Create new
                self.db.execute(
                    text("""
                        INSERT INTO product_descriptions
                        (product_id, descriptif_fr, descriptif_en_specs, last_edited_by_human)
                        VALUES (:product_id, :descriptif_fr, :descriptif_en, :edited_by_human)
                    """),
                    {
                        "product_id": product_id,
                        "descriptif_fr": descriptif_fr,
                        "descriptif_en": descriptif_en,
                        "edited_by_human": edited_by_human
                    }
                )

            self.db.commit()
            logger.info(f"✅ Saved description for product {product_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save description for product {product_id}: {e}")
            self.db.rollback()
            return False

    async def generate_and_save_description(
        self,
        product_id: int,
        length: str = DescriptionLength.MEDIUM
    ) -> Dict:
        """
        Generate and save description in one operation

        Args:
            product_id: Product ID
            length: Description length (short/medium/long)

        Returns:
            Dict with generated descriptions and status
        """
        try:
            # Generate description
            descriptions = await self.generate_description(product_id, length)

            # Save to database
            success = self.save_description(
                product_id=product_id,
                descriptif_fr=descriptions["descriptif_fr"],
                descriptif_en=descriptions["descriptif_en"],
                edited_by_human=False
            )

            return {
                "product_id": product_id,
                "descriptif_fr": descriptions["descriptif_fr"],
                "descriptif_en": descriptions["descriptif_en"],
                "length": length,
                "success": success
            }

        except Exception as e:
            logger.error(f"❌ Failed to generate and save description: {e}")
            return {
                "product_id": product_id,
                "error": str(e),
                "success": False
            }
