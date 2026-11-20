import json
import unittest
from unittest.mock import Mock, patch

from core.engine import EngineUnavailableError, LlamaCppServerEngine


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class TestLlamaCppServerEngine(unittest.TestCase):
    def test_translate_reads_openai_compatible_response(self):
        response = FakeResponse({
            "choices": [{"message": {"content": "  Hola, Master.  "}}]
        })
        with patch("core.engine.urlopen", return_value=response) as mocked:
            engine = LlamaCppServerEngine(
                base_url="http://localhost:8080/",
                model="test-model",
            )
            result = engine.translate("Translate this", max_tokens=64)

        self.assertEqual(result, "Hola, Master.")
        request = mocked.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:8080/v1/chat/completions")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["max_tokens"], 64)

    def test_translate_rejects_malformed_response(self):
        with patch("core.engine.urlopen", return_value=FakeResponse({"choices": []})):
            engine = LlamaCppServerEngine(base_url="http://localhost:8080")
            with self.assertRaises(EngineUnavailableError):
                engine.translate("Translate this")

    def test_translate_requires_configured_server(self):
        engine = LlamaCppServerEngine(base_url="")
        with self.assertRaises(EngineUnavailableError):
            engine.translate("Translate this")

    def test_check_health_accepts_healthy_server(self):
        with patch(
            "core.engine.urlopen",
            return_value=FakeResponse({"status": "ok"}),
        ):
            engine = LlamaCppServerEngine(base_url="http://localhost:8080")
            self.assertTrue(engine.check_health())

    def test_check_health_returns_false_when_server_is_down(self):
        with patch("core.engine.urlopen", side_effect=OSError("offline")):
            engine = LlamaCppServerEngine(base_url="http://localhost:8080")
            self.assertFalse(engine.check_health())


if __name__ == "__main__":
    unittest.main(verbosity=2)
