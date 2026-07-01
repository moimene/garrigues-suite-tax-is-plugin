---
name: suite-is-motor
description: >-
  El motor fiscal Python canónico de Suite Tax IS (ADR-001): el cerebro que firma el número del Impuesto
  sobre Sociedades (Modelos 200/202/222). Úsala cuando el trabajo toque el cálculo de servidor, no la
  mecánica de Harvey: liquidar/firmar/gating/emitir el Modelo 200 por el engine_service, hacer el
  doble-check del número, correr el sanity de no-regresión contra el oráculo GIP, entender la cadena de
  casillas (00550→00547→00552→00562→cuota→00621) y el tope de BINs (art. 26 LIS), los perfiles
  normal/abreviado/PYMES, ECPN, pagina 20 de gastos financieros, proxy foral N-1, SOCIMI, datos fiscales como
  intake HITL, el contrato del bloque parseable que intercambian WF-1 y WF-2, o el puente que renderiza los
  entregables deterministas. Si la pregunta es operar Harvey (Spaces, editar/correr WF-1/WF-2), usa antes
  harvey-sociedades.
metadata:
  version: "1.5.0"
---

# Suite IS — el motor fiscal canónico (cerebro de servidor)

El **motor Python es el cerebro fiscal canónico** (ADR-001, 2026-06-06): firma el número que va al XML
del Modelo 200 y al gating. La web, Harvey y el puente lo **consumen por servicio**; no se reescribe
lógica fiscal fuera de él (el motor de reglas TS está retirado, ADR-002, 2026-06-08). Esta skill es la
vía del taller y el **doble-check** del número que Harvey produce.

## Estado v1.18.1 de importabilidad

La release 2026-07-01 consolida el motor como generador de **base de importacion** `.200` + XML:

- perfiles de estados contables `normal`, `abreviado` y `pymes`;
- ECPN por saldos de balance N/N-1 cuando procede;
- parser directo de Balance/PyG formulado cuando no hay SyS A3 usable;
- pagina 20 de gastos financieros y casillas calculadas por OpenWeb;
- tributacion foral con pagina 26 obligatoria y proxy N-1 marcado como HITL;
- SOCIMI con cuota 0 del Modelo 200 cuando procede;
- precarga N-1 exhaustiva: administradores completos, B.1/B.2 con complementarias `C`, titulares reales
  adicionales y caracter `00027` no arrastrado por depender del resultado 2025;
- datos fiscales AEAT como Fase 0 de intake.

Sociedades WEB/OpenWeb sigue siendo el gate real. El validador interno reduce iteraciones, pero no sustituye el
resultado de importacion.

## Reglas de oro
1. **El motor firma el número.** Si una cifra de Harvey y la del motor discrepan, manda el motor; abre
   incidencia, no "ajustes" a mano.
2. **GIP es no-regresión.** Las cifras-ancla del oráculo (abajo) no cambian sin tests verdes que lo
   justifiquen. Antes de cerrar cualquier cambio de código: `make test && python3 -m pytest parser_core/tests -q && npm run build`.
3. **Confidencialidad.** `CLIENTES/`, `GIP*/` y cualquier dato real son solo locales y gitignored; nunca
   al repo ni a salidas con PII. Las cifras-ancla del oráculo son agregadas y ya constan en `PROGRESO.md`.
4. **Migraciones/RLS en Supabase → aprobación explícita del usuario.** El push/PR es paso humano.

## El servicio (engine_service, FastAPI)
- **Producción (DEMO, datos sintéticos):** `https://suite-is-engine-production.up.railway.app`.
  Salud: `curl -s https://suite-is-engine-production.up.railway.app/salud` → `{"ok":true,"servicio":"engine_service",...}`.
- **Local (desarrollo desde el repo):** `make dev` levanta motor `:8000` + web `:5173`. En **distribución** el motor corre en `127.0.0.1:8000` como **servicio Windows** (Enterprise) o **bundle portable win64** (no-enterprise), no con `make dev` — ver skill `arrancar-motor`.
- **Endpoints (contrato del servicio).** Núcleo documentado en `CLAUDE.md`: `/salud`, `/liquidar`,
  `/firmar`, `/gating`, `/emitir-mod200`, `/reconciliar`, `/expediente/*`. La Fase 1 (core WF-Harvey en
  la consola, sellada 2026-06-13) añadió el **seam orquestado**: `liquidar_orquestado` + `/liquidar-orquestado`
  (y `/firmar` migrado; `/liquidar` queda como red anti-doble-cálculo), `/triaje` (art. 15),
  `/explicar` (fundamento), `GET /reglas-activas` (espejo read-only de las reglas Python) y
  `POST /auditoria-mayores` (read-only, no firma/gating). Verifica la firma exacta de cada endpoint en
  `engine_service/` antes de integrar; los recuentos de tests evolucionan (estado en `PROGRESO.md`).
- **Dos motores que cablea la consola:** `motor_expediente.liquidar_expediente` (liquidación) y
  `motor_triaje_art15.clasificar` (triaje). El lineage/trazas (`on_traza`) ya existe.

## La cadena fiscal (lo que firma el motor)
Cadena de casillas del Modelo 200 que el WF-2 y el motor recalculan, **al céntimo, HALF_UP**:

**Cadena oficial completa** (validada contra el Manual 2025, Cap 05/06):
`00500 → 00501 → 00550 (base previa) → (− 01032 reserva capitalización − 00547 BINs) → 00552 (base imponible)
→ 01330 (tras reserva nivelación) → 00562 (cuota íntegra) → 00582 (cuota íntegra ajustada) → 00592 (cuota
líquida) → 00599 (cuota del ejercicio) → 00611 (cuota diferencial) → 01586 → 00621 (a ingresar/devolver)`.
El esqueleto que más se cita (`00550→00547→00552→00562→00621`) es correcto pero **salta** 01032/00582/00599/00611/01586.

- **Base imponible previa (00550), D8:** `B12 = B2 + B3 + B4 + B5` ≡ fórmula oficial `00550 = 00501 + (00417 − 00418)`,
  donde **B2 = resultado contable (00500)**; **B3 = corrección por el IS = par `00301 − 00302` (+ `00004` si hay
  Impuesto Complementario)**, no solo 00301; B4 = ajustes permanentes, B5 = ajustes temporarios. Control
  **`B2 + B3 = resultado antes de impuestos`** (= casilla **00501**) CONFIRMADO (Manual Cap 05; art. 15.b LIS).
  Para sociedad estándar (00302=00004=0) coincide al céntimo con `construir_plantilla.py` (`=B2+B3+B4+B5`).
- **Tope de compensación de BINs (art. 26 LIS / DA 15ª), por INCN individual** (casilla 00255 del Modelo
  200 anterior): **< 20 M€ → 70 %** (mínimo 1.000.000 € siempre compensable) · **20–60 M€ → 50 %** ·
  **≥ 60 M€ → 25 %**, sobre la base previa (`min(BINs_pendientes, max(mínimo, límite × base_previa), base_previa − B8)`).
  Confirmado contra Manual Cap 05. **Cautelas (no en la fórmula base):** (1) los tramos 50/25 % de la DA 15ª
  tienen **vigencia acotada** (períodos iniciados desde 1-ene-2024 no concluidos a 22-dic-2024; reinstaurados
  tras la STC que anuló el RDL 3/2016) → no son atemporales; (2) el **mínimo de 1 M€ se prorratea** si el
  período < 12 meses; (3) **excepciones** al límite (quitas/esperas, extinción, nueva creación art. 26.3 →
  casilla 00070, reversión de deterioros pre-2021); (4) no confundir con el límite **homónimo del art. 11.12
  LIS** (deterioros art. 13.1: mismos 70/50/25 % y misma DA 15ª, concepto distinto).
- ⚠️ **Discrepancia del taller a reconciliar:** `suite-is/scripts/puente_entregables_v3.py:140` calcula
  `B12 = B2 + B4 + B5` bajo otra convención (B2 = pre-impuestos) y lo **etiqueta** `B2+B3+B4+B5`
  (línea 385). Antes de fiarte de la salida del puente, **cuádrala contra el oráculo GIP**; el número que
  vale es el del motor/WF-2. (No tocar sin tests verdes — regla 2.)

## Oráculo de no-regresión (GIP)
Cifras-ancla verificables en la cabecera de `PROGRESO.md`. Si una corrida las reproduce, el entorno está sano.

- **GIP 2024 (depurado, D8):** 00500 = **47.105.268,85** · ACTIVO = PN+PASIVO = **436.912.437,01** ·
  BI 00552 = **11.068.602,43** · cuota 00562 = **2.767.150,61** · a ingresar 00621 = **2.486.355,42** ·
  **0 divergencias**. (147.417.876,97 / 561.111.165,52 = contable **2025**, caso aparte `/caso/gip2025-sys`.)
- **GIP 2025 (sanity de los WF Harvey):** BI 00552 = **3.208.497,87** · cuota 00562 = **802.124,47** ·
  a ingresar 00621 = **802.124,47**.
- **Casos dorados reales** (`suite-is/tests/test_golden_casos_reales.py`): CASO_REAL_2 (BI<0 → cuota 0),
  CASO_REAL_3 (temporarias → devolución −568.103,76), CASO_REAL_4 (BIN 50 % por INCN 20–60 M€ →
  devolución −484.517,84). Regresión golden **3/3 PASS** contra WF-2 V10 (2026-06-13).

## El contrato del bloque parseable (la API entre superficies)
WF-1, WF-2, el puente y la consola intercambian estado como **TEXTO estructurado** (claves estables = API):

- **WF-1 emite:** `## ESTADO_HARNESS`, `## 01_DATOS`, `## 02_ISSUES`, `## 03_LIQUIDACION_INPUTS` (B2:B10).
- **WF-2 emite:** `ESTADO_HARNESS_V2` (`{H_fase, H_estado, H_sem_rojo, H_sem_verde, H_validada, pendientes_para_siguiente}`)
  + `03_LIQUIDACION_INPUTS_V2` + `05_MAPPING_M200` (casilla|importe + referencia_normativa).
- **Gating:** exporta solo si **🔴 = 0 ∧ 🟡 (impacto) = 0 ∧ `H_validada = sí`**; si no, «BORRADOR no presentable».

Es el contrato a congelar con spec + test; no cambies las claves sin actualizar a todos los consumidores.

## El puente (entregables deterministas, vía taller)
Harvey emite el **texto/bloque** (fiable); un **motor determinista** renderiza los entregables (Document
drafting de Harvey está descartado por probabilístico). Copia el bloque final de WF-2 a un `.txt` **fuera
de git** (`~/Downloads`) y ejecuta:

```bash
python3 suite-is/scripts/puente_entregables_v3.py \
  --bloque ~/Downloads/bloque_final.txt --output-dir ~/Downloads/{CODENAME}_{año}_entregables \
  --nif {CODENAME} --ejercicio {año}
```

Produce, branded Garrigues: `Modelo_200_*.xlsx` · `Liquidacion_*.docx` · `Memoria_Tecnica_*.docx`.
Verifica que imprime 00552/00562/00621 correctos y cuádralos contra el oráculo. Scripts hermanos:
`carta_solicitudes.py` (carta WF-1), `exportar_sys_a3.py` (A3, 6 columnas
`Cuenta|Descripcion|Saldo Final|Debe|Haber|Saldo Inicial`).

## Comprobaciones antes de cerrar un cambio de código
```bash
make test && python3 -m pytest parser_core/tests -q && npm run build
```
Deploy según `DEPLOY.md` (Railway `railway up` + Vercel `vercel deploy --prod`); no reintroducir
`startCommand` en `railway.json` (causa raíz del healthcheck PORT documentada ahí).

## Fuentes (repo `is200transmittalApp`)
- `CLAUDE.md` — frontera de sistemas, endpoints, checks, oráculo.
- `PROGRESO.md` — cifras-ancla y estado P0/P1/P2. `DECISIONES.md` — D1–D18. ADR-001 / ADR-002.
- `docs/memoria/INDEX.md` — punto de entrada de la memoria viva (incl. Fase 1 core consola, Fase 3 ingesta, Fase 4 auditoría).
- `suite-is/Manual_Sociedades_2025_md/` — Manual práctico AEAT (fuente de la cadena de casillas; Cap 05 base, Cap 06 deuda).
- `docs/memoria/2026-06-17-revision-manual-procesos.md` — validación citada de la cadena + tope BIN + matices D8.
- `suite-is/`, `engine_service/`, `parser_core/`, `Extractor-parseador/` — el motor.
