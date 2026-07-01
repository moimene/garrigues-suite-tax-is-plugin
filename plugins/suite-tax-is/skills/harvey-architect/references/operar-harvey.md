# Operar Harvey por navegador (mecánica probada)

Léelo **antes de construir** en Harvey. Es la mecánica que funciona (y los errores que cuestan horas).

## Herramienta y acceso
- Conduces Harvey con el **MCP de Chrome** (claude-in-chrome). Si está diferido, cárgalo con ToolSearch
  ("claude-in-chrome").
- Harvey vive en su web (p.ej. `eu.app.harvey.ai`, según la org).
- **Primera acción SIEMPRE: un screenshot para orientarte** ("mira antes de afirmar"). Verifica que hay
  una pestaña logueada en Harvey; si no, **pídeselo al usuario** (no puedes loguear tú).
- **Límites del navegador:** `computer wait` ≤ 10s; `scroll_amount` ≤ 10; agrupa clics/typing/scrolls
  con `browser_batch` para ir rápido.

## Mapa de navegación
- Barra izquierda: **Assistant · Spaces · Vault · Library · Build · History**.
- **Workflows:** Build → "Workflow Agents" = la lista (`/workflows/manage`). Desde ahí abres un workflow
  (para ejecutarlo) o su **builder** (para editarlo: `/workflows/workflow-builder/{id}`).
- **Spaces:** crea/abre el Space del asunto; dentro tiene su Vault y sus conversaciones.

## Crear / editar un Workflow Agent (en el builder)
El builder tiene a la izquierda un chat "Build with Harvey" y a la derecha el **lienzo con los pasos**.
- **Añadir/ordenar pasos:** desde el lienzo ("Add step").
- **Configurar un paso:** clic en el paso → su panel de config se abre a la derecha (Message, tipos de
  fichero, contexto, etc.).
- **EDITAR EL PROMPT DE UN PASO — el método que FUNCIONA:** clic en el paso → clic en el **icono de
  expandir** del campo de prompt → se abre el **modal "Edit prompt"** → clic dentro del textarea →
  escribe (`type`) → **Save** (modal). Arriba aparece "**Draft has unsaved changes / Save**" → **Save**.
  Para publicar: "**Publish changes**" (arriba dcha.).
  - ⚠️ El cuadro **"Ask Harvey"** (construir por lenguaje natural) **NO captura el tecleo de la
    automatización** de forma fiable: **no lo uses para editar**; usa el modal.
  - Editar el **Message** de un paso File upload o un textarea corto: si no quieres reemplazar, **antepón**
    texto colocando el cursor al inicio y tecleando (prepend es fiable). Para reemplazar todo, el modal.
- **El editor del prompt es un contenteditable Lexical; los @-refs son chips `<button>`, no texto.**
  - **Nunca hagas full-replace (cmd+A → type) en un prompt que contenga un chip @-ref:** perderías la
    referencia. Edición **quirúrgica**: `window.find("texto ancla")` para seleccionar + `document.
    execCommand('insertText', false, "reemplazo")` (registra en Lexical, cambia el contador). Para
    **borrar**, selecciona con `window.find` y pulsa **Backspace real** (`execCommand('delete')` y el
    insertText vacío NO borran en Lexical).
  - Full-replace (cmd+A → type por chunks ≤ 600 chars) sí es seguro en prompts **sin chip**.
  - `type` de >~1000 chars da **timeout CDP a 30 s pero el texto sí entra**: trocea y verifica por
    `innerText`/contador. Si el volcado con banners (`|`, `=`) dispara el filtro "BLOCKED", léelo saneado.
- **@-referencia INLINE para que un paso lea otro:** el contenido de un paso previo (sobre todo
  Freeform/User-input) **solo** llega a un prompt posterior si lo **@-referencias INLINE** en su cuerpo;
  el panel «Workflow Agent context» no inyecta su texto (ver patrón "Gating de calidad").
- **Versionado:** Draft → "Publish changes" crea la versión publicada. Hay historial de versiones.
  «Publish changes» a veces no se muestra en una pestaña ya usada: ábrelo por **Library → fila → Edit
  Agent** o en **pestaña nueva** (Manage → ⋯ → "Open in new tab"), que renderiza la barra completa. La
  **descripción del agente** se edita por el lápiz junto al título (metadata; se aplica al instante, sin Publish).

## Ejecutar un Workflow Agent
- Ábrelo (no el builder). Muestra los pasos en orden.
- **Los pasos File upload los rellena la PERSONA** (sube los ficheros): la automatización **no puede
  subir ficheros** ("solo los que el usuario ha compartido en la sesión").
- Los pasos con **"Paste your text in here"** aceptan texto pegado.
- **"Send"** avanza al siguiente paso.
- ⚠️ **"Finished in N steps" + un cuadro pidiéndote algo = NO ha terminado.** Es un **checkpoint humano**
  (un paso Freeform esperando tu validación/decisión). El workflow continúa al responder.
- Cuando un paso de IA tarda, muestra "Working… (Estimated runtime …)"; puedes seguir en otra cosa.

## Guardarraíles (no los saltes)
- **No subas ficheros** por automatización → los sube el usuario.
- **No publiques, no borres, no ejecutes acciones irreversibles sin OK explícito del usuario.** Tú
  preparas y guías; la persona pulsa el botón. (Borrar workflows, publicar cambios, enviar al cliente.)
- **No toques** workflows/Spaces de otros usuarios sin permiso; pueden ser dependencias.
- **Confidencialidad:** los datos de cliente viven en Vault/Space, **no en el repo de código** (ni en git).
- **Edita prompts solo por el modal "Edit prompt".**

## Errores típicos (y su causa)
| Síntoma | Causa / arreglo |
|---|---|
| El texto tecleado "no entra" al editar | Estabas en "Ask Harvey"; usa el **modal "Edit prompt"**. |
| "Parece que terminó pero no generó nada" | Era un **checkpoint humano** ("Finished in N steps" + cuadro), no el fin. |
| Document drafting sale en blanco / "No changes" | Es **probabilístico**; genera el entregable con el **motor determinista**, no con Harvey. |
| No puedo subir el fichero | La automatización **no sube** a Harvey; que lo suba el usuario. |
| `scroll_amount`/`wait` da error de validación | Límites: scroll ≤ 10, wait ≤ 10s. |
| Un paso "no ve" lo que validó/escribió un paso anterior | No basta con tenerlo en «Workflow Agent context»: **@-referéncialo INLINE** (`@nombre_paso`) en el prompt que lo consume. |
| Editar un prompt rompió un @-ref | Tenía un **chip Lexical**; no uses full-replace. Edición quirúrgica con `window.find` + `execCommand insertText`. |
| No aparece "Publish changes" | Ábrelo por **Library → Edit Agent** o en **pestaña nueva** (Manage → ⋯ → Open in new tab). |
