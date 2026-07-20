# Guide d'installation détaillé

## 1. Préparer Ollama

### Installation native (Linux)

```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable --now ollama
ollama --version
```

### Avec Docker (alternatif)

```bash
docker run -d --name ollama \
  -p 11434:11434 \
  -v ollama_data:/root/.ollama \
  --restart unless-stopped \
  ollama/ollama
```

### Charger le modèle

```bash
# Gemma 3n E4B — environ 3 Go
ollama pull gemma3n:e4b

# Tester
ollama run gemma3n:e4b "Bonjour, qui es-tu ?"
```

> 💡 Si votre machine est juste, vous pouvez essayer un modèle plus petit :
> - `gemma3:2b` (1.6 Go) — moins bon mais plus rapide
> - `gemma3:4b` (3.3 Go) — bon compromis
> - `gemma3n:e2b` (1.5 Go) — variante "efficacité" de Gemma 3n

### Test de l'API

```bash
curl http://localhost:11434/api/tags
```

Doit renvoyer un JSON listant les modèles installés.

## 2. Préparer SearXNG

### Docker Compose (recommandé)

Voir `README.md` section 2.

### Test

```bash
curl "http://localhost:8888/search?q=test&format=json" | python3 -m json.tool | head -30
```

Si vous obtenez du HTML, le format JSON n'est pas activé.

### Configuration minimale de `settings.yml`

```yaml
server:
  bind_address: "0.0.0.0"
  port: 8080
  secret_key: "mettez-un-vrai-secret-ici"

search:
  formats:
    - json
  default_lang: "fr"
  safesearch: 0
  autocomplete: ""
  favicon_resolver: ""

engines:
  - name: duckduckgo
    disabled: false
  - name: wikipedia
    disabled: false
```

## 3. (Optionnel) Satellites vocaux

Voir [AUDIO.md](AUDIO.md) pour Piper + Whisper + wake word.

## 4. Installer l'intégration dans Home Assistant

### Méthode A — Via HACS (recommandé)

1. Ajouter ce repo comme custom repository HACS (type : integration)
2. Installer "Gemma Local Assistant" depuis HACS
3. Redémarrer HA

### Méthode B — Manuelle

```bash
# Sur la machine qui héberge Home Assistant
cd /config
mkdir -p custom_components
cp -r /chemin/vers/ce/repo/custom_components/gemma_assistant \
      custom_components/

# Redémarrer HA
```

### Configurer

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration**
2. Chercher **"Gemma Local Assistant"**
3. Remplir :
   - **URL Ollama** : `http://localhost:11434` (ou `http://host.docker.internal:11434` si HA est en Docker)
   - **Modèle** : `gemma3n:e4b`
   - **URL SearXNG** : `http://localhost:8888`
4. **Soumettre**

### Activer l'agent de conversation

1. **Paramètres** → **Assistants vocaux** → **Ajouter un assistant**
2. Nommer : "Gemma Local"
3. Agent : `Gemma Assistant`
4. STT : `wyoming` (si configuré)
5. TTS : `wyoming` (si configuré)
6. Wake word : `openwakeword` ou `porcupine` (si configuré)
7. Choisir ce pipeline comme **assistant par défaut**

## 5. Tester

### Dans l'UI

**Outils du développeur** → **Services** → `conversation.process` :

```yaml
service: conversation.process
data:
  agent_id: conversation.gemma_assistant
  text: "Bonjour, qui es-tu ?"
```

### Avec la voix

Si vous avez configuré un satellite (ESPHome, etc.) :
*« Hey Jarvis, il fait quel temps demain à Lyon ? »*

### Avec un script

```yaml
# scripts/ask_gemma.yaml
ask_gemma:
  alias: "Demander à Gemma"
  fields:
    question:
      description: "Question à poser"
      example: "Quelles lumières sont allumées ?"
  sequence:
    - service: conversation.process
      data:
        agent_id: conversation.gemma_assistant
        text: "{{ question }}"
```

## 6. Mises à jour du modèle

Quand un nouveau Gemma sort :

```bash
ollama pull gemma3n:e4b   # télécharge la nouvelle version
```

Puis **Paramètres** → **Appareils et services** → **Gemma Assistant** → **Options** :
changer le nom du modèle si besoin.

## 7. Logs & debug

**Paramètres** → **Système** → **Journaux** :
- Filtrer par `gemma_assistant` pour voir les logs du composant
- Filtrer par `ollama` (depuis la CLI : `journalctl -u ollama -f`) pour Ollama
