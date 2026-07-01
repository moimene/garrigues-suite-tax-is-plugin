# Suite Tax IS Plugin Marketplace

Repositorio para distribuir el plugin thin `suite-tax-is` en Claude/Cowork.

Este repo distribuye dos cosas separadas:

- **Plugin Claude thin**: marketplace, skills, comandos, agentes y scripts ligeros.
- **Plugin Codex thin**: manifiesto `.codex-plugin` y marketplace `.agents/plugins/marketplace.json` sobre
  las mismas skills.
- **Motor portable Windows**: zip descargable en `downloads/motor/win64/` cuando esté construido.

## Contenido

- `plugins/suite-tax-is/`: plugin thin `1.18.1` con skills, comandos, agentes y scripts ligeros.
- `.claude-plugin/marketplace.json`: marketplace interno `garrigues-suite-fiscal`.
- `.agents/plugins/marketplace.json`: marketplace repo-local para Codex.
- `plugins/suite-tax-is/.codex-plugin/plugin.json`: manifiesto Codex del plugin.
- `VERSION_MATRIX.md`: compatibilidad entre plugin y motor.
- `downloads/motor/win64/`: carpeta para publicar el zip portable del motor Windows.

No contiene Manual, expedientes reales, PDFs, Excels, ficheros `.200` ni salidas con PII.

## Instalacion por el equipo

### Claude/Cowork

```text
/plugin marketplace add https://github.com/moimene/garrigues-suite-tax-is-plugin
/plugin install suite-tax-is@garrigues-suite-fiscal
```

### Codex

El mismo repo incluye distribucion Codex:

```text
.agents/plugins/marketplace.json
plugins/suite-tax-is/.codex-plugin/plugin.json
```

En entornos Codex con soporte de marketplace/plugin, usa este repo como marketplace interno y selecciona
`suite-tax-is`. Si el entorno no soporta instalacion desde marketplace remoto, clona el repo y apunta Codex
al marketplace local `.agents/plugins/marketplace.json`.

Para datos reales, el motor debe estar arrancado aparte como servicio Windows Enterprise, URL interna Garrigues
o portable local Windows en `http://127.0.0.1:8000`.

## Descarga del motor portable

Cuando esté publicado:

```text
downloads/motor/win64/suite-tax-is-portable-win64-v1.18.1.zip
downloads/motor/win64/suite-tax-is-portable-win64-v1.18.1.zip.sha256
```

El usuario descarga el zip desde GitHub, lo descomprime en Windows y ejecuta:

```powershell
.\scripts\start-suite-tax-is.ps1
```

El motor debe responder en:

```text
http://127.0.0.1:8000/salud
```

## Actualizaciones

1. En el monorepo del motor, cerrar tests y generar el thin con `bash build-plugin.sh entregables-piloto`.
2. Sustituir `plugins/suite-tax-is/` por el contenido del `.plugin` thin validado.
3. Actualizar `.claude-plugin/marketplace.json`, `plugins/suite-tax-is/.claude-plugin/plugin.json` y
   `VERSION_MATRIX.md` a la misma release.
4. En Windows, construir el portable con `build-portable-win64.ps1` desde el monorepo y copiar el zip +
   `.sha256` a `downloads/motor/win64/`.
5. Ejecutar el guardrail anti-PII antes de publicar.
6. Commit, tag y push del repo privado.

## Release actual

- Plugin: `1.18.1`
- Motor minimo: `1.18.1`
- Cambio funcional: precarga N-1 formal completa de pagina 1/2, administradores, participadas B.1, socios B.2,
  titulares reales y registros complementarios; `00027` no se arrastra por depender de 2025.
