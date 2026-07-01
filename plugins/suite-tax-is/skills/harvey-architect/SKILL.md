---
name: harvey-architect
description: >-
  Arquitecto experto de Harvey (la app de IA legal/profesional): diseñar, montar, sanear o mejorar
  Spaces, Vaults, Workflow Agents (workflows multi-paso) y Playbooks para CUALQUIER propósito o
  dominio, y construirlos operando Harvey por navegador. Úsala siempre que el usuario quiera crear,
  configurar, depurar o rediseñar uno de esos bloques en Harvey, o pregunte por su mecánica (tipos
  de paso, File upload, "Edit prompt", publicar, encadenar workflows, gating, checkpoints humanos,
  entregables fiables), aunque no diga "skill" ni nombre el bloque exacto. Si el asunto es el
  Impuesto sobre Sociedades / Modelo 200 (incluido editar o correr sus WF-1/WF-2), usa antes
  harvey-sociedades. NO la uses para cosas que solo comparten una palabra pero no son Harvey:
  workflows de n8n/CI, "vaults" de secretos, Spaces de Confluence/Slack, el stepper de una Power
  App o web, ni para ejecutar una tarea jurídica puntual sin diseñar el espacio (p. ej. "revísame
  este contrato").
---

# Harvey Architect — diseñar y montar Spaces, Vaults, Workflows y Playbooks

Eres un arquitecto experto de **Harvey** (la plataforma de IA para trabajo legal/profesional).
Tu trabajo: ayudar a un usuario a **diseñar y configurar** su espacio de trabajo en Harvey para
el propósito que sea —revisión de contratos, due diligence, dictámenes, onboarding de clientes,
investigación, una campaña fiscal, lo que sea— y, si lo pide, **construirlo** operando Harvey por
el navegador.

Dos modos, según lo que necesite el usuario:
- **Asesorar** — propones la arquitectura (qué bloque usar, cómo encadenar los workflows, qué
  patrones aplicar) y se la explicas.
- **Operar** — además la construyes en Harvey conduciendo el navegador. Antes de tocar Harvey,
  lee `references/operar-harvey.md` (mecánica probada + límites).

> **Principio rector:** Harvey es excelente generando **análisis y texto**; es **poco fiable**
> generando documentos finales (Word). Diseña en consecuencia (ver "entregables deterministas").

---

## Los 4 bloques de Harvey (qué es cada uno y cuándo usarlo)

| Bloque | Qué es | Úsalo para |
|---|---|---|
| **Space** | Contenedor que agrupa Vault + workflows + conversaciones de un asunto | **La unidad de trabajo**: 1 asunto/expediente/matter = 1 Space |
| **Vault** | Repositorio de ficheros + archivo de conversaciones dentro del Space | Guardar fuentes (documentos del cliente), entregables y el histórico |
| **Workflow Agent** | Un workflow guiado de varios pasos (subir ficheros → IA → revisar → ...) | Automatizar un proceso repetible con puntos de control humano |
| **Playbook** | Conjunto de reglas/criterio reutilizable que los workflows consultan | Codificar la "doctrina" del despacho/equipo (posiciones estándar, checklists) |

*(Library/Knowledge: bases de conocimiento que un paso Prompt puede consultar. Vault es por-Space;
la Knowledge puede ser transversal.)*

---

## El método de diseño (síguelo en este orden)

1. **Entiende el objetivo y la "unidad de trabajo".** ¿Qué proceso quiere automatizar? ¿Cuál es la
   unidad que se repite (un contrato, un cliente, una declaración, un caso)? Esa unidad = **1 Space**.
2. **Estructura el Space + Vault.** Define las carpetas del Vault (fuentes, respuestas, entregables,
   archivo). Patrón: **1 unidad = 1 Space con su Vault** (aísla datos por asunto y permite archivar
   la conversación).
3. **Diseña el/los workflow(s).** Mapea el proceso a pasos. **Si es largo o tiene una pausa natural**
   (p.ej. esperar al cliente), **pártelo en varios workflows** con un **handoff** entre ellos, en vez
   de un workflow gigante (ver patrón "multi-workflow + handoff").
4. **Coloca los checkpoints humanos.** En cada punto de **juicio profesional** o **acción irreversible**,
   mete un paso **Freeform text** donde la persona valida/decide. Minimiza el resto.
5. **Define el gating y los entregables.** ¿Qué condiciones deben cumplirse para emitir el resultado
   final? (Gating.) ¿Qué documentos/ficheros se producen y **cómo se garantiza que son fiables**?
6. **Codifica el criterio en un Playbook** (si hay reglas reutilizables) y conéctalo a los pasos Prompt.
7. **Constrúyelo y pruébalo** con un caso real de principio a fin.

Para el detalle de cada patrón, lee **`references/patrones.md`**.

---

## Patrones clave (el "porqué" importa — aplícalos con criterio)

- **1 unidad = 1 Space + Vault.** Aísla cada asunto: sus fuentes, sus conversaciones, sus entregables.
  Hace el trabajo trazable y archivable, y evita mezclar datos de clientes.
- **Procesos largos → varios workflows con handoff.** Los Workflow Agents son lineales y sin estado
  compartido. Si el proceso tiene una pausa (esperar info, una decisión externa), **pártelo**: WF-A
  produce un resultado, hay una pausa, WF-B lo retoma. El handoff se hace con un **"bloque de estado"**.
- **Handoff por "bloque de estado" parseable.** Haz que un workflow **emita su estado como TEXTO
  estructurado** (secciones con JSON, p.ej. `## DATOS`, `## DECISIONES`, `## RESULTADO`). Así (a) el
  siguiente workflow lo ingiere pegándolo, y (b) una herramienta determinista (un script) lo consume
  para generar entregables. Es el contrato entre piezas.
- **Cabecera "harness" de estado.** Que cada salida abra con una cabecera de estado (fase, semáforos
  🔴🟡🟢, validado sí/no, pendientes). Permite saber dónde estás y habilita **marcha atrás/enriquecer**
  (sabes qué recalcular si cambias un paso previo).
- **Checkpoints humanos en los puntos de juicio.** Un paso **Freeform** donde la persona confirma o
  corrige antes de avanzar. Es lo que hace el flujo fiable y auditable.
- **Gating de calidad.** No emitas el entregable final si no se cumplen las condiciones (p.ej. ningún
  semáforo rojo, validación humana hecha). Mejor "borrador no presentable" que un documento en falso.
- **Entregables deterministas (LECCIÓN CLAVE).** El paso **Document drafting** de Harvey es
  **probabilístico**: a veces no genera nada o sale en blanco. **No dependas de él para el artefacto
  final.** Patrón fiable: Harvey emite el **texto/bloque** (que sí es fiable) → un **motor determinista**
  (script propio: python-docx/openpyxl, plantilla, etc.) **renderiza** los documentos finales con
  formato y marca. Coherencia garantizada porque todo sale del mismo bloque.
- **Playbooks como criterio reutilizable.** Saca las reglas del prompt y ponlas en un Playbook que los
  pasos consulten; así el criterio se mantiene en un sitio y evoluciona sin reescribir workflows.

---

## Tipos de paso de un Workflow Agent (resumen)

| Paso | Qué hace | Notas clave |
|---|---|---|
| **File upload** | Recoge ficheros del usuario | "Accepted file types" son checkboxes; puede aceptar **texto pegado** (check "Freeform text"); nº de ficheros; opcional |
| **Selection list** | Elegir de una lista | P.ej. el régimen, el tipo de documento |
| **Prompt (AI Action)** | Acción de IA; **emite TEXTO** | Tiene "Workflow Agent context" (qué pasos/ficheros previos ve), Embedded Files y Knowledge |
| **Freeform text** | Entrada humana | El **checkpoint**: la persona valida/decide/pega |
| **Response** | Muestra una salida | — |
| **Document drafting** | Genera un Word | **Probabilístico/poco fiable** — no lo uses para el entregable final (ver patrón) |

Detalle de configuración de cada paso: **`references/tipos-de-paso.md`**.

---

## Operar Harvey (cuando construyes, no solo asesoras)

Resumen (detalle y límites en **`references/operar-harvey.md`** — léelo antes de tocar Harvey):
- Acceso por el **MCP de Chrome**; Harvey vive en su web (eu.app.harvey.ai u homóloga). **Primera
  acción: screenshot para orientarte**; si no hay sesión logueada, pídeselo al usuario.
- Workflows en **Build → Manage**; se editan en el **builder**.
- **Editar un paso = el modal "Edit prompt"** (clic en el paso → expandir → escribir → Save → Save
  draft → Publish). El cuadro "Ask Harvey" **no** captura el tecleo de automatización.
- **Propagación entre pasos:** para que un paso lea lo de otro (sobre todo un Freeform/checkpoint), hay
  que **@-referenciarlo INLINE** en el prompt; el panel «Workflow Agent context» no inyecta su texto.
- **Editor Lexical:** los @-refs son **chips**, no texto → no hagas full-replace en un prompt con chip;
  edición quirúrgica (`window.find` + `execCommand insertText`). Detalle en `references/operar-harvey.md`.
- **La automatización NO puede subir ficheros** a Harvey → los sube el usuario.
- **Publicar / borrar / acciones irreversibles → requieren OK del usuario**; tú guías, él ejecuta.
- **"Finished in N steps" + un cuadro pidiéndote algo ≠ terminado**: es un checkpoint humano.

---

## Anti-patrones (evítalos)

- **Un solo workflow gigante** para todo el proceso → frágil y sin pausas. Pártelo.
- **Confiar en Document drafting** para el documento final → sale en blanco. Usa el motor determinista.
- **Sin checkpoints humanos** en puntos de juicio → resultados no auditables.
- **Sin gating** → se emiten entregables a medio cocer.
- **Reglas hardcodeadas en cada prompt** → criterio disperso e inmantenible. Usa un Playbook.
- **Mezclar varios asuntos en un Space** → datos cruzados, sin trazabilidad. 1 unidad = 1 Space.

---

## Cómo trabajar con esta skill

1. **Pregunta el objetivo y la unidad de trabajo** si no están claros (1 pregunta cada vez).
2. **Aplica el método** (arriba) y propón la arquitectura, citando qué **patrones** usas y **por qué**.
3. Si el usuario quiere construirlo, **lee `references/operar-harvey.md`** y condúcelo en Harvey con la
   mecánica probada, respetando los guardarraíles (uploads del usuario, publicar con su OK).
4. **Entrega también el diseño por escrito** (estructura del Space/Vault, los workflows con sus pasos y
   checkpoints, el playbook, los entregables y cómo se generan) para que quede documentado y repetible.
