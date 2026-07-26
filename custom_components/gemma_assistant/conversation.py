"""Conversation agent for the Gemma Local Assistant."""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import (
    CONVERSATION_HISTORY_LIMIT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_SEARXNG_URL,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
    FRENCH_MONTHS,
    FRENCH_WEEKDAYS,
    SEARCH_TRIGGER_PATTERN,
)
from .ollama_client import OllamaClient, OllamaError
from .tools import build_default_registry

_LOGGER = logging.getLogger(__name__)

# Registry of conversation agents by config entry id
_AGENTS: dict[str, "GemmaConversationEntity"] = {}

# Pre-compiled trigger for questions that need fresh web data
_SEARCH_TRIGGER_RE = re.compile(SEARCH_TRIGGER_PATTERN, re.IGNORECASE)


def _french_now() -> str:
    """Return the current local date/time formatted in French
    (locale-independent, the HA container locale is usually English)."""
    now = dt_util.now()
    return (
        f"{FRENCH_WEEKDAYS[now.weekday()]} {now.day} "
        f"{FRENCH_MONTHS[now.month - 1]} {now.year}, {now:%H:%M}"
    )


async def async_register_agent(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create and store a conversation agent for this config entry.

    The entity is then added to Home Assistant by the conversation
    platform hook (async_setup_entry below), which also handles the
    entity lifecycle callbacks — do NOT call async_added_to_hass()
    manually here.
    """
    agent = GemmaConversationEntity(hass, entry)
    _AGENTS[entry.entry_id] = agent


def async_unregister_agent(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unregister a conversation agent."""
    _AGENTS.pop(entry.entry_id, None)


def get_agent(hass: HomeAssistant, entry_id: str) -> "GemmaConversationEntity | None":
    return _AGENTS.get(entry_id)


def get_first_agent() -> "GemmaConversationEntity | None":
    """Return any registered agent (first config entry), for panel/action use."""
    return next(iter(_AGENTS.values()), None)


class GemmaConversationEntity(ConversationEntity):
    """Conversation agent powered by Gemma (via Ollama) + tools."""

    _attr_has_entity_name = True
    _attr_name = "Gemma Assistant"
    _attr_supported_features = (
        ConversationEntityFeature.CONTROL
    )

    @property
    def supported_languages(self) -> list[str]:
        """Return the list of languages this agent handles.

        Note: on recent HA versions, ConversationEntity declares
        'supported_languages' as an *abstract property*, so the usual
        _attr_supported_languages shorthand does NOT satisfy it — a real
        override named exactly 'supported_languages' is required,
        otherwise instantiation raises TypeError (abstract class).
        """
        return ["fr"]

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        ConversationEntity.__init__(self)
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        # LLM options
        self._temperature: float = entry.options.get(
            "temperature", DEFAULT_TEMPERATURE
        )
        self._max_tokens: int = entry.options.get("max_tokens", DEFAULT_MAX_TOKENS)
        self._system_prompt: str = entry.options.get(
            "system_prompt", DEFAULT_SYSTEM_PROMPT
        )
        # Per-user (or per-agent) conversation memory
        self._history: list[dict[str, Any]] = []

        # Build the tool registry
        self._tools = build_default_registry(hass)
        # Allow the user to set a custom SearXNG URL via options
        searxng_url = entry.options.get("searxng_url", DEFAULT_SEARXNG_URL)
        # Replace the default search tool with one configured with the URL
        from .tools.search import SearXNGTool

        self._tools.unregister("web_search")
        self._tools.register(SearXNGTool(hass, base_url=searxng_url))

    @property
    def ollama(self) -> OllamaClient:
        """Return the Ollama client stored on the config entry."""
        return self.hass.data[DOMAIN][self.entry.entry_id]

    def _build_system_prompt(self) -> str:
        """System prompt = user prompt + current date/time context.

        Without this, the model has no idea what day it is and answers
        time-relative questions from its (stale) training window.
        """
        return (
            f"{self._system_prompt}\n\n"
            f"Date et heure actuelles : {_french_now()}."
        )

    # ------------------------------------------------------------------
    # ConversationEntity interface
    # ------------------------------------------------------------------
    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: intent.ChatLog,
    ) -> ConversationResult:
        """Process a user utterance and return a response."""
        try:
            response_text = await self.async_process_text(user_input.text or "")
        except Exception as err:  # noqa: BLE001
            # Never let an exception escape to the Assist pipeline: it would
            # be swallowed as "Unexpected error during intent recognition".
            # Show a readable message instead; the real traceback is logged.
            _LOGGER.exception("Unhandled error while processing message")
            response_text = f"Erreur interne de l'agent : {err}"
        return await self._build_result(chat_log, response_text)

    async def async_process_text(self, text: str) -> str:
        """Process a raw user message and return the reply as plain text.

        Single message engine shared by the conversation pipeline, the
        sidebar panel (WebSocket command) and the 'gemma_assistant.ask'
        action — the pre-emptive web search and live date/time context
        apply to all of them.
        """
        text = text.strip()
        if not text:
            return "Je n'ai rien reçu."

        # Build messages: system (with live date/time) + history + new user msg
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        # Add bounded history
        for m in self._history[-CONVERSATION_HISTORY_LIMIT:]:
            messages.append(m)
        messages.append({"role": "user", "content": text})

        tools = self._tools.to_ollama_tools()

        # --------------------------------------------------------------
        # Pre-emptive web search for time-sensitive questions.
        # Small local models (Gemma 3n) rarely decide on their own to call
        # web_search and otherwise answer from stale training data
        # (e.g. "prix du bitcoin" -> valeur de 2023). Detect such questions
        # deterministically and inject fresh SearXNG results into the
        # context instead; it is also faster (one LLM pass instead of two).
        # --------------------------------------------------------------
        if _SEARCH_TRIGGER_RE.search(text) and self._tools.get("web_search"):
            _LOGGER.debug("Time-sensitive question, running web search: %s", text)
            search_result = await self._tools.async_call(
                "web_search", {"query": text, "max_results": 5}
            )
            if search_result and not search_result.startswith(
                ("Erreur", "Impossible")
            ):
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Voici des résultats de recherche web à jour pour "
                            "répondre à la question de l'utilisateur :\n"
                            f"{search_result}\n"
                            "Base ta réponse sur ces résultats (PAS sur ta "
                            "mémoire interne) et précise la date ou la source "
                            "du chiffre cité."
                        ),
                    }
                )
                # Fresh results already in context: answer directly without
                # offering the tools again (avoids a second LLM round-trip).
                tools = None

        try:
            # Tool-calling loop
            for _ in range(5):  # safety bound on tool calls
                response = await self.ollama.async_chat(
                    messages=messages,
                    tools=tools,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
                msg = response.get("message", {})
                tool_calls = msg.get("tool_calls") or []

                if not tool_calls:
                    # Final assistant message
                    assistant_text = (msg.get("content") or "").strip()
                    if not assistant_text:
                        assistant_text = "Je n'ai pas pu générer de réponse."
                    # Persist in history
                    self._history.append({"role": "user", "content": text})
                    self._history.append(
                        {"role": "assistant", "content": assistant_text}
                    )
                    return assistant_text

                # Append the assistant's tool-call message
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.get("content") or "",
                        "tool_calls": tool_calls,
                    }
                )

                # Execute each tool call
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    args = fn.get("arguments", {}) or {}
                    _LOGGER.debug("Calling tool %s with %s", name, args)
                    result = await self._tools.async_call(name, args)
                    messages.append(
                        {
                            "role": "tool",
                            "content": result,
                        }
                    )

            # Too many iterations
            return "J'ai fait trop d'appels d'outils, je m'arrête là."

        except OllamaError as err:
            _LOGGER.exception("Ollama error during conversation")
            return f"Désolé, erreur avec le modèle local : {err}"
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during conversation")
            return f"Erreur inattendue : {err}"

    async def _build_result(
        self,
        chat_log: intent.ChatLog,
        text: str,
    ) -> ConversationResult:
        """Build a ConversationResult with the given response text."""
        intent_response = intent.IntentResponse(language="fr")
        intent_response.async_set_speech(text)
        return ConversationResult(
            response=intent_response,
            conversation_id=chat_log.conversation_id,
        )


# ---------------------------------------------------------------------------
# Conversation platform hook.
# With PLATFORMS = [Platform.CONVERSATION] in __init__.py, Home Assistant
# calls this right after the component setup. A ConversationEntity instance
# is invisible to HA (no state, not selectable in Assist) until it is added
# through async_add_entities — this hook is what makes
# 'conversation.gemma_assistant' actually exist.
# ---------------------------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add the conversation entity created in async_register_agent."""
    agent = get_agent(hass, entry.entry_id)
    if agent is not None:
        async_add_entities([agent])
