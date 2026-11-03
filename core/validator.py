import re


class ValidationError(Exception):
    """Error durante la validacion de una traduccion."""


def contains_term(text, term):
    if not text or not term:
        return False

    if re.fullmatch(r"[^\w\s]+", term):
        return term in text

    if all(ord(char) < 128 for char in term):
        pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    return term.casefold() in text.casefold()


def validate_non_empty(source, translation):
    errors = []

    if not isinstance(source, str) or not source.strip():
        errors.append("El texto original esta vacio o no es valido.")

    if not isinstance(translation, str) or not translation.strip():
        errors.append("La traduccion esta vacia o no es valida.")

    return errors


def validate_terminology(source, translation, glossary):
    errors = []

    for term in glossary.get("terms", []):
        mode = term.get("mode")
        target = term.get("target")
        sources = term.get("source", [])

        if not target or not sources:
            continue

        source_found = any(
            contains_term(source, item) for item in sources
        )

        if not source_found:
            continue

        if mode in ("fixed", "preserve"):
            if not contains_term(translation, target):
                errors.append(
                    f"Terminologia obligatoria ausente: {target}"
                )

    return errors


def validate_structure(source, translation):
    warnings = []

    source_lines = [line for line in source.splitlines() if line.strip()]
    translated_lines = [
        line for line in translation.splitlines() if line.strip()
    ]

    if len(source_lines) > 1 and len(translated_lines) < len(source_lines):
        warnings.append(
            "La traduccion tiene menos lineas no vacias que el original."
        )

    return warnings


def detect_repeated_lines(translation):
    warnings = []
    seen = set()

    for line in translation.splitlines():
        normalized = line.strip()

        if not normalized:
            continue

        key = normalized.casefold()

        if key in seen:
            warnings.append(
                f"Posible linea repetida: {normalized}"
            )
        else:
            seen.add(key)

    return warnings


def validate_translation(source, translation, glossary):
    errors = validate_non_empty(source, translation)

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "warnings": []
        }

    errors.extend(
        validate_terminology(source, translation, glossary)
    )

    warnings = validate_structure(source, translation)
    warnings.extend(detect_repeated_lines(translation))

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
