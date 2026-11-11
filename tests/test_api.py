import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app, get_engine


class FakeEngine:
    is_configured = True

    def translate(self, prompt, max_tokens=512):
        self.prompt = prompt
        self.max_tokens = max_tokens
        return "Hola, Master. Usa tu Command Spell."


class TestTranslationAPI(unittest.TestCase):
    def setUp(self):
        self.engine = FakeEngine()
        app.dependency_overrides[get_engine] = lambda: self.engine
        self.client = TestClient(app)
        self.key_patch = patch.dict(os.environ, {"CHALDEA_API_KEY": "test-secret"})
        self.key_patch.start()

    def tearDown(self):
        self.key_patch.stop()
        app.dependency_overrides.clear()

    def test_health_does_not_require_authentication(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_translation_requires_api_key(self):
        response = self.client.post(
            "/v1/translate",
            json={"text": "Hello, Master."},
        )
        self.assertEqual(response.status_code, 401)

    def test_translation_uses_glossary_and_returns_validation(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={
                "text": "Master, use your Command Spell.",
                "content_type": "dialogue",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["translation"], "Hola, Master. Usa tu Command Spell.")
        self.assertTrue(body["valid"])
        self.assertIn("Command Spell", self.engine.prompt)
        self.assertEqual(body["glossary"], "Chaldea Translator - Fate Glossary")

    def test_rejects_empty_text(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={"text": ""},
        )
        self.assertEqual(response.status_code, 422)

    def test_rejects_unknown_content_profile(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={"text": "Hello", "content_type": "poem"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
