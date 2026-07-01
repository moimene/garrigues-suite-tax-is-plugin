#!/usr/bin/env python3
"""Wrapper de la skill HITL para la capa canonica del motor.

La logica vive en `Extractor-parseador/scripts/validacion_importabilidad_200.py`.
Este wrapper conserva el comando documentado en la skill.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _scripts_dir() -> Path:
    """Localiza `Extractor-parseador/scripts` tanto en el REPO (dev) como en el PLUGIN EMPAQUETADO de Cowork,
    donde el motor se inyecta bajo `engine/` (engine/Extractor-parseador/scripts). Sin esto, la skill rompía
    con RuntimeError al ejecutarse desde el `.plugin` (el validador no estaba en la raíz del bundle)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        for rel in (("Extractor-parseador", "scripts"),
                    ("engine", "Extractor-parseador", "scripts")):
            cand = parent.joinpath(*rel)
            if (cand / "validacion_importabilidad_200.py").exists():
                return cand
    raise RuntimeError("No se encuentra validacion_importabilidad_200.py (ni en el repo ni en el plugin bundled).")


SCRIPTS = _scripts_dir()
sys.path.insert(0, str(SCRIPTS))

import validacion_importabilidad_200 as importabilidad  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="Ruta del .200")
    ap.add_argument("--errors", help="Texto pegado de errores/avisos AEAT/Open")
    ap.add_argument("--ejercicio", default="2025")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    args = ap.parse_args()

    report = importabilidad.analizar_path(
        args.file,
        ejercicio=args.ejercicio,
        errores_aeat_path=args.errors,
        out_json=args.out_json,
        out_md=args.out_md,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["resumen"]["importabilidad_probable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
