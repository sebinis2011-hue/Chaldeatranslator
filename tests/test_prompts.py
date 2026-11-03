import json
import unittest
from pathlib import Path

from core.prompts import (
    build_glossary_rules,
    build_translation_prompt,
    select_relevant_terms,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

with (PROJECT_ROOT / "glossary" / "fate.json").open(encoding="utf-8") as file:
    GLOSSARY = json.load(file)


class TestPromptGlossarySelection(unittest.TestCase):

    def test_selects_only_terms_present_in_english_text(self):
        selected = select_relevant_terms(
            GLOSSARY,
            "Master, use your Command Spell."
        )
        self.assertEqual(
            {term["id"] for term in selected},
            {"master", "command_spell"}
        )

    def test_selects_japanese_terms(self):
        selected = select_relevant_terms(
            GLOSSARY,
            "令呪を使ってください。"
        )
        self.assertEqual(
            {term["id"] for term in selected},
            {"command_spell"}
        )

    def test_excludes_irrelevant_terms(self):
        selected = select_relevant_terms(
            GLOSSARY,
            "Master, use your Command Spell."
        )
        selected_ids = {term["id"] for term in selected}

        self.assertNotIn("noble_phantasm", selected_ids)
        self.assertNotIn("saint_graph", selected_ids)
        self.assertNotIn("magecraft", selected_ids)

    def test_returns_empty_when_no_terms_match(self):
        selected = select_relevant_terms(
            GLOSSARY,
            "The weather is beautiful today."
        )
        self.assertEqual(selected, [])

    def test_omitting_source_text_preserves_legacy_behavior(self):
        selected = select_relevant_terms(GLOSSARY)
        self.assertEqual(len(selected), len(GLOSSARY["terms"]))

    def test_glossary_rules_use_only_relevant_terms(self):
        rules = build_glossary_rules(
            GLOSSARY,
            "Master, use your Command Spell."
        )
        combined = "\n".join(rules)

        self.assertIn("Master", combined)
        self.assertIn("Command Spell", combined)
        self.assertNotIn("Noble Phantasm", combined)
        self.assertNotIn("Saint Graph", combined)
        self.assertNotIn("Magecraft", combined)

    def test_translation_prompt_uses_contextual_selection(self):
        prompt = build_translation_prompt(
            "Master, use your Command Spell.",
            glossary=GLOSSARY
        )

        self.assertIn("Command Spell", prompt)
        self.assertNotIn("Noble Phantasm", prompt)
        self.assertNotIn("Saint Graph", prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)
