"""Date and time tool."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util

from .base import Tool


class DateTimeTool(Tool):
    """Provides the current date and time."""

    name = "get_datetime"
    description = (
        "Retourne la date et l'heure actuelles. À utiliser dès que l'utilisateur "
        "demande l'heure, la date, le jour de la semaine, ou pour contextualiser "
        "une recherche (ex: 'météo demain')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": (
                    "Fuseau horaire IANA (ex: 'Europe/Paris'). "
                    "Optionnel — par défaut celui de Home Assistant."
                ),
            }
        },
        "required": [],
    }

    async def async_call(self, timezone: str | None = None) -> str:
        """Return the current date/time in the requested timezone."""
        if timezone:
            try:
                from zoneinfo import ZoneInfo

                tz = ZoneInfo(timezone)
                now = datetime.now(tz)
                return now.strftime(
                    "Date: %A %d %B %Y\nHeure: %H:%M:%S\nFuseau: %s"
                ) % timezone
            except Exception:  # noqa: BLE001
                # Fallback to HA local time
                pass
        now = dt_util.now()
        return now.strftime(
            "Date: %A %d %B %Y\nHeure: %H:%M:%S\nFuseau: %s"
        ) % str(now.tzinfo)
