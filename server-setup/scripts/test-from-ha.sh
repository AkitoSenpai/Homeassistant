#!/usr/bin/env bash
# ============================================================================
#  test-from-ha.sh
#  A executer DEPUIS la machine Home Assistant
#  Verifie qu on peut joindre le serveur distant
# ============================================================================

set -euo pipefail

# Personnaliser ici l IP de ton serveur
SERVER_IP="${1:-192.168.1.20}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
SEARXNG_PORT="${SEARXNG_PORT:-8888}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "==========================================="
echo "  Test de connectivite HA -> Serveur"
echo "  Serveur : $SERVER_IP"
echo "==========================================="

# 1. Ping
echo ""
echo "1. Ping..."
if ping -c 2 -W 2 "$SERVER_IP" > /dev/null 2>&1; then
  echo -e "   OK Le serveur repond au ping"
else
  echo -e "   KO Pas de reponse au ping"
  echo "   Verifier le reseau et l IP"
fi

# 2. Port Ollama
echo ""
echo "2. Port Ollama ($OLLAMA_PORT)..."
if timeout 5 bash -c "</dev/tcp/$SERVER_IP/$OLLAMA_PORT" 2>/dev/null; then
  echo -e "   OK Port $OLLAMA_PORT ouvert"
  if curl -fsS "http://$SERVER_IP:$OLLAMA_PORT/api/tags" -m 5 2>/dev/null | head -c 200; then
    echo ""
    echo -e "   OK API Ollama accessible"
  else
    echo -e "   WARN Port ouvert mais l API ne repond pas"
  fi
else
  echo -e "   KO Port $OLLAMA_PORT inaccessible"
  echo "   Verifier : sudo ufw status sur le serveur"
fi

# 3. Port SearXNG
echo ""
echo "3. Port SearXNG ($SEARXNG_PORT)..."
if timeout 5 bash -c "</dev/tcp/$SERVER_IP/$SEARXNG_PORT" 2>/dev/null; then
  echo -e "   OK Port $SEARXNG_PORT ouvert"
  if curl -fsS "http://$SERVER_IP:$SEARXNG_PORT/search?q=test&format=json" -m 5 2>/dev/null | head -c 200; then
    echo ""
    echo -e "   OK API SearXNG accessible"
  else
    echo -e "   WARN Port ouvert mais l API ne repond pas"
  fi
else
  echo -e "   KO Port $SEARXNG_PORT inaccessible"
  echo "   Verifier : sudo ufw status sur le serveur"
fi

# 4. Latence
echo ""
echo "4. Latence reseau..."
LATENCY=$(ping -c 5 -W 2 "$SERVER_IP" 2>/dev/null | tail -1 | awk -F'/' '{print $5}')
if [ -n "$LATENCY" ]; then
  echo "   Latence moyenne : ${LATENCY} ms"
  if (( $(echo "$LATENCY < 50" | bc -l) )); then
    echo -e "   OK Excellente (LAN typique)"
  elif (( $(echo "$LATENCY < 200" | bc -l) )); then
    echo -e "   WARN Correcte mais un peu elevee"
  else
    echo -e "   KO Latence elevee -- verifier le reseau"
  fi
fi

echo ""
echo "==========================================="
echo "Si tous les tests sont verts, lance :"
echo "  Parametres HA > Integrations > Ajouter"
echo "  > Gemma Local Assistant"
echo "  > URL Ollama : http://$SERVER_IP:$OLLAMA_PORT"
echo "  > URL SearXNG : http://$SERVER_IP:$SEARXNG_PORT"
echo "==========================================="
