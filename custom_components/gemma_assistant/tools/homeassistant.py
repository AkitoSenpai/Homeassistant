"""Home Assistant control tool: list entities and call services."""
from __future__ import annotations

import json
import logging
from typing import Any

from .base import Tool

_LOGGER = logging.getLogger(__name__)


class HomeAssistantTool(Tool):
    """Tool allowing the assistant to list entities and call services."""

    name = "ha_control"
    description = (
        "Permet d'interroger ou de contrôler Home Assistant. "
        "Actions disponibles : "
        "'list_entities' (liste les entités d'un domaine, ex: 'light', 'switch', 'sensor'), "
        "'get_state' (récupère l'état d'une entité), "
        "'call_service' (appelle un service, ex: light.turn_on avec entity_id et brightness)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list_entities", "get_state", "call_service"],
                "description": "L'action à effectuer.",
            },
            "domain": {
                "type": "string",
                "description": "Domaine (ex: 'light', 'switch'). Utilisé avec list_entities.",
            },
            "entity_id": {
                "type": "string",
                "description": "ID d'entité (ex: 'light.salon'). Utilisé avec get_state et call_service.",
            },
            "service": {
                "type": "string",
                "description": "Service complet (ex: 'light.turn_on'). Utilisé avec call_service.",
            },
            "data": {
                "type": "object",
                "description": "Données additionnelles pour call_service (ex: {'brightness': 200}).",
            },
        },
        "required": ["action"],
    }

    async def async_call(
        self,
        action: str,
        domain: str | None = None,
        entity_id: str | None = None,
        service: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Dispatch the requested action."""
        if action == "list_entities":
            return await self._list_entities(domain)
        if action == "get_state":
            return await self._get_state(entity_id)
        if action == "call_service":
            return await self._call_service(service, entity_id, data or {})
        return f"Action inconnue: {action}"

    async def _list_entities(self, domain: str | None) -> str:
        states = self.hass.states.async_all()
        if domain:
            states = [s for s in states if s.entity_id.startswith(f"{domain}.")]

        if not states:
            return f"Aucune entité trouvée pour le domaine '{domain}'." if domain else "Aucune entité."

        # Limit to a reasonable number to keep the prompt small
        states = states[:50]
        lines = [f"Entités ({len(states)}):"]
        for s in states:
            friendly = s.attributes.get("friendly_name", "")
            lines.append(f"- {s.entity_id} = {s.state} {f'({friendly})' if friendly else ''}")
        return "\n".join(lines)

    async def _get_state(self, entity_id: str | None) -> str:
        if not entity_id:
            return "Erreur: 'entity_id' est requis pour get_state."
        state = self.hass.states.get(entity_id)
        if state is None:
            return f"Entité '{entity_id}' introuvable."
        return json.dumps(
            {
                "entity_id": state.entity_id,
                "state": state.state,
                "attributes": dict(state.attributes),
            },
            ensure_ascii=False,
        )

    async def _call_service(
        self,
        service: str | None,
        entity_id: str | None,
        data: dict[str, Any],
    ) -> str:
        if not service or "." not in service:
            return "Erreur: 'service' doit être au format 'domain.service'."
        domain, service_name = service.split(".", 1)
        payload: dict[str, Any] = {**data}
        if entity_id:
            payload["entity_id"] = entity_id
        try:
            await self.hass.services.async_call(
                domain,
                service_name,
                payload,
                blocking=True,
            )
            return f"Service {service} exécuté avec succès."
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Service call failed")
            return f"Erreur lors de l'appel du service {service}: {err}"
