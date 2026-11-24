package com.sebinis2011.chaldeatranslator.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ModelCatalogTest {
    @Test
    fun initialModelHasPinnedArtifactIntegrityMetadata() {
        val model = ModelCatalog.initial
        assertEquals("Qwen3 1.7B · Q4_K_M", model.name)
        assertEquals(1_282_439_584L, model.sizeBytes)
        assertEquals(64, model.sha256.length)
        assertTrue(model.sha256.matches(Regex("[a-f0-9]{64}")))
        assertEquals(40, model.revision.length)
        assertTrue(model.downloadUrl.contains(model.revision))
        assertTrue(model.downloadUrl.startsWith("https://huggingface.co/"))
    }
}
