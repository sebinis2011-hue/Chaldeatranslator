# ChaldeaTranslator HTTP API

## Estado y alcance

La API expone el núcleo Python:

- `GET /health`: comprueba que el proceso API está vivo y muestra qué motores están configurados.
- `GET /health/ready`: comprueba el motor local o valida que exista al menos un proveedor cloud configurado. No envía texto al proveedor.
- `POST /v1/translate`: traduce con el perfil y el glosario Fate.
- Valida la terminología y la estructura de la traducción.
- Protege las solicitudes mediante `X-API-Key`.

La API puede usar llama.cpp local o proveedores cloud compatibles con OpenAI Chat Completions.

## Modos de motor y privacidad

El cuerpo de `POST /v1/translate` admite estos campos adicionales:

| Campo | Valores | Predeterminado | Descripción |
|---|---|---|---|
| `engine_mode` | `local`, `cloud`, `auto` | `local` | Motor que se debe usar. |
| `provider` | ID configurado | ninguno | Selecciona un proveedor cloud concreto. |
| `allow_cloud` | boolean | `false` | Consentimiento explícito para enviar el prompt a cloud. |

Reglas:

1. `local` nunca llama a un proveedor cloud.
2. `cloud` falla si `allow_cloud` no es `true`.
3. `auto` intenta primero local. Solo usa cloud si local falla y `allow_cloud` es `true`.
4. Si no se especifica `provider`, se selecciona el primer ID en orden alfabético. Es preferible enviar el ID explícitamente.

La interfaz de usuario debe pedir confirmación antes de activar `allow_cloud`. El prompt enviado incluye el texto original, el contexto narrativo, el personaje y las instrucciones/terminología relevante del glosario. No se debe presentar el modo cloud como privado-local.

## Ejemplo local

```bash
API_KEY="$(cat "$HOME/.config/chaldeatranslator/api.key")"
curl -X POST "http://127.0.0.1:8000/v1/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "Master, use your Command Spell.",
    "content_type": "dialogue",
    "context": "A scene from Fate/Grand Order",
    "character": "Ritsuka",
    "engine_mode": "local"
  }'
```

## Ejemplo cloud con consentimiento

```bash
curl -X POST "http://127.0.0.1:8000/v1/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "Master, use your Command Spell.",
    "engine_mode": "cloud",
    "provider": "free-provider-example",
    "allow_cloud": true
  }'
```

No copies el ejemplo cloud sin comprender que el texto y el contexto se envían al proveedor remoto.

## Configuración de proveedores

Copia `config/cloud-providers.example.json` a `config/cloud-providers.json` y define:

- `id`: identificador del proveedor.
- `tier`: etiqueta informativa `free` o `paid`.
- `base_url`: URL base de la API.
- `model`: identificador del modelo.
- `api_key_env`: nombre de la variable de entorno que guarda la clave.
- `api_key_required`: permite omitir la clave solo si el servicio lo admite.
- `chat_completions_path`: ruta configurable, por defecto `/chat/completions`.
- `timeout`: tiempo máximo en segundos.

Exporta `CHALDEA_CLOUD_PROVIDERS_FILE` con la ruta del archivo. Alternativamente, define `CHALDEA_CLOUD_PROVIDERS` con la lista JSON completa. Nunca guardes claves en ese archivo; usa variables de entorno referenciadas por `api_key_env`.

La etiqueta de nivel gratuito es descriptiva y no verifica precios, cuotas ni requisitos de facturación. Verifica las condiciones de cada proveedor. El adaptador genérico solo funciona con endpoints compatibles con OpenAI Chat Completions.

## Modo local en Termux

El script `scripts/termux-local.sh` inicia llama.cpp en el puerto 8080 y FastAPI en el puerto 8000, ambos enlazados únicamente a `127.0.0.1`. Consulta [la guía de Termux](DEVELOPMENT_ENVIRONMENT.md).

La clave local se genera en el propio dispositivo y se guarda en `$HOME/.config/chaldeatranslator/api.key`. No la guardes en Git ni la compartas.

Documentación interactiva: `http://127.0.0.1:8000/docs`.

## Variables de entorno

- `CHALDEA_API_KEY`: clave necesaria para traducir.
- `CHALDEA_LLAMACPP_URL`: URL base del motor llama.cpp.
- `CHALDEA_MODEL_NAME`: nombre lógico del modelo local.
- `CHALDEA_ENGINE_TIMEOUT`: espera máxima de inferencia.
- `CHALDEA_CLOUD_PROVIDERS_FILE`: ruta del archivo JSON de proveedores.
- `CHALDEA_CLOUD_PROVIDERS`: alternativa en línea al archivo JSON.

No expongas la API en una interfaz pública ni cambies el host a `0.0.0.0` sin implementar controles de acceso y TLS.
