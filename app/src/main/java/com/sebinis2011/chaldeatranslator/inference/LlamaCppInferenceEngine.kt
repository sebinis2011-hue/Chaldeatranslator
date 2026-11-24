package com.sebinis2011.chaldeatranslator.inference

import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

/**
 * llama.cpp b5401 JNI adapter. All blocking native work runs on Dispatchers.IO
 * and access to the single native context is serialized.
 */
class LlamaCppInferenceEngine : InferenceEngine {
    companion object {
        init {
            System.loadLibrary("chaldea_llama")
        }
    }

    private val mutex = Mutex()
    @Volatile private var loaded = false

    private external fun nativeLoad(modelPath: String, contextSize: Int, threads: Int): Boolean
    private external fun nativeTranslate(prompt: String, maxTokens: Int): String
    private external fun nativeCancel()
    private external fun nativeUnload()
    private external fun nativeRuntimeInfo(): String

    override suspend fun loadModel(modelFile: File) = withContext(Dispatchers.IO) {
        require(modelFile.isFile && modelFile.canRead()) { "El archivo GGUF no existe o no se puede leer." }
        mutex.withLock {
            loaded = nativeLoad(modelFile.absolutePath, contextSize = 2048, threads = 2)
            check(loaded) { "llama.cpp no pudo cargar el modelo." }
        }
    }

    override suspend fun translate(prompt: String, maxTokens: Int): String =
        withContext(Dispatchers.IO) {
            require(prompt.isNotBlank()) { "El texto de entrada está vacío." }
            mutex.withLock {
                check(loaded) { "No hay un modelo cargado." }
                nativeTranslate(prompt, maxTokens.coerceIn(1, 1024))
            }
        }

    override suspend fun cancel() = withContext(Dispatchers.IO) { nativeCancel() }

    override suspend fun unloadModel() = withContext(Dispatchers.IO) {
        mutex.withLock {
            nativeUnload()
            loaded = false
        }
    }

    override fun runtimeInfo(): RuntimeInfo = RuntimeInfo(
        backend = "llama.cpp b5401",
        modelLoaded = loaded,
        architecture = "arm64-v8a",
        detail = runCatching { nativeRuntimeInfo() }.getOrNull()
    )
}
