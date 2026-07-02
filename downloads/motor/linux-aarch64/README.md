# Motor slim Cowork / Linux aarch64

Este carril no es un `.plugin` autocontenido. El plugin sigue siendo thin; el motor se descarga como artefacto
slim, se verifica por SHA256 y se arranca en loopback dentro del sandbox.

## Artefactos

```text
engine-slim-v1.18.3.tar.gz
engine-slim-v1.18.3.tar.gz.sha256
fetch_engine.sh
```

## Uso

Define la URL exacta del artefacto publicado y ejecuta:

```bash
export SUITE_IS_ENGINE_VERSION=1.18.3
export SUITE_IS_ENGINE_TARBALL_URL="https://github.com/moimene/garrigues-suite-tax-is-plugin/raw/main/downloads/motor/linux-aarch64/engine-slim-v1.18.3.tar.gz"
export SUITE_IS_ENGINE_SHA256="$(cut -d ' ' -f 1 engine-slim-v1.18.3.tar.gz.sha256)"
bash fetch_engine.sh
```

Si el repo privado exige token:

```bash
export SUITE_IS_GH_TOKEN="<token-con-acceso-al-repo>"
bash fetch_engine.sh
```

## Verificacion manual

```bash
shasum -a 256 -c engine-slim-v1.18.3.tar.gz.sha256
curl -s http://127.0.0.1:8000/salud
curl -s http://127.0.0.1:8000/version
```

La version debe ser `>= 1.18.3`.

## Limitaciones

- Este carril asume que el entorno Cowork/Linux trae las dependencias Python de runtime o que IT aporta un mirror
  controlado. El script falla cerrado si faltan dependencias.
- No contiene expedientes, PDFs, Excels, `.200` ni salidas.
- Para Garrigues Windows, usar servicio Enterprise o el portable `win64`.
