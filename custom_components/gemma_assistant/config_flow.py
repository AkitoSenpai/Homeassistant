"""Config flow for Gemma Local Assistant."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_MAX_TOKENS,
    CONF_MODEL,
    CONF_OLLAMA_URL,
    CONF_SEARXNG_URL,
    CONF_SYSTEM_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_SEARXNG_URL,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _async_check_ollama(hass, url: str) -> str | None:
    """Check that Ollama is reachable. Return an error message or None."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            f"{url.rstrip('/')}/api/tags",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return f"Ollama a répondu avec le statut {resp.status}."
    except aiohttp.ClientError as err:
        return f"Impossible de joindre Ollama: {err}"
    return None


async def _async_check_searxng(hass, url: str) -> str | None:
    """Check that SearXNG is reachable. Return an error message or None."""
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            f"{url.rstrip('/')}/",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status not in (200, 302):
                return f"SearXNG a répondu avec le statut {resp.status}."
    except aiohttp.ClientError as err:
        return f"Impossible de joindre SearXNG: {err}"
    return None


class GemmaAssistantConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gemma Local Assistant."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Test connectivity
            ollama_err = await _async_check_ollama(
                self.hass, user_input[CONF_OLLAMA_URL]
            )
            if ollama_err:
                errors["ollama_url"] = "cannot_connect_ollama"
            else:
                searxng_err = await _async_check_searxng(
                    self.hass, user_input[CONF_SEARXNG_URL]
                )
                if searxng_err:
                    errors["searxng_url"] = "cannot_connect_searxng"

            if not errors:
                # Make sure we don't already have an entry
                await self.async_set_unique_id(
                    f"{user_input[CONF_OLLAMA_URL]}_{user_input[CONF_MODEL]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Gemma Assistant",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_OLLAMA_URL, default=DEFAULT_OLLAMA_URL): str,
                vol.Required(CONF_MODEL, default=DEFAULT_MODEL): str,
                vol.Required(CONF_SEARXNG_URL, default=DEFAULT_SEARXNG_URL): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        return GemmaAssistantOptionsFlow(config_entry)


class GemmaAssistantOptionsFlow(OptionsFlow):
    """Handle options for Gemma Local Assistant."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_OLLAMA_URL,
                    default=opts.get(CONF_OLLAMA_URL, DEFAULT_OLLAMA_URL),
                ): str,
                vol.Required(
                    CONF_SEARXNG_URL,
                    default=opts.get(CONF_SEARXNG_URL, DEFAULT_SEARXNG_URL),
                ): str,
                vol.Required(
                    CONF_MODEL,
                    default=opts.get(CONF_MODEL, DEFAULT_MODEL),
                ): str,
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=opts.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=2.0)),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=opts.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                ): vol.All(vol.Coerce(int), vol.Range(min=64, max=8192)),
                vol.Optional(
                    CONF_SYSTEM_PROMPT,
                    default=opts.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT),
                ): vol.All(str, vol.Length(max=4000)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
