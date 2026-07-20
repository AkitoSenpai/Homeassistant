"""Constants for the Gemma Local Assistant integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "gemma_assistant"
MANUFACTURER: Final = "Local AI"
MODEL: Final = "Gemma Assistant"

# Configuration keys
CONF_OLLAMA_URL: Final = "ollama_url"
CONF_MODEL: Final = "model"
CONF_SEARXNG_URL: Final = "searxng_url"
CONF_TEMPERATURE: Final = "temperature"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_SYSTEM_PROMPT: Final = "system_prompt"
CONF_CONTEXT_LENGTH: Final = "context_length"
CONF_REQUEST_TIMEOUT: Final = "request_timeout"

# Defaults
DEFAULT_OLLAMA_URL: Final = "http://localhost:11434"
DEFAULT_MODEL: Final = "gemma3n:e4b"
DEFAULT_SEARXNG_URL: Final = "http://localhost:8888"
DEFAULT_TEMPERATURE: Final = 0.7
DEFAULT_MAX_TOKENS: Final = 1024
DEFAULT_CONTEXT_LENGTH: Final = 4096
DEFAULT_REQUEST_TIMEOUT: Final = 60

DEFAULT_SYSTEM_PROMPT: Final = """Tu es un assistant domotique intelligent et serviable intégré à Home Assistant.
Tu parles en français de manière concise et naturelle.
Tu peux utiliser des outils pour répondre aux questions (recherche internet, date/heure, contrôle de la maison).
Quand tu utilises un outil, explique brièvement ce que tu fais.
Quand tu donnes une réponse vocale, reste bref et clair."""

# Conversation
CONVERSATION_HISTORY_LIMIT: Final = 10  # Nombre de messages gardés en contexte
DEFAULT_NAME: Final = "Gemma Assistant"
