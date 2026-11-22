import unittest

from core.engine import EngineUnavailableError
from core.router import EngineRouter


class FakeEngine:
    def __init__(self, result=None, error=None, configured=True):
        self.result = result
        self.error = error
        self.is_configured = configured
        self.calls = 0

    def translate(self, prompt, max_tokens=512):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class TestEngineRouter(unittest.TestCase):
    def test_local_is_default_and_does_not_use_cloud(self):
        local = FakeEngine(result="local result")
        cloud = FakeEngine(result="cloud result")
        router = EngineRouter(local_engine=local, cloud_engines={"free": cloud})

        result = router.translate("prompt")

        self.assertEqual(result, "local result")
        self.assertEqual(local.calls, 1)
        self.assertEqual(cloud.calls, 0)

    def test_cloud_requires_explicit_consent(self):
        local = FakeEngine(result="local")
        cloud = FakeEngine(result="cloud")
        router = EngineRouter(local_engine=local, cloud_engines={"free": cloud})

        with self.assertRaises(EngineUnavailableError):
            router.translate("private text", mode="cloud", allow_cloud=False)

        self.assertEqual(cloud.calls, 0)

    def test_cloud_mode_uses_selected_provider_with_consent(self):
        local = FakeEngine(result="local")
        free = FakeEngine(result="free result")
        paid = FakeEngine(result="paid result")
        router = EngineRouter(
            local_engine=local,
            cloud_engines={"free": free, "paid": paid},
        )

        result = router.translate(
            "prompt", mode="cloud", allow_cloud=True, provider="paid"
        )

        self.assertEqual(result, "paid result")
        self.assertEqual(paid.calls, 1)
        self.assertEqual(free.calls, 0)
        self.assertEqual(local.calls, 0)

    def test_auto_falls_back_to_cloud_only_with_consent(self):
        local = FakeEngine(error=EngineUnavailableError("offline"))
        cloud = FakeEngine(result="cloud result")
        router = EngineRouter(local_engine=local, cloud_engines={"free": cloud})

        with self.assertRaises(EngineUnavailableError):
            router.translate("prompt", mode="auto", allow_cloud=False)
        self.assertEqual(local.calls, 1)
        self.assertEqual(cloud.calls, 0)

        result = router.translate("prompt", mode="auto", allow_cloud=True)
        self.assertEqual(result, "cloud result")
        self.assertEqual(cloud.calls, 1)

    def test_auto_uses_healthy_local_without_cloud_consent(self):
        local = FakeEngine(result="local result")
        cloud = FakeEngine(result="cloud result")
        router = EngineRouter(local_engine=local, cloud_engines={"free": cloud})

        result = router.translate("prompt", mode="auto", allow_cloud=False)

        self.assertEqual(result, "local result")
        self.assertEqual(local.calls, 1)
        self.assertEqual(cloud.calls, 0)

    def test_status_does_not_expose_provider_secrets(self):
        local = FakeEngine(result="local")
        cloud = FakeEngine(result="cloud")
        router = EngineRouter(local_engine=local, cloud_engines={"public-id": cloud})

        self.assertEqual(
            router.status(),
            {
                "local_configured": True,
                "cloud_configured": True,
                "cloud_providers": ["public-id"],
            },
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
