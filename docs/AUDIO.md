# Configuration audio (TTS + STT + wake word)

Ce guide configure un pipeline vocal **100 % local et léger** pour Home Assistant, utilisant le protocole **Wyoming** (le standard HA pour les services audio).

## Vue d'ensemble

```
[Satellite (micro)] → [Whisper STT] → [Conversation] → [Piper TTS] → [Satellite (HP)]
                                                    ↓
                                              [Gemma via Ollama]
                                                    ↑
                                              [SearXNG (si besoin)]
```

## 1. Piper TTS (Text-to-Speech)

Piper est un TTS neuronal local très rapide et léger. Les voix font ~15-60 Mo.

### Docker

```bash
docker run -d --name wyoming-piper \
  -p 10300:10200 \
  --restart unless-stopped \
  rhasspy/wyoming-piper \
  --voice fr_FR-upmc-medium
```

Voix françaises disponibles :
- `fr_FR-upmc-medium` — voix féminine, bonne qualité (~60 Mo)
- `fr_FR-siwis-medium` — autre voix féminine
- `fr_FR-mls_1840-low` — voix masculine, plus rapide

Test :
```bash
echo '{"text": "Bonjour, je suis Piper"}' | \
  mosquitto_pub -h localhost -t wyoming/piper -s
# ou directement avec un client websocket Wyoming
```

### Configurer dans HA

`configuration.yaml` :

```yaml
tts:
  - platform: wyoming
    host: localhost
    port: 10300
```

Ou via l'UI : **Paramètres** → **Appareils et services** → **Ajouter une intégration** → **Wyoming Protocol**.

## 2. faster-whisper (Speech-to-Text)

Whisper transcrit votre voix en texte, localement.

### Docker

```bash
docker run -d --name wyoming-whisper \
  -p 10301:10300 \
  --restart unless-stopped \
  rhasspy/wyoming-faster-whisper \
  --model tiny --language fr
```

Modèles disponibles (du plus léger au plus précis) :

| Modèle    | Taille  | RAM   | Précision |
|-----------|---------|-------|-----------|
| `tiny`    | ~40 Mo  | ~1 Go | OK        |
| `base`    | ~75 Mo  | ~1 Go | Bien      |
| `small`   | ~250 Mo | ~2 Go | Très bien |
| `medium`  | ~750 Mo | ~5 Go | Excellent |
| `large-v3`| ~1.5 Go | ~10Go | Max       |

**Recommandé pour un Raspberry Pi 4/5** : `tiny` en français.
**Pour un PC moderne** : `base` ou `small`.

### GPU (optionnel, beaucoup plus rapide)

```bash
docker run -d --name wyoming-whisper \
  -p 10301:10300 \
  --gpus all \
  --restart unless-stopped \
  rhasspy/wyoming-faster-whisper \
  --model base --language fr --device cuda
```

### Configurer dans HA

```yaml
stt:
  - platform: wyoming
    host: localhost
    port: 10301
```

## 3. Wake word (mot de réveil)

Sans wake word, vous devez appuyer sur un bouton pour parler. Avec, vous pouvez dire « *Hey Jarvis* » à tout moment.

### Option A : openWakeWord (gratuit, local)

```bash
docker run -d --name wyoming-openwakeword \
  -p 10400:10400 \
  --restart unless-stopped \
  rhasspy/wyoming-openwakeword
```

Modèles de wake words embarqués. Vous pouvez entraîner les vôtres sur https://github.com/dscripka/openWakeWord.

### Option B : Porcupine (gratuit pour usage perso, très léger)

Nécessite une clé API gratuite sur https://console.picovoice.ai/.

## 4. Satellites vocaux

Un satellite = un micro + un haut-parleur + un peu de calcul pour le wake word. Vous en placez dans chaque pièce.

### Options matérielles

| Plateforme      | Difficulté | Coût   | Remarque                       |
|-----------------|-----------|--------|--------------------------------|
| **ESPHome**     | Facile    | ~15 €  | ESP32 + INMP441 + MAX98357A    |
| **Raspberry Pi**| Moyen     | ~80 €  | Plus puissant, micro USB       |
| **PC recyclé**  | Facile    | 0 €    | Micro USB, jack                |

Exemple satellite ESPHome minimal : voir [ESPHome satellite docs](https://www.home-assistant.io/voice_control/satellite/).

## 5. Pipeline vocal complet dans HA

Une fois TTS + STT + (wake word) configurés, créer le pipeline :

1. **Paramètres** → **Assistants vocaux** → **Ajouter un assistant**
2. Remplir :
   - **Nom** : "Gemma Local"
   - **Agent de conversation** : `Gemma Assistant`
   - **Moteur STT** : `wyoming` (Whisper)
   - **Moteur TTS** : `wyoming` (Piper)
3. Cliquer sur le **⋮** du pipeline → **Définir par défaut**

## 6. Test bout-en-bout

1. Aller sur **Paramètres** → **Assistants vocaux**
2. Cliquer sur **"Tester"** (icône micro) à côté de votre pipeline
3. Dire « *Bonjour* » — la transcription doit apparaître
4. Dire « *Quelles lumières sont allumées ?* » — la réponse vocale doit suivre

## 7. Performance & optimisations

- **Latence** : Piper ~100 ms, Whisper `tiny` ~300-500 ms sur CPU, Gemma 3n E4B ~1-3 s pour une réponse courte sur CPU.
- **Latence totale** : ~2-5 s en local, comparable à Alexa.
- **GPU** : divise le temps d'inférence par 5-10 si vous avez une carte NVIDIA.

## 8. Alternatives (si besoin)

- **Edge TTS** (Microsoft voices via `edge-tts` Python) : voix de très haute qualité, gratuit, mais nécessite internet.
- **Coqui TTS** : autre TTS local.
- **Vosk** : alternative à Whisper, plus rapide mais moins précis en français.
