#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA_SERVER="${CHALDEA_LLAMA_SERVER:-$HOME/llama.cpp/build/bin/llama-server}"
MODEL="${CHALDEA_MODEL_PATH:-$HOME/models/Index-Translate-2B.Q4_K_M.gguf}"
ENGINE_PORT="${CHALDEA_ENGINE_PORT:-8080}"
API_PORT="${CHALDEA_API_PORT:-8000}"
CTX_SIZE="${CHALDEA_CTX_SIZE:-2048}"
THREADS="${CHALDEA_THREADS:-4}"
STATE_DIR="$HOME/.local/state/chaldeatranslator"
CONFIG_DIR="$HOME/.config/chaldeatranslator"
LOG_DIR="$HOME/.local/share/chaldeatranslator/logs"
API_KEY_FILE="$CONFIG_DIR/api.key"
ENGINE_PID="$STATE_DIR/llama-server.pid"
API_PID="$STATE_DIR/api.pid"
VENV="$PROJECT_ROOT/.venv"
UVICORN="$VENV/bin/uvicorn"

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

is_running() {
  [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null
}

stop_one() {
  local pid_file="$1"
  local label="$2"
  if is_running "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 1
    done
    kill -9 "$pid" 2>/dev/null || true
    echo "$label detenido."
  fi
  rm -f "$pid_file"
}

case "${1:-}" in
  start)
    command -v curl >/dev/null 2>&1 || fail "Instala curl con: pkg install curl"
    [ -x "$LLAMA_SERVER" ] || fail "No se encuentra llama-server. Ejecuta scripts/termux-setup.sh primero."
    [ -f "$MODEL" ] || fail "No se encuentra el modelo GGUF: $MODEL. Define CHALDEA_MODEL_PATH."
    [ -x "$UVICORN" ] || fail "No existe el entorno Python. Ejecuta scripts/termux-setup.sh primero."
    mkdir -p "$STATE_DIR" "$CONFIG_DIR" "$LOG_DIR"
    chmod 700 "$CONFIG_DIR" "$STATE_DIR" "$LOG_DIR"
    umask 077
    if [ ! -s "$API_KEY_FILE" ]; then
      "$VENV/bin/python" -c 'import secrets; print(secrets.token_urlsafe(32))' > "$API_KEY_FILE"
      chmod 600 "$API_KEY_FILE"
    fi
    export CHALDEA_API_KEY
    CHALDEA_API_KEY="$(cat "$API_KEY_FILE")"
    export CHALDEA_LLAMACPP_URL="http://127.0.0.1:$ENGINE_PORT"
    export CHALDEA_ENGINE_TIMEOUT="${CHALDEA_ENGINE_TIMEOUT:-180}"

    if is_running "$ENGINE_PID"; then
      echo "llama-server ya está iniciado."
    else
      rm -f "$ENGINE_PID"
      echo "Iniciando llama.cpp (contexto=$CTX_SIZE, hilos=$THREADS)..."
      nohup "$LLAMA_SERVER" -m "$MODEL" \
        --host 127.0.0.1 --port "$ENGINE_PORT" \
        --ctx-size "$CTX_SIZE" --threads "$THREADS" --parallel 1 \
        >"$LOG_DIR/llama-server.log" 2>&1 &
      echo $! > "$ENGINE_PID"
    fi

    echo "Esperando a que el modelo cargue..."
    READY=0
    for _ in $(seq 1 90); do
      if ! is_running "$ENGINE_PID"; then
        tail -n 35 "$LOG_DIR/llama-server.log" >&2 || true
        fail "llama-server terminó durante el arranque."
      fi
      if curl -fsS "http://127.0.0.1:$ENGINE_PORT/health" >/dev/null 2>&1; then
        READY=1
        break
      fi
      sleep 2
    done
    [ "$READY" -eq 1 ] || fail "El modelo no respondió en 180 segundos. Revisa $LOG_DIR/llama-server.log."

    if is_running "$API_PID"; then
      echo "La API ya está iniciada."
    else
      rm -f "$API_PID"
      echo "Iniciando API local..."
      (
        cd "$PROJECT_ROOT"
        export CHALDEA_API_KEY CHALDEA_LLAMACPP_URL CHALDEA_ENGINE_TIMEOUT
        nohup "$UVICORN" api.main:app --host 127.0.0.1 --port "$API_PORT" --workers 1 \
          >"$LOG_DIR/api.log" 2>&1 &
        echo $! > "$API_PID"
      )
    fi

    API_READY=0
    for _ in $(seq 1 20); do
      if ! is_running "$API_PID"; then
        tail -n 35 "$LOG_DIR/api.log" >&2 || true
        fail "La API terminó durante el arranque."
      fi
      if curl -fsS "http://127.0.0.1:$API_PORT/health/ready" >/dev/null 2>&1; then
        API_READY=1
        break
      fi
      sleep 1
    done
    [ "$API_READY" -eq 1 ] || fail "La API no quedó lista. Revisa $LOG_DIR/api.log."

    echo
    echo "ChaldeaTranslator está listo SOLO en este teléfono."
    echo "API: http://127.0.0.1:$API_PORT"
    echo "Documentación: http://127.0.0.1:$API_PORT/docs"
    echo "Clave local guardada en: $API_KEY_FILE"
    echo "Para copiarla: cat $API_KEY_FILE"
    echo "Logs: $LOG_DIR"
    ;;
  stop)
    stop_one "$API_PID" "API"
    stop_one "$ENGINE_PID" "llama-server"
    ;;
  status)
    if is_running "$ENGINE_PID"; then
      echo "llama-server: proceso activo"
    else
      echo "llama-server: detenido"
    fi
    if is_running "$API_PID"; then
      echo "API: proceso activo"
    else
      echo "API: detenida"
    fi
    curl -fsS "http://127.0.0.1:$API_PORT/health" 2>/dev/null || true
    echo
    ;;
  logs)
    mkdir -p "$LOG_DIR"
    touch "$LOG_DIR/llama-server.log" "$LOG_DIR/api.log"
    tail -n 40 -f "$LOG_DIR/llama-server.log" "$LOG_DIR/api.log"
    ;;
  *)
    echo "Uso: bash scripts/termux-local.sh {start|stop|status|logs}"
    exit 2
    ;;
esac
