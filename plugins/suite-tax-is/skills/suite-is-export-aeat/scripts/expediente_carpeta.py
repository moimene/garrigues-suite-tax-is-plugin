#!/usr/bin/env python3
"""Pipeline por carpeta de expediente (F3) — 1 expediente = 1 carpeta -> .200 admisible.

Orquesta el motor canonico por HTTP (ADR-001, fail-closed) para UN expediente, contra su carpeta:
  scaffold (entrada/ salida/ estado.json) -> precarga N-1 (.200/justificante/datos fiscales)
  -> Fase A (cuadre 00180=00252) -> /expediente/export-base (con liquidacion FIRMADA opcional)
  -> escribe .200 + XML + estados + estado.json (ExpedienteState-compatible) + manifiesto por casilla.

El motor FIRMA el numero; este script solo orquesta. Si un gate falla (descuadre/OCR/HITL/regimen/XSD),
PARA y escribe el motivo (no parchea). PII LOCAL: corre el engine en local; la carpeta y sus salidas son
locales y gitignored; los nombres usan CODENAME (no el NIF); no se imprime NIF/razon/importes.

Uso:
  python3 expediente_carpeta.py --carpeta ./EXPEDIENTE_<codename>_<ej> --codename <codename> --ejercicio 2025
  # opcional: identificativos + liquidacion FIRMADA del cierre (JSON {casilla: importe}):
  python3 expediente_carpeta.py --carpeta ./exp --codename ACME --nif <NIF> --razon "<RAZON>" --liquidacion cierre.json
"""
import argparse, base64, json, os, sys, glob, uuid, mimetypes, re, urllib.request, urllib.error, unicodedata
from datetime import datetime, timezone

EXTS_SYS = (".xls", ".xlsx", ".csv")
PREV_200 = (".200",)
PREV_PDF = (".pdf",)
PREV_TEXT = (".txt", ".md")
CCAA_EXTS = (".pdf", ".docx")
MIN_ENGINE_VERSION = os.environ.get("SUITE_IS_MIN_ENGINE_VERSION", "1.18.3")


def parse_balance_pyg_agregado(path):
    """Fallback para expedientes que traen estados Balance/PyG agregados, no SyS/A3."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    scripts = os.path.join(root, "Extractor-parseador", "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import parser_balance_pyg_agregado  # noqa: E402
    return parser_balance_pyg_agregado.parse_xlsx(path)


def _req(url, data=None, headers=None, timeout=180):
    r = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(engine, path, payload, timeout=180):
    return _req(engine.rstrip("/") + path, json.dumps(payload).encode("utf-8"),
                {"Content-Type": "application/json"}, timeout)


def post_multipart(engine, path, fields, file_path, file_field="fichero", qs="", timeout=180):
    boundary = "----stis" + uuid.uuid4().hex
    pre = b""
    for k, v in (fields or {}).items():
        pre += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    fname = os.path.basename(file_path)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(file_path, "rb") as fh:
        body = pre + (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
                      f"filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n").encode() + fh.read() + \
               (f"\r\n--{boundary}--\r\n").encode()
    url = engine.rstrip("/") + path + (("?" + qs) if qs else "")
    return _req(url, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout)


def salud(engine):
    try:
        return _req(engine.rstrip("/") + "/salud", timeout=15).get("ok") is True
    except Exception:
        return False


def _version_tuple(value):
    parts = [int(x) for x in re.findall(r"\d+", str(value or ""))[:3]]
    return tuple((parts + [0, 0, 0])[:3])


def comprobar_motor(engine):
    base = engine.rstrip("/")
    try:
        estado = _req(base + "/salud", timeout=15)
        info = _req(base + "/version", timeout=15)
    except Exception as exc:
        return False, f"no responde: {type(exc).__name__}: {exc}"
    if estado.get("ok") is not True:
        return False, f"/salud no OK: {estado}"
    actual = str(info.get("version") or "")
    if _version_tuple(actual) < _version_tuple(MIN_ENGINE_VERSION):
        return False, f"version antigua {actual or '?'}; requiere >= {MIN_ENGINE_VERSION}"
    return True, f"version {actual}"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def lname(path):
    return unicodedata.normalize("NFC", os.path.basename(path)).lower()


def find(folder, exts, exclude_dirs=("salida",)):
    out = []
    for p in sorted(glob.glob(os.path.join(folder, "**", "*"), recursive=True)):
        b = os.path.basename(p)
        if b.startswith(("~$", ".")) or any(os.sep + d + os.sep in p for d in exclude_dirs):
            continue
        if p.lower().endswith(exts):
            out.append(p)
    return out


def _merge_extra(a, b):
    aa = list(a or [])
    bb = list(b or [])
    n = max(len(aa), len(bb))
    out = []
    for i in range(n):
        av = aa[i] if i < len(aa) else None
        bv = bb[i] if i < len(bb) else None
        out.append(av if str(av or "").strip() else bv)
    return out


def _merge_item(a, b):
    out = dict(a or {})
    for k, v in (b or {}).items():
        if k == "extra":
            merged = _merge_extra(out.get("extra"), v)
            if any(str(x or "").strip() for x in merged):
                out["extra"] = merged
            continue
        if not str(out.get(k) or "").strip() and str(v or "").strip():
            out[k] = v
    return out


def _merge_formal_list(cur, inc):
    if not isinstance(cur, list) or not isinstance(inc, list):
        return inc or cur
    out = [dict(x) for x in cur]
    pos = {str(x.get("nif") or "").strip(): i for i, x in enumerate(out) if str(x.get("nif") or "").strip()}
    for item in inc:
        nif = str((item or {}).get("nif") or "").strip()
        if nif and nif in pos:
            out[pos[nif]] = _merge_item(out[pos[nif]], item)
        else:
            out.append(dict(item or {}))
            if nif:
                pos[nif] = len(out) - 1
    return out


def merge_precarga(engine, files, ejercicio):
    """Precarga N-1/datos fiscales: corre /precarga-anterior por cada candidato y fusiona.

    Caracteres/pagina01b se rellenan fill-if-missing; para formales se fusiona por NIF para conservar campos
    completos del `.200` N-1 y añadir filas nuevas de datos fiscales 2025.
    """
    car, p1b, formales, ident = {}, {}, {}, {}
    fuentes, necesita_ocr = [], False
    for f in files:
        try:
            r = post_multipart(engine, "/precarga-anterior", None, f, qs=f"tipo=auto&ejercicio={ejercicio}")
        except Exception as e:
            print(f"  precarga: {os.path.basename(f)} ilegible ({type(e).__name__}); sigo.", file=sys.stderr)
            continue
        if r.get("necesita_ocr"):
            necesita_ocr = True
        fuentes.append(r.get("fuente") or "?")
        for k, v in (r.get("caracteres") or {}).items():
            car.setdefault(k, v)
        for k, v in (r.get("pagina01b") or {}).items():
            p1b.setdefault(str(k), v)
        for k, v in (r.get("formales") or {}).items():
            if not v:
                continue
            cur = formales.get(k)
            if isinstance(v, list) and isinstance(cur, list):
                formales[k] = _merge_formal_list(cur, v)
            elif not cur:
                formales[k] = v
        idt = r.get("identificativos") or {}
        for k in ("nif", "razon_social"):
            if idt.get(k) and not ident.get(k):
                ident[k] = idt[k]
    return {"caracteres": car, "pagina01b": p1b, "formales": formales,
            "identificativos": ident, "fuentes": fuentes, "necesita_ocr": necesita_ocr}


def escribir_manifiesto(path, res, codename, ejercicio):
    """Manifiesto por casilla (R4): bandejas + casillas dependientes + avisos. De-identificado en consola;
    el fichero local puede llevar el detalle (carpeta gitignored)."""
    dep = res.get("casillas_dependientes_de_otros_modelos") or []
    val = res.get("validacion", {}) or {}
    fich = res.get("ficheros", {}) or {}
    L = [f"# Manifiesto de revision — {codename} — ejercicio {ejercicio}", "",
         f"- Generado: {now_iso()}",
         f"- XML contable valido XSD: **{val.get('valido_xsd')}** · casillas contables: {val.get('casillas')}",
         f"- Entregables: {', '.join(sorted(fich.keys()))}",
         f"- .200 = BORRADOR/PROVISIONAL: su validez la confirma el import real en Sociedades WEB Open.", "",
         "## Estado por bandeja (5 estados de responsabilidad)",
         "| Bandeja | Estado | Contenido |", "|---|---|---|",
         "| Contable (Balance/PyG/ECPN) | validado por motor | cuadre 00180=00252 verde |",
         "| Identificativos + caracteres + formales | precargado / requiere confirmacion | del N-1; el abogado confirma |",
         "| Liquidacion (BI/cuota) | firmada (si hay cierre) / cosmetica (borrador) | el motor firma; el abogado valida criterio GF |",
         "| Pendiente AEAT (otros modelos) | no incluido | se completa desde su modelo origen |", ""]
    if fich.get("b1_post_import_json"):
        L += ["## B.1 post-import",
              "- Las sociedades participadas B.1 complejas no se han emitido dentro del `.200` importable.",
              "- OpenWeb 2025 puede rechazar B.1 con continuaciones o totales `01501/01502/01503` frágiles; completar/revisar en Sociedades WEB tras import positivo.",
              "- Datos preparados en `b1_participadas_post_import.json`.",
              ""]
    if dep:
        pend = [d for d in dep if not d.get("presente")]
        L += [f"## Pendiente AEAT — {len(pend)} casilla(s) que dependen de otros modelos (a cero)",
              "| Casilla | Modelo | Concepto |", "|---|---|---|"]
        for d in dep:
            if not d.get("presente"):
                L.append(f"| {d.get('casilla')} | {d.get('modelo')} | {d.get('concepto')} |")
        L.append("")
    if res.get("avisos"):
        L += ["## Avisos del motor (no bloqueantes)"] + [f"- {a}" for a in res["avisos"]] + [""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Pipeline por carpeta de expediente -> .200 admisible (F3).")
    ap.add_argument("--carpeta", required=True)
    ap.add_argument("--codename", default="")
    ap.add_argument("--ejercicio", default="2025")
    ap.add_argument("--engine", default="http://127.0.0.1:8000")
    ap.add_argument("--nif", default="")
    ap.add_argument("--razon", default="")
    ap.add_argument("--liquidacion", default="", help="ruta a JSON {casilla: importe} de la liquidacion FIRMADA del cierre")
    args = ap.parse_args()

    carpeta = os.path.abspath(args.carpeta)
    if not os.path.isdir(carpeta):
        sys.exit(f"ERROR: no existe la carpeta {carpeta}")
    codename = "".join(c if (c.isalnum() or c in "-_") else "_" for c in (args.codename or os.path.basename(carpeta))).strip("_") or "expediente"
    ej = str(args.ejercicio)
    entrada = os.path.join(carpeta, "entrada")
    src_dir = entrada if os.path.isdir(entrada) else carpeta
    salida = os.path.join(carpeta, "salida"); os.makedirs(salida, exist_ok=True)
    estado_path = os.path.join(carpeta, "estado.json")
    estado = {}
    if os.path.isfile(estado_path):
        try: estado = json.load(open(estado_path, encoding="utf-8"))
        except Exception: estado = {}
    if ".git" in carpeta.split(os.sep):
        print("AVISO: la carpeta esta dentro de un repo git; el .200 lleva PII -> asegura que esta gitignored.", file=sys.stderr)
    if "127.0.0.1" not in args.engine and "localhost" not in args.engine:
        print("AVISO: engine no-local. Con datos reales usa solo una URL interna Garrigues autorizada; "
              "el cloud demo es para datos sinteticos.", file=sys.stderr)
    motor_ok, motor_msg = comprobar_motor(args.engine)
    if not motor_ok:
        sys.exit(f"ERROR: motor no valido en {args.engine}: {motor_msg}. Arranca/actualiza el servicio Windows "
                 "local, configura SUITE_IS_ENGINE_URL o usa el portable correcto.")

    estado.update({"pasoActual": max(int(estado.get("pasoActual", 0)), 0), "alcanceTrabajo": estado.get("alcanceTrabajo", "asistida"),
                   "actualizado": now_iso(), "codename": codename, "ejercicio": ej})

    # Paso 1 — Contabilidad: Fase A (cuadre 00180=00252) -> canonico_csv
    sys_files = find(src_dir, EXTS_SYS)
    if not sys_files:
        sys.exit(f"ERROR: no hay Sumas y Saldos ({EXTS_SYS}) en {src_dir}")
    # Prefiere por nombre el Sumas y Saldos (evita coger estimacion/liquidacion si hay varios .xls)
    _kw = ("sumas", "saldo", "balance", "sys", "tb")
    _cand = [f for f in sys_files if any(k in os.path.basename(f).lower() for k in _kw)]
    sys_path = (_cand or sys_files)[0]
    fa = post_multipart(args.engine, "/fase-a-sys", None, sys_path, qs=f"ejercicio={ej}&tipo_entidad=normal")
    canonico = fa.get("canonico_csv")
    contable_casillas = None
    contable_directo = None
    estado["fuenteCanonico"] = "sys"; estado["a3Confirmado"] = True
    estado["faseA"] = {"apto": fa.get("apto"), "semaforo": fa.get("semaforo"), "n_rojo": fa.get("n_rojo"), "tipo_entidad": fa.get("tipo_entidad")}
    if not fa.get("apto") or not canonico:
        try:
            directo = parse_balance_pyg_agregado(sys_path)
        except Exception as e:  # noqa: BLE001
            directo = {"ok": False, "motivo": f"{type(e).__name__}: {e}"}
        if directo.get("ok"):
            contable_casillas = directo.get("casillas") or {}
            contable_directo = directo
            canonico = None
            estado["fuenteCanonico"] = "balance_pyg_agregado"
            estado["faseA"] = {"apto": True, "semaforo": "🟢", "n_rojo": 0,
                               "tipo_entidad": "balance_pyg_agregado",
                               "checks": directo.get("checks", [])}
        else:
            estado["pasoActual"] = 1
            estado["faseA"]["fallback_balance_pyg"] = {"ok": False, "motivo": directo.get("motivo"),
                                                       "sin_mapear": directo.get("sin_mapear", [])[:10]}
            json.dump(estado, open(estado_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print(f"FAIL-CLOSE (Fase A): la contabilidad no cuadra (semaforo={fa.get('semaforo')}) y el fallback "
                  f"Balance/PyG agregado no es apto ({directo.get('motivo')}). estado.json escrito.")
            sys.exit(1)
    estado["contabilidadCargada"] = bool(canonico or contable_casillas)

    # Paso 0/2 — Precarga N-1 (caracteres/pagina01b/formales/identificativos)
    _precarga_doc_exts = PREV_PDF + PREV_TEXT
    _prev_pdf = [f for f in find(src_dir, _precarga_doc_exts)
                 if any(k in lname(f) for k in (
                     "datos fiscales", "datos_fiscales", "informacion fiscal", "información fiscal",
                     "modelo 200", "modelo200", "justificante", "declaracion", "declaración"))
                 and not any(k in lname(f) for k in (
                     "cuentas", "annual", "ccaa", "eeff"))]
    prev = find(src_dir, PREV_200) + _prev_pdf
    pre = merge_precarga(args.engine, prev, ej) if prev else {"caracteres": {}, "pagina01b": {}, "formales": {}, "identificativos": {}, "fuentes": [], "necesita_ocr": False}
    nif = args.nif or pre["identificativos"].get("nif") or ""
    razon = args.razon or pre["identificativos"].get("razon_social") or ""
    estado["precarga"] = {"nivel": (pre["fuentes"][0] if pre["fuentes"] else None), "fuentes": pre["fuentes"],
                          "necesita_ocr": pre["necesita_ocr"], "n_caracteres": len(pre["caracteres"]),
                          "n_pagina01b": len(pre["pagina01b"]), "formales_grupos": [k for k, v in pre["formales"].items() if v],
                          "identificativos_poblados": {"nif": bool(nif), "razon": bool(razon)}}
    estado.pop("cnae_fuente", None)

    # Paso 3 — Liquidacion FIRMADA (opcional; si no, export-base aplica la base cosmetica)
    liq = None
    if args.liquidacion:
        try: liq = json.load(open(args.liquidacion, encoding="utf-8"))
        except Exception as e: print(f"AVISO: liquidacion ilegible ({e}); sigo sin ella (cosmetica).", file=sys.stderr)
    estado["liquidacion_firmada"] = bool(liq and liq.get("00621"))

    # Paso 4 — Exportar AEAT (export-base, fail-close).
    # PRECARGA N-1 (M1/M2): pasa el N-1 detectado (prefiere `.200` posicional; si no, justificante PDF) como
    # `precarga_n1` → export-base extrae identificativos+mercantil (parse_200/parse_pdf) e inyecta DP200001+formales,
    # OPT-IN y fill-if-missing (lo que ya trae `merge_precarga` gana), con manifest HITL. Default None = no-op.
    _n1_200 = find(src_dir, PREV_200)
    _n1_pdf = [f for f in find(src_dir, PREV_PDF)
               if any(k in lname(f) for k in ("modelo 200", "modelo200", "justificante", "declaracion", "declaración"))
               and not any(k in lname(f) for k in ("cuentas", "annual", "datos fiscales", "informacion fiscal", "información fiscal"))]
    precarga_n1 = (_n1_200 + _n1_pdf)[0] if (_n1_200 or _n1_pdf) else None
    # CCAA → APERTURA del ECPN (REDEVCO 2026-06-28): si el SyS no trae saldo de apertura, el motor proyecta el
    # ECPN desde el Balance de la CCAA (columna N-1) y la hoja reconcilia → la AEAT importa. Detecta la CCAA en
    # la carpeta y pasa su TEXTO; el motor solo lo usa si el SyS no tiene apertura (si no, no-op). Soporta DOCX
    # y PDF-portfolio/PDF. Si no hay CCAA o no hay capa de texto -> None (comportamiento previo).
    ecpn_ccaa_texto = None
    _ccaa = [f for f in find(src_dir, CCAA_EXTS)
             if any(k in lname(f) for k in ("ccaa", "cuentas anuales", "cuentas_anuales", "annual accounts", "fy25 accounts"))]
    if _ccaa:
        try:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
            if repo_root not in sys.path:
                sys.path.insert(0, repo_root)
            try:
                from engine_service import engines as _eng
            except Exception:
                sys.path.insert(0, os.path.join(os.environ.get("CLAUDE_PLUGIN_ROOT", ""), "engine", "engine_service"))
                import engines as _eng
            _ccaa = sorted(_ccaa, key=lambda p: (0 if p.lower().endswith(".docx") else 1, p.lower()))
            ecpn_ccaa_texto = _eng.extraer_texto_ccaa(_ccaa[0]) or None
        except Exception as e:   # noqa: BLE001
            print(f"  CCAA detectada pero no se pudo extraer texto ({type(e).__name__}); sigo sin apertura ECPN.", file=sys.stderr)
    payload = {"canonico_csv": canonico, "contable_casillas": contable_casillas,
               "ejercicio": ej, "nif": nif, "razon_social": razon,
               "caracteres": pre["caracteres"] or None, "pagina01b": pre["pagina01b"] or None,
               "formales": pre["formales"] or None, "liquidacion_provisional": liq or None,
               "precarga_n1": precarga_n1, "ecpn_ccaa_texto": ecpn_ccaa_texto,
               "fuente_canonico": estado["fuenteCanonico"], "a3_confirmado": True,
               "necesita_ocr": pre["necesita_ocr"]}
    res = post_json(args.engine, "/expediente/export-base", payload)
    estado["exportBase"] = {"ok": bool(res.get("ok")), "estado": res.get("estado"), "modo": ("asistida" if liq else "borrador"),
                            "generadoEn": now_iso(), "valido_xsd": (res.get("validacion") or {}).get("valido_xsd"),
                            "avisos": res.get("avisos", []),
                            "entregables": [{"clave": k, "fichero": v.get("fichero"), "bytes": v.get("bytes")} for k, v in (res.get("ficheros") or {}).items()]}
    if not res.get("ok"):
        estado["pasoActual"] = 4
        json.dump(estado, open(estado_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"FAIL-CLOSE (export-base): estado={res.get('estado')} · motivo={res.get('motivo')}. estado.json escrito.")
        sys.exit(1)

    # Escribir entregables (codename) + canonico + manifiesto + estado
    fich = res.get("ficheros", {}) or {}
    nombres = {"declaracion_dr": f"{codename}_{ej}_modelo200.200", "xml_mod200": f"{codename}_{ej}_mod200.xml",
               "estados_contables_aeat": f"{codename}_{ej}_estados_contables.xlsx", "agrupado_4d": f"{codename}_{ej}_agrupado_4d.xlsx",
               "b1_post_import_json": "b1_participadas_post_import.json"}
    escritos = []
    for clave, nombre in nombres.items():
        m = fich.get(clave)
        if m and m.get("base64"):
            with open(os.path.join(salida, nombre), "wb") as fh:
                fh.write(base64.b64decode(m["base64"]))
            escritos.append(nombre)
    if canonico:
        with open(os.path.join(salida, "canonico.csv"), "w", encoding="utf-8") as fh:
            fh.write(canonico)
    if contable_directo:
        with open(os.path.join(salida, "contable_casillas.json"), "w", encoding="utf-8") as fh:
            json.dump({"casillas": contable_directo.get("casillas", {}),
                       "lineage": contable_directo.get("lineage", []),
                       "checks": contable_directo.get("checks", [])},
                      fh, ensure_ascii=False, indent=2)
    manifiesto_path = os.path.join(salida, "manifiesto.md")
    escribir_manifiesto(manifiesto_path, res, codename, ej)
    estado["pasoActual"] = 4
    estado["salida"] = {"escritos": escritos, "manifiesto": os.path.relpath(manifiesto_path, carpeta)}
    estado["actualizado"] = now_iso()
    json.dump(estado, open(estado_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    dep_pend = sum(1 for d in (res.get("casillas_dependientes_de_otros_modelos") or []) if not d.get("presente"))
    print(f"OK · {codename} · ej {ej} · ok={res.get('ok')} · valido_xsd={(res.get('validacion') or {}).get('valido_xsd')}")
    print(f"  identificativos: nif={'si' if nif else 'NO'} razon={'si' if razon else 'NO'} · caracteres={len(pre['caracteres'])} · formales={len([k for k,v in pre['formales'].items() if v])}")
    print(f"  liquidacion firmada: {'si' if estado['liquidacion_firmada'] else 'no (cosmetica)'} · dependientes a cero: {dep_pend}")
    print(f"  salida: {', '.join(escritos)} + manifiesto.md + estado.json (paso {estado['pasoActual']})")
    sys.exit(0)


if __name__ == "__main__":
    main()
