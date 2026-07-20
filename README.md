# 🏠 Gemma Local Assistant

> Assistant conversationnel 100 % local pour Home Assistant, basé sur **Gemma 3n E4B** (via Ollama), **SearXNG** pour la recherche internet, et une stack audio légère (Piper TTS + Whisper STT).

[![Local](https://img.shields.io/badge/100%25-local-green)](#)
[![No API key](https://img.shields.io/badge/no%20API%20key-required-blue)](#)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Component-orange)](#)

---

## ✨ Fonctionnalités

- 🤖 **Conversation naturelle** en français (LLM local, données privées)
- 🔍 **Recherche internet** via SearXNG self-hosted
- 🛠️ **Système d'outils extensible** (tool calling natif Ollama)
- 🎤 **Compatible pipeline vocal** Home Assistant (TTS + STT + wake word)
- 💬 **Historique de conversation** (mémoire des 10 derniers échanges)
- 🏡 **Contrôle domotique** (allumer lumières, lire états, appeler services…)

## 🏗️ Architecture

```
┌──────────────────┐    ┌─────────────────┐
│  Voix (Whisper)  │───▶│  Home Assistant │
└──────────────────┘    │  + Pipeline     │
       ▲                └────────┬────────┘
       │                         │
       │ TTS (Piper)             ▼
       │                ┌─────────────────┐
┌──────────────────┐    │  gemma_assistant│
│  Satellites      │◀───│  (ce composant) │
│  (ESPHome, etc.) │    └────────┬────────┘
└──────────────────┘             │
                                 ├──▶ Ollama (Gemma 3n E4B)
                                 ├──▶ SearXNG (recherche)
                                 └──▶ Home Assistant API
                                          (entités / services)
```

## 📦 Pré-requis

| Service         | Recommandation                                    |
|-----------------|---------------------------------------------------|
| **Ollama**      | v0.3+ avec modèle `gemma3n:e4b`                   |
| **SearXNG**     | Instance locale avec `json` activé dans settings  |
| **RAM**         | 8 Go minimum (Ollama) + 1 Go (Piper/Whisper)      |
| **CPU**         | x86_64 moderne ou Apple Silicon (GPU recommandé)  |
| **Home Assistant** | 2024.6+ (supporte les `conversation agents`)   |

## 🚀 Installation rapide

### 1. Installer Ollama + le modèle

```bash
# Installer Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Démarrer le service
systemctl enable --now ollama

# Télécharger Gemma 3n E4B (~ 3 Go)
ollama pull gemma3n:e4b
```

### 2. Installer SearXNG

Le plus simple : via Docker.

```bash
mkdir -p ~/searxng && cd ~/searxng
cat > docker-compose.yml <<EOF
version: "3.7"
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8888:8080"
    volumes:
      - ./settings.yml:/etc/searxng/settings.yml:ro
    restart: unless-stopped
EOF

# Activer le format JSON (obligatoire pour l'outil)
cat > settings.yml <<EOF
server:
  bind_address: "0.0.0.0"
  secret_key: "change-me-in-prod"
search:
  formats:
    - json
  default_lang: "fr"
  safesearch: 0
EOF

docker compose up -d
```

Test : `curl "http://localhost:8888/search?q=test&format=json" | head`

### 3. Installer Piper TTS + Whisper STT (optionnel mais recommandé)

Voir [docs/AUDIO.md](docs/AUDIO.md) pour le setup complet. Le plus simple : les conteneurs Wyoming.

```bash
# Piper (TTS français)
docker run -d --name piper \
  -p 10300:10200 \
  rhasspy/wyoming-piper \
  --voice fr_FR-upmc-medium

# faster-whisper (STT)
docker run -d --name whisper \
  -p 10301:10300 \
  rhasspy/wyoming-faster-whisper \
  --model tiny --language fr
```

> Le modèle `tiny` est très léger (~40 Mo) et largement suffisant pour de la domotique.

### 4. Installer l'intégration

```bash
# Copier le dossier dans votre installation HA
cp -r custom_components/gemma_assistant \
   /config/custom_components/
# (adaptez /config selon votre installation)

# Redémarrer Home Assistant, puis :
# Paramètres > Appareils et services > Ajouter une intégration
# -> "Gemma Local Assistant"
# -> Entrer l'URL Ollama (http://localhost:11434) et SearXNG (http://localhost:8888)
```

### 5. Activer l'agent de conversation

1. **Paramètres** > **Assistants vocaux** > **Ajouter un assistant**
2. **Agent de conversation** : `Gemma Assistant`
3. **STT** : `wyoming` (Whisper)
4. **TTS** : `wyoming` (Piper)
5. Choisir ce pipeline comme assistant par défaut.

## 🛠️ Outils fournis

L'agent peut appeler automatiquement ces outils :

| Outil          | Description                                              |
|----------------|----------------------------------------------------------|
| `web_search`   | Recherche internet via SearXNG                           |
| `get_datetime` | Date/heure actuelle (avec fuseau)                        |
| `ha_control`   | Lister entités, lire état, appeler services              |

Exemple : vous dites *« Éteins la lumière du salon et donne-moi la météo à Lyon demain »* →
1. L'IA appelle `ha_control(call_service, light.turn_off, light.salon)`
2. Puis `web_search("météo Lyon demain")` pour récupérer les infos
3. Et vous répond en une seule phrase.

## 🔌 Ajouter ses propres outils

Voir [docs/TOOLS.md](docs/TOOLS.md) — c'est aussi simple que :

```python
# custom_components/gemma_assistant/tools/my_tool.py
from .base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "..."
    parameters = {...}

    async def async_call(self, **kwargs) -> str:
        return "résultat"
```

Puis l'enregistrer dans `tools/__init__.py::build_default_registry`.

## 💡 Exemples d'usage

| Vous dites…                                     | Ce qui se passe                                   |
|-------------------------------------------------|---------------------------------------------------|
| *« Il fait quelle heure ? »*                    | Appelle `get_datetime`                            |
| *« Quelles lumières sont allumées ? »*          | Appelle `ha_control(list_entities, light)`        |
| *« Éteins le salon »*                           | Appelle `ha_control(call_service, light.turn_off)`|
| *« C'est quoi la capitale du Japon ? »*         | Appelle `web_search`                              |
| *« Résume-moi l'actu tech du jour »*            | Appelle `web_search` + résume                     |

## 📁 Structure du projet

```
.
├── custom_components/gemma_assistant/   # Le composant
│   ├── __init__.py
│   ├── manifest.json
│   ├── const.py
│   ├── ollama_client.py                 # Client HTTP Ollama
│   ├── conversation.py                  # Agent de conversation
│   ├── config_flow.py                   # UI de configuration
│   ├── tools/                           # Outils disponibles
│   │   ├── base.py
│   │   ├── search.py                    # SearXNG
│   │   ├── datetime_tool.py
│   │   └── homeassistant.py             # Contrôle HA
│   └── strings.json
├── docs/
│   ├── INSTALL.md                       # Guide détaillé
│   ├── TOOLS.md                         # Comment coder un outil
│   └── AUDIO.md                         # Setup TTS/STT
└── examples/
    ├── configuration.yaml
    └── automations.yaml
```

## 🐛 Dépannage

**Ollama pas détecté** :
```bash
curl http://localhost:11434/api/tags
# Doit renvoyer la liste des modèles.
```

**SearXNG renvoie du HTML au lieu de JSON** :
Vérifier que `formats: [json]` est dans `settings.yml`, puis :
```bash
docker restart searxng
```

**L'agent n'apparaît pas dans les assistants** :
Redémarrer HA après installation. Vérifier les logs :
**Paramètres** > **Système** > **Journaux** → filtrer par `gemma_assistant`.

**Whisper transcrit mal** :
Préférer le modèle `base` (~150 Mo) au `tiny` si votre CPU suit.
Sinon, dicter dans un micro de qualité raisonnable.

## 📜 Licence

MIT — faites-en ce que vous voulez, c'est un point de départ.

---

Made with ❤️ pour une domotique **privée**, **locale** et **gratuite**.
