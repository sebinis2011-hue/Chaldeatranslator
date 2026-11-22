"""Selector de motores local y cloud con consentimiento explícito.

Los proveedores se configuran mediante CHALDEA_CLOUD_PROVIDERS (JSON) o
CHALDEA_CLOUD_PROVIDERS_FILE. Las claves se referencian por variables de entorno.
"""

import json
import os
from pathlib import Path

from core.cloud_engine import OpenAICompatibleCloudEngine
from core.engine import EngineUnavailableError, LlamaCppServerEngine


class EngineRouter:
    def __init__(self, local_engine=None, cloud_engines=None):
        self.local_engine = local_engine or LlamaCppServerEngine()
        self.cloud_engines = (
            cloud_engines if cloud_engines is not None
            else self._load_cloud_engines()
        )

    @staticmethod
    def _load_cloud_engines():
        config_file = os.getenv("CHALDEA_CLOUD_PROVIDERS_FILE", "")
        if config_file:
            try:
                raw = Path(config_file).expanduser().read_text(encoding="utf-8")
            except OSError as exc:
                raise EngineUnavailableError(
                    "No se pudo leer CHALDEA_CLOUD_PROVIDERS_FILE."
                ) from exc
        else:
            raw = os.getenv("CHALDEA_CLOUD_PROVIDERS", "[]")

        try:
            configs = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EngineUnavailableError(
                "La configuración de proveedores cloud debe ser JSON válido."
            ) from exc

        if not isinstance(configs, list):
            raise EngineUnavailableError(
                "La configuración de proveedores cloud debe ser una lista JSON."
            )

        engines = {}
        for config in configs:
            if not isinstance(config, dict):
                continue
            provider_id = config.get("id")
            if not isinstance(provider_id, str) or not provider_id.strip():
                continue
            try:
                engine = OpenAICompatibleCloudEngine.from_environment(config)
            except (KeyError, TypeError, ValueError):
                continue
            if engine and engine.is_configured:
                engines[provider_id] = engine
        return engines

    @property
    def cloud_configured(self):
        return bool(self.cloud_engines)

    def status(self):
        local_configured = bool(
            getattr(self.local_engine, "is_configured", False)
        )
        return {
            "local_configured": local_configured,
            "cloud_configured": self.cloud_configured,
            "cloud_providers": sorted(self.cloud_engines),
        }

    def check_local_health(self):
        checker = getattr(self.local_engine, "check_health", None)
        return bool(checker and checker())

    def translate(
        self,
        prompt,
        max_tokens=512,
        mode="local",
        allow_cloud=False,
        provider=None,
    ):
        if mode not in ("local", "cloud", "auto"):
            raise EngineUnavailableError("Modo de motor desconocido.")

        if mode == "local":
            return self.local_engine.translate(prompt, max_tokens=max_tokens)

        if not allow_cloud:
            raise EngineUnavailableError(
                "El envío a proveedores cloud no está autorizado para esta solicitud. "
                "Confirma expresamente el envío antes de activar allow_cloud."
            )

        if mode == "cloud":
            return self._cloud_engine(provider).translate(
                prompt, max_tokens=max_tokens
            )

        # auto: intentar local primero. El fallback cloud solo existe con
        # consentimiento explícito para esta solicitud.
        try:
            return self.local_engine.translate(prompt, max_tokens=max_tokens)
        except EngineUnavailableError as local_error:
            try:
                return self._cloud_engine(provider).translate(
                    prompt, max_tokens=max_tokens
                )
            except EngineUnavailableError as cloud_error:
                raise EngineUnavailableError(
                    "Fallaron el motor local y el proveedor cloud autorizado. "
                    f"Detalle local: {local_error} Detalle cloud: {cloud_error}"
                ) from cloud_error

    def _cloud_engine(self, provider):
        if not self.cloud_engines:
            raise EngineUnavailableError(
                "No hay proveedores cloud configurados."
            )
        if provider:
            engine = self.cloud_engines.get(provider)
            if engine is None:
                raise EngineUnavailableError(
                    f"El proveedor cloud '{provider}' no está configurado o habilitado."
                )
            return engine
        return self.cloud_engines[sorted(self.cloud_engines)[0]]
