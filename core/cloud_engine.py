"""Adaptador configurable para proveedores cloud OpenAI-compatible.

Las claves se leen exclusivamente desde variables de entorno. Nunca se
incluyen en respuestas, logs ni archivos de configuración versionados.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.engine import EngineUnavailableError


class OpenAICompatibleCloudEngine:
    def __init__(
        self,
        provider_id,
        base_url,
        model,
        api_key="",
        timeout=90,
        chat_completions_path="/chat/completions",
    ):
        self.provider_id = provider_id
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or ""
        self.api_key = api_key or ""
        self.timeout = float(timeout)
        path = chat_completions_path or "/chat/completions"
        self.chat_completions_path = "/" + path.strip("/")

    @property
    def is_configured(self):
        return bool(self.base_url and self.model)

    @classmethod
    def from_environment(cls, config):
        api_key_env = config.get("api_key_env")
        api_key = os.getenv(api_key_env, "") if api_key_env else ""
        if config.get("api_key_required", True) and not api_key:
            return None
        return cls(
            provider_id=config["id"],
            base_url=config.get("base_url", ""),
            model=config.get("model", ""),
            api_key=api_key,
            timeout=config.get("timeout", os.getenv("CHALDEA_ENGINE_TIMEOUT", "90")),
            chat_completions_path=config.get(
                "chat_completions_path", "/chat/completions"
            ),
        )

    def translate(self, prompt, max_tokens=512):
        if not self.is_configured:
            raise EngineUnavailableError(
                "El proveedor cloud no tiene URL base o modelo configurado."
            )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key

        request = Request(
            self.base_url + self.chat_completions_path,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # No propagar cuerpos del proveedor: podrían contener datos internos.
            raise EngineUnavailableError(
                f"El proveedor cloud '{self.provider_id}' rechazó la solicitud "
                f"(HTTP {exc.code})."
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise EngineUnavailableError(
                f"No se pudo contactar con el proveedor cloud '{self.provider_id}'."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EngineUnavailableError(
                f"El proveedor cloud '{self.provider_id}' devolvió JSON inválido."
            ) from exc

        try:
            translation = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EngineUnavailableError(
                f"El proveedor cloud '{self.provider_id}' devolvió una respuesta "
                "sin traducción válida."
            ) from exc

        if not isinstance(translation, str) or not translation.strip():
            raise EngineUnavailableError(
                f"El proveedor cloud '{self.provider_id}' devolvió una traducción vacía."
            )
        return translation.strip()
