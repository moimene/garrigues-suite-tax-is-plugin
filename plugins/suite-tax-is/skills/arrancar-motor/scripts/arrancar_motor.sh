#!/usr/bin/env bash
# Arranca el motor Suite Tax IS (engine_service, ADR-001) desde el motor EMPAQUETADO en el plugin (engine/),
# dentro del entorno de Cowork. ROBUSTO a redes corporativas que bloquean PyPI (403): instala las
# dependencias OFFLINE desde los wheels incrustados (engine/vendor/wheels), sin tocar la red.
# Orden de estrategias (idempotente):
#   0) motor ya arriba -> nada
#   1) motor remoto (SUITE_IS_ENGINE_URL) -> usarlo, no instalar nada local
#   2) deps ya importables (sandbox que ya las trae) -> saltar install
#   3) install OFFLINE desde wheels incrustados (sin red; resuelve el proxy que bloquea PyPI)
#   4) install ONLINE (honra PIP_INDEX_URL si IT da un mirror interno)
#   5) error accionable con las 3 salidas
# PII: corre en loopback (127.0.0.1); el dato del expediente no sale del entorno.
set -uo pipefail
PORT="${SUITE_IS_PORT:-8000}"
BASE="http://127.0.0.1:${PORT}"
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
ENGINE="$PLUGIN_ROOT/engine"
WHEELS="$ENGINE/vendor/wheels"
REQ="$ENGINE/vendor/requirements-runtime.txt"
PY="${PYTHON:-python3}"

ping() {  # ping <base-url> -> "up"/"down"
  "$PY" - "$1" <<'PY' 2>/dev/null
import sys, urllib.request, json
try:
    ok = json.load(urllib.request.urlopen(sys.argv[1] + "/salud", timeout=5)).get("ok")
    print("up" if ok else "down")
except Exception:
    print("down")
PY
}

deps_ok() {  # ¿están importables las deps de runtime?
  "$PY" - <<'PY' 2>/dev/null
import importlib
for m in ("fastapi","uvicorn","pandas","lxml","openpyxl","yaml","multipart"):
    importlib.import_module(m)
print("ok")
PY
}

# 0) ¿ya arriba?
if [ "$(ping "$BASE")" = "up" ]; then echo "✓ motor ya operativo en $BASE"; exit 0; fi

# 1) ¿motor remoto provisto por IT? (no se instala nada en local)
if [ -n "${SUITE_IS_ENGINE_URL:-}" ]; then
  if [ "$(ping "$SUITE_IS_ENGINE_URL")" = "up" ]; then
    echo "✓ usando motor remoto en $SUITE_IS_ENGINE_URL (SUITE_IS_ENGINE_URL)"; exit 0
  fi
  echo "AVISO: SUITE_IS_ENGINE_URL=$SUITE_IS_ENGINE_URL no responde; intento arrancar el motor local."
fi

if [ ! -d "$ENGINE/engine_service" ]; then
  echo "ERROR: no encuentro el motor empaquetado en $ENGINE (¿plugin sin engine/?)"; exit 1
fi

# 2) ¿deps ya presentes? si no, instalar
if [ "$(deps_ok)" != "ok" ]; then
  # 3) OFFLINE desde wheels incrustados (sin red). pip elige los wheels compatibles con esta arch/Python.
  if [ -d "$WHEELS" ] && ls "$WHEELS"/*.whl >/dev/null 2>&1; then
    echo "→ Instalando dependencias OFFLINE desde wheels incrustados (sin red)…"
    "$PY" -m pip install -q --no-index --find-links "$WHEELS" --break-system-packages -r "$REQ" 2>&1 | tail -3 || true
  fi
  # 4) ONLINE como respaldo (honra PIP_INDEX_URL del mirror interno si IT lo configura)
  if [ "$(deps_ok)" != "ok" ]; then
    echo "→ Wheels offline insuficientes para esta plataforma; intento pip online (usa PIP_INDEX_URL si hay mirror)…"
    "$PY" -m pip install -q --break-system-packages -r "$REQ" 2>&1 | tail -3 || true
  fi
  # 5) sigue sin poder: error accionable
  if [ "$(deps_ok)" != "ok" ]; then
    echo "ERROR: no pude instalar las dependencias del motor (¿proxy bloquea PyPI y los wheels no cubren esta plataforma?)."
    echo "  Plataforma detectada: arch=$(uname -m) · $("$PY" --version 2>&1)"
    echo "  Soluciónalo de UNA de estas formas:"
    echo "   a) reempaqueta el plugin con wheels para ESTA plataforma (build-selfcontained.sh, VENDOR_PYVER acorde);"
    echo "   b) define PIP_INDEX_URL apuntando al mirror interno de PyPI de Garrigues (Artifactory/Nexus);"
    echo "   c) define SUITE_IS_ENGINE_URL con un motor ya hospedado por IT."
    exit 1
  fi
fi

# 6) arrancar
echo "→ Arrancando el motor en $BASE …"
( cd "$ENGINE" && nohup "$PY" -m uvicorn engine_service.app:app --host 127.0.0.1 --port "$PORT" >/tmp/suite_is_motor.log 2>&1 & )
for _ in $(seq 1 45); do
  sleep 1
  if [ "$(ping "$BASE")" = "up" ]; then echo "✓ motor OK en $BASE"; exit 0; fi
done
echo "ERROR: el motor no respondió en 45s. Revisa /tmp/suite_is_motor.log"; tail -5 /tmp/suite_is_motor.log 2>/dev/null
exit 1
