# ChaldeaTranslator: Android nativo independiente

Estado: diseño técnico inicial; **no compilar todavía**.

## Objetivo

Entregar una APK Android instalable que traduzca localmente con un modelo GGUF, sin Termux, Python, servidor HTTP local ni cuenta cloud. Internet se usa solo para descargar la aplicación, sus componentes/modelos y actualizaciones. Una vez instalado el modelo, la traducción debe funcionar sin conexión.

## Decisión de arquitectura

- UI: Kotlin + Jetpack Compose.
- Capa de aplicación: ViewModel + Kotlin Coroutines/Flow.
- Persistencia de preferencias e historial: DataStore y Room, con historial desactivado inicialmente hasta definir retención/exportación.
- Motor: llama.cpp embebido como biblioteca nativa C/C++ compilada con Android NDK y CMake.
- Frontera nativa: JNI pequeña y versionada; Kotlin no debe conocer structs internos de llama.cpp.
- Núcleo literario: portar a Kotlin el constructor de prompts, selección del glosario Fate y validadores Python actuales. Mantener pruebas de paridad con fixtures del proyecto.
- Transporte: cliente HTTP dentro de la app para descargas; no levantar FastAPI ni un servidor localhost.
- Modelo: GGUF en almacenamiento privado de la app; carga desde ruta local con mmap cuando el motor y el sistema lo permitan.

## Reutilización del repositorio actual

| Componente actual | Decisión |
|---|---|
| `core/prompts.py` | Portar reglas y perfiles a Kotlin; conservar fixtures y pruebas de paridad. |
| `core/validator.py` | Portar reglas de terminología/estructura a Kotlin y comparar resultados con pruebas Python. |
| `glossary/fate.json` | Reutilizar el JSON como recurso versionado; validar esquema y versión al cargar. |
| `api/main.py` | No ejecutar en Android. Sus validaciones de entrada pasan a la capa de dominio. |
| `core/engine.py` | Sustituir el adaptador HTTP por una interfaz `InferenceEngine` implementada mediante JNI. |
| `scripts/termux-*.sh` | Mantener como modo de desarrollo legado hasta que la APK pase los criterios de aceptación. |
| Motor cloud del PR #4 | No forma parte del primer lanzamiento Android. No se enviará texto fuera del dispositivo en el modo local. |

## Capas y contratos

1. **presentation**: pantallas, estado de descarga, progreso, traducción y errores accionables.
2. **domain**: `TranslationRequest`, perfiles de contenido, constructor de prompt, glosario y validación.
3. **data**: catálogo de modelos, descarga, verificación, instalación atómica y preferencias.
4. **inference**: interfaz Kotlin `InferenceEngine`; implementación JNI; gestión explícita de carga, generación, cancelación y liberación.
5. **native**: llama.cpp fijado a un commit/tag revisado; CMake produce bibliotecas compartidas para `arm64-v8a`.

No se permite que la UI llame JNI directamente ni que el código nativo administre vistas, red o almacenamiento Android.

## Gestión segura de modelos

- Catálogo con identificador estable, nombre, URL HTTPS, tamaño exacto, SHA-256, arquitectura/modelo, cuantización, contexto recomendado, licencia y procedencia.
- No incluir un GGUF grande dentro del APK: aumentaría el tamaño de instalación, duplicaría almacenamiento y dificultaría actualizar modelos.
- Descargar a un archivo temporal `.part`; nunca marcarlo como instalado antes de validar longitud y SHA-256.
- Reanudar solo si el servidor soporta HTTP Range y los validadores ETag/Last-Modified siguen coincidiendo. Si no, reiniciar limpiamente.
- Escribir en bloques pequeños; nunca cargar el archivo completo en RAM.
- Verificar espacio libre antes de empezar y volver a comprobarlo durante la descarga.
- Tras verificación, mover el temporal al nombre final mediante operación atómica dentro del mismo volumen.
- Mantener un manifiesto local de estado; recuperar descargas incompletas al reiniciar.
- Usar almacenamiento privado de la app para el modelo activo. Para importar desde SAF, copiar en streaming y verificar; no asumir que una URI externa equivale a una ruta de archivo.
- Catálogo y hashes deben provenir de un origen controlado y HTTPS. La integridad SHA-256 detecta corrupción, no demuestra por sí sola la identidad del publicador: el catálogo de lanzamiento debe estar versionado y autenticado.

## Memoria y rendimiento

- No fijar un contexto grande por defecto. Contexto, batch, número de hilos y capas aceleradas deben depender del modelo, memoria disponible y perfil del dispositivo.
- Primera carga en modo CPU estable; no activar Vulkan/OpenCL/GPU por suposición. Medir compatibilidad y estabilidad antes de ofrecer aceleración.
- Ejecutar inferencia fuera del hilo principal; generar tokens incrementalmente y permitir cancelar.
- Una sola sesión de inferencia activa en el primer MVP para evitar duplicar buffers KV y provocar OOM.
- Cerrar el contexto nativo al cambiar de modelo, salir del servicio de inferencia o recibir presión de memoria.
- Registrar latencia, tokens/s y memoria estimada sin guardar texto del usuario.
- No prometer que un modelo 2B/4B cabe solo por mirar RAM física: Android, GPU, buffers, KV cache, contexto y otras apps consumen memoria adicional.

## Compatibilidad y empaquetado inicial

- ABI inicial: `arm64-v8a`; añadir otras ABI solo después de tener pruebas y demanda.
- `minSdk`: API 28 como línea base inicial a validar con NDK y dependencias.
- `compileSdk/targetSdk`: API 36, con pruebas de comportamiento y restricciones de Android 16.
- Usar CMake/NDK mediante Gradle `externalNativeBuild`; incluir bibliotecas nativas en el APK.
- Fijar versiones de Gradle, Android Gradle Plugin, Kotlin, NDK y CMake; no usar versiones dinámicas.
- Generar APK de depuración para pruebas y APK release firmada con clave fuera del repositorio.
- Separar artefactos por ABI si más adelante se publican builds para varias arquitecturas.

## Descargas y ciclo de vida

- Descarga iniciada explícitamente por el usuario, con notificación visible y cancelación.
- Implementar cliente HTTP con streaming, límites de tiempo, reintentos con backoff, Range/ETag y validación de Content-Length.
- Diseñar el trabajo como reanudable/idempotente: Android puede detener procesos, cambiar red, reiniciar o aplicar cuotas.
- Seleccionar API de transferencia según versión Android (User-Initiated Data Transfer Job cuando corresponda; alternativa compatible con notificación/foreground service donde sea necesario). No depender de un worker infinito.
- Respetar Wi-Fi/datos móviles, batería, espacio y preferencia de descarga.
- La UI debe reflejar estados reales: queued, downloading, paused, verifying, installing, ready, failed y cancelled.

## Seguridad y privacidad

- Sin permiso de almacenamiento amplio, sin root y sin servidor escuchando en la red.
- Sin claves API ni proveedor cloud en el MVP local.
- No ejecutar scripts o binarios descargados arbitrariamente. El motor nativo viene empaquetado y firmado con la APK.
- Verificar modelos por hash y metadatos; limitar redirecciones y dominios del catálogo.
- No registrar prompts, traducciones ni claves en logs/crash reports.
- Historial local opcional, borrable y con retención explícita; no sincronizar por defecto.
- Revisar licencias de llama.cpp, dependencias, glosario y cada modelo antes de distribuir.

## Riesgos que deben cerrarse antes de compilar release

1. API JNI incompatible o cambios upstream de llama.cpp.
2. Error de ABI o símbolos faltantes al cargar `.so`.
3. Modelo incompatible, GGUF truncado o hash incorrecto.
4. Descarga interrumpida, Range incorrecto o servidor sin soporte de reanudación.
5. Espacio insuficiente por coexistencia de archivo temporal y final.
6. OOM al cargar pesos, contexto/KV cache o durante generación.
7. Bloqueo ANR por ejecutar inferencia en main thread.
8. Fuga de memoria nativa al cambiar de modelo o cancelar.
9. Restricciones Android 14–16 en foreground services y cuotas de jobs.
10. Fallo de SAF por URI revocada o proveedor de archivos no local.
11. Prompt/glosario portado con divergencias semánticas respecto al Python.
12. Licencia/model card ausente o incompatible con redistribución.
13. Actualización fallida que deja la app sin modelo anterior.
14. Firma release, permisos o configuración de red incorrectos.

## Puerta de calidad previa a compilación

No iniciar build de release hasta completar:

- [ ] commit exacto de llama.cpp fijado y licencia revisada.
- [ ] NDK/CMake/AGP/Kotlin fijados y disponibles en CI.
- [ ] CMake produce `arm64-v8a` sin OpenMP, sin GGML_NATIVE y sin backends no validados.
- [ ] JNI expone solo operaciones necesarias y devuelve errores tipados.
- [ ] pruebas unitarias Kotlin de prompt, glosario, validación y catálogo.
- [ ] pruebas de paridad Python↔Kotlin con los mismos casos.
- [ ] prueba de descarga parcial, reanudación, cancelación, hash inválido y disco lleno.
- [ ] prueba de carga/descarga de modelo repetida y cancelación de generación.
- [ ] prueba de memoria con modelo de referencia en dispositivo real.
- [ ] prueba sin Internet después de instalar el modelo.
- [ ] análisis de APK: ABI correcta, bibliotecas incluidas, sin secretos ni archivos GGUF accidentales.
- [ ] prueba de instalación limpia, actualización y rollback del modelo.

## Criterios de aceptación MVP

1. Instala en Android ARM64 sin Termux.
2. Descarga, verifica y prepara un GGUF desde la propia app.
3. Traduce offline usando el motor nativo.
4. Conserva perfiles dialogue/narration/thought/ability y glosario Fate.
5. Muestra progreso, cancelación y errores recuperables.
6. No envía texto del usuario a Internet durante traducción local.
7. No se bloquea la interfaz y libera recursos al terminar.
8. Supera pruebas en el Vivo Y39 5G antes de declararse compatible con ese dispositivo.

## Nota de alcance

Este documento define decisiones y pruebas; no afirma que exista ya una APK ni que la integración nativa esté compilada. La implementación debe avanzar por hitos verificables y no sustituir la versión Termux hasta superar los criterios anteriores.
