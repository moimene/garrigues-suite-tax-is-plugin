#!/usr/bin/env python3
"""verificar_sys_vs_ccaa.py — GUARDARRAÍL del camino CCAA→SyS(LLM)→motor (EPIC B).

Dado el Sumas y Saldos A3 que el LLM infirió desde la CCAA, lo pasa por el MOTOR y exige tres cosas:
  1) el balance CUADRA en el motor:            dif(00180−00252) ≈ 0
  2) NINGUNA cuenta queda «sin regla»:         0 cuentas no mapeadas
  3) los totales del motor COINCIDEN con los TOTALES DECLARADOS en la CCAA (los que leyó el LLM):
        00180 == TOTAL ACTIVO   ·   00252 == TOTAL PN+PASIVO   ·   resultado == Resultado del ejercicio
Si las tres pasan, el LLM leyó bien y el SyS es base válida (entra al flujo normal del expediente).
Si falla (3), el LLM transcribió mal algún importe → revisar (HITL); no es un fallo del motor.

Esto sustituye la dependencia de OCR/Docling: la lectura la hace el LLM (visión) y AQUÍ se comprueba
objetivamente contra los propios totales de la CCAA. El motor firma; el LLM solo propone.

Uso (los importes son los totales que el LLM leyó de la CCAA del cliente; ejemplo con cifras ficticias):
  python3 verificar_sys_vs_ccaa.py --sys RUTA/SyS.xlsx --ejercicio 2025 \
      --total-activo 12345678.90 --total-pn-pasivo 12345678.90 --resultado 1234567.89 [--repo RUTA] [--tol 1.0]
Salida: informe + exit 0 (verde) / 1 (revisar).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile


def _find_repo(start: str) -> str:
    """Localiza la raíz que contiene Extractor-parseador/ y engine_service/ (dev) o engine/ (plugin)."""
    cands = [start, os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    for base in cands:
        d = base
        for _ in range(8):
            if os.path.isdir(os.path.join(d, "Extractor-parseador")) and os.path.isdir(os.path.join(d, "engine_service")):
                return d
            if os.path.isdir(os.path.join(d, "engine", "Extractor-parseador")):
                return os.path.join(d, "engine")
            d = os.path.dirname(d)
    raise SystemExit("No encuentro la raíz del motor (Extractor-parseador + engine_service). Usa --repo.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sys", required=True, help="SyS A3 .xlsx inferido de la CCAA")
    ap.add_argument("--ejercicio", default="2025")
    ap.add_argument("--total-activo", type=float, required=True, help="TOTAL ACTIVO declarado en la CCAA")
    ap.add_argument("--total-pn-pasivo", type=float, required=True, help="TOTAL PN+PASIVO declarado en la CCAA")
    ap.add_argument("--resultado", type=float, required=True, help="Resultado del ejercicio declarado en la CCAA")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--tol", type=float, default=1.0, help="tolerancia en € (def. 1,00)")
    a = ap.parse_args()

    repo = a.repo or _find_repo(os.path.dirname(os.path.abspath(a.sys)))
    sys.path.insert(0, repo)
    sys.path.insert(0, os.path.join(repo, "Extractor-parseador", "scripts"))
    from engine_service.engines import run_pipeline  # noqa: E402
    import builder  # noqa: E402

    with tempfile.TemporaryDirectory() as td:
        man = run_pipeline([a.sys], td, ejercicio=a.ejercicio)
        if man.get("estado") == "error":
            print("🔴 motor en error:", man.get("detalle") or man); return 1
        canon = [{"cuenta": r["Cuenta"], "denom": r.get("Descripción", ""), "sf": float(r["Saldo Final"])}
                 for r in csv.DictReader(open(os.path.join(td, "agrupado_4d.csv"), encoding="utf-8-sig"), delimiter=";")
                 if r.get("Saldo Final")]
    cdir = os.path.join(repo, "Extractor-parseador", "data", "campaigns", a.ejercicio)
    cas, _lin, cua, _pyg, _sec = builder.proyectar(
        canon, json.load(open(os.path.join(cdir, "mapeo_pgc_aeat.json"))),
        json.load(open(os.path.join(cdir, "catalogo_contable.json"))))

    a180, a252, res = cas.get("00180", 0.0), cas.get("00252", 0.0), cua["resultado"]
    chk = [
        ("balance cuadra (dif 00180−00252 = 0)", abs(cua["dif"]) <= a.tol, f"dif={cua['dif']:.2f}"),
        ("0 cuentas sin regla", len(cua["no_map"]) == 0, f"sin_regla={cua['no_map'][:6]}"),
        ("00180 == TOTAL ACTIVO (CCAA)", abs(a180 - a.total_activo) <= a.tol, f"motor={a180:.2f} vs CCAA={a.total_activo:.2f}"),
        ("00252 == TOTAL PN+PASIVO (CCAA)", abs(a252 - a.total_pn_pasivo) <= a.tol, f"motor={a252:.2f} vs CCAA={a.total_pn_pasivo:.2f}"),
        ("resultado == Resultado del ejercicio (CCAA)", abs(res - a.resultado) <= a.tol, f"motor={res:.2f} vs CCAA={a.resultado:.2f}"),
    ]
    print("=== Verificación SyS(LLM) ↔ CCAA por el motor ===")
    ok = True
    for nombre, passed, detalle in chk:
        print(f"  [{'OK ' if passed else 'XX'}] {nombre}  ({detalle})")
        ok = ok and passed
    print("VEREDICTO:", "🟢 VERDE — el LLM leyó bien; SyS válido para el expediente" if ok
          else "🔴 REVISAR (HITL) — el SyS no reproduce la CCAA; revisar importes/cuentas inferidas")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
