"""API HTTP de ChaldeaTranslator.

La API orquesta prompts, glosario, motor y validacion. No aloja ni descarga
el modelo: llama.cpp debe estar disponible en CHALDEA_LLAMACPP_URL.
"""

import hmac
import json
import os
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from core.engine import EngineUnavailableError, LlamaCppServerEngine
from core.prompts import build_translation_prompt
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
        "API de traduccion literaria con glosario contextual de Fate. "
        "Requiere un servidor llama.cpp compatible con OpenAI."
    ),
    version="0.1.0",
)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    content_type: Literal["dialogue", "narration", "thought", "ability"] = "dialogue"
    context: str | None = Field(default=None, max_length=4000)
    character: str | None = Field(default=None, max_length=120)
    max_tokens: int = Field(default=512, ge=1, le=2048)


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
    return LlamaCppServerEngine()


@app.get("/health")
def health():
    engine = get_engine()
    return {
        "status": "ok",
        "engine_configured": engine.is_configured,
        "api_key_configured": bool(os.getenv("CHALDEA_API_KEY")),
    }


@app.post(
    "/v1/translate",
    response_model=TranslationResponse,
    dependencies=[Depends(require_api_key)],
)
def translate(
    payload: TranslationRequest,
    engine: LlamaCppServerEngine = Depends(get_engine),
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
