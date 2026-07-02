---
name: descubrir-expediente
description: >-
  Fase 0 de intake de expediente del Impuesto sobre Sociedades: trabaja SIN subir ficheros, descubre y clasifica
  los documentos dentro de una carpeta local, construye un manifiesto de fuentes, detecta huecos, formula preguntas
  al usuario y reitera hasta que la información esté lista para correr el motor. Identifica Sumas y Saldos, `.200`
  o PDF N-1, datos fiscales, GIS/liquidación, cuentas anuales, salidas previas y formatos ES/EN/multipestaña.
  ÚSALA cuando el usuario comparta una ruta de carpeta, diga «analiza el expediente», «prepara la información para
  el motor», «clasifica los documentos», «¿está todo?», «trabaja desde la carpeta» o quiera evitar subir ficheros.
metadata:
  version: "1.3.0"
---

# Fase 0 — Intake del expediente desde carpeta

Trabajar **sin subir ficheros**: el abogado conecta/comparte la carpeta del expediente y esta skill inventaría
los documentos, clasifica fuentes y guía una conversación corta hasta dejar un **manifiesto listo para motor**.
El trabajo inicial lo hace un **script determinista**: no se vuelcan PDFs al modelo.

## Cómo
1. Asegúrate de que la **carpeta del expediente está conectada** a la conversación (selector de carpeta de
   Cowork). Si no, pide al abogado que la conecte (o que comparta su ruta, abajo).
2. Ejecuta el inventario:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/descubrir-expediente/scripts/inventario_carpeta.py" "<ruta-de-la-carpeta>"
```

3. Lee el resultado:
   - `manifest.seleccion_motor`: fuentes propuestas.
   - `manifest.listo_para_motor`: si existe el mínimo para arrancar.
   - `manifest.calidad_intake`: `bloqueado`, `mínimo` o `completo`.
   - `manifest.bloqueos_semanticos`: problemas de contenido que harían fallar el motor o la importabilidad.
   - `manifest.preguntas_usuario`: preguntas concretas para cerrar huecos.
4. Si hay preguntas, hazlas al usuario y reitera. Si el usuario añade documentos, vuelve a ejecutar el inventario.
5. Solo cuando `listo_para_motor=true`, continúa con el motor. Si la calidad es `mínimo`, explica qué faltará
   resolver después (formales, N-1, datos fiscales, CCAA o liquidación).

## Dossier por bloques (checklist captado / vacío, antes del motor)

Tras el inventario, ejecuta el **DOSSIER**: vuelca el N-1 a un checklist **bloque a bloque** (determinista, sin
motor) con estado `captado`/`parcial`/`vacío`, fuente y pregunta por cada hueco. Incluye el bloque de **GRUPO
FISCAL** (00009 dominante / 00010 dependiente → **nº de grupo 00040 + NIF de la dominante**), que la AEAT exige y
que, si falta, sólo se descubría por rechazo en Open.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/descubrir-expediente/scripts/dossier_expediente.py" "<ruta-de-la-carpeta>" 2025
```

Lee `bloques[]` (estado + fuente), `criticos_pendientes`, `confirmacion_requerida` y `listo_para_motor`.
Bloques: identificativos, caracteres pág 1, grupo fiscal, modelo de cuentas, administradores, B.1, B.2,
titular/representantes, apertura N-1 (ECPN) y **datos fiscales AEAT 2025 completos**. 0 PII en el resumen
(estados/contadores/códigos, no NIF/importes).

### Primer paso obligatorio: presentar la FICHA y pedir confirmación al abogado

La salida trae una **FICHA DE CONFIGURACIÓN PROPUESTA** (`confirmacion_requerida`): el *read-back* de lo que el
motor ha leído del N-1. **El motor NO arranca hasta que el abogado confirma o corrige esta ficha**, aunque no haya
críticos pendientes. Esto es lo que da la «configuración de la declaración lo más completa posible»: una persona
valida la identidad y la configuración antes de generar nada.

Protocolo del primer paso:
1. **Presenta la ficha al abogado** en lenguaje claro: «Esto es lo que he leído del N-1 y así configuraría la
   declaración», bloque a bloque, con su estado (`CONFIRMAR` lo leído, `REVISAR` lo parcial, `COMPLETAR` lo vacío).
2. Marca explícitamente lo que **debe revisar aunque salga poblado**: todo lo extraído de **PDF best-effort**
   (caracteres pág 1, B.1, titular) y **siempre el grupo fiscal** (nº 00040 + NIF de la dominante).
3. **Pide confirmación o correcciones.** No arranques el motor hasta un «confirmo» explícito del abogado; si
   corrige algún dato, recógelo y vuelve a presentar la ficha.
4. Sólo con la ficha confirmada y `listo_para_motor=true` (sin críticos) continúa al motor.

## Qué clasifica
- **Sumas y Saldos** (REQUERIDO).
- **Sumas y Saldos en `.xlsb`**: se detecta como fuente contable probable, pero **no es entrada directa del
  motor**; hay que convertirlo/exportarlo a `.xlsx` o `.csv` antes de correr.
- **`.200` del año anterior** o **Modelo 200 / justificante N-1 PDF**.
- **Datos fiscales AEAT 2025** PDF/digital: no solo presencia del fichero; hay que extraer y clasificar su
  contenido fiscal útil.
- **GIS / liquidación** Excel, como referencia fiscal o input validado según confirme el abogado.
- **Cuentas anuales** PDF.
- **Salidas previas** (`salida/`), ignoradas por defecto salvo diagnóstico.
- **Otros** a revisar.
- Resuelve el «¿le pasaste los datos fiscales? hay otro documento»: si está en la carpeta, **lo detecta solo**.
- Avisa si el Sumas y Saldos es **multipestaña** (qué hoja es el balance) o viene en **inglés** (el motor ya lo
  soporta, v1.7.0+).

## Criterio de listo

- `bloqueado`: falta Sumas y Saldos en formato motor-ready (`.xlsx`, `.xls` o `.csv`).
- `bloqueado`: solo hay un posible SyS en `.xlsb`; pedir conversión trazable a `.xlsx`/`.csv`. Esto **no**
  reabre el modelo de cuentas: si existe `.200` N-1, el perfil normal/abreviado/PYMES se arrastra desde
  `DP200001B`.
- `bloqueado`: el SyS existe pero no es semánticamente usable, por ejemplo `Saldo Inicial` ausente o todo a cero.
- `mínimo`: hay Sumas y Saldos; se puede correr el motor, pero habrá huecos que pedir o diferir.
- `completo`: hay Sumas y Saldos + datos fiscales + fuente N-1 + CCAA. La liquidación/GIS puede existir, pero no
  convierte criterio fiscal en pre-import; se marca para revisión/post-import si no está validada.

No confundas `listo_para_motor` con `importabilidad_probable`: el intake prepara fuentes; la importabilidad la
decide el validador y, finalmente, Sociedades WEB.

## Contrato de intake — bloques esenciales por sociedad (el motor escucha y se nutre)

El **primer acto** de cualquier declaración es **cargar y verificar TODA la información que hay que parsear**,
sociedad a sociedad, **antes** de arrancar el motor. El inventario clasifica los *ficheros*; este contrato cierra
el *contenido*: tras detectar el N-1, **precarga el N-1** (`engines.precarga_n1_extraer`, determinista; `.200` ▸
PDF best-effort) y **presenta al abogado un checklist por bloque** (captado / vacío). Bloques esenciales:

| Bloque | Fuente principal | Dónde acaba en el `.200` | Si falta |
|---|---|---|---|
| Identificativos (NIF, denominación, domicilio) | N-1 + datos fiscales | DP200001 (pág 1) | **bloquea**: sin denominación/NIF el `.200` sale en blanco |
| Caracteres de configuración pág 1 (tipo entidad/régimen) | N-1 (marcas `X NNNNN`) | DP200001 (cubo 3) | arrastra del N-1 + **confírmalos**; excepción: `00027` base negativa/cero no se arrastra porque depende del resultado 2025 |
| Modelo de cuentas / pág 1B | `.200` N-1 determinista; PDF/CCAA como fallback | DP200001B | si viene de `.200` N-1, **se arrastra por continuidad** y no queda como punto abierto salvo que el abogado declare cambio. Si solo viene de PDF/CCAA o falta, confirmar |
| **Grupo fiscal** (si 00009/00010) — nº de grupo + NIF dominante | N-1 (pág 1: «Número de grupo fiscal» + «NIF de la entidad representante/dominante») | DP200001B campos 6 y 7 | **bloquea el miembro**: sin 00040 y NIF dominante, Open rechaza (10031, «00040 sin contenido»). Dependiente: campo 7 = NIF de la dominante (no el suyo) |
| Administradores | N-1 | DP200002 campos 6-35 (hasta 5 slots) | aviso + pide |
| **B.1 — sociedades en las que participa** | N-1 (bloque «Participaciones de la declarante») | `.200` solo si es bloque simple (≤3 participadas completas, sin continuación). Si es complejo, **post-import/HITL** en `b1_participadas_post_import.json` | aviso + pide; tras import positivo, completar/revisar en Sociedades WEB si queda fuera |
| B.2 — socios/partícipes de la declarante | N-1 | DP200002 campos 100-143, con complementarias `C` si hay más de 6 | aviso + pide |
| Titular real / secretario / representantes | N-1 | DP200002B (titular 145-151, **sin 148**; titulares adicionales con complementarias `C`) | aviso + pide |
| Contabilidad con **apertura N-1** (saldo inicial) | SyS (saldo inicial) o CCAA (columna N-1) | balance + ECPN (DP200009/10/11) | **solo en modelo NORMAL** bloquea el ECPN (sin apertura se rechaza E25400632/645). En **abreviado/PYMES el ECPN es VOLUNTARIO** → no bloquea ni exige apertura (el motor lo omite limpio: no emite 09/10/11 y declara campo15=0) |
| Datos fiscales AEAT 2025 completos | Consulta de Datos Fiscales digital/OCR | liquidación, arrastres, ajustes HITL y contraste fiscal | **P0 de intake**: si falta, el `.200` puede importar pero la liquidación queda incompleta/cosmética; pedir o marcar alcance |

**Protocolo de iteración (no se arranca el motor con huecos esenciales):**
1. Ejecuta el inventario y, si hay N-1, **precarga y muestra el checklist por bloque** (captado/vacío).
2. Para cada bloque esencial **vacío**, pregunta al abogado: ¿aporta el `.200` N-1 (arrastre determinista) o lo
   confirma/completa en Sociedades WEB? Si el N-1 es **PDF**, advierte que la extracción es *best-effort* y que
   caracteres y B.1 deben **confirmarse** aunque salgan poblados. B.1 complejo no viaja dentro del `.200`
   importable: viaja como artefacto local post-import para evitar FRECH por `01501/01502/01503`.
3. Reitera hasta que el abogado dé por **completo** el intake de esa sociedad. Solo entonces continúa al motor.
4. Todo bloque arrastrado del N-1 viaja con **aviso HITL** («revisión del abogado OBLIGATORIA»): el motor *se
   nutre* del N-1 pero **no decide identidad/configuración** por su cuenta.

> Por qué importa: un `.200` con página 1 sin marcar, denominación vacía o «sociedades en las que participa» en
> blanco es un problema de **coherencia**, no de liquidación. El motor solo firma el número; la **identidad y la
> configuración** las suministra el intake y las confirma el abogado.

## Regla dura — Datos fiscales AEAT 2025

La Consulta de Datos Fiscales del ejercicio es una fuente de **datos fiscales mapeables**, no un adjunto genérico.
Cuando exista, la skill debe extraerla y presentar un bloque propio en la FICHA antes de correr el motor.

Extraer y clasificar:

- **Liquidación directa**: retenciones e ingresos a cuenta, retenciones de cuentas bancarias si constan y pagos
  fraccionados Modelo 202. Van a casillas de liquidación, con confirmación del abogado.
- **Arrastres**: BINs pendientes, deducciones pendientes y otros créditos fiscales con casilla destino o referencia
  AEAT. Se contrastan contra el `.200` N-1; no se decide su aplicación automáticamente.
- **Ajustes HITL**: sanciones, recargos e intereses de demora. Si están contabilizados como gasto, son candidatos
  a ajuste extracontable positivo o a clasificación específica, pero **nunca se autoaplican**.
- **Gestión/terceros**: rectificativas, comprobaciones, operaciones notariales/registrales/catastrales y otras
  incidencias que pueden explicar diferencias con contabilidad.

Tratamiento obligatorio:

- Pagos fraccionados y retenciones -> liquidación, no base imponible.
- BINs/deducciones -> cuadros de arrastre/aplicación, no casilla final automática.
- Sanciones/recargos/intereses -> `hitl_requerido`; el motor solo propone la revisión.
- Si el PDF es imagen o el texto es débil -> `requiere_vision/OCR` y HITL.
- Si no hay datos fiscales -> marcar alcance: importabilidad posible, liquidación no completa.

Salida esperada del dossier: bloque **Datos fiscales AEAT 2025 completos** con `casillas_directas`,
`arrastres`, `ajustes_hitl`, `gestion`, fuente, calidad y confirmación requerida.

## Guardrail SyS inferido por LLM

Si el SyS viene generado por LLM desde CCAA, debe traer:

- columnas A3: `Cuenta`, `Descripción`, `Saldo Final`, `Debe`, `Haber`, `Saldo Inicial`;
- `Saldo Inicial` leído de la columna N-1/apertura de CCAA o del Modelo 200 anterior, no rellenado a cero;
- saldos acumulados de patrimonio neto, no solo movimientos/YTD.

**En modelo de cuentas abreviado/PYMES el ECPN es VOLUNTARIO** (no se incluye por defecto): la apertura N-1 NO
es necesaria y la ausencia de ECPN no bloquea ni es finding. Lo que sigue aplica solo si el modelo es **NORMAL**
o si el abogado opta por incluir el ECPN.

Si `Saldo Inicial` está todo a cero (y se va a incluir el ECPN): el ECPN necesita apertura N-1 (la AEAT recalcula
cierres/totales; apertura cero acaba en `E25400632/E25400645`). Dos caminos:
- **Hay CCAA en la carpeta** → no se bloquea: el motor toma la apertura del ECPN de la **columna N-1 del Balance
  de la CCAA** (`engines.extraer_texto_ccaa` → `ecpn_sys.proyectar_desde_balance`). Avisa de **revisar el cuadre
  del ECPN en Fase 2**. Mejor aún: regenera el SyS con la skill `ccaa-a-sys-a3` (apertura N-1 + PN acumulado).
- **No hay CCAA** → bloquea: regenera el SyS con apertura N-1 real (o aporta la CCAA). No corras el motor.

El mapeo PN→ECPN por columnas y por año está en `ccaa-a-sys-a3/references/ecpn-pgc-columnas.md`.

## Conectar/compartir la carpeta y copiar su ruta
- **Cowork:** conecta la carpeta del expediente a la conversación (**«conectar carpeta»**); así el asistente la
  lee directa, sin subir ficheros.
- **Windows — copiar la ruta:** en el Explorador, **Mayús + clic derecho** sobre la carpeta →
  **«Copiar como ruta de acceso»**. (Alternativa: clic en la barra de direcciones → copiar.)
- **Mac — copiar la ruta:** en Finder, clic derecho sobre la carpeta → mantén pulsada **⌥ (Opción)** →
  **«Copiar "…" como nombre de ruta»** (atajo **⌘⌥C**).
- La ruta copiada sirve para indicar la **subcarpeta exacta** dentro de lo conectado.

## Reglas
- **Determinista:** clasifica por extensión + nombre + un *sniff* ligero de cabecera; **no** manda PDFs al LLM
  (ahorro de tokens — el esfuerzo lo hace el parser).
- **Requerido = Sumas y Saldos motor-ready** (`.xlsx`, `.xls` o `.csv`); lo demás mejora la precarga. Si solo hay
  `.xlsb`, pide exportarlo/convertirlo manteniendo trazabilidad (vale en formato **ES o EN**).
- **Iterar con el usuario:** no inventes si hay ambigüedad. Pregunta por la fuente correcta y vuelve a inventariar.
- **PII local:** nombres de fichero locales; en el chat, **codename**. Datos reales solo en la carpeta.
