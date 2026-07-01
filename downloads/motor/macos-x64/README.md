# Motor portable macOS Intel

Esta carpeta publica el motor fiscal Python portable para macOS Intel (`x64`).

## Artefactos esperados

```text
suite-tax-is-portable-macos-x64-v1.18.1.zip
suite-tax-is-portable-macos-x64-v1.18.1.zip.sha256
```

El zip debe construirse en macOS Intel o con un proceso de build que genere runtime Python y dependencias
compatibles con `x64`.

## Uso por el usuario

1. Descargar `suite-tax-is-portable-macos-x64-v1.18.1.zip`.
2. Descomprimirlo en una carpeta local.
3. Ejecutar:

```bash
chmod +x scripts/start-suite-tax-is.sh
./scripts/start-suite-tax-is.sh
```

4. Verificar salud:

```text
http://127.0.0.1:8000/salud
```

Si el zip supera el limite de GitHub para ficheros versionados, publicarlo como GitHub Release asset y dejar
aqui el checksum/enlace.
