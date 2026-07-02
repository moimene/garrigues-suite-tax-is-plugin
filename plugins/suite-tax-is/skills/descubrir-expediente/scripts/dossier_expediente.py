#!/usr/bin/env python3
"""dossier_expediente.py — DOSSIER de expediente del Impuesto sobre Sociedades: el intake EXHAUSTIVO que carga y
verifica, BLOQUE A BLOQUE, TODA la información que la declaración va a necesitar, ANTES de correr el motor.

Extiende `inventario_carpeta.py` (que clasifica los ficheros) leyendo además el N-1 (`.200` posicional o PDF
best-effort, vía parser_declaracion_previa) y proyectando un CHECKLIST por bloque: captado / parcial / vacío +
fuente + pregunta al abogado para cada hueco. Incluye el bloque de GRUPO FISCAL (00009/00010 → nº de grupo 00040 +
NIF de la dominante), que es config que la AEAT exige y que, si falta, sólo se descubre por rechazo en Open.

DETERMINISTA y sin motor (los parsers son funciones puras). 0 PII en la salida: estados, contadores y códigos de
casilla, nunca NIF/razón/importes (en el chat, codename). Uso:

    python3 dossier_expediente.py "<ruta-de-la-carpeta>"
"""
import sys, os, json, re

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)                                   # inventario_carpeta.py (misma carpeta)


def _add_parser_path():
    """Localiza parser_declaracion_previa.py tanto en el plugin empaquetado (engine/Extractor-parseador/scripts)
    como en el repo (Extractor-parseador/scripts). Tolerante a ambos layouts."""
    cands = [
        os.path.join(_HERE, "..", "..", "..", "engine", "Extractor-parseador", "scripts"),   # plugin empaquetado
        os.path.join(_HERE, "..", "..", "..", "..", "Extractor-parseador", "scripts"),        # repo
    ]
    d = _HERE
    for _ in range(8):                                       # fallback: subir y buscar
        cands.append(os.path.join(d, "Extractor-parseador", "scripts"))
        cands.append(os.path.join(d, "engine", "Extractor-parseador", "scripts"))
        d = os.path.dirname(d)
    for c in cands:
        if os.path.isfile(os.path.join(c, "parser_declaracion_previa.py")):
            sys.path.insert(0, os.path.abspath(c))
            return True
    return False


import inventario_carpeta as inv  # noqa: E402

_PARSER_OK = _add_parser_path()
try:
    import parser_declaracion_previa as pdp  # noqa: E402
except Exception:
    pdp = None
    _PARSER_OK = False


def _precarga_n1(folder, manifest, ejercicio):
    """Parsea el N-1 (preferente `.200` posicional; si no, PDF best-effort) → dict precarga. Sin motor."""
    sel = manifest.get("seleccion_motor") or {}
    if not pdp:
        return {}, None, None
    p200 = sel.get("prev200")
    if p200:
        path = os.path.join(folder, p200)
        try:
            return pdp.parse_200(path, ejercicio=str(int(ejercicio) - 1)), "N-1 .200", os.path.basename(path)
        except Exception:
            pass
    ppdf = sel.get("modelo200_pdf")
    if ppdf:
        path = os.path.join(folder, ppdf)
        try:
            return pdp.parse_pdf(path, ejercicio=str(int(ejercicio) - 1)), "N-1 PDF (best-effort)", os.path.basename(path)
        except Exception:
            pass
    return {}, None, None


def _estado(captado, parcial=False):
    return "captado" if captado else ("parcial" if parcial else "vacio")


def construir_dossier(folder, ejercicio="2025"):
    roles, sysinfo, notes, faltan, reco, preguntas, manifest = inv.scan(folder)
    prec, fuente_n1, fichero_n1 = _precarga_n1(folder, manifest, ejercicio)
    car = (prec.get("caracteres") or {}) if prec else {}
    ident = (prec.get("identificativos") or {}) if prec else {}
    flags = sorted(k for k in car if re.match(r"^0\d{4}$", str(k)))      # caracteres tipo flag (X NNNNN)
    bloques = []

    def add(nombre, captado, detalle, fuente, parcial=False, pregunta=None, critico=False, confirmar=False,
            datos=None):
        est = _estado(captado, parcial)
        # El abogado debe confirmar (no sólo cuando falta): también si la fuente es PDF best-effort (extracción
        # falible) o si es configuración de alto impacto (grupo fiscal, modelo de cuentas) marcada con confirmar=True.
        _best_effort = "best-effort" in (fuente or "").lower()
        req = (est != "captado") or confirmar or _best_effort
        if _best_effort and est == "captado" and "confirmar aunque" not in detalle:
            detalle += " · CONFIRMAR aunque salga poblado (extracción PDF best-effort)"
        bloque = {"bloque": nombre, "estado": est, "detalle": detalle,
                  "fuente": fuente, "critico": critico, "requiere_confirmacion": req,
                  "pregunta": pregunta if not captado else None}
        if datos is not None:   # valores para la FICHA (casilla:importe); el `detalle` queda 0-PII (códigos/contadores)
            bloque["datos_ficha"] = datos
        bloques.append(bloque)

    # 1. Identificativos (NIF + denominación + CNAE) — bloquea si falta NIF/denominación
    nif, razon, cnae = bool(ident.get("nif")), bool(ident.get("razon_social")), bool(ident.get("cnae"))
    add("Identificativos (NIF · denominación · CNAE)", nif and razon,
        f"NIF {'✓' if nif else '—'} · denominación {'✓' if razon else '—'} · CNAE {'✓' if cnae else '—'}",
        fuente_n1 or "datos fiscales / N-1", parcial=(nif or razon),
        pregunta="Aporta NIF + denominación (y CNAE 2025) del N-1 o de los datos fiscales.", critico=True)

    # 2. Caracteres de configuración pág 1 (tipo entidad / régimen)
    add("Caracteres de configuración (pág 1)", bool(flags),
        f"{len(flags)} marcados: {', '.join(flags) if flags else '—'}", fuente_n1 or "N-1",
        pregunta="Sin caracteres del N-1: confirma tipo de entidad/régimen para la página 1.")

    # 3. GRUPO FISCAL (00009 dominante / 00010 dependiente) → nº grupo 00040 + NIF de la dominante
    es_dom, es_dep = car.get("00009") == "1", car.get("00010") == "1"
    if es_dom or es_dep:
        tiene_g40 = bool(str(car.get("00040") or "").strip())
        # dominante: el NIF de la dominante = su propio NIF (declarante). dependiente: NIF de la dominante (del grupo)
        tiene_nifdom = es_dom or bool(str(car.get("nif_dominante") or "").strip())
        rol = "dominante (00009)" if es_dom else "dependiente (00010)"
        add("Grupo fiscal (nº de grupo + NIF dominante)", tiene_g40 and tiene_nifdom,
            f"{rol} · nº de grupo 00040 {'✓' if tiene_g40 else '✗'} · NIF dominante {'✓' if tiene_nifdom else '✗'}",
            fuente_n1 or "N-1 (pág 1B)", parcial=(tiene_g40 or tiene_nifdom),
            pregunta=("Falta el Nº de grupo fiscal (00040) y/o el NIF de la sociedad dominante. Están en el "
                      "Modelo 200 N-1 (pág 1: «Número de grupo fiscal» y «NIF de la entidad representante/"
                      "dominante»). Apórtalos para que la declaración del miembro importe."), critico=True, confirmar=True)

    # 4. Modelo de estados de cuentas (pág 1B) — del N-1 (la continuidad año a año es la norma: cambiar de modelo
    #    es excepcional). Si viene de `.200` N-1, queda CERRADO por continuidad y no se plantea como hueco; si viene
    #    de PDF best-effort se muestra para confirmación. Si no consta, se pregunta.
    _me = (prec.get("modelo_estados") or {}) if prec else {}
    if _me:
        _txt = (f"N-1: Balance {_me.get('balance', '?')} · ECPN {_me.get('ecpn', '?')} · PyG {_me.get('pyg', '?')}"
                " — ARRASTRADO por continuidad")
        _no_normal = any(v in ("abreviado", "pymes") for v in _me.values())
        if _no_normal:
            _txt += " · el motor emite abreviado/PYMES (opt-in, certificado en Open); en esos modelos el ECPN es VOLUNTARIO"
        add("Modelo de estados de cuentas (pág 1B)", True, _txt, fuente_n1 or "N-1",
            confirmar=("best-effort" in (fuente_n1 or "").lower()))
    else:
        add("Modelo de estados de cuentas (pág 1B)", False,
            "no consta en el N-1; el motor presenta NORMAL por defecto; confírmalo (normal/abreviado/PYMES)",
            "N-1 / CCAA", parcial=True,
            pregunta="Confirma el modelo de estados de cuentas (normal/abreviado/PYMES).")

    # 5-8. Bloques mercantiles del N-1
    adm = len(prec.get("administradores") or []) if prec else 0
    b1 = prec.get("participaciones_b1") or [] if prec else []
    b2 = prec.get("participaciones_b2") or [] if prec else []
    reps = len(prec.get("representantes") or []) if prec else 0
    tit = len(prec.get("titulares_reales") or []) if prec else 0
    b1_inc = sum(1 for e in b1 if not str(e.get("pais") or "").strip())
    add("Administradores (apartado A)", adm > 0, f"{adm} administrador(es)", fuente_n1 or "N-1",
        pregunta="Aporta administradores (apartado A) del N-1.")
    add("B.1 — sociedades en las que participa", len(b1) > 0,
        f"{len(b1)} participada(s)" + (f" · {b1_inc} sin país (revisar)" if b1_inc else ""),
        fuente_n1 or "N-1", parcial=(b1_inc > 0),
        pregunta="Aporta el bloque B.1 (sociedades participadas) del N-1, con país/nominal/%.")
    add("B.2 — socios/partícipes de la declarante", len(b2) > 0, f"{len(b2)} socio(s)", fuente_n1 or "N-1",
        pregunta="Aporta el bloque B.2 (socios) del N-1, con NIF + % de participación.")
    add("Titular real / secretario / representantes", (tit + reps) > 0,
        f"titular real {tit} · representantes {reps}", fuente_n1 or "N-1",
        pregunta="Confirma titular real / representantes (o exención del art. 4.2).")

    # 8b. Arrastre de liquidación N-1 que ahorra picado (SURFACE, no decide — ADR-001): BINs pendientes (art. 26
    #     LIS) extraídos del N-1 + recordatorio de deducciones pendientes por insuficiencia de cuota. El motor se
    #     nutre del N-1 pero el abogado confirma (HITL). Importes -> FICHA (datos_ficha); detalle 0-PII.
    _arr = (prec.get("pendientes_arrastre") or {}) if prec else {}
    _bins = _arr.get("bins")
    add("BINs pendientes de compensar (art. 26 LIS) — arrastre N-1", bool(_bins),
        (f"N-1: {_bins['n_anios']} año(s) con saldo pendiente a aplicar (ver importe en FICHA) — confirmar"
         if _bins else "no detectados en el N-1 (o N-1 sin tabla de compensación); revisar manualmente si procede"),
        fuente_n1 or "N-1 (DP200015)", parcial=bool(_bins),
        pregunta="Confirma las BINs pendientes de compensar a arrastrar (art. 26 LIS); el motor no decide la compensación.",
        datos=({"bins_pendientes_total": _bins["total_euros"], "n_anios": _bins["n_anios"]} if _bins else None))
    add("Deducciones pendientes por insuficiencia de cuota — arrastre N-1", False,
        "revisar en el N-1 (deducciones doble imposición/incentivos pendientes de aplicar); arrastre manual del abogado",
        "N-1 (liquidación)", parcial=True,
        pregunta="Revisa y arrastra las deducciones pendientes por insuficiencia de cuota del N-1 (HITL; el motor no decide).")

    # 9. Contabilidad con apertura N-1 (ECPN) — del inventario (sysinfo). El ECPN es OBLIGATORIO solo en modelo de
    #    cuentas NORMAL; en abreviado/PYMES es VOLUNTARIO -> no bloquea ni exige apertura N-1 (no se incluye por
    #    defecto; el motor lo omite limpio y declara ECPN «no consta»). Solo haría falta si el abogado opta por
    #    incluir el ECPN explícitamente.
    _ecpn_voluntario = any(_me.get(k) in ("abreviado", "pymes") for k in ("balance", "ecpn", "pyg"))
    if _ecpn_voluntario:
        add("Contabilidad con apertura N-1 (ECPN)", True,
            "ECPN VOLUNTARIO (modelo abreviado/PYMES): no se incluye por defecto; la apertura N-1 no es necesaria "
            "salvo que el abogado opte por incluir el ECPN.",
            "modelo de cuentas (pág 1B)")
    else:
        ap_ok = bool(sysinfo and sysinfo.get("legible") and sysinfo.get("tiene_saldo_inicial")
                     and sysinfo.get("saldo_inicial_no_cero", 0) > 0)
        hay_ccaa = bool(roles.get("ccaa"))
        add("Contabilidad con apertura N-1 (ECPN)", ap_ok,
            ("apertura N-1 presente" if ap_ok else
             ("sin apertura, pero hay CCAA: el motor la deriva (revisar ECPN en Fase 2)" if hay_ccaa
              else "sin apertura y SIN CCAA: el ECPN se rechazará (E25400632/645)")),
            "SyS (saldo inicial) / CCAA (columna N-1)", parcial=(not ap_ok and hay_ccaa),
            pregunta="Regenera el SyS con apertura N-1 real (skill ccaa-a-sys-a3) o aporta la CCAA.",
            critico=(not ap_ok and not hay_ccaa))

    # 10. Datos fiscales del ejercicio — PARSEADO best-effort. Es bloque P0 de intake porque aporta pagos a cuenta,
    #     retenciones, arrastres fiscales y alertas de ajustes extracontables. Frontera ADR-001:
    #     - casillas directas verificadas contra DR (01766, 00601/003/005) -> liquidación, con confirmación;
    #     - BINs/deducciones pendientes -> arrastres HITL;
    #     - sanciones/recargos/intereses/procedimientos -> ajustes_hitl/gestión, nunca autoaplicados.
    #     Los IMPORTES van a la FICHA (datos_ficha); el `detalle` queda 0-PII (códigos + contador).
    #     Extracción de PDF = revisión del abogado OBLIGATORIA.
    _df_path = (manifest.get("seleccion_motor") or {}).get("datos_fiscales")
    if _df_path and pdp:
        _df = pdp.parse_datos_fiscales(os.path.join(folder, _df_path))
        _cods = sorted((_df.get("casillas") or {}).keys())
        _n_arr = len(_df.get("arrastres") or [])
        _n_ajt = len(_df.get("ajustes_hitl") or [])
        _n_ges = len(_df.get("gestion") or [])
        _est = _df.get("estado", "vacio")
        _det = (f"parseado best-effort: {len(_cods)} casilla(s) directas {_cods}"
                + f" · arrastres { _n_arr } · ajustes HITL { _n_ajt } · gestión/terceros { _n_ges }"
                + (" · PDF imagen sin texto → visión" if _df.get("requiere_vision") else "")
                + " · confirmar aunque salga poblado")
        add("Datos fiscales del ejercicio (AEAT 2025 completo)", _est == "captado", _det,
            "datos fiscales PDF (best-effort)", parcial=(_est == "parcial"),
            pregunta=("Confirma datos fiscales AEAT 2025: retenciones/pagos fraccionados van a liquidación; "
                      "BINs/deducciones a arrastres; sanciones/recargos/intereses/procedimientos a revisión HITL "
                      "de ajustes. La extracción PDF es falible."),
            datos=({
                "casillas_directas": _df.get("casillas") or {},
                "arrastres": _df.get("arrastres") or [],
                "ajustes_hitl": _df.get("ajustes_hitl") or [],
                "gestion": _df.get("gestion") or [],
            } if _est != "vacio" else None))
    else:
        add("Datos fiscales del ejercicio (AEAT 2025 completo)", False,
            "no aportados (sin retenciones/pagos fraccionados, arrastres, deducciones pendientes ni alertas AEAT precargadas)",
            "datos fiscales PDF",
            pregunta=("Aporta la Consulta de Datos Fiscales AEAT 2025 digital. Debe revisarse para retenciones, "
                      "pagos fraccionados Modelo 202, BINs/deducciones pendientes, sanciones, recargos, intereses, "
                      "procedimientos y operaciones de terceros."))

    n_captado = sum(1 for b in bloques if b["estado"] == "captado")
    n_vacio = sum(1 for b in bloques if b["estado"] == "vacio")
    criticos_pendientes = [b for b in bloques if b["critico"] and b["estado"] != "captado"]
    confirmacion_requerida = [b["bloque"] for b in bloques if b.get("requiere_confirmacion")]
    dossier = {
        "codename": manifest.get("codename"), "ejercicio": str(ejercicio),
        "fuente_n1": fuente_n1, "fichero_n1": fichero_n1, "parser_ok": _PARSER_OK,
        "bloques": bloques, "n_bloques": len(bloques), "n_captado": n_captado, "n_vacio": n_vacio,
        "criticos_pendientes": [b["bloque"] for b in criticos_pendientes],
        "confirmacion_requerida": confirmacion_requerida,
        # El motor NO arranca hasta que el abogado confirma la ficha: aunque no haya críticos pendientes,
        # la configuración leída del N-1 (sobre todo PDF best-effort y grupo fiscal) debe validarla una persona.
        "requiere_confirmacion_abogado": bool(confirmacion_requerida),
        "listo_para_motor": manifest.get("listo_para_motor") and not criticos_pendientes,
        "inventario": manifest,
    }
    return dossier


def main():
    if len(sys.argv) < 2:
        sys.exit('Uso: python3 dossier_expediente.py "<ruta-de-la-carpeta>" [ejercicio]')
    folder = os.path.abspath(sys.argv[1])
    ejercicio = sys.argv[2] if len(sys.argv) > 2 else "2025"
    if not os.path.isdir(folder):
        sys.exit(f"ERROR: no existe la carpeta {folder}")
    d = construir_dossier(folder, ejercicio)
    icon = {"captado": "✓", "parcial": "◐", "vacio": "✗"}
    print(f"DOSSIER — {d['codename']} · ejercicio {d['ejercicio']}"
          + (f" · N-1: {d['fuente_n1']}" if d["fuente_n1"] else " · SIN N-1 (formales/config en blanco)"))
    if not d["parser_ok"]:
        print("  ⚠ parser N-1 no disponible en este entorno: el dossier sólo refleja el inventario de ficheros.")
    for b in d["bloques"]:
        crit = " [crítico]" if b["critico"] and b["estado"] != "captado" else ""
        print(f"  {icon[b['estado']]} {b['bloque']}{crit}: {b['detalle']}  ·  fuente: {b['fuente']}")
    print(f"  RESUMEN: {d['n_captado']}/{d['n_bloques']} captados · {d['n_vacio']} vacíos"
          + (f" · CRÍTICOS pendientes: {', '.join(d['criticos_pendientes'])}" if d["criticos_pendientes"] else ""))
    # FICHA DE CONFIGURACIÓN PROPUESTA: el read-back que el abogado confirma o corrige ANTES de generar.
    conf = [b for b in d["bloques"] if b.get("requiere_confirmacion")]
    if conf:
        print("  ── FICHA DE CONFIGURACIÓN PROPUESTA (confírmala o corrígela antes de generar el .200) ──")
        for b in conf:
            marca = {"vacio": "COMPLETAR", "parcial": "REVISAR"}.get(b["estado"], "CONFIRMAR")
            print(f"    [{marca}] {b['bloque']}: {b['detalle']}  ·  fuente: {b['fuente']}")
            if b.get("pregunta"):
                print(f"             ↳ {b['pregunta']}")
    print("  LISTO PARA MOTOR: " + (
        "sí, una vez el abogado CONFIRME la ficha de arriba" if d["listo_para_motor"]
        else "no — cierra antes los críticos/huecos"))
    print("JSON " + json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
