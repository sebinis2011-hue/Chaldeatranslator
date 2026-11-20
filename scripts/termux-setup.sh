#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA_DIR="${CHALDEA_LLAMA_DIR:-$HOME/llama.cpp}"
JOBS="${CHALDEA_BUILD_JOBS:-2}"

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

command -v pkg >/dev/null 2>&1 || fail "Este instalador debe ejecutarse dentro de Termux."
[ "$(uname -m)" = "aarch64" ] || fail "Se requiere Android ARM64 (aarch64); arquitectura detectada: $(uname -m)."

echo "== ChaldeaTranslator: preparación local para Termux =="
echo "No se instalará ningún servicio de nube ni se descargará un modelo de IA."

pkg update
pkg install -y clang cmake git make pkg-config python curl libandroid-spawn

if [ ! -d "$LLAMA_DIR/.git" ]; then
  if [ -e "$LLAMA_DIR" ]; then
    fail "$LLAMA_DIR existe pero no es un repositorio Git. Define CHALDEA_LLAMA_DIR con otra ruta."
  fi
  git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LLAMA_DIR"
else
  echo "Usando llama.cpp existente en $LLAMA_DIR"
fi

echo "== Compilando llama-server para el propio Android =="
cmake -S "$LLAMA_DIR" -B "$LLAMA_DIR/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DGGML_OPENMP=OFF \
  -DLLAMA_BUILD_SERVER=ON \
  -DLLAMA_BUILD_TESTS=OFF \
  -DLLAMA_BUILD_EXAMPLES=ON \
  -DLLAMA_CURL=OFF

cmake --build "$LLAMA_DIR/build" --config Release --target llama-server --parallel "$JOBS"

[ -x "$LLAMA_DIR/build/bin/llama-server" ] || fail "La compilación terminó, pero no se encontró llama-server."

echo "== Preparando el entorno Python =="
python -m venv "$PROJECT_ROOT/.venv"
"$PROJECT_ROOT/.venv/bin/python" -m pip install --upgrade pip
"$PROJECT_ROOT/.venv/bin/python" -m pip install -r "$PROJECT_ROOT/requirements.txt"

mkdir -p "$HOME/models"
echo
echo "Preparación terminada."
echo "Ejecutable: $LLAMA_DIR/build/bin/llama-server"
echo "Coloca un modelo GGUF compatible en: $HOME/models/"
echo "Después ejecuta:"
echo "  CHALDEA_MODEL_PATH=$HOME/models/TU_MODELO.gguf bash $PROJECT_ROOT/scripts/termux-local.sh start"
echo
echo "Nota: la compilación puede tardar y consumir bastante batería/almacenamiento."
