# Publicar una versión

becwright se distribuye por tres canales desde un único release de GitHub:

- **PyPI** — el paquete de Python (`pip` / `pipx`).
- **npm** — un paquete lanzador (`becwright`) más cinco paquetes por plataforma
  con `os`/`cpu` (`@becwright/<target>`), cada uno con un binario precompilado,
  para que quien no usa Python pueda instalarlo.

## Configuración inicial (una vez)

- **PyPI**: vía Trusted Publishing (OIDC), sin token almacenado. Ver el job
  `pypi` en [`.github/workflows/release.yml`](../.github/workflows/release.yml).
- **npm**:
  - Crear el scope/org `@becwright` en npm y asegurar que la cuenta también sea
    dueña del nombre sin scope `becwright`.
  - Agregar un token de acceso de automatización como secreto del repositorio
    `NPM_TOKEN`.

## Sacar una versión

1. Subir la versión en `pyproject.toml` (las versiones de npm se derivan del tag
   de git al publicar, no hace falta editarlas).
2. Commit y crear un **release de GitHub** con tag `vX.Y.Z` (debe coincidir con
   `pyproject.toml`).
3. Publicar el release dispara `release.yml`, que:
   - construye y prueba el binario en todas las plataformas (macOS como binario universal2),
   - stagea cada binario en su paquete `@becwright/<target>` (`npm/stage.mjs`),
   - fija la versión de cada paquete npm desde el tag (`npm/set-version.mjs`),
   - publica primero los paquetes de plataforma y luego el lanzador,
   - construye y publica el paquete de Python en PyPI.

## Notas

- Los paquetes de plataforma se publican antes que el lanzador para que sus
  `optionalDependencies` resuelvan de inmediato.
- `npm publish` no es idempotente: re-ejecutar una versión ya publicada falla.
  Subí la versión para volver a publicar.
- Para probar los binarios sin publicar, ejecutá el workflow **Build binaries**
  manualmente (`workflow_dispatch`).
