# Selección inicial del modelo local

Estado: **selección aprobada; artefacto pendiente de verificación antes de habilitar descargas**.

## Decisión

- Modelo base: Qwen3-1.7B.
- Cuantización objetivo: GGUF Q4_K_M.
- Archivo candidato: `Qwen_Qwen3-1.7B-Q4_K_M.gguf`.
- Repositorio candidato del GGUF: `bartowski/Qwen_Qwen3-1.7B-GGUF`.
- Tamaño publicado por el repositorio candidato: aproximadamente 1.28 GB (el tamaño exacto debe leerse de la revisión concreta del archivo antes de descargar).
- Runtime objetivo: llama.cpp nativo mediante JNI, CPU ARM64 (`arm64-v8a`) como primera ABI.
- El GGUF se descarga por separado; no se incrusta en el APK.
- La app debe permitir añadir y cambiar modelos sin recompilarla.

## Procedencia y licencia

El modelo base oficial es [Qwen/Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B). La organización Qwen declara licencia Apache 2.0 para sus modelos abiertos.

El GGUF Q4_K_M candidato está en [bartowski/Qwen_Qwen3-1.7B-GGUF](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF), no en el repositorio oficial de Qwen. El cuantizador indica que se generó con llama.cpp b5200 y una importance matrix. Debemos conservar esta atribución y revisar los metadatos/licencia del repositorio y del archivo concreto antes de distribuirlo.

Referencias técnicas:
- [Qwen3 oficial](https://github.com/QwenLM/Qwen3): recomienda llama.cpp b5401 o posterior para soporte completo de Qwen3.
- [GGUF candidato Q4_K_M](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF).
- [Modelo base oficial](https://huggingface.co/Qwen/Qwen3-1.7B).

## Puerta de seguridad: no inventar hashes

No registrar una URL de descarga activa ni un SHA-256 supuesto. Antes de publicar el modelo en el catálogo instalable, CI o una revisión controlada debe obtener de la revisión exacta de Hugging Face:
1. ID inmutable de revisión (commit).
2. Nombre exacto del archivo.
3. Tamaño exacto en bytes.
4. SHA-256 del archivo completo, obtenido de metadatos fiables del repositorio o calculado sobre el artefacto descargado.
5. Licencia y atribución aplicables al modelo y a la cuantización.

La aplicación debe rechazar un manifiesto incompleto. El hash no puede descargarse del mismo endpoint mutable que entrega el GGUF sin una raíz de confianza fijada en la app.

## Perfil inicial conservador

El contexto máximo anunciado por el modelo no es un objetivo de configuración para el teléfono. La primera configuración de pruebas debe comenzar con:
- contexto: 2,048 tokens; probar 1,024 si la memoria es insuficiente;
- batch pequeño;
- 2 hilos como punto de partida, después medir 2–4;
- un único modelo/contexto nativo activo;
- generación fuera del hilo principal;
- cancelación y liberación explícitas;
- sin GPU/Vulkan hasta verificar soporte real en el dispositivo.

Estos valores son hipótesis iniciales de perfil, no promesas de rendimiento. El consumo real incluye pesos, KV cache, buffers y memoria de la aplicación.

## Catálogo intercambiable

El modelo debe identificarse por un ID estable, no por el nombre visible ni por una ruta fija. Cada entrada futura del catálogo debe declarar como mínimo:
- ID, nombre y descripción;
- proveedor y repositorio;
- revisión inmutable;
- URL HTTPS permitida;
- nombre de archivo y tamaño exacto;
- SHA-256 fijado;
- licencia y atribución;
- formato GGUF y arquitectura compatible;
- contexto recomendado y perfil de memoria;
- versión mínima del runtime llama.cpp.

El gestor debe descargar a `.part`, reanudar solo si Range/ETag son coherentes, verificar tamaño y hash, y activar mediante renombrado atómico. El modelo activo anterior se conserva hasta que el nuevo cargue correctamente; si falla, se revierte.

## Validación antes de recomendarlo como modelo definitivo

Qwen3-1.7B Q4_K_M es el primer candidato aprobado para integrar, no un resultado de benchmark. Compararemos con al menos un candidato mayor/alternativo usando un conjunto de textos Fate:
- precisión de terminología y glosario;
- español latino natural;
- preservación de nombres, habilidades, títulos y formato;
- consistencia de voz/personaje;
- alucinaciones, omisiones y repeticiones;
- latencia, RAM máxima, temperatura y batería en el Vivo Y39 5G.

No declarar el modelo óptimo hasta ejecutar esas pruebas en el dispositivo real.
