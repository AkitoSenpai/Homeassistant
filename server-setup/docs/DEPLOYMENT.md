# 🖥️ Déploiement multi-machines

Architecture cible : **Home Assistant sur une machine** + **IA/outils sur un serveur Linux distant**.

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  Home Assistant (PC / RPi)   │         │  Serveur Linux distant       │
│  192.168.1.10                │   LAN   │  192.168.1.20                │
│                              │◀───────▶│                              │
│  - gemma_assistant           │   HTTP  │  - Ollama (Gemma 3n E4B)     │
│  - Piper TTS  (optionnel)    │         │    :11434                    │
│  - Whisper STT (optionnel)   │         │  - SearXNG                   │
│  - Satellites vocaux         │         │    :8888                     │
└──────────────────────────────┘         │  - Pare-feu UFW              │
                                        └──────────────────────────────┘
```

## 1. Préparer le serveur distant

### Prérequis

- Debian 11+ ou Ubuntu 22.04+
- Accès SSH avec sudo
- 8 Go de RAM minimum
- 10 Go d'espace libre pour le modèle
- Ports 11434 et 8888 accessibles depuis la machine HA

### Installation automatisée

```bash
# Sur le serveur, en tant que root :
sudo apt update && sudo apt install -y git
git clone <url-de-ce-repo>
cd Homeassistant/server-setup
chmod +x scripts/*.sh
sudo ./scripts/install-server.sh
```

Le script va :
1. ✅ Installer Ollama + le modèle `gemma3n:e4b`
2. ✅ Configurer Ollama pour écouter sur `0.0.0.0:11434`
3. ✅ Installer Docker + SearXNG
4. ✅ Configurer le pare-feu (UFW) : ports ouverts **uniquement** pour le sous-réseau HA
5. ✅ Tester les services

### Personnalisation avant install

Dans `install-server.sh`, adapte la variable :

```bash
HA_SUBNET="192.168.0.0/16"   # ⚠️ Adapte à TON réseau
```

Pour connaître ton sous-réseau :
```bash
# Sur la machine Home Assistant
ip route | grep default
# Ex: 192.168.1.1 → sous-réseau 192.168.1.0/24
#     192.168.0.1 → sous-réseau 192.168.0.0/24
```

## 2. Configuration côté Home Assistant

### Option A — Via l'UI (recommandé)

1. Copier le dossier de l'intégration :
   ```bash
   # Sur la machine HA
   scp -r user@serveur:/path/to/Homeassistant/custom_components/gemma_assistant \
       /config/custom_components/
   ```
   (Adapte `/config` selon ton installation HA — Home Assistant OS, Supervised, Container…)

2. **Paramètres** → **Appareils et services** → **Ajouter une intégration** → **Gemma Local Assistant**

3. Remplir :
   - **URL Ollama** : `http://192.168.1.20:11434` (adresse IP du serveur)
   - **URL SearXNG** : `http://192.168.1.20:8888`
   - **Modèle** : `gemma3n:e4b`

4. Soumettre → ✅ l'intégration teste la connectivité.

### Option B — Via configuration.yaml

Ajouter dans `configuration.yaml` :

```yaml
# (L'intégration doit de toute façon être dans custom_components/)
# Les options sont gérées par l'UI ; le YAML sert surtout au logger.

logger:
  default: info
  logs:
    custom_components.gemma_assistant: debug
```

## 3. Test de bout-en-bout

### Sur le serveur

```bash
# Vérifier qu'Ollama répond
curl http://localhost:11434/api/tags

# Vérifier que SearXNG répond
curl 'http://localhost:8888/search?q=test&format=json' | python3 -m json.tool | head -20

# Lancer le healthcheck complet
./scripts/healthcheck.sh
```

### Sur Home Assistant

**Outils du développeur** → **Services** → `conversation.process` :

```yaml
service: conversation.process
data:
  agent_id: conversation.gemma_assistant
  text: "Bonjour, qui es-tu et où es-tu hébergé ?"
```

Réponse attendue : Gemma doit répondre en français, mentionner qu'il est local.

### Test de l'outil de recherche

```yaml
service: conversation.process
data:
  agent_id: conversation.gemma_assistant
  text: "Cherche-moi la dernière news sur Home Assistant et résume-la."
```

## 4. Dépannage réseau

### Le pare-feu bloque

```bash
# Sur le serveur, vérifier que les ports sont ouverts
sudo ufw status verbose

# Si besoin, ajouter le sous-réseau HA
sudo ufw allow from 192.168.1.0/24 to any port 11434 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 8888 proto tcp
sudo ufw reload
```

### Ollama n'est pas accessible depuis le LAN

Vérifier qu'il écoute bien sur 0.0.0.0 :

```bash
sudo ss -tlnp | grep 11434
# Doit afficher : LISTEN 0 128 0.0.0.0:11434 0.0.0.0:*
# Si c'est 127.0.0.1:11434, c'est que l'override systemd n'est pas pris en compte.

# Le recharger
sudo systemctl edit ollama   # vérifier que l'override est bon
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Latence trop élevée

Causes possibles :
- **CPU trop chargé** : `top` sur le serveur pendant une question
- **Modèle non quantifié** : vérifier avec `ollama list`
- **Réseau Wi-Fi instable** : passer en Ethernet
- **RAM saturée** : `free -h` — si swap plein, réduire `OLLAMA_NUM_PARALLEL`

### Test de latence depuis HA

```bash
# Sur la machine HA
time curl http://192.168.1.20:11434/api/tags
# Doit retourner en < 100ms
```

## 5. Mise à jour

### Modèles Ollama

```bash
# Sur le serveur
./scripts/update-models.sh
```

### SearXNG

```bash
# Sur le serveur
cd /opt/searxng
docker compose pull
docker compose up -d
```

### Home Assistant (intégration)

Mettre à jour le code de `custom_components/gemma_assistant/`, puis redémarrer HA.

## 6. Sécurité (LAN privé)

Ton setup est sur LAN privé, ce qui est **déjà très bien**. Pour aller plus loin :

- ✅ Activer HTTPS via reverse-proxy (Nginx) si tu veux exposer sur Internet
- ✅ Mettre à jour régulièrement : `apt upgrade`
- ✅ Sauvegarder le dossier `/opt/searxng` et `/usr/share/ollama/.ollama` (modèles)
- ❌ Ne JAMAIS exposer Ollama directement sur Internet sans auth (les requêtes sont coûteuses !)

## 7. Monitoring

### Healthcheck automatique

```bash
# Une seule fois, installer le timer systemd
sudo mkdir -p /opt/ai-server
sudo cp scripts/healthcheck.sh /opt/ai-server/
sudo chmod +x /opt/ai-server/healthcheck.sh

sudo cp systemd/ai-server-monitor.service /etc/systemd/system/
sudo cp systemd/ai-server-monitor.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ai-server-monitor.timer

# Consulter les logs
journalctl -u ai-server-monitor -f
```

### Monitoring externe (optionnel)

Le serveur expose des métriques Prometheus sur Ollama (route `/metrics` activable via `OLLAMA_METRICS=true`).

## 8. Architecture alternative

Si tu veux **tout en local sur une seule machine** (sans réseau), réfère-toi à [`docs/INSTALL.md`](../docs/INSTALL.md) du dossier `custom_components`.

L'intégration fonctionne **de manière identique** — il suffit de mettre `http://localhost:11434` au lieu de l'IP du serveur.
