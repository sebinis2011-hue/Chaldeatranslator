#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

MODEL="${CHALDEA_MODEL_PATH:-$HOME/.cache/huggingface/hub/models--IndexTeam--Index-Translate-2B-GGUF/snapshots/3a0eca6ce931d88d00614d427ab3ed8ff0743902/Index-Translate-2B.Q4_K_M.gguf}"
LLAMA_CLI="${CHALDEA_LLAMA_CLI:-$HOME/llama.cpp/build/bin/llama-cli}"

if [ ! -f "$MODEL" ]; then
    echo "Error: no se encuentra el modelo: $MODEL" >&2
    exit 1
fi

if [ ! -x "$LLAMA_CLI" ]; then
    echo "Error: llama-cli no existe o no es ejecutable: $LLAMA_CLI" >&2
    exit 1
fi

echo "================================"
echo "     CHALDEA TRANSLATOR"
echo "================================"
echo "Introduce el texto que deseas traducir."
echo "Escribe FIN en una línea para terminar."
echo

INPUT=""

while IFS= read -r LINE; do
    [ "$LINE" = "FIN" ] && break
    INPUT+="$LINE"$'\n'
done

if [ -z "${INPUT//[[:space:]]/}" ]; then
    echo "No se introdujo ningún texto." >&2
    exit 1
fi

PROMPT="Traduce el siguiente texto al español latino natural. Conserva los nombres propios y la terminología de Fate: Master, Servant, Noble Phantasm y Command Spell. Traduce 聖杯戦争 como Guerra del Santo Grial. Respeta la personalidad y las emociones de los personajes. Traduce todo el texto sin omitir ni repetir frases. Devuelve solamente la traducción.

$INPUT"

exec "$LLAMA_CLI" \
    -m "$MODEL" \
    --jinja \
    --chat-template-kwargs '{"enable_thinking":false}' \
    --temp 0 \
    -c 2048 \
    -t 4 \
    -n 256 \
    -p "$PROMPT"
