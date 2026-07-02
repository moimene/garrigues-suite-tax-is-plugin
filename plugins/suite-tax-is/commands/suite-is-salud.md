---
description: Comprueba salud y version del motor
allowed-tools: Bash(curl:*)
---

Comprueba la salud y version del **engine_service** (el motor fiscal canónico).

Para datos reales usa el motor local/IT, no el demo cloud:

```bash
curl -s http://127.0.0.1:8000/salud
curl -s http://127.0.0.1:8000/version
```

Esperado: `ok:true` y `version >= 1.18.3` (o el umbral `SUITE_IS_MIN_ENGINE_VERSION`). Reporta:

- **Verde** si responde `ok:true` y la version cumple el minimo.
- **Rojo** si no responde, si `/version` no existe o si la version es antigua. En ese caso no generes
  declaraciones: pide actualizar/reiniciar el servicio Windows, portable o `SUITE_IS_ENGINE_URL`.
