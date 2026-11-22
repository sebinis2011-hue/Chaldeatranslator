import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app, get_engine


class FakeEngine:
    is_configured = True

    def __init__(self):
        self.prompt = ""
        self.options = {}

    def status(self):
        return {
            "local_configured": True,
            "cloud_configured": False,
            "cloud_providers": [],
        }

    def check_local_health(self):
        return False

    def translate(
        self, prompt, max_tokens=512, mode="local",
        allow_cloud=False, provider=None,
    ):
        self.prompt = prompt
        self.options = {
            "max_tokens": max_tokens,
            "mode": mode,
            "allow_cloud": allow_cloud,
            "provider": provider,
        }
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
        self.assertEqual(self.engine.options["mode"], "local")
        self.assertFalse(self.engine.options["allow_cloud"])

    def test_cloud_choice_is_passed_only_when_explicitly_requested(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={
                "text": "Hello, Master.",
                "engine_mode": "cloud",
                "provider": "example",
                "allow_cloud": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.engine.options["mode"], "cloud")
        self.assertEqual(self.engine.options["provider"], "example")
        self.assertTrue(self.engine.options["allow_cloud"])

    def test_rejects_empty_text(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={"text": ""},
        )
        self.assertEqual(response.status_code, 422)

    def test_rejects_whitespace_only_text(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={"text": "  \n\t  "},
        )
        self.assertEqual(response.status_code, 422)

    def test_readiness_returns_503_when_no_engine_is_ready(self):
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)

    def test_rejects_unknown_content_profile(self):
        response = self.client.post(
            "/v1/translate",
            headers={"X-API-Key": "test-secret"},
            json={"text": "Hello", "content_type": "poem"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
