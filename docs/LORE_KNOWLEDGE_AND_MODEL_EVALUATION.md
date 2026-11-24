# ChaldeaTranslator — conocimiento TYPE-MOON y selección del modelo local

Estado: especificación de producto e investigación inicial. No implica que un modelo haya sido benchmarkeado en el Vivo ni que exista ya un modelo ganador.

## 1. Principio fundamental: conocimiento externo al modelo

No intentar meter todo Fate/TYPE-MOON dentro de los pesos del LLM. El modelo base aporta comprensión y generación; la app aporta conocimiento preciso mediante un paquete local de lore (RAG ligero), glosarios y reglas verificables. Esto evita depender de que el modelo recuerde correctamente detalles de canon y permite corregir el conocimiento sin descargar otro modelo.

Arquitectura de conocimiento:
- Modelo GGUF: traducción, comprensión contextual, redacción y desambiguación.
- Lore Pack TYPE-MOON: conceptos, relaciones, cronología, fuentes, etiquetas de canon y notas de continuidad.
- Glosario de traducción: términos japoneses/ingleses/españoles, traducciones preferidas, variantes prohibidas y reglas por contexto.
- Validador determinista: nombres, términos protegidos, consistencia, estructura, etiquetas y omisiones.
- Retrieval local: SQLite FTS5 inicialmente; embeddings/vector search solo si las pruebas demuestran una mejora suficiente para justificar memoria y tamaño adicionales.

El LLM no debe inventar una respuesta de lore cuando el paquete no tenga evidencia. Debe marcar 'sin fuente local' o pedir una fuente.

## 2. Alcance de la base TYPE-MOON

Organizar el conocimiento por franquicia, obra, edición/idioma y continuidad. No asumir que todos los universos, rutas, adaptaciones y spin-offs comparten exactamente las mismas reglas.

Taxonomía inicial:
- Cosmología y fundamentos: Root/Akasha, Mystery/Arcane según traducción y contexto, Human Order, textura del mundo y conceptos afines.
- Magecraft: magecraft vs True Magic, Magecraft Systems, Magecraft Foundations, Magic Formulae, rituales, equivalencias, límites y costes.
- Recursos y órganos: Magic Circuits, Od, Mana, capacidad, calidad, activación y restricciones.
- Herencia y herramientas: Magic Crests, Mystic Codes, bounded fields, talleres, ley lines y contratos.
- Disciplinas: refuerzo, proyección, alteración, transmutación, alquimia, astrología, Kabbalah y tradiciones regionales, sin universalizar sus reglas.
- Seres y categorías: humanos, magi, Dead Apostles, Ancestors, Phantasmal Species, Divine Spirits, Heroic Spirits, Servants y otras clases según la obra.
- Sistemas específicos de obra: Holy Grail Wars, Servant containers, Command Spells, Noble Phantasms, Rayshifting, Chaldea systems, etc.
- Personajes, lugares, objetos, organizaciones, relaciones y cronologías.

## 3. Procedencia y niveles de certeza

Cada afirmación debe llevar una etiqueta:
- CANON_PRIMARY: obra/material oficial consultado directamente; registrar obra, capítulo/página/escena y edición si se conoce.
- CANON_SECONDARY: material oficial complementario, entrevista o material de referencia.
- REFERENCE_COMPILATION: recopilación de fans con referencia trazable al material original; nunca elevarla automáticamente a canon primario.
- INFERENCE: deducción compatible con fuentes, explicando los pasos.
- FANON: interpretación comunitaria no confirmada.
- USER_AU: regla propia del proyecto/continuidad del usuario; nunca sobrescribirla con canon oficial.
- UNKNOWN/CONFLICT: evidencia insuficiente o fuentes contradictorias.

Jerarquía de fuentes: obras originales y materiales oficiales verificables > materiales oficiales complementarios > traducciones verificadas y diccionarios con referencias > wikis y comunidades como índices de localización, no como autoridad final.

Guardar idioma original, traducción, localizador, fecha de consulta, URL/ISBN si aplica, licencia/permiso de uso y nota del traductor. No copiar capítulos, libros, guiones ni grandes fragmentos protegidos. La base debe contener metadatos, conceptos breves, paráfrasis propias y referencias; incorporar texto del usuario solo para su uso local y con procedencia marcada.

## 4. Modelo de datos sugerido

Entidades:
- Concept(id, canonical_name, aliases[], japanese_term, category, short_definition, work_scope[], certainty, source_ids[])
- Rule(id, subject_id, predicate, object_or_value, conditions[], exceptions[], certainty, source_ids[])
- Character(id, names[], affiliations[], abilities[], relations[], work_scope[], source_ids[])
- Work(id, title, medium, route_or_episode, continuity_id, release_version)
- Source(id, title, publisher_or_author, source_type, locator, language, url_or_isbn, consulted_at, reliability)
- TermEntry(id, source_term, target_term, language_pair, domain, context, status, forbidden_variants[], notes, priority)
- ContinuityOverride(id, continuity_id, target_id, override_type, value, author='user')

Reglas: toda afirmación factual debe poder remontarse a uno o más source_ids; los conflictos se conservan como conflictos y no se fusionan en una verdad artificial. Los overrides AU tienen precedencia solo dentro de su continuidad.

## 5. Magecraft: esquema de relaciones que el motor debe respetar

Usar esto como mapa inicial de investigación, no como sustituto de leer la fuente concreta:
- Magic Circuits: sistema pseudo-nervioso asociado al magus; convertir fuerza vital en energía mágica y conectar con fundamentos según la descripción de materiales de referencia.
- Magecraft Foundation: sistema/teoría grabado en el mundo o transmitido por una tradición; el magus establece contacto y ejecuta fórmulas bajo sus reglas.
- Magic Formula: instrucciones/función que se activa mediante comando y energía.
- Magecraft: reproducción artificial de fenómenos misteriosos; no equipararla sin matices con True Magic.
- Od/Mana: mantener distinción terminológica y registrar variaciones por obra/fuente; no tratarlos como sinónimos automáticos.
- Magic Crest, Mystic Code, bounded field, ley lines, workshop y ritual: conceptos separados con relaciones tipadas, no una bolsa genérica de 'hechizos'.

Antes de describir una regla como universal, comprobar si es específica de una familia, escuela, era, lugar, ruta o sistema.

## 6. Selección del LLM: shortlist, no ganador prematuro

El requisito es traducción inglés/japonés a español latino, obediencia a glosario, conservación de nombres y estilo, comprensión de contexto TYPE-MOON y ejecución local con memoria limitada. El número de parámetros por sí solo no mide conocimiento factual ni calidad de traducción.

Candidatos de investigación:
- Qwen3-4B-Instruct GGUF Q4_K_M: referencia fuerte para calidad; ficha oficial indica 4B parámetros, soporte declarado de 100+ idiomas, contexto nativo 32K y archivo Q4_K_M de aproximadamente 2.5 GB. Licencia Apache 2.0 en la ficha GGUF consultada. Los pesos ocupan aproximadamente 2.5 GB, pero la RAM total será mayor por KV cache, buffers y runtime.
- Qwen3-1.7B-Instruct GGUF: candidato de eficiencia que debe incluirse en la comparación; comprobar disponibilidad oficial de GGUF, calidad de español/japonés y consistencia terminológica antes de adoptarlo.
- Gemma 3 4B IT QAT GGUF: candidato alternativo con soporte multilingüe declarado por Google; revisar condiciones de uso específicas de Gemma antes de distribuir pesos o permitir descargas desde la app. No asumir que sus términos equivalen a Apache 2.0.
- Mantener el actual Index-Translate-2B.Q4_K_M como baseline hasta identificar su origen, licencia, arquitectura, tamaño exacto y calidad. No eliminarlo por intuición.

Recomendación provisional: benchmarkear primero Qwen3-1.7B y Qwen3-4B Q4_K_M; usar Gemma 3 4B IT QAT como comparador sujeto a revisión de licencia. En el teléfono con 8 GB anunciados, el 4B Q4 puede ser viable, pero no se garantiza: Android, KV cache y buffers consumen memoria adicional. La decisión final debe salir de pruebas reales.

## 7. Benchmark específico ChaldeaTranslator

Crear un conjunto de evaluación propio, con ejemplos redactados o autorizados y pares de referencia revisados. Separar entrenamiento/desarrollo de prueba final para no ajustar prompts al test.

Conjunto mínimo inicial: 100–200 segmentos:
- 25 diálogos con voces/personajes diferentes.
- 20 fragmentos narrativos.
- 20 pensamientos internos.
- 20 habilidades, Noble Phantasms, títulos y terminología.
- 15 casos ambiguos que requieran contexto.
- 10 casos adversariales: nombres similares, negaciones, texto mixto, instrucciones inyectadas dentro del texto fuente y términos protegidos.

Métricas:
- Fidelidad semántica y omisiones/adiciones, evaluadas por revisión humana.
- Consistencia de términos del glosario y conservación de nombres propios.
- Naturalidad del español latino y voz del personaje.
- Cumplimiento de formato, saltos de línea y etiquetas.
- Alucinación de lore y afirmaciones sin fuente.
- Tokens/segundo, tiempo hasta primer token, latencia total, RAM pico, tamaño del modelo, batería/temperatura y tasa de cierres.

Evaluar cada modelo con idénticos prompts, contexto recuperado, parámetros, hardware y versión de llama.cpp. Hacer varias corridas y registrar mediana y percentil 95. No escoger ganador por una sola traducción ni por benchmarks generales del fabricante.

## 8. Optimización de calidad por encima del tamaño

1. Recuperar solo las 3–8 entradas de lore/glosario relevantes para el segmento, no pegar una enciclopedia entera al prompt.
2. Incluir fuente y nivel de certeza en cada fragmento recuperado.
3. Separar instrucciones del traductor del texto fuente; delimitar texto no confiable para reducir prompt injection.
4. Aplicar restricciones deterministas a nombres, términos protegidos y formato.
5. Usar contexto corto por defecto y aumentarlo solo cuando la escena lo necesite; el contexto largo aumenta KV cache y latencia.
6. Generar en modo no-thinking para traducción rutinaria si la calidad lo permite; reservar razonamiento adicional para desambiguación y revisión, comparando coste.
7. Ofrecer perfiles de calidad y velocidad, sin mantener dos modelos cargados a la vez.
8. No hacer fine-tuning inicialmente: primero medir RAG + glosario + prompting. Fine-tuning requiere dataset con derechos, evaluación y recursos que pueden no estar disponibles.

## 9. Fuentes iniciales consultadas

- Qwen3-4B-GGUF model card: https://huggingface.co/Qwen/Qwen3-4B-GGUF
- Gemma 3 model card: https://gemma.ai/models/gemma-3/
- TYPE-MOON Wiki Magecraft (referencias a materiales y obras): https://typemoon.fandom.com/wiki/Magecraft
- TMdict Magecraft (entrada con fuente indicada Fate/side material): https://www.tmdict.com/en/ma.magecraft
- TYPE-MOON Wiki Encyclopedia/Fsm: https://typemoon.fandom.com/wiki/Encyclopedia/Fsm

Las wikis y diccionarios anteriores son pistas de investigación y referencias secundarias; comprobar los materiales originales antes de marcar una afirmación como CANON_PRIMARY.