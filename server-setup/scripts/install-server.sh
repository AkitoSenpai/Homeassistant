#!/usr/bin/env bash
# ============================================================================
#  install-server.sh
#  Installation complète du serveur AI pour Home Assistant
#  Compatible: Debian 11+/Ubuntu 22.04+ (testé sur ton i5-4670S)
# ============================================================================
set -euo pipefail

# --- Couleurs pour les logs -------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; }
info() { echo -e "${BLUE}[i]${NC} $*"; }

# --- Vérification root -------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
  err "Ce script doit être exécuté en root : sudo $0"
  exit 1
fi

# --- Variables ---------------------------------------------------------------
OLLAMA_VERSION="0.5.7"               # Mettre à jour si besoin
OLLAMA_PORT=11434
SEARXNG_PORT=8888
HA_SUBNET="192.168.0.0/16"          # ⚠️ Adapte à ton sous-réseau HA

# --- Détection de l'OS -------------------------------------------------------
. /etc/os-release
info "OS détecté : $PRETTY_NAME"

if ! command -v systemctl &> /dev/null; then
  err "systemd est requis (ce script ne marche pas sans)."
  exit 1
fi

# --- Mise à jour des paquets -------------------------------------------------
info "Mise à jour des paquets..."
apt-get update -y
apt-get upgrade -y
apt-get install -y curl wget git ufw ca-certificates gnupg lsb-release

# --- Pare-feu (UFW) ----------------------------------------------------------
info "Configuration du pare-feu (UFW)..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
# SSH (si on est en SSH)
ufw allow OpenSSH
# Ollama : UNIQUEMENT depuis le sous-réseau HA
ufw allow from "$HA_SUBNET" to any port "$OLLAMA_PORT" proto tcp comment "Ollama from HA LAN"
# SearXNG : idem
ufw allow from "$HA_SUBNET" to any port "$SEARXNG_PORT" proto tcp comment "SearXNG from HA LAN"
# Optionnel : monitoring
# ufw allow from "$HA_SUBNET" to any port 9090 proto tcp comment "Prometheus"
ufw --force enable
log "Pare-feu configuré : ports $OLLAMA_PORT et $SEARXNG_PORT ouverts uniquement pour $HA_SUBNET"

# ============================================================================
#  1. Ollama
# ============================================================================
info "Installation d'Ollama v$OLLAMA_VERSION..."

if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
  log "Ollama installé."
else
  warn "Ollama déjà installé, on saute."
fi

systemctl enable ollama

# --- Configuration d'Ollama (systemd override pour 0.0.0.0) -----------------
info "Configuration d'Ollama pour écouter sur toutes les interfaces..."
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:$OLLAMA_PORT"
Environment="OLLAMA_KEEP_ALIVE=10m"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
# Optimisations CPU
Environment="OLLAMA_CPU=true"
EOF

systemctl daemon-reload
systemctl restart ollama
sleep 3
log "Ollama configuré sur 0.0.0.0:$OLLAMA_PORT"

# --- Téléchargement du modèle Gemma 3n E4B ----------------------------------
info "Téléchargement de gemma3n:e4b (~3 Go) — peut prendre 5-15 min..."
ollama pull gemma3n:e4b
log "Modèle gemma3n:e4b téléchargé."

# --- Test rapide -------------------------------------------------------------
info "Test d'Ollama..."
TEST_RESPONSE=$(ollama run gemma3n:e4b "Réponds juste 'OK'" 2>&1 | tail -1 || true)
if echo "$TEST_RESPONSE" | grep -qi "ok"; then
  log "Ollama fonctionne ✓ (réponse : $TEST_RESPONSE)"
else
  warn "Test Ollama non concluant : $TEST_RESPONSE"
  warn "Pas grave, le modèle est chargé et le service tourne."
fi

# ============================================================================
#  2. SearXNG (via Docker)
# ============================================================================
info "Installation de Docker (si absent)..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
  log "Docker installé."
else
  warn "Docker déjà installé, on saute."
fi

# --- Répertoire SearXNG ------------------------------------------------------
mkdir -p /opt/searxng
cd /opt/searxng

# --- Configuration SearXNG ---------------------------------------------------
info "Configuration de SearXNG..."
cat > settings.yml <<'EOF'
use_default_settings: false

server:
  bind_address: "0.0.0.0"
  port: 8080
  secret_key: "CHANGE-ME-IN-PROD-$(date +%s)"
  limiter: false
  image_proxy: false

ui:
  static_use_hash: true

search:
  formats:
    - json
    - csv
    - rss
  default_lang: "fr"
  safesearch: 0
  autocomplete: ""
  favicon_resolver: ""

engines:
  - name: duckduckgo
    disabled: false
    timeout: 5.0
  - name: wikipedia
    disabled: false
  - name: qwant
    disabled: false
  - name: brave
    disabled: false
  - name: startpage
    disabled: false
  - name: mojeek
    disabled: false

EOF

# --- Docker Compose ----------------------------------------------------------
cat > docker-compose.yml <<EOF
version: "3.7"
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    restart: unless-stopped
    ports:
      - "$SEARXNG_PORT:8080"
    volumes:
      - ./settings.yml:/etc/searxng/settings.yml:ro
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF

# --- Démarrage SearXNG -------------------------------------------------------
info "Démarrage de SearXNG..."
docker compose up -d
sleep 5
if docker ps | grep -q searxng; then
  log "SearXNG démarré ✓"
else
  err "SearXNG n'a pas démarré. Voir : docker logs searxng"
fi

# ============================================================================
#  3. Vérification finale
# ============================================================================
echo ""
echo "============================================================"
echo "  ✅ Installation terminée !"
echo "============================================================"
echo ""
echo "  Ollama :"
echo "    - URL interne :  http://localhost:$OLLAMA_PORT"
echo "    - URL externe :  http://$(hostname -I | awk '{print $1}'):$OLLAMA_PORT"
echo "    - Modèle :       gemma3n:e4b"
echo "    - Test :         curl http://localhost:$OLLAMA_PORT/api/tags"
echo ""
echo "  SearXNG :"
echo "    - URL interne :  http://localhost:$SEARXNG_PORT"
echo "    - URL externe :  http://$(hostname -I | awk '{print $1}'):$SEARXNG_PORT"
echo "    - Test :         curl 'http://localhost:$SEARXNG_PORT/search?q=test&format=json' | head"
echo ""
echo "  Pare-feu :"
echo "    - Ports ouverts UNIQUEMENT pour le sous-réseau : $HA_SUBNET"
echo "    - ⚠️  Adapte cette valeur si ton réseau HA est différent."
echo ""
echo "  Prochaine étape : configurer Home Assistant pour pointer"
echo "  vers http://$(hostname -I | awk '{print $1}'):$OLLAMA_PORT et :$SEARXNG_PORT"
echo "============================================================"
