# Patrones de diseño en Harvey (referencia)

Patrones reutilizables para diseñar Spaces, Vaults y Workflow Agents de calidad, **en cualquier
dominio**. Cada uno incluye el **porqué** (úsalos con criterio, no como dogma) y un ejemplo genérico.

## Índice
1. 1 unidad = 1 Space + Vault
2. Procesos largos → varios workflows con handoff
3. Bloque de estado parseable (el contrato entre piezas)
4. Cabecera "harness" de estado
5. Checkpoints humanos
6. Gating de calidad
7. Entregables deterministas (la lección clave)
8. Máxima inferencia + huecos marcados
9. Playbooks: el criterio reutilizable

---

## 1. 1 unidad = 1 Space + Vault
**Qué:** cada instancia del proceso (un contrato, un cliente, un caso, una operación) vive en su propio
Space, con su Vault.
**Por qué:** aísla datos por asunto (clave en entornos con secreto profesional), hace el trabajo trazable
y archivable, y evita que se crucen fuentes o conversaciones de asuntos distintos.
**Ejemplo:** revisión de contratos → 1 contrato = 1 Space "Contrato X · Cliente Y"; el Vault guarda el
contrato, los anexos, la conversación de revisión y el informe final.
**Cómo:** define las carpetas del Vault por rol: `fuentes/`, `respuestas/`, `entregables/`, `archivo/`.

## 2. Procesos largos → varios workflows con handoff
**Qué:** parte un proceso largo en varios Workflow Agents conectados, en vez de uno gigante.
**Por qué:** los Workflow Agents son lineales y **sin estado compartido**. Si el proceso tiene una **pausa
natural** (esperar info del cliente, una aprobación, una firma), un único workflow no la modela bien.
Partirlo da puntos de reanudación, runs más cortos y mantenibilidad.
**Ejemplo:** WF-A "Análisis" (produce un borrador + una lista de preguntas) → *pausa: el cliente responde*
→ WF-B "Cierre" (incorpora respuestas y produce el entregable).
**Cómo:** el handoff entre A y B se hace con el **bloque de estado** (patrón 3): A lo emite, la persona lo
**pega** en B (o se sube como fichero).

## 3. Bloque de estado parseable (el contrato entre piezas)
**Qué:** haz que un workflow **emita su estado como TEXTO estructurado** — secciones etiquetadas con JSON,
p.ej.:
```
## DATOS
{ ...campos clave... }
## DECISIONES
[ ...issues/decisiones con su estado... ]
## RESULTADO
{ ...el número/veredicto/inputs del entregable... }
```
**Por qué:** el texto es el **contrato universal**. Sirve para (a) el handoff entre workflows (se pega),
y (b) que una **herramienta determinista** (un script) lo consuma y genere los entregables sin ambigüedad.
Es más fiable que pasar ficheros y desacopla la IA (que razona) del render (que es mecánico).
**Cómo:** en el prompt del último paso de IA, pide explícitamente ese bloque con un formato fijo. Mantén
las **claves estables** (son una API): si cambian, rompes a los consumidores.

## 4. Cabecera "harness" de estado
**Qué:** que **cada salida** abra con una cabecera de estado: fase actual, **semáforos** (🔴🟡🟢⚪),
validado (sí/no) y **pendientes para el siguiente paso**.
**Por qué:** convierte una cadena de documentos/outputs en una **máquina de estados legible**. Sabes de un
vistazo dónde estás, qué bloquea y qué falta. Y habilita **marcha atrás/enriquecer**: si cambias un paso
previo, el harness te dice qué hay que recalcular aguas abajo y qué queda obsoleto.
**Ejemplo:** `> ESTADO | Fase 2/4 Análisis | 🔴0 🟡2 🟢5 | validado: no | pendientes: [recibir respuestas]`.

## 5. Checkpoints humanos
**Qué:** un paso **Freeform text** donde la persona valida/decide en cada punto de **juicio profesional**
o **acción irreversible**.
**Por qué:** es lo que hace el flujo **auditable y responsable**. La IA infiere y propone; la persona
firma. No metas checkpoints por todo —solo donde de verdad hace falta criterio humano— para "simplificar
al máximo la intervención".
**Ejemplo:** "valida estas N incidencias antes de calcular"; "confirma el resultado antes de emitir".

## 6. Gating de calidad
**Qué:** una **condición dura** que debe cumplirse para emitir el entregable final (p.ej. cero semáforos
rojos, ningún amarillo con impacto sin resolver, validación humana hecha).
**Por qué:** evita entregar a medio cocer. Es mejor un explícito **"BORRADOR no presentable — faltan X"**
que un documento que parece final pero no lo es.
**Cómo:** el paso que produce el entregable empieza comprobando la condición; si no se cumple, emite el
aviso de bloqueo en vez del entregable. (Y los pasos Document drafting respetan ese gating.)
**⚠️ Mecánica verificada (propagación de checkpoints):** el output de un paso **Freeform / User-input**
(p.ej. la validación humana que mira el gating) **NO se propaga** a los prompts posteriores por tenerlo
en «Workflow Agent context»; hay que **@-referenciarlo INLINE** dentro del prompt que lo consume (escribe
`@nombre_del_paso` en el cuerpo del prompt de gating). Síntoma del fallo: el gating "no ve" la validación
y la da por no hecha. Es el mismo patrón handoff (3), pero **dentro de un mismo workflow**.

## 7. Entregables deterministas (LA LECCIÓN CLAVE)
**Qué:** **no generes el documento final con el paso Document drafting de Harvey.** Harvey emite el
**texto/bloque**; un **motor determinista propio** (script) **renderiza** los Word/Excel/PDF finales.
**Por qué:** Document drafting es **probabilístico** — en la práctica falla a menudo (no-op, en blanco).
Para entregables de cliente necesitas **fiabilidad, formato y marca**. Un script (python-docx, openpyxl,
una plantilla) lo da, es **reproducible** y, como todo sale del **mismo bloque**, los entregables son
**coherentes entre sí** (el número del informe = el del Excel = el del XML).
**Ejemplo:** el bloque `## RESULTADO` alimenta un script que produce: informe.docx (con membrete),
tabla.xlsx (con formato) y, si aplica, el fichero de exportación — todos con las mismas cifras.
**Regla:** Harvey para **analizar y redactar texto**; el motor para **fabricar el artefacto**.

## 8. Máxima inferencia + huecos marcados
**Qué:** pide a los pasos de IA que **infieran todo lo que puedan** de las fuentes y **marquen
explícitamente** lo que no pueden deducir (`input_humano_requerido`) en vez de inventarlo.
**Por qué:** maximiza la automatización sin sacrificar rigor. El checkpoint humano se centra solo en los
huecos marcados. Nunca inventes datos críticos.
**Ejemplo:** "rellena los campos con su evidencia y procedencia; lo que no conste, márcalo como pendiente".

## 9. Playbooks: el criterio reutilizable
**Qué:** saca las **reglas/criterio** (posiciones estándar, checklists, qué es aceptable/inaceptable) del
prompt y ponlas en un **Playbook** que los pasos consulten (vía Knowledge/Embedded Files).
**Por qué:** centraliza la "doctrina" del equipo en un sitio, la hace **evolucionar sin reescribir
workflows**, y da consistencia entre asuntos. El workflow ejecuta; el playbook decide el criterio.
**Ejemplo:** un playbook de revisión de contratos con las cláusulas-tipo, las redacciones aceptables y las
líneas rojas; el WF de revisión lo consulta para clasificar cada cláusula.

---

## Cómo combinarlos (receta típica de un "expediente")
1. **1 Space + Vault** por asunto (patrón 1).
2. **WF-A** ingiere fuentes → IA con **máxima inferencia** (8) consultando un **Playbook** (9) → emite un
   **bloque** (3) con **harness** (4); un **checkpoint humano** (5) valida.
3. *Pausa* (si la hay) → **WF-B** retoma el bloque (handoff, 2+3) → **gating** (6) → emite el bloque final.
4. El **motor determinista** (7) toma el bloque final y fabrica los **entregables** coherentes.
