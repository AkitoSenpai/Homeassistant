# Créer ses propres outils

Le système d'outils de Gemma Assistant est conçu pour être facilement extensible. Chaque outil est une simple classe Python.

## Anatomie d'un outil

```python
# custom_components/gemma_assistant/tools/mon_outil.py
from .base import Tool


class MonOutil(Tool):
    name = "mon_outil"                         # Nom unique (utilisé par le LLM)
    description = "..."                        # Description que le LLM lit
    parameters = {                              # JSON Schema des paramètres
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "À quoi sert ce paramètre",
            },
        },
        "required": ["param1"],
    }

    async def async_call(self, **kwargs) -> str:
        """Exécute l'outil et retourne une string (sera injectée au LLM)."""
        # ... votre logique ...
        return "Résultat"
```

## Enregistrer l'outil

Dans `custom_components/gemma_assistant/tools/__init__.py` :

```python
from .mon_outil import MonOutil

def build_default_registry(hass) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(DateTimeTool(hass))
    registry.register(SearXNGTool(hass))
    registry.register(HomeAssistantTool(hass))
    registry.register(MonOutil(hass))   # ← ajouter ici
    return registry
```

Puis redémarrer Home Assistant.

## Exemple 1 : Outil "ma_météo"

```python
import aiohttp
from .base import Tool


class MeteoTool(Tool):
    name = "meteo"
    description = (
        "Donne la météo actuelle d'une ville via l'API Open-Meteo (gratuite, "
        "sans clé). Utiliser dès que l'utilisateur parle de météo, température, "
        "pluie, soleil, etc."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ville": {
                "type": "string",
                "description": "Nom de la ville (ex: 'Lyon', 'Paris')",
            }
        },
        "required": ["ville"],
    }

    async def async_call(self, ville: str) -> str:
        # 1) Géocodage
        session = self.hass.helpers.aiohttp_client.async_get_clientsession(self.hass)
        async with session.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": ville, "count": 1, "language": "fr"},
        ) as r:
            data = await r.json()
        if not data.get("results"):
            return f"Ville '{ville}' introuvable."
        loc = data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        nom = loc["name"]

        # 2) Météo actuelle
        async with session.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        ) as r:
            weather = await r.json()["current"]

        codes = {
            0: "dégagé", 1: "principalement dégagé", 2: "partiellement nuageux",
            3: "couvert", 45: "brouillard", 61: "pluie légère",
            63: "pluie modérée", 65: "pluie forte", 80: "averses",
            95: "orage",
        }
        cond = codes.get(weather["weather_code"], "inconnue")
        return (
            f"Météo à {nom} : {cond}, {weather['temperature_2m']}°C, "
            f"vent {weather['wind_speed_10m']} km/h."
        )
```

## Exemple 2 : Outil "calendrier"

Lit les événements du calendrier configuré dans HA :

```python
from datetime import timedelta
import homeassistant.util.dt as dt_util
from .base import Tool


class CalendrierTool(Tool):
    name = "calendrier"
    description = (
        "Liste les événements du calendrier 'personnel' pour aujourd'hui "
        "ou les N prochains jours."
    )
    parameters = {
        "type": "object",
        "properties": {
            "nb_jours": {
                "type": "integer",
                "description": "Nombre de jours à venir (1-14). Défaut 1.",
                "default": 1,
            }
        },
        "required": [],
    }

    async def async_call(self, nb_jours: int = 1) -> str:
        now = dt_util.now()
        end = now + timedelta(days=nb_jours)
        events = await self.hass.components.calendar.async_get_events(
            self.hass, "calendar.personnel", now, end
        )
        if not events:
            return "Aucun événement prévu."
        lines = [f"{len(events)} événement(s) :"]
        for ev in events[:10]:
            start = ev.start.get("dateTime", ev.start.get("date"))
            lines.append(f"- {ev.summary} ({start})")
        return "\n".join(lines)
```

## Bonnes pratiques

1. **Description claire** : le LLM s'appuie *uniquement* sur la `description` pour décider d'utiliser l'outil. Soyez précis sur le *quand* l'utiliser.
2. **Retour concis** : renvoyez du texte court, formaté pour que le LLM puisse le digérer facilement. Évitez de renvoyer 10 Ko de JSON brut.
3. **Gestion d'erreurs** : renvoyez une string d'erreur lisible plutôt que de lever une exception, l'agent saura rebondir.
4. **Pas d'effets de bord non sollicités** : un outil ne doit faire que ce qui est demandé.
5. **Idempotence** : si possible, l'appel répété doit produire le même résultat (sinon prévenez dans la description).
6. **Pas de secrets dans les paramètres** : le LLM voit tout, ne lui passez pas de mots de passe.

## Debug

Pour voir quels outils sont appelés et leurs arguments :

`configuration.yaml` :
```yaml
logger:
  logs:
    custom_components.gemma_assistant: debug
```

Vous verrez dans les logs :
```
DEBUG - Calling tool web_search with {'query': 'météo Lyon'}
DEBUG - Calling tool ha_control with {'action': 'list_entities', 'domain': 'light'}
```

## Tester un outil seul

```python
# test_tool.py (à exécuter dans /config)
import asyncio
from custom_components.gemma_assistant.tools.search import SearXNGTool

async def main():
    # On a besoin d'un mock hass, c'est plus simple via pytest
    pass
```

Le plus simple est de tester via l'agent directement : *« Cherche [ce que ton outil doit faire] »* et observer le log.
