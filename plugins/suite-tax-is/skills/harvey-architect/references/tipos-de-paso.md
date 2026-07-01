# Tipos de paso de un Workflow Agent (referencia)

Un Workflow Agent es una secuencia de pasos. Estos son los tipos y su configuración. Diseña la
secuencia alternando **entradas** (file upload, freeform, selection), **acciones de IA** (prompt) y
**salidas** (response, document drafting), con **checkpoints humanos** (freeform) en los puntos de juicio.

## Índice
- File upload
- Selection list
- Prompt (AI Action)
- Freeform text
- Response
- Document drafting
- Cómo encadenar los pasos (contexto entre pasos)

---

## File upload — recoger ficheros del usuario
Recoge uno o varios ficheros que los pasos siguientes podrán leer.

Configuración:
- **Message**: el texto/instrucción que ve el usuario ("Sube el contrato a revisar…").
- **Number of files**: `Exactly N` (o rangos). Pon `Exactly 1` cuando esperas un único documento.
- **Accepted file types**: son **checkboxes** — `Documents`, `Data and spreadsheets`, `Presentations`,
  `Emails`, `Images`, y **`Freeform text`**.
  - Marcar **`Freeform text`** habilita además un cuadro **"Paste your text in here"**: el usuario puede
    **pegar texto** en vez de subir un fichero. Útil para recibir un **bloque de estado** de otro
    workflow (handoff por pegado) sin manejar ficheros.
  - Marca varias categorías si quieres flexibilidad (p.ej. `Documents` + `Freeform text` para aceptar
    el bloque pegado o como `.docx/.txt/.pdf`).
- **Make step optional**: si el fichero no siempre aplica.
- **Label of file(s) collected**: el nombre de variable con que los pasos siguientes referencian estos
  ficheros.

> **Límite operativo:** la automatización por navegador **no puede subir ficheros** a Harvey ("solo
> ficheros que el usuario ha compartido en la sesión"). En la práctica, los **sube siempre la persona**.
> Los pasos de **texto pegado** sí los puede rellenar la persona (o, con cuidado, pegarse).

## Selection list — elegir de una lista
El usuario elige una opción de un conjunto cerrado (p.ej. "tipo de contrato", "jurisdicción",
"régimen"). Útil para **ramificar** el comportamiento del workflow o fijar un parámetro.

## Prompt (AI Action) — la acción de IA
El caballo de batalla: ejecuta una instrucción de IA y **emite TEXTO**. Configuración:
- **Prompt**: la instrucción (edítala por el **modal "Edit prompt"**, ver `operar-harvey.md`).
- **Workflow Agent context**: **qué pasos/ficheros previos puede ver** este prompt. Conecta aquí los
  file uploads y los outputs de pasos anteriores que necesite. (Es cómo "fluye" el estado.)
- **Embedded Files / Knowledge**: ficheros o bases de conocimiento que el prompt puede consultar (p.ej.
  un **Playbook**, una guía normativa).
- Buenas prácticas del prompt:
  - Dale **rol** y **tarea** claros.
  - Pídele que **abra con una cabecera de estado (harness)** y, si va a haber handoff, que **emita un
    bloque parseable** (secciones con JSON) al final. Ver `patrones.md`.
  - Si hay una directiva condicional (p.ej. "si el gating es X…"), antepón una **directiva principal**
    explícita para que no se quede sin ejecutar ninguna rama.

## Freeform text — el checkpoint humano
Un paso donde **la persona escribe o pega**. Es el mecanismo de **validación/decisión humana**:
- Validar/!corregir lo inferido por la IA.
- Tomar una decisión de juicio (aceptar/rechazar/modificar).
- Pegar el **bloque de estado** de otro workflow para el handoff.
- Confirmar el "número" o resultado antes de cerrar.

Colócalos en cada punto de **juicio profesional** o **acción irreversible**. Son pocos y deliberados:
"minimiza la intervención salvo donde de verdad hace falta una persona".

## Response — mostrar una salida
Presenta texto al usuario (un resumen, el resultado, el bloque de estado para copiar).

## Document drafting — generar un Word (⚠ poco fiable)
Genera un documento Word con IA. **Es probabilístico**: en la práctica **falla con frecuencia** (no-op,
documento en blanco, "No changes were suggested"). **No lo uses para el entregable final.**

Patrón fiable en su lugar (ver `patrones.md` → "entregables deterministas"):
1. Un paso **Prompt** emite el **bloque parseable** (texto) con todos los datos del entregable.
2. Un **motor determinista** propio (script) **renderiza** el Word/Excel/PDF final desde ese bloque, con
   formato y marca corporativa, de forma reproducible.

Document drafting puede servir como *preview* o borrador interno, nunca como la entrega.

---

## Cómo encadenar los pasos (el flujo de estado)
Los pasos no comparten estado automáticamente: **conéctalos por el "Workflow Agent context"** de cada
paso Prompt (qué pasos previos ve). El estado "viaja" así:
- Un file upload o freeform aporta datos → un Prompt los lee (vía context) → emite texto → el siguiente
  Prompt lee ese texto (vía context) → etc.
- **Entre workflows distintos** no hay context compartido: el handoff se hace **materializando el estado
  en texto** (el bloque parseable) y **volviéndolo a meter** (pegado o subido) en el siguiente workflow.
