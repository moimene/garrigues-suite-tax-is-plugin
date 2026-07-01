# Motor portable Windows

Esta carpeta publica el motor fiscal Python portable para instalaciones no-enterprise.

## Artefactos esperados

```text
suite-tax-is-portable-win64-v1.18.1.zip
suite-tax-is-portable-win64-v1.18.1.zip.sha256
```

El zip no esta incluido todavia porque debe construirse en Windows para asegurar runtime Python y wheels
`win_amd64`.

## Construccion

Desde el monorepo del motor, en Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-portable-win64.ps1 -Version 1.18.1
```

El script genera:

```text
dist\suite-tax-is-portable-win64-v1.18.1.zip
dist\suite-tax-is-portable-win64-v1.18.1.zip.sha256
```

Copia ambos ficheros a esta carpeta y publica un nuevo commit.

## Uso por el usuario

1. Descargar `suite-tax-is-portable-win64-v1.18.1.zip`.
2. Descomprimirlo en una carpeta local de Windows.
3. Ejecutar:

```powershell
.\scripts\start-suite-tax-is.ps1
```

4. Verificar salud:

```text
http://127.0.0.1:8000/salud
```

El plugin Claude se instala aparte desde el marketplace del repo.
