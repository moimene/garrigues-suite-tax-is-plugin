# Suite Tax IS — Codex

Distribucion Codex del plugin `suite-tax-is`.

## Que instala

- Skills Codex desde `skills/`.
- Metadatos del plugin en `.codex-plugin/plugin.json`.
- Entrada de marketplace repo-local en `.agents/plugins/marketplace.json`.

No instala el motor fiscal Python. El motor `1.18.1` debe estar disponible aparte como servicio Windows,
URL interna Garrigues o portable local.

## Instalacion

Este repo puede usarse como marketplace/plugin local de Codex:

```text
https://github.com/moimene/garrigues-suite-tax-is-plugin
```

El marketplace Codex esta en:

```text
.agents/plugins/marketplace.json
```

El plugin Codex esta en:

```text
plugins/suite-tax-is/.codex-plugin/plugin.json
```

## Motor

Antes de ejecutar una declaracion, comprueba:

```text
http://127.0.0.1:8000/salud
```

Para instalaciones no-enterprise, descarga el portable Windows desde:

```text
downloads/motor/win64/
```
