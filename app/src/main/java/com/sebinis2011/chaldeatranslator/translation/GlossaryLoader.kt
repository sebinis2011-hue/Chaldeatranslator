package com.sebinis2011.chaldeatranslator.translation

import android.content.Context
import kotlinx.serialization.json.Json

object GlossaryLoader {
    private val parser = Json {
        ignoreUnknownKeys = true
        isLenient = false
    }

    fun loadBundled(context: Context): GlossaryDocument {
        val json = context.assets.open("glossary/fate.json")
            .bufferedReader(Charsets.UTF_8)
            .use { it.readText() }
        return parser.decodeFromString<GlossaryDocument>(json)
    }
}
