#!/usr/bin/env bash
# fetch_engine.sh — Cowork: aprovisiona el motor SIN meterlo en el .plugin (evita FILE_TOO_LARGE).
# Descarga un artefacto INMUTABLE por version, verifica sha256 ANTES de ejecutar, extrae, arranca y
# comprueba /version. Supply-chain first: nada de 'main', nada de ejecutar código sin checksum.
#
# Contrato (env):
#   SUITE_IS_ENGINE_VERSION   version pineada (default 1.18.3)
#   SUITE_IS_ENGINE_TARBALL_URL  URL del release asset engine-slim-vX.Y.Z.tar.gz  (OBLIGATORIO)
#   SUITE_IS_ENGINE_SHA256    sha256 esperado (default: el de 1.18.3, abajo)
#   SUITE_IS_GH_TOKEN         token si el release asset es de un repo PRIVADO (opcional)
#   SUITE_IS_ENGINE_HOME      dir de extracción (default /tmp/suite-is-engine-<ver>)
#   SUITE_IS_PORT             puerto (default 8000)
set -uo pipefail
VER="${SUITE_IS_ENGINE_VERSION:-1.18.3}"
SHA="${SUITE_IS_ENGINE_SHA256:-7274f74982ca72c986cca3e8e91ae6a32610f14d146b35bd719d34cebf4afcce}"
DEST="${SUITE_IS_ENGINE_HOME:-/tmp/suite-is-engine-$VER}"
PORT="${SUITE_IS_PORT:-8000}"
BASE="http://127.0.0.1:$PORT"
TB="/tmp/engine-slim-$VER.tar.gz"

ge() { python3 - "$1" "$VER" <<'PY' 2>/dev/null   # ge <actual> : ¿actual >= VER?
import sys
def t(v):
    n=[int(x) for x in __import__('re').findall(r'\d+', v)][:3];
    return tuple(n+[0]*(3-len(n)))
print("ok" if t(sys.argv[1])>=t(sys.argv[2]) else "no")
PY
}
motor_ver() { curl -s --max-time 3 "$1/version" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('version',''))" 2>/dev/null; }

# 0) ¿ya operativo y con version suficiente? -> nada
V="$(motor_ver "$BASE")"; if [ -n "$V" ] && [ "$(ge "$V")" = "ok" ]; then echo "OK  motor ya operativo en $BASE version=$V"; exit 0; fi
[ -n "$V" ] && echo "AVISO: motor en $BASE version=$V < $VER; se re-aprovisiona."

# 1) deps del sandbox — NO instalar a ciegas
if ! python3 -c "import fastapi,uvicorn,pandas,lxml,openpyxl,yaml,pdfplumber,xlrd" 2>/dev/null; then
  echo "ERROR: faltan dependencias del motor en este entorno."
  echo "  El sandbox de Cowork debería traerlas. Si no: pip install con requirements PINNEADOS (no a ciegas)."
  exit 1
fi

# 2) URL obligatoria + descarga del artefacto INMUTABLE (token si el repo es privado)
if [ -z "${SUITE_IS_ENGINE_TARBALL_URL:-}" ]; then
  echo "ERROR: define SUITE_IS_ENGINE_TARBALL_URL con el release asset engine-slim-v$VER.tar.gz"; exit 1
fi
echo "-> Descargando engine-slim-v$VER (inmutable)…"
if [ -n "${SUITE_IS_GH_TOKEN:-}" ]; then
  curl -fSL --max-time 120 -H "Authorization: Bearer $SUITE_IS_GH_TOKEN" -H "Accept: application/octet-stream" -o "$TB" "$SUITE_IS_ENGINE_TARBALL_URL" || { echo "ERROR: descarga falló (¿token/URL del release privado?)"; exit 1; }
else
  curl -fSL --max-time 120 -o "$TB" "$SUITE_IS_ENGINE_TARBALL_URL" || { echo "ERROR: descarga falló (¿repo privado sin SUITE_IS_GH_TOKEN?)"; exit 1; }
fi

# 3) VERIFICAR sha256 ANTES de ejecutar nada (supply-chain)
if ! echo "$SHA  $TB" | sha256sum -c - >/dev/null 2>&1; then
  echo "ABORT: sha256 no coincide con el pineado ($VER). No ejecuto código no verificado."; rm -f "$TB"; exit 1
fi
echo "   sha256 OK"

# 4) extraer
rm -rf "$DEST"; mkdir -p "$DEST"; tar -xzf "$TB" -C "$DEST" || { echo "ERROR: tar corrupto"; exit 1; }
[ -d "$DEST/engine/engine_service" ] || { echo "ERROR: el tarball no trae engine/engine_service"; exit 1; }

# 5) arrancar en loopback
echo "-> Arrancando motor en $BASE…"
( cd "$DEST/engine" && nohup python3 -m uvicorn engine_service.app:app --host 127.0.0.1 --port "$PORT" >/tmp/suite_is_motor.log 2>&1 & )

# 6) esperar + VERSION GUARD tras arrancar
for _ in $(seq 1 45); do
  sleep 1; V="$(motor_ver "$BASE")"
  if [ -n "$V" ] && [ "$(ge "$V")" = "ok" ]; then echo "OK  motor v$V en $BASE (engine-slim verificado por sha256)"; exit 0; fi
done
echo "ERROR: el motor no respondió con version>=$VER en 45s. Revisa /tmp/suite_is_motor.log"; exit 1
