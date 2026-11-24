# ChaldeaTranslator Android

Este directorio será el proyecto Android independiente (Kotlin/Compose + NDK/JNI). La aplicación no dependerá de Termux, Python, FastAPI ni de un servidor local.

**Estado actual:** arquitectura aprobada como dirección técnica; el proyecto Android todavía no está implementado ni compilado.

Antes de añadir módulos Gradle y código nativo, consulta:

- [Arquitectura y plan de migración](../docs/ANDROID_NATIVE_MIGRATION.md)

## Principios no negociables

- Inferencia local por defecto y sin envío remoto de texto.
- Modelo GGUF descargado bajo demanda, nunca incluido dentro del APK.
- Descarga reanudable, validación SHA-256 e instalación atómica.
- llama.cpp embebido como biblioteca nativa; no ejecutar un proceso shell.
- No compilar en el teléfono del usuario; usar CI/build reproducible cuando sea posible.
- No eliminar Termux hasta que la APK supere pruebas reales en el dispositivo objetivo.

## Próximo hito

Crear el esqueleto Gradle reproducible y la interfaz Kotlin del motor; después integrar una versión fijada de llama.cpp y ejecutar CI antes de distribuir un APK de prueba.
