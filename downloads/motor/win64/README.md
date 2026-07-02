# Motor portable Windows

Esta carpeta publica el motor fiscal Python portable para instalaciones no-enterprise.

## Artefactos esperados

```text
suite-tax-is-portable-win64-v1.18.3.zip
suite-tax-is-portable-win64-v1.18.3.zip.sha256
```

El zip incluido conserva el runtime/wheels `win_amd64` del portable anterior y rebasa motor+plugin a `1.18.3`.
Antes de despliegue amplio en Windows real, ejecutar `scripts\smoke-suite-tax-is.ps1`.

## Construccion

Desde el monorepo del motor, en Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-portable-win64.ps1 -Version 1.18.3
```

El script genera:

```text
dist\suite-tax-is-portable-win64-v1.18.3.zip
dist\suite-tax-is-portable-win64-v1.18.3.zip.sha256
```

Copia ambos ficheros a esta carpeta y publica un nuevo commit si el zip no supera el limite de GitHub para
ficheros versionados. Si lo supera, publicalo como GitHub Release asset y deja aqui el checksum/enlace.

## Uso por el usuario

1. Descargar `suite-tax-is-portable-win64-v1.18.3.zip`.
2. Descomprimirlo en una carpeta local de Windows.
3. Verificar checksum:

```powershell
$hash = (Get-FileHash .\suite-tax-is-portable-win64-v1.18.3.zip -Algorithm SHA256).Hash.ToLower()
$expected = (Get-Content .\suite-tax-is-portable-win64-v1.18.3.zip.sha256).Split(" ")[0].ToLower()
if ($hash -ne $expected) { throw "SHA256 no coincide" }
```

4. Ejecutar:

```powershell
.\scripts\start-suite-tax-is.ps1
```

5. Verificar salud y version:

```text
http://127.0.0.1:8000/salud
http://127.0.0.1:8000/version
```

El plugin se instala aparte desde el marketplace del repo.
