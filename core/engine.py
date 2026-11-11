"""Adaptador HTTP para un servidor llama.cpp compatible con OpenAI.

El modelo no se descarga ni se inicia desde la API. El servidor llama.cpp
se ejecuta por separado y se configura mediante CHALDEA_LLAMACPP_URL.
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class EngineUnavailableError(RuntimeError):
    """El motor de traduccion no esta configurado o no responde."""


class LlamaCppServerEngine:
    def __init__(self, base_url=None, model=None, timeout=None):
        self.base_url = (
            base_url if base_url is not None
            else os.getenv("CHALDEA_LLAMACPP_URL", "")
        ).rstrip("/")
        self.model = model or os.getenv("CHALDEA_MODEL_NAME", "local-model")
        self.timeout = timeout or float(
            os.getenv("CHALDEA_ENGINE_TIMEOUT", "120")
        )

    @property
    def is_configured(self):
        return bool(self.base_url)

    def translate(self, prompt, max_tokens=512):
        if not self.is_configured:
            raise EngineUnavailableError(
                "Configura CHALDEA_LLAMACPP_URL para conectar llama.cpp."
            )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": False,
        }
        request = Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise EngineUnavailableError(
                "No se pudo contactar con el servidor llama.cpp."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EngineUnavailableError(
                "llama.cpp devolvio una respuesta que no es JSON valido."
            ) from exc

        try:
            translation = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EngineUnavailableError(
                "La respuesta de llama.cpp no contiene una traduccion valida."
            ) from exc

        if not isinstance(translation, str) or not translation.strip():
            raise EngineUnavailableError(
                "llama.cpp devolvio una traduccion vacia."
            )

        return translation.strip()
