# Suite Tax IS — Codex

Guia corta para usar Suite Tax IS desde Codex.

## Instalacion

El repo contiene:

```text
.agents/plugins/marketplace.json
plugins/suite-tax-is/.codex-plugin/plugin.json
```

Instala o apunta Codex al marketplace del repo y selecciona `suite-tax-is`.

## Motor

Codex no instala el motor. Antes de trabajar:

```text
http://127.0.0.1:8000/salud
```

Si no responde, arranca el servicio Windows/portable o configura `SUITE_IS_ENGINE_URL`.

## Uso

1. Abre una conversacion por declaracion o grupo.
2. Da la ruta local del expediente.
3. Usa `/is-nueva` para una sociedad o `/suite-is-export-aeat` para lote.
4. Revisa el manifiesto y valida el `.200` en Sociedades WEB/OpenWeb.

Los datos reales deben quedarse en local o infraestructura interna.
