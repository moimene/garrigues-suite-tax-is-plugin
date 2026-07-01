---
name: harvey-sociedades
description: >-
  Operar Harvey (eu.app.harvey.ai, org Garrigues) para la campaña del Impuesto sobre Sociedades
  (Modelo 200): usar Spaces, Vaults y Workflow Agents (WF-1 Análisis · WF-2 Cierre), el patrón
  expediente = 1 Space, el handoff del «resumen de estado» WF-1→WF-2, el gating, generar los
  entregables con el puente Python, y editar/renombrar/publicar workflows u onboarding del Space.
  ÚSALA SIEMPRE que el trabajo toque Harvey + Impuesto sobre Sociedades / Modelo 200 / "Sociedades":
  preparar o revisar una declaración del IS en Harvey, correr o editar WF-1/WF-2, montar o sanear un
  Space/Vault de expediente, el bloque parseable, los entregables (Memoria/Liquidación/Modelo 200), o
  dudas de mecánica de Harvey (subir ficheros, "Edit prompt", "Customize", "View as", publicar). Aunque
  el usuario no diga "skill", si menciona Harvey + Sociedades/IS/Modelo 200, úsala.
---

# Harvey — Campaña de Sociedades (Impuesto sobre Sociedades · Modelo 200)

Manual operativo para preparar el Modelo 200 **dentro de Harvey** (Spaces + Workflow Agents + Vault),
como *fallback* fiable de la plataforma web (ADR-001). Codifica mecánica **verificada en vivo**: sigue
los gotchas al pie de la letra — ahorran horas y evitan publicar/borrar por error.

## Reglas de oro (léelas antes de tocar nada)
1. **Mira antes de afirmar.** Primera acción **siempre**: un screenshot para orientarte. No asumas el
   estado de la UI; cámbialo solo tras verlo.
2. **Tú conduces, el abogado sube los ficheros.** La automatización **no puede subir ficheros** a Harvey
   ni manejar el diálogo de archivos del SO. Tú navegas, seleccionas régimen, tecleas en los pasos de
   texto, copias/pegas el bloque y lanzas el puente; **el abogado sube** los documentos en cada run.
3. **Lo irreversible lo ejecuta el usuario.** **No borres** workflows ni **publiques** cambios sin OK
   explícito del usuario. Renombrar es reversible; publicar contenido y borrar, no.
4. **No toques workflows de otros.** Solo se editan los de `moises.menendez@garrigues.com`. Los
   "Conversor…" de Stefano (dependencia de la Fase A de WF-1) y los "[MERC]" de Belén: **intactos**.
5. **Confidencialidad.** NIF, razón social, contabilidad e importes del cliente viven **solo** en el
   Vault/Space del expediente — **nunca** en git, ni en esta skill, ni en nombres/descr. de workflows
   (Harvey avisa: "do not include confidential info" en esos campos).

## Cómo conducir Harvey
- Herramienta: el **MCP `claude-in-chrome`** (si está diferido, cárgalo con ToolSearch "claude-in-chrome").
  Harvey está en **eu.app.harvey.ai** (esfera Garrigues). Crea/usa una pestaña con `tabs_context_mcp`.
- Si la extensión no está conectada o no hay sesión logueada, **pídeselo al usuario** (no puedes loguear).
- En el dominio Harvey **el JS está bloqueado**; usa `read_page` / `get_page_text` / screenshots para leer.
- Límites: `computer wait` ≤ 10 s; `scroll_amount` ≤ 10; agrupa acciones con `browser_batch`.

## Arquitectura — el pipeline en una frase
**① Análisis (WF-1) → «resumen de estado» (bloque) + carta y A3 como TEXTO → (pausa) → ② Cierre (WF-2) →
gating → entregables como TEXTO (pasos `entregable_*`) + bloque final → pegar en las plantillas Garrigues
del Vault.** Solo **2 toques humanos**: validar incidencias (WF-1) y validar el número (WF-2).
*(Refactor 2026-06-10: Harvey AUTOSUFICIENTE — sin Document drafting; el puente queda como vía del taller.)*
*(Estado consolidado 2026-06-13: **WF-2 Version 10** + **lote v1.4 saneado D1–D10** publicados; D12
resuelto; **regresión golden 3/3 PASS**. Resumen al final, en «Estado y versión».)*

- **WF-1** "① EMPIEZA AQUÍ · Análisis" — builder `019e991b-7165-7268-90fb-09114abb486c`. Fases 1-3:
  intake (Fase A: ingiere el SyS y deriva B2/B3/B10), motor de issues (citas LIS/RIS/BOE), liquidación
  preliminar, carta de solicitudes. Emite el **bloque parseable**: `## ESTADO_HARNESS`, `## 01_DATOS`,
  `## 02_ISSUES`, `## 03_LIQUIDACION_INPUTS`.
- **WF-2** "② Cierre y entrega" — builder `019e9942-1889-7874-89e4-417fd3c526b9`. Fase 4: ingiere el
  bloque + respuestas del cliente, recalcula, **valida el número** en el **Checkpoint 2 dedicado**
  (paso `validacion_numero`), **gating duro**, emite el bloque final `ESTADO_HARNESS_V2` +
  `03_LIQUIDACION_INPUTS_V2` + `05_MAPPING_M200`.
- **D12 RESUELTO (V10, 2026-06-13):** el gating lee la validación del Checkpoint 2 por una
  **@-referencia INLINE `@validacion_numero`** dentro del prompt `gating_resultado` (tenerla solo en
  «Workflow Agent context» NO inyectaba su contenido → daba `H_validada = no`). Por eso **se valida en
  el paso dedicado** (Paso 9); el workaround v1.3 de validar en el primer paso de ② quedó **revertido**.
- **Gating** (en WF-2): exporta solo si **🔴 = 0 ∧ 🟡 (impacto) = 0 ∧ `H_validada = sí`**; si no →
  «BORRADOR no presentable».
- **Entregables fiables = TEXTO emitido por Harvey** en los pasos `carta_solicitudes_texto` (WF-1) y
  `entregable_memoria` / `entregable_liquidacion` / `entregable_modelo200` (WF-2, gating-aware), que el
  abogado pega en las **plantillas Garrigues del Vault** (`plantillas_vault/`). Los Document drafting se
  ELIMINARON (probabilísticos, salían en blanco). El puente Python queda como vía del taller (lotes/Excel-estado).
- Verifica los IDs en **Build → Manage** (`eu.app.harvey.ai/workflows/manage`); el builder es
  `eu.app.harvey.ai/workflows/workflow-builder/{id}`.
- **Caso de referencia (sanity check), GIP 2025:** BI (00552) = **3.208.497,87** · cuota íntegra (00562)
  = **802.124,47** · a ingresar (00621) = **802.124,47**. (GIP 2024: 11.068.602,43 / 2.767.150,61 /
  2.486.355,42.) Si tu run reproduce estas cifras, el entorno está sano.
- **Regresión golden 3/3 PASS sobre WF-2 V10 (2026-06-13):** además del sanity GIP, los 3 casos dorados
  reales del motor se reprodujeron al céntimo contra ② en vivo — CASO_REAL_2 (BI<0 → cuota 0),
  CASO_REAL_3 (temporarias → devolución −568.103,76) y CASO_REAL_4 (BIN al 50 % por INCN 20-60 M€ →
  devolución −484.517,84), los 3 con `H_validada:si` y EXPORTABLE. El recálculo fiscal del WF coincide
  con el motor Python canónico (cadena 00550→00547→00552→00562→cuota líquida→00621, tope BIN art. 26).

## Qué NO auto-detecta la campaña (valídalo a mano en el Checkpoint 1)
El motor de issues **sí** cubre: gastos no deducibles art. 15 (13 letras + 15 bis), exención art. 21 (div y
pv), compensación de BINs con tope por INCN, limitación de gastos financieros art. 16, reservas de
capitalización/nivelación, DDI internacional, tipos de gravamen y conciliación de pagos fraccionados. Pero
**NO detecta automáticamente** (hoy dependen de que el abogado los introduzca/valide en el Checkpoint 1, o
viven solo en la capa de auditoría read-only): **amortizaciones (art. 12), deterioros e provisiones (art.
13/14), diferencias temporarias en general, bonificaciones (art. 33/34), deducción por doble imposición
interna (art. 30), deducción I+D+i (art. 35) y la tributación mínima / cuota líquida mínima (art. 30 bis,
INCN ≥ 20 M€)**. No asumas cobertura que no existe: si el expediente tiene esas magnitudes, recábalas y
téclealas. Detalle y propuestas de cierre en `docs/memoria/2026-06-17-revision-manual-procesos.md`.

## El patrón EXPEDIENTE = 1 Space + 2 Vaults
- **1 declaración = 1 Space** `IS {año} - {cliente}`. Dentro:
  - **Data:** un **Vault de expediente** (docs del cliente: SyS, CCAA, IS anterior, respuestas, +
    entregables al cierre) **+** el **Vault de recursos reutilizable** `📘 Suite IS — Cómo usar y
    Recursos` (sin PII: quickstart, playbook, glosario, plantilla, punteros a herramientas/AEAT).
  - **Tools:** los 2 workflows definitivos (**① / ②**) + el Playbook `IS-Reglas-Fiscales` (18 reglas;
    es el catálogo de reglas que aplica el motor — no se lanza a mano).
  - **Ask Harvey** del Space: chat grounded en los recursos → si el Vault de recursos está poblado, un
    abogado puede preguntar "¿cómo empiezo?" y se le responde desde el quickstart/playbook.
- El **Vault de recursos** se mantiene UNA vez y se **adjunta a cada Space** nuevo (no se duplica).

## Correr una declaración de principio a fin
El abogado sube los ficheros; tú conduces el resto. Pausa en los 2 checkpoints.

1. **Abre WF-1 desde el Space** (tarjeta ① → "Run agent"). Pide al abogado que **suba**: Sumas y Saldos,
   CCAA + memoria, IS del año anterior y la plantilla `EXP_plantilla_2024.xlsx`. *(Si usan el conversor
   de Stefano, su "Tabla 1" es el SyS ideal.)*
2. **Selecciona el régimen** (General / PYMES ERD / ETVE / SOCIMI / Fondo) y pulsa **Send**.
3. WF-1 hace el intake → **confirmar huecos** (paso Freeform; puedes teclear "Confirmo; lo pendiente no
   afecta a la liquidación").
4. **✋ Checkpoint 1 — validar incidencias** (paso Freeform). Valida cada issue (mantén las del caso de
   referencia; decide opciones como Reserva de capitalización según lo que reproduzca el ancla). Incluye
   las decisiones por ISSUE-XXX.
5. WF-1 emite la **liquidación preliminar** + la **carta de solicitudes COMO TEXTO** (paso
   `carta_solicitudes_texto`, con la **TABLA A3** tras `--- FIN CARTA ---`) + el **bloque parseable**.
   **Copia el bloque** con el botón **Copy** de la última respuesta (la del `03_LIQUIDACION_INPUTS`);
   pega la carta en `Carta_Solicitudes.docx` y la A3 en `SyS_A3.xlsx` (plantillas del Vault).
6. *(Pausa cliente. El abogado envía la carta y espera respuestas.)*
7. **Abre WF-2 desde el Space** (tarjeta ② → "Run agent"). **Paso 1:** pega el bloque en "Paste your
   text in here" (Harvey lo convierte a `.txt`) → Send. **Paso 2:** el abogado **sube las respuestas del
   cliente** (.docx/.pdf/.xlsx/.csv) → Send.
8. WF-2 ingiere y recalcula. **✋ Checkpoint 2 — validar el número** (paso Freeform dedicado
   `validacion_numero`): cuadra **00552 / 00562 / 00621** contra el preliminar e incluye la línea
   literal **`H_validada = si`** + evidencia. Send. *(El gating lo lee por la @-ref inline de D12 —
   valida AQUÍ, en el paso dedicado, no solo en el primer paso de ②.)*
9. **Gating**: pasa si 🔴0 ∧ 🟡0 ∧ `H_validada=si` (Estado "cerrado", Exportable "Sí"). WF-2 emite los
   **3 entregables COMO TEXTO** (`entregable_memoria`, `entregable_liquidacion`, `entregable_modelo200`
   con TABLA A casilla|importe, TABLA B mapping y TABLA A3 si el SyS está en contexto) y el **bloque
   final** (`05_MAPPING_M200` con casillas + referencia_normativa). Si el gating falla, los `entregable_*`
   emiten solo «BORRADOR no presentable» + bloqueos.
10. **Pega cada texto en su plantilla del Vault** (Memoria.docx / Liquidacion.docx / Modelo_200.xlsx /
   SyS_A3.xlsx) y guarda los rellenos en `entregables/`. *(Vía taller: el puente, abajo.)*

## Generar entregables con el puente (vía del TALLER — opcional, ya no necesaria para entregar)
Para lotes, regenerar el Excel-estado o doble-check del número. Copia el bloque final de WF-2 a un
`.txt` **en `~/Downloads` (fuera de git)** y ejecuta:
```bash
python3 suite-is/scripts/puente_entregables_v3.py \
  --bloque ~/Downloads/bloque_final.txt --output-dir ~/Downloads/{cliente}_{año}_entregables \
  --nif {CODENAME} --ejercicio {año}
```
Produce, branded Garrigues: `Modelo_200_*.xlsx` · `Liquidacion_*.docx` · `Memoria_Tecnica_*.docx`.
Verifica que imprime 00552/00562/00621 correctos. **Fórmula canónica de la base previa (00550, D8 en
vivo desde v1.3/v1.4):** `B12 = B2 + B3 + B4 + B5`, con **B2 = resultado contable (00500)** y el control
**B2 + B3 = resultado antes de impuestos** — es lo que firma el WF-2 y el motor (`construir_plantilla.py`).
⚠️ **Discrepancia del taller a reconciliar:** `puente_entregables_v3.py` aún calcula `B12 = B2 + B4 + B5`
bajo otra convención (B2 = pre-impuestos) y encima lo **etiqueta** `B2+B3+B4+B5` (línea 385) — antes de
fiarte de su salida, **cuádrala contra el oráculo GIP**; el número que vale es el del WF-2/motor. La
carta de solicitudes de WF-1: `suite-is/scripts/carta_solicitudes.py`.
Export A3 (6 columnas): `suite-is/scripts/exportar_sys_a3.py`.

## Editar y publicar workflows (mecánica que SÍ funciona)
- **Renombrar / describir un WF:** builder → menú **`⋯`** (arriba dcha.) → **"Edit agent details"** →
  edita Name/Description → **Save changes**. Se aplica **al instante** (metadato, sin publish).
- **Editar el texto de un paso:**
  - Pasos **Prompt / Document drafting** → abre el panel del paso → **icono expandir** del campo
    *Instructions* → modal **"Edit prompt"** → click al inicio del texto → `type` → **Save** (modal).
  - Pasos **Freeform text / File upload** → edita el **textarea Message** directamente:
    `left_click` dentro → `cmd+a` → `type`.
  - El cuadro **"Ask Harvey" del builder NO captura el tecleo** de automatización — no lo uses para editar.
- **Guardar/publicar:** tras editar un paso aparece barra **"Draft has unsaved changes · Revert · Save"**
  → **Save**. Para pasos **Prompt/Freeform**, además aparece **"Publish changes"** (arriba dcha.) →
  **publicar requiere OK del usuario**. Para el **Message de un File-upload**, el cambio se aplica al
  **Guardar** (no hay "Publish changes" aparte).
- El **canvas del builder a veces sale en blanco**: haz un `scroll` sobre él para que renderice los pasos.
- **Un WF no puede lanzar/abrir otro WF** (acaba en *Response*). Para ramificar hay **Selection list +
  Conditional**, pero el salto entre WF lo da el abogado a mano.

## Onboarding / configurar un Space
- **Orientación para abogados internos = tarjetas de *Tools*** (es lo único que ven al entrar; el
  mensaje "Welcome" es **solo para externos/invitados** — un miembro interno NO lo ve, "View as" solo
  ofrece External/Guests). Por eso:
  - **Numera los workflows** (vía Edit agent details): `① EMPIEZA AQUÍ · Análisis…` / `② Cierre y
    entrega…`. La sección Tools se vuelve el mapa.
  - **Enriquece el 1er paso de WF-1** (File-upload del SyS) con el big-picture ("estás en el ① de 2…
    copia el «resumen de estado» para el ②…").
- **Customize del Space** (lápiz ✎): pestañas **Appearance** (logo/accent/header image), **Welcome**
  (Título+Contenido, toggle Visible + Preview — externos), **About** (Name+Description). Las **chips del
  Ask Harvey NO son personalizables**.
- **Crear un Vault** (p. ej. el de recursos): Data → **"+ Vault"** → **"Create vault"** → fuente
  **"Upload files or folders"** → Next → nombre + descripción → **Create** → **Select** → **Add to
  space**. (El abogado sube luego los ficheros; supported: PDF/Word/Excel…)
- **Recablear Tools de un Space** (p. ej. al limpiar workflows obsoletos): `+ Workflow Agents` para
  añadir; en cada tarjeta `⋯` → **Remove** (quita del Space; reversible) — hazlo **antes** de borrar
  globalmente los obsoletos para no dejar el Space sin herramientas.

## Gotchas verificados (tabla de referencia rápida)
| # | Situación | Qué hacer / qué esperar |
|---|---|---|
| 1 | Subir ficheros | **Solo el abogado**; el picker es disco, **no lee del Vault**. |
| 2 | Editar paso Prompt/DocDrafting | Modal **"Edit prompt"** (expandir Instructions). |
| 3 | Editar paso Freeform/File-upload | Textarea Message directo (click→cmd+a→type). |
| 4 | Renombrar WF | `⋯` → Edit agent details (instantáneo, sin publish). |
| 5 | Publicar | Prompt/Freeform → "Publish changes" (**OK usuario**); File-upload Message → al Guardar. |
| 6 | Canvas en blanco | `scroll` sobre el canvas para renderizar. |
| 7 | Encadenar workflows | No se puede (acaba en Response); usa Selection list + Conditional. |
| 8 | Mensaje "Welcome" | Solo externos/invitados; internos no lo ven. |
| 9 | Handoff bloque | Paso 1 de WF-2 acepta texto pegado (→ .txt). Si salen "??", pega antes en texto plano. |
| 10 | Word nativo en blanco | Es esperable → usa el **puente Python**. |
| 11 | "Finished in N steps" + cuadro | **No** ha terminado: es un **checkpoint humano**. |
| 12 | Borrar en Manage | Checkbox(es) → barra inferior "Delete" → confirmar (**lo hace el usuario**). Tras scroll, clica el checkbox exacto (clicar la fila navega al builder). |
| 13 | Validar el número (D12) | Hazlo en el **Checkpoint 2 dedicado** (`validacion_numero`); el gating lo lee por @-ref inline. Validar solo en el 1er paso de ② NO basta. |

## Estado y versión (consolidado 2026-06-13)
Las cifras de esta sección son verificables en `harvey-suiteis-live-findings.md` y `PROGRESO.md`.

- **WF-2 Version 10 publicada (2026-06-13 18:33)** — fija **D12**: el gating lee el Checkpoint 2 por
  **@-referencia inline `@validacion_numero`** (no por el panel de contexto). Validación de vuelta al
  paso dedicado; workaround v1.3 **revertido**.
- **Lote v1.4 saneado D1–D10 publicado (2026-06-13)** en ① (D1–D5) y ② (D6–D10), método quirúrgico
  in-place (chip `@validacion_numero` preservado). Clave fiscal: **D8 = `B12 = B2+B3+B4+B5`** (B3 suma)
  en `ingesta_respuestas` y `entregable_liquidacion`; **D9 = columnas A3 a spec** `Cuenta|Descripcion|
  Saldo Final|Debe|Haber|Saldo Inicial`; **D7 = verificaciones legacy 1–7 eliminadas** (el ítem 4
  contradecía el criterio 00370/00573). Re-sanity sobre lo publicado (run 427118036, CASO_REAL_4) **VERDE**.
- **Regresión golden 3/3 PASS** (CASO_REAL_2/3/4 al céntimo) → D12 estable ×3 + recálculo del WF = motor.
- **Pendiente cosmético (no bloqueante):** unificar el separador de banners (① usa `·`, ② usa `|`). Diferido.
- **Aprendizaje de edición (builder Lexical):** los @-refs son chips `<button>`, no texto → **nunca**
  full-replace (cmd+A) en un prompt con chip; edición quirúrgica con `window.find` + `execCommand
  insertText`. «Publish changes» fiable abriendo el agente por Library → fila → Edit Agent (o pestaña nueva).

## Fuentes (en el repo `is200transmittalAPP`)
- `suite-is/distribucion_abogados/PLAYBOOK_Harvey_Declaracion_IS.md` — manual del abogado (7 pasos).
- `suite-is/distribucion_abogados/vault_onboarding/` — Quickstart + Recursos & herramientas terceras.
- `docs/superpowers/notes/2026-06-07-harvey-saneado-expediente.md` — verificación del saneado + patrón.
- `suite-is/scripts/` — el puente y demás motor determinista.
- Memoria del proyecto `harvey-suiteis-live-findings.md` — log vivo (IDs, hallazgos, estado).
- Detalle de mecánica click-a-click: `references/builder-mechanics.md`.
