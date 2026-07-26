"""SearXNG search tool for the Gemma assistant."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .base import Tool

_LOGGER = logging.getLogger(__name__)


class SearXNGTool(Tool):
    """Tool that performs web search via a local SearXNG instance."""

    name = "web_search"
    description = (
        "Effectue une recherche internet via SearXNG et retourne un résumé "
        "des résultats (titres, snippets, URLs). À utiliser pour les questions "
        "d'actualité, les faits généraux, la météo, les recettes, le code, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "La requête de recherche en français ou en anglais.",
            },
            "max_results": {
                "type": "integer",
                "description": "Nombre maximum de résultats à retourner (défaut 5).",
                "default": 5,
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    }

    def __init__(self, hass: Any, base_url: str = "http://localhost:8888") -> None:
        super().__init__(hass)
        self.base_url = base_url.rstrip("/")

    async def async_call(self, query: str, max_results: int = 5) -> str:
        """Perform the search and return a formatted result string."""
        params = {
            "q": query,
            "format": "json",
            "language": "fr",
            "safesearch": 0,
            "categories": "general",
        }
        url = f"{self.base_url}/search?{urlencode(params)}"

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return (
                        f"Erreur SearXNG: statut {resp.status}. "
                        "Vérifiez que SearXNG tourne et que 'json' est activé "
                        "dans settings.yml."
                    )
                data = await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.warning("SearXNG connection error: %s", err)
            return (
                f"Impossible de joindre SearXNG à {self.base_url}. "
                "Vérifiez qu'il est démarré."
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("SearXNG unexpected error")
            return f"Erreur lors de la recherche: {err}"

        results = data.get("results", [])[:max_results]
        if not results:
            return f"Aucun résultat trouvé pour : {query}"

        # Format the results for the LLM
        lines = [f"Résultats de recherche pour « {query} » :\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "").strip()
            snippet = r.get("content", "").strip()
            url_r = r.get("url", "").strip()
            lines.append(f"{i}. {title}")
            if snippet:
                lines.append(f"   {snippet}")
            if url_r:
                lines.append(f"   Source: {url_r}")
            lines.append("")

        return "\n".join(lines)
