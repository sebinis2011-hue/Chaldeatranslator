# ChaldeaTranslator

Traductor literario para videojuegos y novelas visuales, con ejecución local y una API HTTP opcional.

## Estado del proyecto

El núcleo incluye construcción de prompts, selección contextual de terminología Fate y validación terminológica. La API FastAPI puede enrutar solicitudes a un motor local llama.cpp o a proveedores cloud compatibles con el formato OpenAI Chat Completions.

La API y los motores de inferencia son componentes separados. El repositorio no incluye modelos GGUF ni aloja modelos de IA.

## Modos de ejecución

- **local:** usa llama.cpp en el dispositivo o servidor configurado. Es el modo predeterminado y no envía el texto a un proveedor cloud.
- **cloud:** usa el proveedor seleccionado. Requiere consentimiento explícito en cada solicitud mediante `allow_cloud: true`.
- **auto:** intenta primero el motor local. Solo puede recurrir a cloud si la solicitud también contiene `allow_cloud: true`.

El modo automático nunca debe habilitar el envío cloud por sí solo. La interfaz que consuma la API debe explicar qué texto saldrá del dispositivo y pedir confirmación antes de establecer `allow_cloud: true`.

## Proveedores cloud

Se admiten proveedores que implementen un endpoint compatible con OpenAI Chat Completions. Cada proveedor se configura de forma independiente en `config/cloud-providers.json`, usando como base el ejemplo:

```bash
cp config/cloud-providers.example.json config/cloud-providers.json
export CHALDEA_CLOUD_PROVIDERS_FILE="$PWD/config/cloud-providers.json"
```

En cada entrada configura:

- `id`: identificador que se envía en el campo `provider`.
- `tier`: etiqueta informativa, por ejemplo `free` o `paid`; no cambia el comportamiento técnico.
- `base_url` y `model`: endpoint y nombre exacto del modelo del proveedor.
- `api_key_env`: nombre de la variable de entorno que contiene la clave. No escribas la clave directamente en el JSON.
- `api_key_required`: usa `false` solo si el proveedor realmente permite solicitudes sin clave.
- `chat_completions_path`: ruta del endpoint, si no es `/chat/completions`.

Puedes registrar proveedores gratuitos y de pago a la vez. La etiqueta `free` no garantiza que el servicio sea gratuito, que no tenga límites o que no solicite verificación de pago: comprueba las condiciones del proveedor antes de usarlo. El adaptador inicial cubre la interfaz OpenAI-compatible; los proveedores con APIs distintas necesitarán adaptadores específicos.

Las claves se cargan desde variables de entorno, no se devuelven en `/health` y no deben subirse a Git. No configures servicios que requieran tarjeta o pagos si no tienes autorización y supervisión para ello.

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

La compilación se realiza en el teléfono y puede tardar, calentar el dispositivo y consumir varios GB temporales. El modelo no se descarga automáticamente.

## Desarrollo y pruebas

- Python recomendado: 3.12.
- Instala las dependencias: `python -m pip install -r requirements.txt`.
- Comprueba la sintaxis: `python -m compileall -q api core tests`.
- Ejecuta las pruebas: `python -m unittest discover -s tests -v`.
- GitHub Actions valida Python 3.12 y 3.13, dependencias, scripts Bash y pruebas unitarias.

## API HTTP

La API ofrece `GET /health`, `GET /health/ready` y `POST /v1/translate`. Consulta [la documentación de la API](docs/API.md).

## Privacidad y costes

- El modo local no requiere alojamiento ni inferencia de pago.
- Cloud envía el prompt completo (texto, contexto y términos relevantes del glosario) al proveedor seleccionado.
- No hay fallback cloud silencioso: requiere `allow_cloud: true` en esa solicitud.
- No subas modelos GGUF, archivos de configuración privados, claves API ni historiales personales.
- Codespaces es opcional; úsalo solo dentro de la cuota gratuita y sin activar facturación.
- OCR contextual y memoria persistente siguen pendientes de implementación y validación.
