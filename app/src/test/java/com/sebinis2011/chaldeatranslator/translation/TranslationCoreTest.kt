package com.sebinis2011.chaldeatranslator.translation

import org.junit.Assert.*
import org.junit.Test

class TranslationCoreTest {
    private val glossary = GlossaryDocument(
        terms = listOf(
            GlossaryTerm("noble_phantasm", listOf("Noble Phantasm"), "Noble Phantasm", "fixed"),
            GlossaryTerm("master", listOf("Master"), "Master", "preserve")
        )
    )

    @Test fun promptIncludesOnlyRelevantGlossaryTerms() {
        val prompt = TranslationCore.buildPrompt("The Master used a Noble Phantasm.", glossary)
        assertTrue(prompt.contains("Noble Phantasm"))
        assertTrue(prompt.contains("Master"))
        assertFalse(prompt.contains("Grail"))
    }

    @Test fun validatorDetectsMissingFixedTerm() {
        val result = TranslationCore.validate(
            "The Master used a Noble Phantasm.",
            "El mago usó su fantasma noble.",
            glossary
        )
        assertFalse(result.valid)
        assertTrue(result.errors.any { it.contains("Noble Phantasm") })
    }

    @Test fun validatorAcceptsProtectedTerms() {
        val result = TranslationCore.validate(
            "The Master used a Noble Phantasm.",
            "El Master utilizó un Noble Phantasm.",
            glossary
        )
        assertTrue(result.valid)
    }

    @Test fun rejectsBlankSource() {
        val result = TranslationCore.validate(" ", "texto", glossary)
        assertFalse(result.valid)
    }
}
