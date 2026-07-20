"""The Gemma Local Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .ollama_client import OllamaClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gemma Local Assistant from a config entry."""
    _LOGGER.debug("Setting up Gemma Local Assistant entry: %s", entry.entry_id)

    # Initialiser le client Ollama
    ollama_client = OllamaClient(
        hass=hass,
        base_url=entry.data.get("ollama_url", "http://localhost:11434"),
        model=entry.data.get("model", "gemma3n:e4b"),
        timeout=entry.data.get("request_timeout", 60),
    )

    # Vérifier la connexion à Ollama
    try:
        await ollama_client.async_verify_connection()
    except Exception as err:
        raise ConfigEntryNotReady(f"Impossible de se connecter à Ollama: {err}") from err

    # Stocker le client dans hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = ollama_client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Enregistrer l'agent de conversation
    from .conversation import async_register_agent

    await async_register_agent(hass, entry)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Gemma Local Assistant entry: %s", entry.entry_id)

    # Désenregistrer l'agent
    from .conversation import async_unregister_agent

    async_unregister_agent(hass, entry)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        ollama_client: OllamaClient = hass.data[DOMAIN].pop(entry.entry_id)
        await ollama_client.async_close()

    return unload_ok
