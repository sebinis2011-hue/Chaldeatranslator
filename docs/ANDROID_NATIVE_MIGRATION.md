# ChaldeaTranslator Android nativo — plan de migración

Estado: diseño técnico inicial; todavía no es una APK compilable ni una implementación terminada.
Rama: feature/android-native-app
Objetivo: sustituir Termux + FastAPI + proceso llama-server por una aplicación Android autónoma, con inferencia GGUF local y sin servicio remoto.

## 1. Decisión arquitectónica

**Objetivo A (principal):** Kotlin + Jetpack Compose para la aplicación; llama.cpp integrado como biblioteca C/C++ mediante JNI/NDK. No iniciar procesos shell, no depender de Termux, Python, Uvicorn, localhost ni un servidor HTTP dentro del teléfono.

**Referencia técnica:** el ejemplo oficial examples/llama.android de ggml-org/llama.cpp demuestra una integración Android con Kotlin/JNI. Fijar una versión/commit de llama.cpp y portar una capa mínima propia; no copiar APIs internas sin comprobar compatibilidad de versión.

**Alcance inicial de ABI:** arm64-v8a, que coincide con el dispositivo ARM64 objetivo. Añadir otras ABI solo cuando haya una matriz de pruebas y necesidad real.

**Min SDK:** decidir tras crear el proyecto Gradle y probar las APIs de transferencia; objetivo inicial propuesto API 26+, con rutas alternativas para transferencias en versiones anteriores. No fijar compile/target SDK ni versiones de AGP/Kotlin hasta validar el toolchain disponible y la matriz de CI.

## 2. Módulos

- app: Activity, navegación Compose, permisos mínimos, estados de instalación y traducción.
- core/domain: contratos de traducción, perfiles, validación y modelos de dominio Kotlin.
- core/translation: construcción de prompts, selección contextual de términos y validación.
- core/inference: interfaz InferenceEngine y ciclo de vida del motor.
- native/llama: JNI delgado para cargar/liberar modelo, configurar contexto, generar, cancelar y liberar memoria.
- core/modelmanager: catálogo versionado, descargas reanudables, verificación y activación atómica del GGUF.
- core/storage: preferencias, historial opcional y gestión de archivos.
- core/diagnostics: informes locales sin texto traducido, prompts, claves ni rutas privadas.

No trasladar FastAPI a Android. La API HTTP seguirá siendo un adaptador opcional para otros entornos, no una dependencia de la APK.

## 3. Reutilización de la versión Python

Reimplementar en Kotlin y cubrir con pruebas equivalentes:
- Perfiles dialogue, narration, thought, ability.
- Reglas de traducción es-419.
- Selección contextual de términos del glosario Fate.
- Reglas fixed/preserve/contextual y notas.
- Validación de términos protegidos, líneas faltantes y repeticiones.

El archivo glossary/fate.json se conserva como recurso versionado y se valida contra un esquema al iniciar. No convertir el glosario a constantes duplicadas en Kotlin.

La lógica de core/prompts.py y core/validator.py es la fuente de comportamiento. Las pruebas tests/test_prompts.py y tests/test_validator.py se convierten en vectores de prueba compartidos/fixtures para exigir paridad. No cambiar silenciosamente el significado del glosario.

## 4. Motor nativo y perfil de rendimiento

- JNI debe exponer operaciones pequeñas: loadModel, unloadModel, translate, cancel, getRuntimeInfo.
- Un único contexto de inferencia por proceso en la primera versión; serializar solicitudes con Mutex. Evitar dos cargas del mismo GGUF.
- Ejecutar inferencia fuera del hilo principal; progreso/resultado por coroutines/Flow.
- Empezar con CPU ARM64 y backend portable. No prometer aceleración Vulkan/GPU hasta tener soporte probado en el dispositivo y fallback seguro.
- Configuración conservadora inicial: contexto 1024–2048, batch pequeño y 2–4 hilos según núcleos/memoria. Medir y adaptar; no copiar el contexto 8192/batch 512 del ejemplo como valor por defecto.
- Antes de cargar: validar formato, tamaño, espacio libre, memoria disponible aproximada y compatibilidad del manifiesto. Rechazar modelos que no quepan con margen.
- Manejar OOM: capturar errores nativos donde sea posible, liberar contexto/modelo, mostrar diagnóstico y ofrecer perfil de menor memoria. No reintentar indefinidamente.
- Respetar lifecycle: liberar recursos al cerrar/cambiar modelo; impedir que la pantalla rote y dispare otra carga; evitar mantener el modelo vivo cuando la app está en segundo plano por tiempo prolongado.

## 5. Descarga e instalación de modelos

Catálogo remoto versionado con: ID, nombre, URL, tamaño exacto, SHA-256, licencia, origen, arquitectura/formato compatible, contexto recomendado y memoria mínima estimada. No confiar en el nombre de archivo ni en un hash obtenido del mismo canal no autenticado.

Flujo seguro:
1. Mostrar tamaño, licencia, origen y espacio requerido antes de descargar.
2. Exigir confirmación explícita para datos móviles; preferir Wi-Fi y carga cuando el usuario lo elija.
3. Descargar a archivo .part, usando HTTP Range + ETag/If-Range cuando el servidor lo soporte; si no, reiniciar limpiamente.
4. Persistir estado/progreso; reanudar después de cierre, pérdida de red o reinicio.
5. Verificar longitud y SHA-256 contra un manifiesto firmado o un hash fijado y revisado en la app.
6. Rechazar mismatch, HTML de error guardado como GGUF, redirección insegura, tamaño inesperado o archivo truncado.
7. Renombrar atómicamente a nombre final solo tras verificar.
8. Mantener el modelo anterior hasta comprobar que el nuevo carga; rollback si falla.

Guardar por defecto en almacenamiento específico de la aplicación. Explicar que desinstalar borra esos datos; ofrecer exportación/selección SAF más adelante sin solicitar permisos generales de almacenamiento. Nunca borrar modelos existentes durante una actualización fallida.

## 6. Transferencias Android

La transferencia debe ser visible, cancelable y reanudable. Para transferencias iniciadas por el usuario, evaluar User-Initiated Data Transfer Job en las versiones que lo soportan; usar una ruta compatible para versiones anteriores. WorkManager puede ser apropiado para tareas diferibles/reintentos, pero no asumir que un worker de larga duración es ilimitado: Android 16 puede aplicar cuotas de JobScheduler incluso a workers foreground. Probar Doze, cierre de proceso, reinicio, falta de espacio y cambio Wi-Fi/datos.

No depender de Google Play AI Packs para la distribución APK directa; reservar esa opción para una futura publicación mediante Play y tener en cuenta sus requisitos.

## 7. Seguridad y privacidad

- Sin analítica, telemetría, anuncios, login, claves API ni tráfico de inferencia remoto por defecto.
- Permiso INTERNET solo para descargar catálogo/modelos y verificar actualizaciones; el motor debe funcionar en modo avión tras la descarga.
- HTTPS obligatorio; validar hosts permitidos, redirecciones y límites de tamaño.
- No registrar texto fuente, traducciones, prompt, glosario contextual, rutas privadas ni tokens.
- Desactivar backups automáticos de modelos/historial salvo elección explícita y documentada.
- El catálogo no puede ejecutar código ni indicar bibliotecas nativas arbitrarias; solo metadatos de modelos permitidos.
- Licencias de modelos y de llama.cpp visibles antes de descarga/instalación.

## 8. Fallos previstos y mitigaciones

| Riesgo | Mitigación y prueba |
|---|---|
| JNI/API de llama.cpp cambia | Fijar commit, encapsular JNI, actualizar deliberadamente y compilar CI por ABI. |
| APK instala pero falta .so | Verificar empaquetado arm64-v8a, System.loadLibrary y smoke test en dispositivo/emulador. |
| GGUF corrupto o HTML | SHA-256 + tamaño + comprobación de carga antes de activar. |
| Descarga se interrumpe | .part, Range/ETag, estado persistente, pruebas de desconexión. |
| Poco espacio | Preflight con margen, comprobar espacio antes y durante; no eliminar modelo anterior. |
| OOM / cierre Android | Perfil bajo, contexto pequeño, un solo modelo, liberación nativa y diagnóstico. |
| Sobrecalentamiento / batería | Limitar hilos, no bloquear UI, medir duración y permitir cancelar. |
| Android mata la descarga | API de transferencia adecuada, notificación, reanudación y pruebas de reinicio. |
| Prompt/glosario difiere de Python | Fixtures compartidos y tests de paridad exacta. |
| Traducción vacía/repetida/terminología incorrecta | Validador local y advertencias sin afirmar calidad perfecta. |
| Falla al actualizar | Descarga a staging, verificación y cambio atómico con rollback. |
| Fuga de contenido privado | Red solo para descargas, sin texto de usuario en logs/red, pruebas de tráfico. |

## 9. Puertas de calidad antes de compilar una versión candidata

**G0 — arquitectura:** módulos, versiones fijadas, licencia y origen del modelo definidos.
**G1 — compilación reproducible:** Gradle/NDK/CMake compilan arm64-v8a desde CI; dependencias fijadas; SBOM/licencias revisadas.
**G2 — lógica:** pruebas Kotlin para todos los casos Python; 100% de fixtures existentes pasan.
**G3 — JNI:** carga, inferencia corta, cancelación, descarga de recursos, repetición de 20 ciclos y ausencia de crash.
**G4 — descargas:** resume, checksum incorrecto, disco lleno, HTTP 404/429/5xx, TLS, archivo truncado y reinicio probados.
**G5 — dispositivo real:** instalación limpia, primer arranque, modelo, modo avión, memoria, temperatura, batería, cambio de app y recuperación de fallos en Vivo Y39 5G.
**G6 — release:** APK firmada de prueba, permisos mínimos, inspección de dependencias, sin endpoints remotos de inferencia, sin secretos ni modelos embebidos accidentalmente.

No declarar optimizada ni compilar release final hasta superar las puertas aplicables. Publicar cifras de rendimiento solo después de medirlas en el dispositivo.

## 10. Orden de implementación

1. Crear proyecto Android/Gradle y CI reproducible.
2. Portar prompts, glosario y validador a Kotlin con pruebas de paridad.
3. Integrar llama.cpp por JNI fijado a un commit.
4. Implementar gestor de modelos seguro y reanudable.
5. Crear UI de diagnóstico, descarga, selección de modelo y traducción.
6. Ejecutar pruebas unitarias, instrumentadas y de dispositivo.
7. Perfilar y optimizar; luego generar APK candidata.

## Fuentes técnicas consultadas

- Android NDK / CMake: https://developer.android.com/ndk/guides/cmake
- Android background data transfers: https://developer.android.com/develop/background-work/background-tasks/data-transfer-options
- Play for On-device AI (solo si se distribuye por Google Play): https://developer.android.com/google/play/on-device-ai
- Ejemplo oficial llama.cpp Android: https://github.com/ggml-org/llama.cpp/tree/master/examples/llama.android