# ChaldeaTranslator HTTP API

## Estado y alcance

La API ofrece una interfaz HTTP para el núcleo Python:

- `GET /health`: comprueba que el proceso API está vivo.
- `GET /health/ready`: comprueba que llama.cpp responde.
- `POST /v1/translate`: traduce con el perfil y el glosario Fate.
- Valida la terminología y la estructura de la traducción.
- Protege las solicitudes de traducción mediante `X-API-Key`.

La API no incluye ni descarga un modelo GGUF. Se conecta a un servidor llama.cpp compatible con OpenAI.

## Modo local en Termux

El script `scripts/termux-local.sh` inicia llama.cpp en el puerto 8080 y FastAPI en el puerto 8000, ambos enlazados únicamente a `127.0.0.1`. Consulta [la guía de Termux](DEVELOPMENT_ENVIRONMENT.md) para compilar e iniciar el sistema.

La clave se genera en el propio dispositivo y se guarda en `$HOME/.config/chaldeatranslator/api.key`. No la guardes en Git ni la compartas.

## Solicitud de traducción

Con los procesos locales iniciados:

```bash
API_KEY="$(cat "$HOME/.config/chaldeatranslator/api.key")"
curl -X POST "http://127.0.0.1:8000/v1/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "Master, use your Command Spell.",
    "content_type": "dialogue",
    "context": "A scene from Fate/Grand Order",
    "character": "Ritsuka"
  }'
```

Documentación interactiva: `http://127.0.0.1:8000/docs`.

## Configuración avanzada

- `CHALDEA_API_KEY`: clave necesaria para traducir.
- `CHALDEA_LLAMACPP_URL`: URL base del motor llama.cpp.
- `CHALDEA_MODEL_NAME`: nombre lógico del modelo.
- `CHALDEA_ENGINE_TIMEOUT`: espera máxima de inferencia en segundos.

En modo local, el lanzador configura `CHALDEA_LLAMACPP_URL=http://127.0.0.1:8080` automáticamente.

No expongas la API en una interfaz pública ni cambies el host a `0.0.0.0` sin implementar controles de acceso y TLS.
