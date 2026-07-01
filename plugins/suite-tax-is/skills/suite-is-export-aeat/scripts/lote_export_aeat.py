#!/usr/bin/env python3
"""Lote de export AEAT — carpeta de Sumas y Saldos por sociedad -> base de importacion AEAT por sociedad.

Para cada SyS de la carpeta llama al engine (`POST /exportar-aeat`, ADR-001) y escribe, por sociedad:
  - <codename>_<ejercicio>_mod200.xml        (XML mod200 validado contra XSD; entregable PRIMARIO)
  - <codename>_<ejercicio>_modelo200.200     (fichero BOE de ancho fijo importable en Sociedades WEB)
  - <codename>_<ejercicio>_estados_contables_aeat.xlsx (XLSX auxiliar de Balance/PyG/ECPN; no importable)
  - <codename>_<ejercicio>_agrupado_4d.xlsx  (XLSX A3 secundario)
y un informe_lote.md + resumen.csv con ok / valido_xsd / provisional / casillas dependientes / motivo.

Solo orquesta: el numero lo FIRMA el motor (fail-closed; un SyS descuadrado NO emite XML).

PII (regla dura 2): el DR, el XML y los XLSX contienen datos reales (NIF, razon, cifras). En Garrigues Windows
Enterprise, corre contra el motor local/IT (http://127.0.0.1:8000 o URL interna autorizada); NUNCA subas la
carpeta de salida al repo. Los nombres de salida usan un CODENAME (no el NIF). La produccion cloud es DEMO:
usala solo con datos sinteticos.

Uso:
  python3 lote_export_aeat.py --carpeta ./expedientes --ejercicio 2024 --out ./_export_aeat_out
  # opcional, identificativos + liquidacion firmada por sociedad:
  python3 lote_export_aeat.py --carpeta ./expedientes --map ./map.csv --out ./_out
    map.csv (UTF-8, ';'): fichero;codename;nif;razon_social;liquidacion
      - fichero = nombre del SyS (basename)         - liquidacion = ruta a un JSON {casilla: importe} del cierre firmado (opcional)
"""
import argparse, base64, csv, glob, json, mimetypes, os, sys, urllib.parse, urllib.request, urllib.error, uuid

EXTS = (".xls", ".xlsx", ".csv")


def post_multipart(url, fields, file_field, file_path, timeout=180):
    boundary = "----suiteis" + uuid.uuid4().hex
    pre = b""
    for k, v in fields.items():
        pre += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode("utf-8")
    fname = os.path.basename(file_path)
    ctype = mimetypes.guess_type(fname)[0] or "application/octet-stream"
    with open(file_path, "rb") as fh:
        data = fh.read()
    pre += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
            f"filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n").encode("utf-8")
    body = pre + data + (f"\r\n--{boundary}--\r\n").encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def salud(engine):
    try:
        with urllib.request.urlopen(engine.rstrip("/") + "/salud", timeout=15) as r:
            return json.loads(r.read().decode("utf-8")).get("ok") is True
    except Exception:
        return False


def safe_codename(s):
    keep = "".join(c if (c.isalnum() or c in "-_") else "_" for c in s)
    return keep.strip("_") or "sociedad"


def load_map(path):
    m = {}
    if not path:
        return m
    with open(path, encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh, delimiter=";"):
            key = (row.get("fichero") or "").strip()
            if key:
                m[key] = {k: (row.get(k) or "").strip() for k in ("codename", "nif", "razon_social", "liquidacion")}
    return m


def write_b64(meta, dest):
    b64 = (meta or {}).get("base64")
    if not b64:
        return False
    with open(dest, "wb") as fh:
        fh.write(base64.b64decode(b64))
    return True


def main():
    ap = argparse.ArgumentParser(description="Lote de export AEAT (.200 + XML) por sociedad.")
    ap.add_argument("--carpeta", required=True, help="Carpeta con un SyS por sociedad (.xls/.xlsx/.csv).")
    ap.add_argument("--out", default="", help="Carpeta de salida (por defecto <carpeta>/_export_aeat_out).")
    ap.add_argument("--ejercicio", default="2024")
    ap.add_argument("--engine", default="http://127.0.0.1:8000", help="Base URL del engine (LOCAL para datos reales).")
    ap.add_argument("--map", default="", help="CSV opcional fichero;codename;nif;razon_social;liquidacion.")
    ap.add_argument("--solo-contable", action="store_true",
                    help="Emite el .200 SOLO con contable (sin liquidación base). Por defecto el .200 lleva la "
                         "liquidación BASE coherente del motor (págs 12/14/14B) para que importe limpio (sin EMALOBL).")
    args = ap.parse_args()

    if not os.path.isdir(args.carpeta):
        sys.exit(f"ERROR: no existe la carpeta {args.carpeta}")
    out = args.out or os.path.join(args.carpeta, "_export_aeat_out")
    os.makedirs(out, exist_ok=True)
    if os.path.isdir(os.path.join(out, ".git")) or ".git" in os.path.abspath(out).split(os.sep):
        print("AVISO: la carpeta de salida parece estar dentro de un repo git. El DR/XML contienen PII: "
              "asegura que esta gitignored.", file=sys.stderr)
    if "127.0.0.1" not in args.engine and "localhost" not in args.engine:
        print("AVISO: engine no-local. Con datos reales usa solo una URL interna Garrigues autorizada; "
              "el cloud demo es para datos sinteticos.",
              file=sys.stderr)

    if not salud(args.engine):
        sys.exit(f"ERROR: el engine no responde en {args.engine}/salud. Arranca el servicio Windows local "
                 "o configura SUITE_IS_ENGINE_URL y reintenta.")

    mp = load_map(args.map)
    ficheros = sorted(f for f in glob.glob(os.path.join(args.carpeta, "**", "*"), recursive=True)
                      if f.lower().endswith(EXTS) and not os.path.basename(f).startswith(("~$", ".")))
    if not ficheros:
        sys.exit(f"ERROR: no hay ficheros {EXTS} en {args.carpeta}")

    ej = str(args.ejercicio)
    # `ejercicio` va por QUERY STRING (el endpoint /exportar-aeat lo lee como query param; un campo multipart se
    # ignoraba -> default 2024 -> un SyS 2025 descuadraba). El resto (nif/razon/liquidacion) sí son form fields.
    # `liquidacion_base=true` (default, salvo --solo-contable): el .200 lleva la liquidación BASE coherente del
    # motor (págs 12/14/14B/DID) → importa limpio como DECLARACIÓN (sin EMALOBL). Si la sociedad trae liquidación
    # firmada en el map.csv, el motor la usa y este flag es inerte.
    _q = {"ejercicio": ej}
    if not args.solo_contable:
        _q["liquidacion_base"] = "true"
    url = args.engine.rstrip("/") + "/exportar-aeat?" + urllib.parse.urlencode(_q)
    rows = []
    print(f"== Lote export AEAT · {len(ficheros)} sociedad(es) · ejercicio {ej} · engine {args.engine}")
    for i, fpath in enumerate(ficheros, 1):
        base = os.path.basename(fpath)
        cfg = mp.get(base, {})
        codename = safe_codename(cfg.get("codename") or os.path.splitext(base)[0])
        liq = ""
        if cfg.get("liquidacion"):
            try:
                with open(cfg["liquidacion"], encoding="utf-8") as fh:
                    liq = json.dumps(json.load(fh), ensure_ascii=False)
            except Exception as e:
                print(f"  [{i}/{len(ficheros)}] {codename}: liquidacion ilegible ({e}); sigo sin ella.", file=sys.stderr)
        # `ejercicio` NO va aquí (va por query, arriba). nif/razon/liquidacion sí son form fields del endpoint.
        fields = {"nif": cfg.get("nif", ""), "razon_social": cfg.get("razon_social", ""), "liquidacion": liq}
        try:
            res = post_multipart(url, fields, "fichero", fpath)
        except urllib.error.HTTPError as e:
            try:
                detalle = json.loads(e.read().decode("utf-8")).get("detail", str(e))
            except Exception:
                detalle = f"HTTP {e.code}"
            rows.append({"codename": codename, "ok": False, "valido_xsd": "", "provisional": "",
                         "liquidacion": bool(liq), "xlsx_aeat": False, "xlsx_a3": False,
                         "dep_pendientes": "", "motivo": str(detalle)[:200]})
            print(f"  [{i}/{len(ficheros)}] {codename}: ERROR {detalle}"); continue
        except Exception as e:
            rows.append({"codename": codename, "ok": False, "valido_xsd": "", "provisional": "",
                         "liquidacion": bool(liq), "xlsx_aeat": False, "xlsx_a3": False,
                         "dep_pendientes": "", "motivo": str(e)[:200]})
            print(f"  [{i}/{len(ficheros)}] {codename}: ERROR {e}"); continue

        fich = res.get("ficheros", {})
        ok = bool(res.get("ok"))
        if ok and "xml_mod200" in fich:
            write_b64(fich["xml_mod200"], os.path.join(out, f"{codename}_{ej}_mod200.xml"))
        if "declaracion_dr" in fich:
            write_b64(fich["declaracion_dr"], os.path.join(out, f"{codename}_{ej}_modelo200.200"))
        xlsx_aeat = ok and write_b64(
            fich.get("estados_contables_aeat"),
            os.path.join(out, f"{codename}_{ej}_estados_contables_aeat.xlsx"),
        )
        xlsx_a3 = ok and write_b64(
            fich.get("agrupado_4d"),
            os.path.join(out, f"{codename}_{ej}_agrupado_4d.xlsx"),
        )
        dep = res.get("casillas_dependientes_de_otros_modelos") or []
        dep_pend = [d for d in dep if not d.get("presente")]
        val = res.get("validacion", {})
        declaracion = fich.get("declaracion_dr") or {}
        rows.append({"codename": codename, "ok": ok, "valido_xsd": bool(val.get("valido_xsd")),
                     "provisional": bool(declaracion.get("provisional")),
                     "liquidacion": bool(declaracion.get("contiene_liquidacion")),
                     "xlsx_aeat": bool(xlsx_aeat), "xlsx_a3": bool(xlsx_a3),
                     "dep_pendientes": len(dep_pend), "motivo": ("" if ok else str(res.get("motivo", ""))[:200])})
        print(f"  [{i}/{len(ficheros)}] {codename}: {'OK' if ok else 'FAIL'}"
              f"{'' if ok else ' · ' + str(res.get('motivo',''))[:80]}"
              f"{' · XLSX AEAT' if xlsx_aeat else ''}"
              f"{' · XLSX A3' if xlsx_a3 else ''}"
              f"{(' · ' + str(len(dep_pend)) + ' casillas dependientes a cero') if dep_pend else ''}")

    # Informe + CSV
    n_ok = sum(1 for r in rows if r["ok"])
    n_fail = len(rows) - n_ok
    n_dep = sum(1 for r in rows if r["ok"] and r["dep_pendientes"])
    with open(os.path.join(out, "resumen.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["codename", "ok", "valido_xsd", "provisional", "liquidacion", "xlsx_aeat", "xlsx_a3", "dep_pendientes", "motivo"], delimiter=";")
        w.writeheader(); w.writerows(rows)
    lines = [f"# Informe lote export AEAT — ejercicio {ej}", "",
             f"- Sociedades: **{len(rows)}** · OK: **{n_ok}** · con incidencia: **{n_fail}**",
             f"- OK pero con casillas dependientes de otros modelos a cero (revisar 202/222/242/216): **{n_dep}**",
             "- .200 = PROVISIONAL (la AEAT no publica XSD de la declaracion completa): valida la importacion real en Sociedades WEB.",
             "", "| Sociedad | OK | XML valido XSD | XLSX AEAT | XLSX A3 | .200 provisional | Liquidacion | Casillas dep. a 0 | Motivo |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['codename']} | {'OK' if r['ok'] else 'FAIL'} | {r['valido_xsd']} | "
                     f"{r['xlsx_aeat']} | {r['xlsx_a3']} | {r['provisional']} | {r['liquidacion']} | "
                     f"{r['dep_pendientes']} | {r['motivo']} |")
    lines += ["", "## Excepciones (requieren intervención humana)"]
    exc = [r for r in rows if (not r["ok"]) or r["dep_pendientes"]]
    if exc:
        for r in exc:
            why = r["motivo"] or f"{r['dep_pendientes']} casilla(s) dependiente(s) de otros modelos a cero"
            lines.append(f"- **{r['codename']}**: {why}")
    else:
        lines.append("- (ninguna)")
    with open(os.path.join(out, "informe_lote.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"== Hecho. {n_ok} OK / {n_fail} con incidencia. Salida en {out} (informe_lote.md + resumen.csv).")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
