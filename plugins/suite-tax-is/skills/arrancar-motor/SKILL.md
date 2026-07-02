---
name: arrancar-motor
description: >-
  Comprueba o arranca el motor fiscal Suite Tax IS (engine_service, ADR-001). En Garrigues Windows Enterprise,
  el plugin thin NO trae motor embebido: debe existir un servicio Windows local en `127.0.0.1:8000` o una URL
  interna `SUITE_IS_ENGINE_URL`. En paquetes self-contained Linux/Cowork, puede arrancar desde `engine/`. Úsala
  antes de `/is-nueva` o cuando el motor no responda. El dato real debe quedarse en entorno local o interno
  Garrigues; nunca en motor demo cloud.
metadata:
  version: "1.3.0"
---

# Arrancar / comprobar el motor

Esta skill garantiza que el resto del plugin (`/is-nueva`, `is-stepper-orquestador`, `expediente_carpeta.py`)
tenga un motor disponible.

## Modos soportados

1. **Windows Enterprise (recomendado Garrigues):**
   - el plugin es thin y no contiene `engine/`;
   - IT arranca un servicio Windows local en `http://127.0.0.1:8000`, o configura `SUITE_IS_ENGINE_URL`;
   - si no responde, no intentes instalar dependencias dentro del plugin: reporta que falta arrancar/configurar
     el motor Windows.
2. **Portable no-enterprise Windows:**
   - el plugin sigue siendo thin;
   - el usuario arranca el motor desde `suite-tax-is-portable-win64-v1.18.3.zip` con `start-suite-tax-is.ps1`;
   - el motor queda disponible en `http://127.0.0.1:8000`.
3. **Self-contained Linux/Cowork:**
   - solo si el paquete trae `engine/` + wheels compatibles;
   - entonces puede ejecutarse el bootstrap `arrancar_motor.sh`.
4. **Desarrollo repo:**
   - usar `make dev` o `python3 -m uvicorn engine_service.app:app` desde el repo, no desde el plugin thin.

## Cómo
Primero comprueba salud y version:

```bash
curl -s http://127.0.0.1:8000/salud
curl -s http://127.0.0.1:8000/version
```

Si hay `SUITE_IS_ENGINE_URL`, comprueba esa URL. Solo continúa si `/salud` responde `{"ok":true}` y
`/version.version >= 1.18.3` (o el umbral definido en `SUITE_IS_MIN_ENGINE_VERSION`).

Solo en self-contained Linux/Cowork con `engine/` presente, ejecuta el bootstrap:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/arrancar-motor/scripts/arrancar_motor.sh"
```

Estrategias del bootstrap Linux:

- Si `http://127.0.0.1:8000/salud` ya responde `{"ok":true}` y `/version >= 1.18.3`, no hace nada.
- Si el motor responde pero es antiguo, falla cerrado y exige actualizar/reiniciar el servicio.
- Si defines `SUITE_IS_ENGINE_URL`, usa ese motor remoto solo si supera el mismo guardrail de version.
- Instala las dependencias **OFFLINE** desde los wheels incrustados (`engine/vendor/wheels`, `--no-index`):
  **no toca la red**, así que funciona aunque PyPI esté bloqueado.
- Si los wheels no cubren la plataforma, intenta `pip` online (honra `PIP_INDEX_URL` si IT da un mirror interno).
- Arranca `uvicorn engine_service.app:app` en `127.0.0.1:8000` (loopback) y espera a `/version`. Logs en
  `/tmp/suite_is_motor.log`.

> El self-contained Linux/aarch64 no es el paquete operativo para Garrigues Windows. Para Windows, usar servicio
> IT local/URL interna o el portable no-enterprise win64 cuando exista.

## Cuándo
- **Al empezar** cada conversación de declaración (antes de `/is-nueva`).
- Cuando veas un error de conexión con el motor.

## Reglas
- **PII local/interna:** el motor debe correr en loopback Windows o infraestructura interna Garrigues; el dato del
  expediente (SyS, PDF) no se publica fuera. No subas datos reales al repo ni uses el motor demo cloud.
- **No** reescribe lógica fiscal: solo comprueba/levanta el motor canónico (ADR-001), ya corra como servicio Windows (Enterprise), bundle portable local win64 (no-enterprise) o `engine/` (self-contained Linux). El plugin thin **no** lo trae dentro.
- Verifica `VERSION_MATRIX.md`: plugin `1.18.3` requiere motor funcional `1.18.3` o superior compatible.
- Si el arranque falla en Windows Enterprise, escalar a IT o configurar `SUITE_IS_ENGINE_URL`; en no-enterprise,
  arrancar el portable win64. No parchees el cálculo.
