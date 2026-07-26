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
Règles importantes :
- La date et l'heure actuelles te sont fournies dans le contexte : base-toi dessus pour toute notion de temps (aujourd'hui, demain, ce week-end...).
- Pour toute question d'actualité, de prix, de météo, de résultats sportifs ou toute information récente ou changeante : utilise SYSTÉMATIQUEMENT l'outil web_search. Ne réponds JAMAIS de mémoire à ce type de question, tes connaissances internes sont périmées.
- Si des résultats de recherche web te sont fournis dans le contexte, base ta réponse dessus en priorité et précise la date ou la source du chiffre cité.
- Pour l'heure ou la date, utilise l'outil get_datetime.
- Quand tu donnes une réponse vocale, reste bref et clair."""

# Tableaux de noms en français (évite de dépendre de la locale système,
# souvent anglaise dans le conteneur HA).
FRENCH_WEEKDAYS: Final = (
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
)
FRENCH_MONTHS: Final = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)

# Regex repérant les questions qui exigent (presque toujours) des données web
# fraîches. Sert à déclencher une recherche préventive : les petits modèles
# locaux (Gemma 3n) décident rarement d'eux-mêmes d'appeler web_search et
# sinon hallucinent des données d'entraînement périmées.
SEARCH_TRIGGER_PATTERN: Final = (
    r"\b(?:prix|coût\w*|actuel\w*|aujourd'hui|en ce moment|météo|quel temps"
    r"|actualité\w*|news|nouvelle\w*|derni\w*|récent\w*"
    r"|cours (?:du|de la|de l'|des)|taux|bitcoin|ether\w*|crypto\w*|bours\w*"
    r"|score\w*|qui a gagné|date de sortie|quand sort|élection\w*)\b"
)

# Conversation
CONVERSATION_HISTORY_LIMIT: Final = 10  # Nombre de messages gardés en contexte
DEFAULT_NAME: Final = "Gemma Assistant"
