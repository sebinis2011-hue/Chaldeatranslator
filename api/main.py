"""API HTTP de ChaldeaTranslator.

La API conserva el pipeline de prompts, glosario y validación, y permite
seleccionar motor local o proveedores cloud compatibles.
"""

import hmac
import json
import os
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from core.engine import EngineUnavailableError
from core.prompts import build_translation_prompt
from core.router import EngineRouter
from core.validator import validate_translation


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_PATH = PROJECT_ROOT / "glossary" / "fate.json"


def load_fate_glossary():
    try:
        return json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("No se pudo cargar el glosario Fate.") from exc


app = FastAPI(
    title="ChaldeaTranslator API",
    description=(
        "API de traducción literaria con glosario contextual de Fate y "
        "motores locales o cloud configurables."
    ),
    version="0.2.0",
)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    content_type: Literal["dialogue", "narration", "thought", "ability"] = "dialogue"
    context: str | None = Field(default=None, max_length=4000)
    character: str | None = Field(default=None, max_length=120)
    max_tokens: int = Field(default=512, ge=1, le=2048)
    engine_mode: Literal["local", "cloud", "auto"] = "local"
    provider: str | None = Field(default=None, min_length=1, max_length=80)
    allow_cloud: bool = False

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El texto no puede estar vacío.")
        return value


class TranslationResponse(BaseModel):
    translation: str
    valid: bool
    errors: list[str]
    warnings: list[str]
    glossary: str


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    expected = os.getenv("CHALDEA_API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API protegida: configura CHALDEA_API_KEY antes de traducir.",
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clave API ausente o incorrecta.",
        )


def get_engine():
    return EngineRouter()


@app.get("/health/live")
@app.get("/health")
def health():
    """Comprueba el proceso y publica solo el estado no secreto de los motores."""
    engine_status = get_engine().status()
    return {
        "status": "ok",
        "engines": engine_status,
        "api_key_configured": bool(os.getenv("CHALDEA_API_KEY")),
    }


@app.get("/health/ready")
def readiness():
    """La API está lista si hay un motor local sano o cloud configurado."""
    engine = get_engine()
    engine_status = engine.status()
    if engine_status["local_configured"] and engine.check_local_health():
        return {"status": "ready", "available_mode": "local"}
    if engine_status["cloud_configured"]:
        # La configuración se valida localmente; no se envía texto ni se
        # realiza una petición facturable al proveedor durante readiness.
        return {
            "status": "ready",
            "available_mode": "cloud",
            "cloud_providers": engine_status["cloud_providers"],
        }
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No hay un motor local disponible ni proveedores cloud configurados.",
    )


@app.post(
    "/v1/translate",
    response_model=TranslationResponse,
    dependencies=[Depends(require_api_key)],
)
def translate(
    payload: TranslationRequest,
    engine: EngineRouter = Depends(get_engine),
):
    glossary = load_fate_glossary()
    prompt = build_translation_prompt(
        payload.text,
        glossary=glossary,
        content_type=payload.content_type,
        context=payload.context,
        character=payload.character,
    )

    try:
        translated = engine.translate(
            prompt,
            max_tokens=payload.max_tokens,
            mode=payload.engine_mode,
            allow_cloud=payload.allow_cloud,
            provider=payload.provider,
        )
    except EngineUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    validation = validate_translation(
        payload.text,
        translated,
        glossary,
    )

    return TranslationResponse(
        translation=translated,
        valid=validation["valid"],
        errors=validation["errors"],
        warnings=validation["warnings"],
        glossary=glossary["metadata"]["name"],
    )
