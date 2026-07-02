# Motor portable macOS Apple Silicon

Esta carpeta publica el motor fiscal Python portable para macOS Apple Silicon (`arm64`).

## Artefactos esperados

```text
suite-tax-is-portable-macos-arm64-v1.18.3.zip
suite-tax-is-portable-macos-arm64-v1.18.3.zip.sha256
```

El zip incluido conserva runtime/wheels Apple Silicon del portable anterior y rebasa motor+plugin a `1.18.3`.
Antes de despliegue amplio, ejecutar smoke en macOS Apple Silicon real.

## Uso por el usuario

1. Descargar `suite-tax-is-portable-macos-arm64-v1.18.3.zip`.
2. Descomprimirlo en una carpeta local.
3. Verificar checksum:

```bash
shasum -a 256 -c suite-tax-is-portable-macos-arm64-v1.18.3.zip.sha256
```

4. Ejecutar:

```bash
chmod +x scripts/start-suite-tax-is.sh
./scripts/start-suite-tax-is.sh
```

5. Verificar salud y version:

```text
http://127.0.0.1:8000/salud
http://127.0.0.1:8000/version
```

Si el zip supera el limite de GitHub para ficheros versionados, publicarlo como GitHub Release asset y dejar
aqui el checksum/enlace.
