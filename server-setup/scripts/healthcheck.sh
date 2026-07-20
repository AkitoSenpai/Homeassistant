#!/usr/bin/env bash
# ============================================================================
#  healthcheck.sh
#  Vérifie l'état des services Ollama et SearXNG
# ============================================================================

set -euo pipefail
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

OLLAMA_URL="http://localhost:11434"
SEARXNG_URL="http://localhost:8888"

echo "==========================================="
echo "  🩺 Healthcheck - $(hostname)"
echo "  📅 $(date)"
echo "==========================================="

# --- Ollama ------------------------------------------------------------------
echo ""
echo "🤖 Ollama :"
if systemctl is-active --quiet ollama; then
  echo -e "  Service systemd : ${GREEN}actif${NC}"
else
  echo -e "  Service systemd : ${RED}inactif${NC}"
fi

if curl -fsS "$OLLAMA_URL/api/tags" -m 5 > /dev/null 2>&1; then
  echo -e "  API /api/tags   : ${GREEN}OK${NC}"
  echo "  Modèles chargés :"
  curl -fsS "$OLLAMA_URL/api/tags" 2>/dev/null | \
    python3 -c "import sys, json; d=json.load(sys.stdin); [print(f'    - {m[\"name\"]} ({m[\"size\"]//1024//1024} Mo)') for m in d.get('models', [])]" \
    || echo "    (parsing JSON échoué)"
else
  echo -e "  API /api/tags   : ${RED}KO${NC}"
fi

# --- SearXNG -----------------------------------------------------------------
echo ""
echo "🔍 SearXNG :"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^searxng$"; then
  echo -e "  Conteneur Docker : ${GREEN}actif${NC}"
else
  echo -e "  Conteneur Docker : ${RED}inactif${NC}"
fi

if curl -fsS "$SEARXNG_URL/search?q=test&format=json" -m 5 > /dev/null 2>&1; then
  echo -e "  API /search     : ${GREEN}OK${NC}"
  RESULT_COUNT=$(curl -fsS "$SEARXNG_URL/search?q=test&format=json" 2>/dev/null | \
    python3 -c "import sys, json; print(len(json.load(sys.stdin).get('results', [])))" 2>/dev/null || echo "?")
  echo "  Résultats test   : $RESULT_COUNT"
else
  echo -e "  API /search     : ${RED}KO${NC}"
fi

# --- Ressources --------------------------------------------------------------
echo ""
echo "💻 Ressources :"
echo "  CPU : $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d',' -f1)% utilisé"
echo "  RAM : $(free -h | awk '/^Mem:/ {print $3 " / " $2 " (" int($3/$2*100) "%)"}')"
echo "  Disque / : $(df -h / | awk 'NR==2 {print $5 " utilisé (" $4 " libre)"}')"

# --- Température CPU (si lm-sensors installé) --------------------------------
if command -v sensors &> /dev/null; then
  echo ""
  echo "🌡️  Températures :"
  sensors | grep -E "Core|Package" | head -4
fi

echo ""
echo "==========================================="
