# Desarrollo y ejecución local

## Android con Termux (sin nube)

El modo local ejecuta dos procesos dentro de Termux:

1. `llama-server` carga el modelo GGUF y ofrece la API compatible con OpenAI en `127.0.0.1:8080`.
2. FastAPI conecta con ese motor y expone ChaldeaTranslator en `127.0.0.1:8000`.

Todo permanece en el teléfono. Los puertos están vinculados a loopback, no a `0.0.0.0`, por lo que no se publica el servicio a otros dispositivos de la red.

### Requisitos

- Termux actualizado, instalado desde una fuente oficial del proyecto.
- Android ARM64 (aarch64).
- Espacio libre suficiente para clonar y compilar llama.cpp, instalar dependencias y almacenar el GGUF. La compilación puede necesitar varios GB temporales.
- Un modelo GGUF compatible con llama.cpp. El repositorio no lo descarga ni incluye sus pesos.

### Instalación

Desde el directorio donde clonaste este repositorio:

```bash
bash scripts/termux-setup.sh
```

El script instala Clang, CMake, Git, Python, curl y `libandroid-spawn`; clona llama.cpp si aún no existe; compila el objetivo `llama-server` con OpenMP desactivado y prepara un entorno virtual Python. No instala servicios remotos ni descarga un modelo.

### Modelo e inicio

Guarda el GGUF en el directorio privado de Termux, por ejemplo `$HOME/models/`. Después:

```bash
CHALDEA_MODEL_PATH="$HOME/models/TU_MODELO.gguf" bash scripts/termux-local.sh start
```

El nombre `TU_MODELO.gguf` es un marcador: reemplázalo por el nombre real del archivo. Puedes ajustar el consumo de memoria con variables de entorno:

- `CHALDEA_CTX_SIZE=2048` (predeterminado; bajar a 1024 si falta memoria).
- `CHALDEA_THREADS=4` (predeterminado; ajustable).
- `CHALDEA_BUILD_JOBS=2` (hilos de compilación; usa 1 si el teléfono se queda sin memoria).
- `CHALDEA_MODEL_PATH` para la ruta exacta del modelo.

### Control y diagnóstico

```bash
bash scripts/termux-local.sh status
bash scripts/termux-local.sh logs
bash scripts/termux-local.sh stop
```

La clave de la API se genera localmente y se guarda con permisos privados en `$HOME/.config/chaldeatranslator/api.key`. No la publiques ni la subas a Git. Los registros quedan en `$HOME/.local/share/chaldeatranslator/logs/`.

La API y llama.cpp se enlazan a `127.0.0.1` exclusivamente. No cambies el host a `0.0.0.0` para usarlo desde Internet; eso requiere autenticación, TLS, controles de acceso y una revisión de seguridad adicional.

### Límites reales

- El modelo se ejecuta en CPU por defecto; no se promete aceleración GPU en Termux.
- La velocidad depende del modelo, cuantización, temperatura y memoria disponible.
- Android puede detener procesos en segundo plano por batería o memoria. Mantén Termux abierto mientras traduces.
- Una compilación local no garantiza que cualquier GGUF funcione. Revisa la licencia, formato y requisitos del modelo antes de descargarlo.
- OCR contextual y memoria persistente todavía no forman parte del modo local.

## Entorno remoto opcional

GitHub Codespaces permite editar y ejecutar pruebas, pero no es necesario para la inferencia local. Su disponibilidad depende de la cuota gratuita de la cuenta. No habilites facturación ni agregues un método de pago para este proyecto.
