import json
import unittest
from pathlib import Path

from core.validator import validate_translation


PROJECT_ROOT = Path(__file__).resolve().parent.parent

with (PROJECT_ROOT / "glossary" / "fate.json").open(encoding="utf-8") as file:
    GLOSSARY = json.load(file)


class TestTranslationValidator(unittest.TestCase):

    def test_valid_translation(self):
        result = validate_translation(
            "Command Spell, Master y Servant.",
            "Command Spell, Master y Servant.",
            GLOSSARY
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_detect_missing_command_spell(self):
        result = validate_translation(
            "Command Spell, Master y Servant.",
            "Hechizo de Comando, Master y Servant.",
            GLOSSARY
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("Command Spell" in error for error in result["errors"])
        )

    def test_detect_missing_noble_phantasm(self):
        result = validate_translation(
            "Noble Phantasm activated.",
            "El poder se ha activado.",
            GLOSSARY
        )
        self.assertFalse(result["valid"])

    def test_empty_translation(self):
        result = validate_translation(
            "Hello, Master.",
            "",
            GLOSSARY
        )
        self.assertFalse(result["valid"])
        self.assertTrue(result["errors"])

    def test_empty_source(self):
        result = validate_translation("", "Hola.", GLOSSARY)
        self.assertFalse(result["valid"])

    def test_repeated_lines_warning(self):
        result = validate_translation(
            "Hello.",
            "Hola.\nHola.",
            GLOSSARY
        )
        self.assertTrue(
            any("repetida" in warning for warning in result["warnings"])
        )

    def test_structure_warning(self):
        result = validate_translation(
            "Primera linea.\nSegunda linea.\nTercera linea.",
            "Primera linea.",
            GLOSSARY
        )
        self.assertTrue(
            any("lineas" in warning for warning in result["warnings"])
        )
        self.assertTrue(result["valid"])

    def test_no_false_positive_without_protected_terms(self):
        result = validate_translation(
            "今日はいい天気ですね。",
            "Hoy hace buen tiempo.",
            GLOSSARY
        )
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
