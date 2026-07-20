"""Ollama API client for the Gemma Local Assistant."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_CONTEXT_LENGTH,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama errors."""


class OllamaConnectionError(OllamaError):
    """Raised when cannot connect to Ollama."""


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(
        self,
        hass: HomeAssistant,
        base_url: str,
        model: str,
        timeout: int = 60,
    ) -> None:
        """Initialize the Ollama client."""
        self.hass = hass
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            self._session = async_get_clientsession(self.hass)
        return self._session

    async def async_close(self) -> None:
        """Close the client (no-op, session is managed by HA)."""
        # On ne ferme pas la session car elle est partagée avec HA
        pass

    async def async_verify_connection(self) -> None:
        """Verify that Ollama is reachable and the model is available."""
        try:
            async with self.session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise OllamaConnectionError(
                        f"Ollama responded with status {resp.status}"
                    )
                data = await resp.json()
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                model_base = self.model.split(":")[0]
                if model_base not in models and self.model not in [
                    m.get("name") for m in data.get("models", [])
                ]:
                    _LOGGER.warning(
                        "Model %s not found in Ollama. Available: %s. "
                        "Run: ollama pull %s",
                        self.model,
                        models,
                        self.model,
                    )
        except aiohttp.ClientError as err:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}: {err}"
            ) from err

    async def async_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Send a chat request to Ollama.

        messages: list of {"role": "user"|"assistant"|"system"|"tool", "content": ..., "tool_calls": [...]}
        tools: list of tool definitions in Ollama format
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": DEFAULT_CONTEXT_LENGTH,
            },
        }

        if tools:
            payload["tools"] = tools

        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise OllamaError(
                        f"Ollama chat failed (status {resp.status}): {text}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise OllamaConnectionError(
                f"Connection error to Ollama: {err}"
            ) from err
        except asyncio.TimeoutError as err:
            raise OllamaError(f"Timeout while waiting for Ollama: {err}") from err

    async def async_generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """Simple generation (non-chat) — for utility tasks."""
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise OllamaError(
                        f"Ollama generate failed (status {resp.status}): {text}"
                    )
                data = await resp.json()
                return data.get("response", "")
        except aiohttp.ClientError as err:
            raise OllamaConnectionError(
                f"Connection error to Ollama: {err}"
            ) from err
