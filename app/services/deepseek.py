"""
DeepSeek V4 Pro Integration Service

This module provides integration with DeepSeek API for:
- Text generation and completion
- Product data extraction from documents
- Embedding generation for vector search
"""
import os
import httpx
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DeepSeekService:
    """
    Service for interacting with DeepSeek V4 Pro API

    Provides methods for:
    - Generating text completions
    - Extracting structured product data from documents
    - Creating vector embeddings for semantic search
    """

    def __init__(self):
        """Initialize DeepSeek service with configuration from environment variables"""
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.embedding_model = os.getenv("DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding")

        if not self.api_key:
            logger.warning("⚠️  DEEPSEEK_API_KEY not configured!")

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion using DeepSeek V4 Pro

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            response_format: Optional format specification (e.g., {"type": "json_object"})

        Returns:
            Response dict with content and metadata

        Raises:
            ValueError: If API key is not configured
            httpx.HTTPStatusError: If API request fails
        """
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                logger.info(f"✅ DeepSeek completion generated: {len(content)} chars")

                return {
                    "content": content,
                    "model": result.get("model", self.model),
                    "usage": result.get("usage", {}),
                    "finish_reason": result["choices"][0].get("finish_reason")
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ DeepSeek API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ DeepSeek request failed: {str(e)}")
            raise

    async def extract_product_data(
        self,
        text: str,
        language: str = "fr"
    ) -> Dict[str, Any]:
        """
        Extract structured product data from text using DeepSeek

        Args:
            text: The extracted text from PDF/Excel
            language: Target language for descriptions (fr/en)

        Returns:
            Structured product data with:
            - ref_produit: Product reference/part number
            - marque: Manufacturer/brand
            - designation: Product designation/name
            - descriptif_fr: French description
            - descriptif_en: English description
            - technical_specs: Dictionary of technical attributes

        Raises:
            ValueError: If JSON parsing fails
        """
        system_prompt = """You are an expert technical specification extractor for industrial components.
Extract structured data from the provided text and return it as JSON.

Required fields:
- ref_produit: Product reference/part number
- marque: Manufacturer/brand
- designation: Product designation/name
- descriptif_fr: French description (detailed, professional)
- descriptif_en: English description (detailed, professional)
- technical_specs: Dictionary of technical attributes with values and units

Format the technical_specs as:
{
  "attribute_name": {"value": "value", "unit": "unit"},
  ...
}

Be precise with units (V, A, W, Hz, °C, mm, etc.)."""

        user_prompt = f"""Extract product specifications from this text:

{text}

Return the result as valid JSON only, no markdown formatting."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            result = await self.generate_completion(
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            data = json.loads(result["content"])

            logger.info(f"✅ Extracted product data: {data.get('ref_produit', 'unknown')}")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse DeepSeek JSON response: {e}")
            raise ValueError("Invalid JSON response from DeepSeek")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using DeepSeek

        Args:
            text: Text to embed

        Returns:
            List of float values representing the embedding

        Raises:
            ValueError: If API key is not configured
            httpx.HTTPStatusError: If API request fails
        """
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.embedding_model,
            "input": text
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                result = response.json()
                embedding = result["data"][0]["embedding"]

                logger.info(f"✅ Generated embedding: {len(embedding)} dimensions")

                return embedding

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ DeepSeek embedding error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"❌ DeepSeek embedding failed: {str(e)}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Check if DeepSeek service is properly configured

        Returns:
            Health status dict
        """
        return {
            "status": "healthy" if self.api_key else "unhealthy",
            "service": "deepseek",
            "model": self.model,
            "embedding_model": self.embedding_model,
            "api_key_configured": bool(self.api_key)
        }


# Singleton instance for use across the application
deepseek_service = DeepSeekService()
