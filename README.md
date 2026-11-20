# ChaldeaTranslator

Traductor literario multilingüe para videojuegos y novelas visuales, con ejecución local, OCR contextual y memoria de traducción.

## Estado actual

El repositorio contiene el núcleo inicial de construcción de prompts, selección contextual de terminología Fate y validación de traducciones, además de pruebas unitarias.

## Desarrollo

- [Entorno de desarrollo en la nube](docs/DEVELOPMENT_ENVIRONMENT.md)
- [Código principal](core/)
- [Glosario Fate](glossary/fate.json)
- [Pruebas](tests/)

### Ejecutar pruebas localmente

Requiere Python 3.12 o posterior. Desde la raíz del repositorio:

```bash
python -m compileall -q core tests
python -m unittest discover -s tests -v
```

### Desarrollo remoto

Usa **Code → Codespaces → Create codespace** en GitHub. La configuración de `.devcontainer/` prepara el entorno Python remoto y ejecuta las pruebas al iniciar.

GitHub Actions también ejecuta las pruebas automáticamente. Consulta la pestaña **Actions** para ver los resultados.

## Motor de traducción

El script `chaldea-translator.sh` está orientado al entorno Termux y espera una instalación local de `llama.cpp` y el modelo GGUF Index-Translate-2B. El entorno cloud de desarrollo no incluye ni ejecuta ese modelo automáticamente.

## Privacidad

No subas `config/settings.json`, modelos GGUF, tokens, claves API, historiales privados ni archivos de usuario al repositorio.
