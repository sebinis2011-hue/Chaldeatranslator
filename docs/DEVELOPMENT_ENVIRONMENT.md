# Entorno de desarrollo en la nube

ChaldeaTranslator puede editarse y probarse en un entorno remoto de GitHub Codespaces, sin instalar Python ni ejecutar las pruebas en el teléfono.

## Qué ofrece esta configuración

- Entorno Linux remoto con Python 3.12 y Git.
- Extensiones de Python para VS Code.
- Instalación de dependencias y ejecución automática de las pruebas al crear el entorno.
- GitHub Actions ejecuta pruebas en Python 3.12 y 3.13 en cada push a `main`, ramas `cloud/**` o `feature/**`, y en pull requests hacia `main`.

## Abrir el entorno

1. Abre el repositorio en GitHub.
2. Selecciona **Code → Codespaces → Create codespace**.
3. Elige la rama `main`.
4. Espera a que el contenedor termine de prepararse. Las pruebas se ejecutan automáticamente.

La disponibilidad de Codespaces depende de las cuotas gratuitas de la cuenta. Úsalo solo dentro de la cuota incluida y no habilites facturación ni agregues un método de pago para este proyecto.

## Límite importante: desarrollo cloud no equivale a inferencia cloud

El entorno remoto permite editar código y ejecutar pruebas unitarias. No descarga ni ejecuta automáticamente el modelo Index-Translate-2B GGUF ni llama.cpp. La inferencia local sigue dependiendo del modelo y del binario configurados en el dispositivo.

Para mover la inferencia a otro servidor haría falta un backend separado, con recursos de cómputo y un modelo accesible desde ese servidor. No se configura ningún servicio de inferencia de pago en este proyecto.

## Datos locales y secretos

- `config/settings.json` permanece fuera de Git mediante `.gitignore`.
- Los modelos GGUF y los datos locales no se suben al repositorio.
- No guardes tokens, claves API ni credenciales en el código o en commits.
