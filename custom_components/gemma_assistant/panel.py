"""Sidebar panel app, WebSocket chat command and 'ask' action.

This is what turns gemma_assistant from a simple conversation agent into
a fullblown, always-present app inside Home Assistant:

- a "Gemma" entry in the left sidebar (custom panel -> <gemma-panel> JS
  webcomponent), opening a chat page styled like the rest of the UI,
  also visible in the mobile app's side menu;
- a WebSocket command 'gemma_assistant/chat' used by that panel (no need
  to juggle auth tokens, the frontend connection is already authenticated);
- a 'gemma_assistant.ask' action returning the reply, for automations.
"""
from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.components import frontend, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "gemma"
STATIC_URL_PREFIX = "/gemma_assistant_static"
SERVICE_ASK = "ask"


async def async_setup_app(hass: HomeAssistant) -> None:
    """Register panel + WebSocket command + action (called once).

    Invoked from the component-level async_setup, which Home Assistant
    runs when the domain is first loaded — even for a purely
    config-flow based integration.
    """
    # 1. Serve the panel's JS module from the integration directory
    static_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL_PREFIX, str(static_dir), cache_headers=True)]
    )

    # 2. Sidebar entry -> custom panel rendering the <gemma-panel> component
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Gemma",
        sidebar_icon="mdi:robot-happy-outline",
        frontend_url_path=PANEL_URL_PATH,
        config={
            "_panel_custom": {
                "name": "gemma-panel",
                "module_url": f"{STATIC_URL_PREFIX}/gemma-panel.js",
            }
        },
        require_admin=False,
    )

    # 3. WebSocket command used by the panel
    websocket_api.async_register_command(hass, ws_gemma_chat)

    # 4. 'gemma_assistant.ask' action (automations/scripts, with response)
    hass.services.async_register(
        DOMAIN,
        SERVICE_ASK,
        async_handle_ask,
        schema=vol.Schema({vol.Required("text"): str}),
        supports_response=SupportsResponse.ONLY,
    )

    _LOGGER.info(
        "Gemma app ready: sidebar panel '/gemma', ws '%s/chat', action '%s.%s'",
        DOMAIN,
        DOMAIN,
        SERVICE_ASK,
    )
    # Note: everything registered here is runtime-only. If the integration
    # is removed, the panel disappears automatically at the next restart —
    # no explicit teardown needed.


def _any_agent():
    """Return any registered conversation agent (first config entry)."""
    from .conversation import get_first_agent

    return get_first_agent()


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/chat",
        vol.Required("text"): str,
    }
)
@websocket_api.async_response
async def ws_gemma_chat(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """Handle a chat message coming from the sidebar panel."""
    agent = _any_agent()
    if agent is None:
        connection.send_error(
            msg["id"], "no_agent", "Aucun agent Gemma n'est configuré."
        )
        return
    try:
        reply = await agent.async_process_text(msg["text"])
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Panel chat failed")
        connection.send_error(msg["id"], "chat_failed", str(err))
        return
    connection.send_result(msg["id"], {"response": reply})


async def async_handle_ask(call: ServiceCall) -> ServiceResponse:
    """Handle the gemma_assistant.ask action."""
    agent = _any_agent()
    if agent is None:
        return {"response": "Aucun agent Gemma n'est configuré."}
    reply = await agent.async_process_text(call.data["text"])
    return {"response": reply}
