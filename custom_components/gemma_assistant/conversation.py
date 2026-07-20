"""Conversation agent for the Gemma Local Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
    ConversationResult,
    async_should_expose,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONVERSATION_HISTORY_LIMIT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_SEARXNG_URL,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
)
from .ollama_client import OllamaClient, OllamaError
from .tools import build_default_registry

_LOGGER = logging.getLogger(__name__)

# Registry of conversation agents by config entry id
_AGENTS: dict[str, "GemmaConversationEntity"] = {}


async def async_register_agent(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register a conversation agent for this config entry."""
    agent = GemmaConversationEntity(hass, entry)
    _AGENTS[entry.entry_id] = agent
    await agent.async_added_to_hass()


def async_unregister_agent(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unregister a conversation agent."""
    _AGENTS.pop(entry.entry_id, None)


def get_agent(hass: HomeAssistant, entry_id: str) -> "GemmaConversationEntity | None":
    return _AGENTS.get(entry_id)


class GemmaConversationEntity(ConversationEntity):
    """Conversation agent powered by Gemma (via Ollama) + tools."""

    _attr_has_entity_name = True
    _attr_name = "Gemma Assistant"
    _attr_supported_features = (
        ConversationEntityFeature.CONTROL
    )

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

    # ------------------------------------------------------------------
    # ConversationEntity interface
    # ------------------------------------------------------------------
    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: intent.ChatLog,
    ) -> ConversationResult:
        """Process a user utterance and return a response."""
        text = user_input.text.strip()
        if not text:
            return await self._build_result(chat_log, "Je n'ai rien reçu.")

        # Build messages: system + history + new user message
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt}
        ]
        # Add bounded history
        for m in self._history[-CONVERSATION_HISTORY_LIMIT:]:
            messages.append(m)
        messages.append({"role": "user", "content": text})

        try:
            # Tool-calling loop
            for _ in range(5):  # safety bound on tool calls
                response = await self.ollama.async_chat(
                    messages=messages,
                    tools=self._tools.to_ollama_tools(),
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
                    return await self._build_result(chat_log, assistant_text)

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
            return await self._build_result(
                chat_log,
                "J'ai fait trop d'appels d'outils, je m'arrête là.",
            )

        except OllamaError as err:
            _LOGGER.exception("Ollama error during conversation")
            return await self._build_result(
                chat_log,
                f"Désolé, erreur avec le modèle local : {err}",
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected error during conversation")
            return await self._build_result(
                chat_log,
                f"Erreur inattendue : {err}",
            )

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
# Optional: a platform setup that adds the entity to the entity registry.
# Home Assistant's conversation integration auto-discovers ConversationEntity
# subclasses, so we don't strictly need this, but it makes the entity visible
# in the UI.
# ---------------------------------------------------------------------------
async def async_setup_entry_platform(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the conversation entity from a config entry."""
    agent = get_agent(hass, entry.entry_id)
    if agent is not None:
        async_add_entities([agent])
