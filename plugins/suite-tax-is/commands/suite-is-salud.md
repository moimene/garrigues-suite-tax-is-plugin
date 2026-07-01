---
description: Comprueba la salud del motor en produccion
allowed-tools: Bash(curl:*)
---

Comprueba la salud del **engine_service** (el motor fiscal canónico) en producción.

Ejecuta el health check documentado en `CLAUDE.md`:

```bash
curl -s https://suite-is-engine-production.up.railway.app/salud
```

Esperado: `{"ok":true,"servicio":"engine_service",...}`. Reporta:

- **Verde** si responde `ok:true` (el motor está vivo; recuerda que producción es **DEMO** con datos
  sintéticos — datos reales bloqueados por Auth+RLS, D18).
- **Rojo** si no responde o devuelve error: indícalo y apunta a `DEPLOY.md` (causa raíz del healthcheck
  PORT documentada ahí; no reintroducir `startCommand` en `railway.json`). No intentes "arreglarlo" por
  otra vía sin el usuario.
