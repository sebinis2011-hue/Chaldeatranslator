# ChaldeaTranslator

Traductor literario para videojuegos y novelas visuales, con ejecución local y una API HTTP opcional.

## Estado del proyecto

La base incluye construcción de prompts, selección contextual de terminología Fate, validación terminológica y una API FastAPI que se comunica con un servidor llama.cpp compatible con la API de OpenAI.

La API y el motor de inferencia son componentes separados. El repositorio no incluye el modelo GGUF ni aloja un modelo de IA.

## Ejecutar en Android con Termux

El modo local permite ejecutar llama.cpp y la API en el mismo teléfono, sin Render ni un servidor de inferencia externo.

1. Clona este repositorio dentro del almacenamiento privado de Termux.
2. Ejecuta `bash scripts/termux-setup.sh` para instalar herramientas, compilar `llama-server` y preparar el entorno Python.
3. Coloca un modelo GGUF compatible en `$HOME/models/`.
4. Inicia ambos procesos con:

```bash
CHALDEA_MODEL_PATH="$HOME/models/TU_MODELO.gguf" bash scripts/termux-local.sh start
```

El servidor y la API escuchan únicamente en `127.0.0.1`; no se exponen a la red Wi-Fi. Para detenerlos, usa `bash scripts/termux-local.sh stop`. Consulta [la guía detallada de Termux](docs/DEVELOPMENT_ENVIRONMENT.md).

La compilación se realiza en el teléfono y puede tardar, calentar el dispositivo y consumir varios GB temporales. Mantén el teléfono ventilado, conectado a corriente si es seguro y cierra otras aplicaciones pesadas. El modelo no se descarga automáticamente.

## Desarrollo y pruebas

- Python recomendado: 3.12.
- Instala las dependencias: `python -m pip install -r requirements.txt`.
- Comprueba la sintaxis: `python -m compileall -q api core tests`.
- Ejecuta las pruebas: `python -m unittest discover -s tests -v`.
- GitHub Actions valida Python 3.12 y 3.13, dependencias, scripts Bash y pruebas unitarias.

## API HTTP

La API ofrece `GET /health`, `GET /health/ready` y `POST /v1/translate`. Consulta [la documentación de la API](docs/API.md).

## Privacidad y costes

- El modo Termux es local y no requiere alojamiento ni inferencia de pago.
- No subas modelos GGUF, archivos de configuración privados, claves API ni historiales personales.
- Codespaces es opcional; úsalo solo dentro de la cuota gratuita y sin activar facturación.
- OCR contextual y memoria persistente siguen pendientes de implementación y validación.

## Aplicación Android nativa (en desarrollo)

La rama `feature/native-llama-engine` amplía la aplicación Kotlin + Jetpack Compose con una primera integración nativa, separada del modo Termux:

- Proyecto Gradle Android con `minSdk 26`, `compileSdk 35`, NDK fijado y ABI inicial `arm64-v8a`.
- llama.cpp `b5401` integrado por CMake/JNI para inferencia CPU.
- Catálogo inicial Qwen3 1.7B Q4_K_M con revisión, tamaño y SHA-256 fijados.
- Descarga explícita reanudable con comprobación de tamaño y SHA-256 antes de activar el GGUF.
- Pantalla inicial para descargar, cargar el modelo y ejecutar traducción local.
- Pruebas unitarias del catálogo y CI que compila el motor nativo.

**Estado real:** la ruta de inferencia nativa ya está implementada en código, pero su compilación y funcionamiento todavía deben confirmarse en CI y en el Vivo Y39 5G. La pantalla usa un prompt inicial y aún no está conectada completamente con perfiles, construcción de prompts, glosario contextual y validador Kotlin. No considerar todavía una versión estable. Consulta [el estado de integración nativa](docs/NATIVE_RUNTIME_STATUS.md).

Para abrirla, importa la raíz del repositorio en Android Studio y selecciona el módulo `:app`. La CI usa Gradle 8.9 y JDK 17.
