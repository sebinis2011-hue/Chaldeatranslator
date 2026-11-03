import re


CONTENT_PROFILES = {
    "dialogue": (
        "Traduce un dialogo entre personajes. Conserva la personalidad, "
        "el registro, el ritmo conversacional, el sarcasmo, la ironia, "
        "el humor y la intencion emocional de cada intervencion."
    ),
    "narration": (
        "Traduce una narracion literaria. Conserva la ambientacion, "
        "el ritmo, las imagenes descriptivas y la continuidad narrativa. "
        "Utiliza un español natural y fluido."
    ),
    "thought": (
        "Traduce pensamientos internos. Conserva la voz interior, "
        "las emociones, las dudas, las contradicciones y el subtexto "
        "del personaje."
    ),
    "ability": (
        "Traduce una descripcion de habilidad, tecnica o Noble Phantasm. "
        "Respeta la terminologia de Fate, los efectos, las condiciones, "
        "las limitaciones y las relaciones causales del texto original."
    )
}


BASE_RULES = [
    "Traduce al español latino natural (es-419).",
    "Conserva exactamente el significado del texto original.",
    "No inventes acontecimientos, explicaciones ni informacion.",
    "No resumas, omitas ni repitas contenido.",
    "Respeta la personalidad y la voz individual de cada personaje.",
    "Conserva el sarcasmo, la ironia, el humor y los dobles sentidos.",
    "Adapta expresiones cuando la traduccion literal resulte artificial.",
    "No alteres nombres propios, titulos ni relaciones entre personajes.",
    "Conserva los saltos de linea y la estructura del texto.",
    "Si existe ambiguedad, no inventes una interpretacion.",
    "Devuelve solamente la traduccion, sin comentarios adicionales."
]


def _contains_source(text, source):
    """Comprueba una fuente sin aceptar coincidencias parciales en palabras."""
    if not isinstance(source, str) or not source:
        return False

    if source.isascii():
        pattern = r"(?<!\w)" + re.escape(source) + r"(?!\w)"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    return source.casefold() in text.casefold()


def select_relevant_terms(glossary, source_text=None):
    """Devuelve solo los terminos presentes en el texto original.

    source_text=None conserva el comportamiento anterior y devuelve
    todas las entradas. Esto mantiene la compatibilidad con llamadas
    externas que utilicen la funcion sin el nuevo argumento.
    """
    if not isinstance(glossary, dict):
        return []

    terms = glossary.get("terms", [])
    if not isinstance(terms, list):
        return []

    if source_text is None:
        return terms

    if not isinstance(source_text, str) or not source_text:
        return []

    selected = []

    for term in terms:
        if not isinstance(term, dict):
            continue

        sources = term.get("source", [])
        if isinstance(sources, str):
            sources = [sources]

        if not isinstance(sources, list):
            continue

        if any(_contains_source(source_text, item) for item in sources):
            selected.append(term)

    return selected


def build_glossary_rules(glossary, source_text=None):
    if not isinstance(glossary, dict):
        return []

    rules = glossary.get("rules", {})
    if not isinstance(rules, dict):
        rules = {}

    preserve_fixed = rules.get("preserve_fixed_terms", True)
    respect_context = rules.get("respect_context", True)

    instructions = []

    if (
        preserve_fixed
        and rules.get("do_not_replace_with_synonyms", True)
    ):
        instructions.append(
            "No sustituyas los terminos establecidos por sinonimos."
        )

    relevant_terms = select_relevant_terms(glossary, source_text)

    for term in relevant_terms:
        mode = term.get("mode")
        target = term.get("target")
        sources = term.get("source", [])

        if isinstance(sources, str):
            sources = [sources]

        if not target or not sources:
            continue

        source_text_label = ", ".join(
            str(source) for source in sources if source
        )

        if mode in ("fixed", "preserve") and preserve_fixed:
            instructions.append(
                f"Terminologia obligatoria: {source_text_label} = {target}. "
                f"Conserva exactamente la forma {target}."
            )

        elif mode == "contextual" and respect_context:
            instructions.append(
                f"Termino contextual: {source_text_label}. "
                f"Utiliza {target} como referencia y respeta el contexto."
            )

        else:
            continue

        note = term.get("notes")
        if note:
            instructions.append(
                f"Nota terminologica: {note}"
            )

    return instructions


def build_translation_prompt(
    text,
    glossary=None,
    content_type="dialogue",
    context=None,
    character=None
):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("El texto que se va a traducir esta vacio.")

    if content_type not in CONTENT_PROFILES:
        raise ValueError(f"Perfil desconocido: {content_type}")

    instructions = list(BASE_RULES)
    instructions.append(CONTENT_PROFILES[content_type])

    if glossary is not None:
        instructions.extend(
            build_glossary_rules(glossary, source_text=text)
        )

    if character:
        instructions.append(
            f"Personaje o voz principal: {character}. "
            "Respeta su caracterizacion sin inventar rasgos."
        )

    if context:
        instructions.append(
            "Contexto narrativo de referencia: " + str(context)
        )

    rules_text = "\n".join(
        f"- {instruction}" for instruction in instructions
    )

    return (
        "INSTRUCCIONES DE TRADUCCION\n"
        + rules_text
        + "\n\nTEXTO ORIGINAL\n"
        + text
        + "\n\nTRADUCCION:"
    )
