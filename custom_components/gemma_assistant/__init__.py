"""The Gemma Local Assistant integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .ollama_client import OllamaClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CONVERSATION]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Gemma component itself (sidebar panel, WS chat, action).

    Runs once when the domain is first loaded, before the first config
    entry — Home Assistant calls it even for a config-flow only integration.
    """
    from .panel import async_setup_app

    await async_setup_app(hass)
    return True


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

    # Créer l'agent de conversation AVANT le forward (la plateforme
    # conversation le récupère via get_agent() et l'ajoute comme entité)
    from .conversation import async_register_agent

    await async_register_agent(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Gemma Local Assistant entry: %s", entry.entry_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Désenregistrer l'agent
        from .conversation import async_unregister_agent

        async_unregister_agent(hass, entry)
        ollama_client: OllamaClient = hass.data[DOMAIN].pop(entry.entry_id)
        await ollama_client.async_close()

    return unload_ok
