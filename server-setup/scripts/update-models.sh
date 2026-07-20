#!/usr/bin/env bash
# ============================================================================
#  update-models.sh
#  Met a jour Ollama et tous les modeles installes
# ============================================================================
set -euo pipefail

echo "Mise a jour d'Ollama..."
if command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Ollama n'est pas installe."
  exit 1
fi

echo ""
echo "Mise a jour des modeles..."
mapfile -t MODELS < <(ollama list | awk 'NR>1 {print $1}')
for model in "${MODELS[@]}"; do
  echo "  -> $model"
  ollama pull "$model"
done

echo ""
echo "Mise a jour terminee."
ollama list
