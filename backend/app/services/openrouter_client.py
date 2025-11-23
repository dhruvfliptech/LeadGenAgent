"""
OpenRouter API Client - Unified interface for multiple AI models.

Provides access to GPT-4, Claude 3.5, Qwen, Grok, and other models
through a single API key and consistent interface.
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    OpenRouter API client for accessing multiple AI models.

    Supports:
    - OpenAI GPT-4 (text generation, embeddings)
    - Anthropic Claude 3.5 (complex reasoning, long context)
    - Qwen 2.5 (multilingual, diverse tasks)
    - Grok (creative, conversational)
    """

    def __init__(self):
        """Initialize OpenRouter client."""
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.timeout = settings.AI_TIMEOUT_SECONDS

        if not self.api_key:
            logger.warning("OpenRouter API key not configured. AI features will use placeholder responses.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://fliptechpro.com",  # Optional: for rankings
            "X-Title": "FlipTech Pro Lead Generation",  # Optional: shows in OpenRouter dashboard
            "Content-Type": "application/json"
        }

    async def generate_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_message: Optional[str] = None
    ) -> str:
        """
        Generate text completion using specified model.

        Args:
            prompt: The user prompt/message
            model: Model identifier (defaults to AI_MODEL_DEFAULT)
            max_tokens: Maximum tokens to generate (defaults to AI_MAX_TOKENS)
            temperature: Sampling temperature (defaults to AI_TEMPERATURE)
            system_message: Optional system message for context

        Returns:
            Generated text response
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not set. Returning placeholder response.")
            return f"[Placeholder AI Response - Configure OPENROUTER_API_KEY to enable real AI]\n\nPrompt: {prompt[:100]}..."

        model = model or settings.AI_MODEL_DEFAULT
        max_tokens = max_tokens or settings.AI_MAX_TOKENS
        temperature = temperature or settings.AI_TEMPERATURE

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"AI generation failed: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"OpenRouter request error: {str(e)}")
            raise Exception(f"AI generation request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in AI generation: {str(e)}")
            raise

    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding vector for text (for semantic search).

        Args:
            text: Text to embed
            model: Embedding model (defaults to AI_MODEL_EMBEDDINGS)

        Returns:
            Embedding vector (1536 dimensions for text-embedding-ada-002)
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not set. Returning placeholder embedding.")
            # Return a random-ish but deterministic embedding based on text hash
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            import random
            random.seed(hash_val)
            return [random.uniform(-1, 1) for _ in range(1536)]

        model = model or settings.AI_MODEL_EMBEDDINGS

        payload = {
            "model": model,
            "input": text
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return data["data"][0]["embedding"]

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter embedding API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Embedding generation failed: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"OpenRouter embedding request error: {str(e)}")
            raise Exception(f"Embedding generation request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in embedding generation: {str(e)}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            model: Embedding model (defaults to AI_MODEL_EMBEDDINGS)

        Returns:
            List of embedding vectors
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not set. Returning placeholder embeddings.")
            return [await self.generate_embedding(text) for text in texts]

        model = model or settings.AI_MODEL_EMBEDDINGS

        payload = {
            "model": model,
            "input": texts
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                return [item["embedding"] for item in data["data"]]

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {str(e)}")
            # Fallback to individual requests
            return [await self.generate_embedding(text, model) for text in texts]

    async def generate_with_model(
        self,
        prompt: str,
        model_name: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate completion with a specific model by name.

        Args:
            prompt: The user prompt
            model_name: 'gpt4', 'claude', 'qwen', 'grok', or full model identifier
            system_message: Optional system message
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            Generated text response
        """
        # Map friendly names to model identifiers
        model_map = {
            "gpt4": settings.AI_MODEL_DEFAULT,
            "claude": settings.AI_MODEL_CLAUDE,
            "qwen": settings.AI_MODEL_QWEN,
            "grok": settings.AI_MODEL_GROK
        }

        model = model_map.get(model_name.lower(), model_name)

        return await self.generate_completion(
            prompt=prompt,
            model=model,
            system_message=system_message,
            **kwargs
        )


# Global client instance
_openrouter_client: Optional[OpenRouterClient] = None


def get_openrouter_client() -> OpenRouterClient:
    """Get or create OpenRouter client singleton."""
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = OpenRouterClient()
    return _openrouter_client
