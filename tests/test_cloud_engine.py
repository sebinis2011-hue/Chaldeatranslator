import json
import unittest
from unittest.mock import patch

from core.cloud_engine import OpenAICompatibleCloudEngine
from core.engine import EngineUnavailableError


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class TestOpenAICompatibleCloudEngine(unittest.TestCase):
    def test_sends_bearer_key_and_reads_translation(self):
        response = FakeResponse({
            "choices": [{"message": {"content": "  Traducción cloud  "}}]
        })
        with patch("core.cloud_engine.urlopen", return_value=response) as mocked:
            engine = OpenAICompatibleCloudEngine(
                provider_id="test",
                base_url="https://example.invalid/v1",
                model="free-model",
                api_key="secret-value",
            )
            result = engine.translate("prompt", max_tokens=90)

        self.assertEqual(result, "Traducción cloud")
        request = mocked.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://example.invalid/v1/chat/completions",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-value")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "free-model")
        self.assertEqual(payload["max_tokens"], 90)

    def test_supports_custom_chat_completions_path(self):
        response = FakeResponse({
            "choices": [{"message": {"content": "ok"}}]
        })
        with patch("core.cloud_engine.urlopen", return_value=response) as mocked:
            engine = OpenAICompatibleCloudEngine(
                provider_id="custom",
                base_url="https://example.invalid",
                model="model",
                chat_completions_path="/v1/chat/completions",
            )
            engine.translate("prompt")
        self.assertEqual(
            mocked.call_args.args[0].full_url,
            "https://example.invalid/v1/chat/completions",
        )

    def test_rejects_missing_configuration(self):
        engine = OpenAICompatibleCloudEngine(
            provider_id="missing", base_url="", model=""
        )
        with self.assertRaises(EngineUnavailableError):
            engine.translate("prompt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
