# ChaldeaTranslator

Traductor literario para videojuegos y novelas visuales, con ejecución local y una API HTTP opcional.

## Estado del proyecto

La base actual incluye construcción de prompts, selección contextual de terminología Fate, validación terminológica y una API FastAPI que se comunica con un servidor llama.cpp compatible con la API de OpenAI.

La API y el motor de inferencia son componentes separados. El repositorio no incluye el modelo GGUF ni aloja un modelo de IA.

## Desarrollo y pruebas

- Python recomendado: 3.12.
- Instala las dependencias: `python -m pip install -r requirements.txt`.
- Comprueba la sintaxis: `python -m compileall -q api core tests`.
- Ejecuta las pruebas: `python -m unittest discover -s tests -v`.
- Consulta [el entorno de desarrollo cloud](docs/DEVELOPMENT_ENVIRONMENT.md).

GitHub Actions comprueba Python 3.12 y 3.13, consistencia de dependencias, sintaxis del script Termux y pruebas unitarias con cobertura de ramas.

## API HTTP

La API ofrece `GET /health`, `GET /health/ready` y `POST /v1/translate`.

Consulta [la documentación de la API](docs/API.md) para configurarla y conectar un servidor llama.cpp. Antes de habilitar traducciones, configura `CHALDEA_API_KEY` y `CHALDEA_LLAMACPP_URL` como variables de entorno; nunca guardes claves en el repositorio.

## Ejecución local

El script `chaldea-translator.sh` está orientado a Termux. Requiere un binario local de llama.cpp y un modelo GGUF compatible. Las rutas se pueden configurar mediante `CHALDEA_LLAMA_CLI` y `CHALDEA_MODEL_PATH`.

## Privacidad y costes

- No subas modelos GGUF, archivos de configuración privados, tokens, claves API ni historiales personales.
- El entorno de desarrollo cloud es opcional; utiliza solo la cuota gratuita disponible y no actives facturación.
- La API no proporciona inferencia gratuita por sí misma: necesita un servidor de modelo accesible.
- OCR contextual y memoria persistente deben considerarse funciones pendientes hasta que estén implementadas y probadas en el repositorio.
