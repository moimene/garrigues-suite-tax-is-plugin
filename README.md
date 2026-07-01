# Suite Tax IS

Repositorio privado para instalar y actualizar Suite Tax IS en Claude/Cowork y Codex.

Suite Tax IS prepara la base de importacion del Impuesto sobre Sociedades: `.200` DR200 + XML mod200, usando
un motor fiscal Python local o interno. El plugin aporta la guia operativa, skills y comandos; el motor firma
los calculos y debe estar disponible aparte.

## Que hay en este repo

| Ruta | Para que sirve |
| --- | --- |
| `.claude-plugin/marketplace.json` | Marketplace para Claude/Cowork. |
| `.agents/plugins/marketplace.json` | Marketplace para Codex. |
| `plugins/suite-tax-is/` | Plugin thin comun: skills, comandos, agentes y manifiestos. |
| `downloads/motor/win64/` | Descarga del motor portable Windows. |
| `downloads/motor/macos-arm64/` | Descarga del motor portable macOS Apple Silicon. |
| `downloads/motor/macos-x64/` | Descarga del motor portable macOS Intel. |
| `VERSION_MATRIX.md` | Compatibilidad entre plugin y motor. |

No debe contener expedientes reales, PDFs, Excels, `.200`, Manuales ni salidas con PII.

## Instalacion del plugin

### Claude/Cowork

```text
/plugin marketplace add https://github.com/moimene/garrigues-suite-tax-is-plugin
/plugin install suite-tax-is@garrigues-suite-fiscal
```

### Codex

El repo incluye manifiesto Codex en:

```text
.agents/plugins/marketplace.json
plugins/suite-tax-is/.codex-plugin/plugin.json
```

En un entorno Codex con soporte de plugins/marketplaces, apunta al marketplace del repo y selecciona
`suite-tax-is`. Si el entorno no permite marketplace remoto, clona el repo y usa el marketplace local.

## Instalacion del motor

El plugin no instala el motor. Antes de preparar declaraciones, el motor debe responder en:

```text
http://127.0.0.1:8000/salud
```

Opciones:

- **Windows Enterprise:** servicio local gestionado por IT o `SUITE_IS_ENGINE_URL` interna.
- **Portable Windows:** descargar el zip desde `downloads/motor/win64/`, descomprimir y ejecutar
  `scripts\start-suite-tax-is.ps1`.
- **Portable macOS Apple Silicon:** descargar el zip desde `downloads/motor/macos-arm64/`, descomprimir y
  ejecutar `scripts/start-suite-tax-is.sh`.
- **Portable macOS Intel:** descargar el zip desde `downloads/motor/macos-x64/`, descomprimir y ejecutar
  `scripts/start-suite-tax-is.sh`.

Artefactos esperados para la release actual:

```text
downloads/motor/win64/suite-tax-is-portable-win64-v1.18.1.zip
downloads/motor/win64/suite-tax-is-portable-win64-v1.18.1.zip.sha256
downloads/motor/macos-arm64/suite-tax-is-portable-macos-arm64-v1.18.1.zip
downloads/motor/macos-arm64/suite-tax-is-portable-macos-arm64-v1.18.1.zip.sha256
downloads/motor/macos-x64/suite-tax-is-portable-macos-x64-v1.18.1.zip
downloads/motor/macos-x64/suite-tax-is-portable-macos-x64-v1.18.1.zip.sha256
```

Regla de tamano: si un zip supera el limite de GitHub para ficheros versionados en git, se publica como
GitHub Release asset y se deja aqui el enlace/checksum. No se fuerza un binario grande dentro del historial.

## Primer uso

1. Instala el plugin.
2. Arranca o valida el motor con `/suite-is-salud` o la skill `arrancar-motor`.
3. Prepara una carpeta de expediente local con la informacion contable, el `.200` N-1 y anexos disponibles.
4. Ejecuta `/is-nueva` para una sociedad o `/suite-is-export-aeat` para lote.
5. Revisa el manifiesto de salida y valida el `.200` en Sociedades WEB/OpenWeb.

OpenWeb sigue siendo el gate final de importabilidad.

## Actualizar una version

1. Publicar plugin y motor con la misma version funcional segun `VERSION_MATRIX.md`.
2. Sustituir `plugins/suite-tax-is/` por el thin validado.
3. Construir los portables Windows/macOS y copiar zip + `.sha256` a `downloads/motor/<plataforma>/`.
4. Ejecutar guardrail anti-PII.
5. Commit, tag y push.

Release actual: `1.18.1`.
