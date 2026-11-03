import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.json"


class ConfigurationError(Exception):
    """Error de configuración de Chaldea Translator."""


def load_config():
    if not CONFIG_FILE.is_file():
        raise ConfigurationError(f"No existe el archivo: {CONFIG_FILE}")

    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"JSON inválido: {exc}") from exc

    for section in ("application", "engine", "translation", "storage"):
        if section not in config:
            raise ConfigurationError(f"Falta la sección: {section}")

    engine = config["engine"]

    for key in ("executable", "model", "context_size", "threads", "max_tokens"):
        if key not in engine:
            raise ConfigurationError(f"Falta engine.{key}")

    engine["executable"] = os.path.expandvars(engine["executable"].replace("$HOME", str(Path.home())))
    engine["model"] = os.path.expandvars(engine["model"].replace("$HOME", str(Path.home())))

    return config


def validate_engine(config):
    engine = config["engine"]
    executable = Path(engine["executable"])
    model = Path(engine["model"])

    errors = []

    if not executable.is_file():
        errors.append(f"No se encuentra llama-cli: {executable}")

    if not model.is_file():
        errors.append(f"No se encuentra el modelo: {model}")

    if engine["context_size"] <= 0:
        errors.append("context_size debe ser mayor que cero")

    if engine["threads"] <= 0:
        errors.append("threads debe ser mayor que cero")

    if engine["max_tokens"] <= 0:
        errors.append("max_tokens debe ser mayor que cero")

    if errors:
        raise ConfigurationError("\\n".join(errors))

    return True
