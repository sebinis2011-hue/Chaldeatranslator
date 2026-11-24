package com.sebinis2011.chaldeatranslator.inference

import java.io.File

/**
 * Stable Kotlin boundary for the future llama.cpp JNI adapter.
 * Implementations must run inference off the main thread and serialize access
 * to the single native model/context.
 */
interface InferenceEngine {
    suspend fun loadModel(modelFile: File)
    suspend fun translate(prompt: String, maxTokens: Int): String
    suspend fun cancel()
    suspend fun unloadModel()
    fun runtimeInfo(): RuntimeInfo
}

data class RuntimeInfo(
    val backend: String,
    val modelLoaded: Boolean,
    val architecture: String? = null,
    val detail: String? = null
)
