"""Date and time tool."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util

from ..const import FRENCH_MONTHS, FRENCH_WEEKDAYS
from .base import Tool


def _format_fr(now: datetime, tz_label: str) -> str:
    """Format a datetime in French (locale-independent)."""
    return (
        f"Date: {FRENCH_WEEKDAYS[now.weekday()]} {now.day} "
        f"{FRENCH_MONTHS[now.month - 1]} {now.year}\n"
        f"Heure: {now:%H:%M:%S}\n"
        f"Fuseau: {tz_label}"
    )


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
        tz_label = str(dt_util.DEFAULT_TIME_ZONE)
        if timezone:
            try:
                from zoneinfo import ZoneInfo

                tz = ZoneInfo(timezone)
                now = datetime.now(tz)
                tz_label = timezone
            except Exception:  # noqa: BLE001
                # Fallback to HA local time
                now = dt_util.now()
        else:
            now = dt_util.now()
        return _format_fr(now, tz_label)
