# ChaldeaTranslator HTTP API

## Estado y alcance

La API ofrece una interfaz HTTP para el nucleo Python. La version inicial
incluye:

- `GET /health`: estado del proceso y configuracion basica.
- `POST /v1/translate`: traduccion con el perfil y el glosario Fate.
- Validacion posterior de terminologia y estructura.
- Autenticacion mediante la cabecera `X-API-Key`.

La API **no incluye ni descarga un modelo**. El motor se conecta a un servidor
`llama.cpp` que exponga la API compatible con OpenAI.

## Desarrollo

Python 3.12 es la version recomendada.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configura una clave aleatoria para las solicitudes:

```bash
export CHALDEA_API_KEY="reemplaza-por-una-clave-larga-y-aleatoria"
```

Cuando exista un servidor llama.cpp compatible, configura su URL:

```bash
export CHALDEA_LLAMACPP_URL="http://127.0.0.1:8080"
export CHALDEA_MODEL_NAME="local-model"
```

Inicia la API:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Documentacion interactiva: `/docs`. Estado: `/health`.

## Ejemplo de solicitud

```bash
curl -X POST "http://127.0.0.1:8000/v1/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $CHALDEA_API_KEY" \
  -d '{
    "text": "Master, use your Command Spell.",
    "content_type": "dialogue",
    "context": "A scene from Fate/Grand Order",
    "character": "Ritsuka"
  }'
```

## Despliegue

Para un despliegue publico, configura `CHALDEA_API_KEY` como variable secreta
del servicio. No la guardes en Git ni en el codigo cliente.

Configura tambien `CHALDEA_LLAMACPP_URL` para que apunte a un servidor de
inferencia accesible desde el servicio. Una URL como `127.0.0.1` dentro de
Render apunta al propio contenedor de Render; no conecta automaticamente con
el telefono ni con un servidor externo.

No se debe desplegar el endpoint de traduccion sin una clave API. La API
responde con error 503 si falta `CHALDEA_API_KEY` o si el motor no esta
configurado/disponible.

## Variables de entorno

| Variable | Obligatoria | Descripcion |
|---|---|---|
| `CHALDEA_API_KEY` | Si, para traducir | Secreto para autenticar solicitudes |
| `CHALDEA_LLAMACPP_URL` | Si, para traducir | URL base del servidor llama.cpp |
| `CHALDEA_MODEL_NAME` | No | Nombre de modelo esperado por el servidor |
| `CHALDEA_ENGINE_TIMEOUT` | No | Tiempo maximo de espera en segundos (120 por defecto) |

El endpoint de salud no expone valores secretos.
