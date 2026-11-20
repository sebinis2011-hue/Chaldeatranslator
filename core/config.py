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
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfigurationError(f"JSON inválido: {exc}") from exc

    if not isinstance(config, dict):
        raise ConfigurationError("La configuración debe ser un objeto JSON.")

    for section in ("application", "engine", "translation", "storage"):
        if section not in config or not isinstance(config[section], dict):
            raise ConfigurationError(f"Falta la sección válida: {section}")

    engine = config["engine"]
    for key in ("executable", "model", "context_size", "threads", "max_tokens"):
        if key not in engine:
            raise ConfigurationError(f"Falta engine.{key}")

    for key in ("executable", "model"):
        if not isinstance(engine[key], str) or not engine[key].strip():
            raise ConfigurationError(f"engine.{key} debe ser una ruta no vacía.")
        expanded = engine[key].replace("$HOME", str(Path.home()))
        engine[key] = os.path.expandvars(expanded)

    for key in ("context_size", "threads", "max_tokens"):
        value = engine[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ConfigurationError(f"engine.{key} debe ser un entero mayor que cero.")

    return config


def validate_engine(config):
    try:
        engine = config["engine"]
    except (KeyError, TypeError) as exc:
        raise ConfigurationError("Falta la sección engine.") from exc

    executable = Path(engine["executable"])
    model = Path(engine["model"])
    errors = []

    if not executable.is_file():
        errors.append(f"No se encuentra llama-cli: {executable}")
    elif not os.access(executable, os.X_OK):
        errors.append(f"llama-cli no tiene permiso de ejecución: {executable}")

    if not model.is_file():
        errors.append(f"No se encuentra el modelo: {model}")

    if errors:
        raise ConfigurationError("\n".join(errors))

    return True
