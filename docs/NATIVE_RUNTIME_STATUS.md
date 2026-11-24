# Estado de la integración nativa

## Implementado en esta rama

- llama.cpp fijado al tag `b5401`, incorporado mediante CMake FetchContent.
- Biblioteca JNI propia `chaldea_llama` para `arm64-v8a`.
- Carga y liberación del modelo, contexto CPU, tokenización, decodificación y generación limitada.
- Adaptador Kotlin `LlamaCppInferenceEngine` compatible con el contrato `InferenceEngine`.
- Catálogo de Qwen3 1.7B Q4_K_M fijado a una revisión concreta de Hugging Face.
- Descarga explícita a archivo parcial, reanudación HTTP Range/ETag, comprobación de tamaño y SHA-256, y activación del archivo después de verificarlo.
- UI inicial para descargar, cargar y ejecutar una traducción local.
- CI ampliada para instalar NDK/CMake y compilar la APK nativa.

## Artefacto del modelo fijado

- Base: `Qwen/Qwen3-1.7B`.
- Cuantizador: `bartowski`.
- Repositorio GGUF: `bartowski/Qwen_Qwen3-1.7B-GGUF`.
- Revisión: `dcb19155b962dbb6389f4691a982043a8e651022`.
- Archivo: `Qwen_Qwen3-1.7B-Q4_K_M.gguf`.
- Tamaño exacto: `1,282,439,584` bytes.
- SHA-256 LFS: `72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb`.
- La inferencia está configurada inicialmente a 2,048 tokens y 2 hilos; son valores de arranque sujetos a medición, no máximos del modelo.

## Límites que siguen abiertos

1. La compilación nativa aún debe pasar CI; no se debe considerar probada hasta que Actions termine correctamente.
2. El motor implementa una ruta básica de texto y no está todavía conectado a la construcción de prompts, perfiles y validador del núcleo Kotlin. La pantalla usa por ahora un prompt inicial de traducción.
3. Falta streaming de tokens a la UI; la generación actual devuelve el resultado al terminar.
4. La cancelación marca el indicador nativo, pero la llamada de decodificación en curso no puede interrumpirse instantáneamente.
5. Falta probar en el Vivo Y39 5G consumo de RAM, velocidad, temperatura, batería, cierres por presión de memoria y 20 ciclos de carga/liberación.
6. Falta evaluar la calidad real del modelo con un conjunto de pruebas Fate y compararlo con modelos alternativos.
7. El catálogo inicial es un modelo estático versionado; falta una pantalla para administrar múltiples modelos y borrar los instalados con confirmación.
8. Falta revisar formalmente todos los avisos de licencia del GGUF cuantizado y de llama.cpp para una distribución pública.

## Criterio de aceptación

No declarar la app funcional hasta que:
- la CI compile CMake/JNI y empaquete `libchaldea_llama.so` para arm64;
- las pruebas Kotlin pasen;
- la app descargue el archivo completo y rechace un hash incorrecto;
- el dispositivo cargue el modelo y genere una traducción real sin conexión;
- se validen estabilidad, memoria, temperatura y privacidad en hardware real.

La descarga del GGUF requiere Internet y aproximadamente 1.28 GB de datos. Una vez descargado y verificado, la inferencia está diseñada para ejecutarse localmente, sin enviar el texto a un servidor.
