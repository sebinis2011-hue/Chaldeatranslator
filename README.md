# ChaldeaTranslator

Traductor literario multilingue para videojuegos y novelas visuales, con
ejecucion local, OCR contextual y memoria de traduccion.

## Desarrollo

- Python recomendado: 3.12.
- Instala dependencias: `pip install -r requirements.txt`.
- Ejecuta pruebas: `python -m unittest discover -s tests -v`.
- Consulta [el entorno de desarrollo cloud](docs/DEVELOPMENT_ENVIRONMENT.md).

## API HTTP

La primera API usa FastAPI y un adaptador para un servidor llama.cpp compatible
con OpenAI. La API no descarga ni aloja el modelo.

Consulta [docs/API.md](docs/API.md) para instalar, configurar y ejecutar el
servidor, protegerlo con una clave y conectar el motor de inferencia.

El modelo GGUF y el servidor llama.cpp siguen siendo componentes separados.
