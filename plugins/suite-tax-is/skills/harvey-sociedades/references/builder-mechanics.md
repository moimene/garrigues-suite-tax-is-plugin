# Mecánica click-a-click de Harvey (builder, Space, Vault)

Detalle operativo verificado. Las coordenadas exactas cambian entre cargas — guíate por screenshots y
los textos de los elementos, no por píxeles fijos. Conduce con el MCP `claude-in-chrome`.

## Abrir un builder de workflow
1. `navigate` a `eu.app.harvey.ai/workflows/workflow-builder/{id}`.
2. Espera ~8 s (carga pesada). Si el canvas (mitad derecha) sale **en blanco**, haz un `scroll` (arriba o
   abajo) sobre él → renderiza los pasos. El panel izquierdo es el chat "Build with Harvey" (historial,
   no es el workflow).
3. La barra superior derecha tiene **Test**, a veces **Share**, **Publish changes** (solo si hay draft
   sin publicar) y **`⋯`**.

## Renombrar / editar detalles de un WF (instantáneo, sin publish)
1. `⋯` (arriba dcha.) → **"Edit agent details"**.
2. Modal con **Workflow Agent name**, Practice area(s), Document classification tags, **Description**.
   Aviso: no metas info confidencial (es visible en el workspace).
3. Click en el campo Name → `cmd+a` → `type` el nuevo nombre (los caracteres ①②▶«»→ se teclean bien).
4. **Save changes** → toast "Workflow Agent details updated". El título y la tarjeta del Space se
   actualizan al instante.

## Editar el texto de un paso
Primero abre el paso: click en su tarjeta del canvas → se abre su panel de config a la derecha.

**Paso Prompt / Document drafting (campo *Instructions*):**
1. En el campo Instructions hay un **icono de expandir** (↗) abajo-derecha → click → se abre el modal
   **"Edit prompt"** (textarea grande).
2. Para *prepend*: click al inicio del texto → (opcional `cmd+Up` para ir al principio) → `type` el
   bloque nuevo + `\n\n`. Para *reemplazar*: `cmd+a` → `type`.
3. **Save** (botón del modal) → el panel inline refleja el cambio.

**Paso Freeform text / File upload (campo *Message*):**
1. Click dentro del **textarea Message** → `cmd+a` → `type`. (Para textos largos, trocea en ~600 chars
   para evitar el timeout CDP de `type`; los `\n` crean saltos de línea, no envían.)
2. Para leer el valor actual completo (la a11y solo da el placeholder): haz `scroll` dentro del textarea
   y `zoom` por tramos.

**Guardar y publicar:**
- Tras editar aparece barra **"Draft has unsaved changes · Revert · Save"** → **Save** → "Changes saved".
- Si es paso **Prompt/Freeform**, el botón **"Publish changes"** (arriba dcha., negro) queda activo →
  **pídele OK al usuario** → click → toast "Workflow published successfully".
- Si es el **Message de un File-upload**, el cambio queda aplicado al **Save** (no aparece "Publish
  changes"; reescribir el mismo texto no genera "unsaved changes" → confirma que está aplicado).
- ⚠️ El cuadro **"Ask Harvey"** del builder NO captura el tecleo de automatización. No lo uses.

## Paleta de tipos de paso ("Add step")
User input: File upload · Freeform text · Selection list · Review table selection. AI action: Prompt ·
Document drafting · Review table. Logic: **Conditional**. Output: Response. **No existe "lanzar otro
workflow"** → un WF acaba en Response; no encadena con otro WF.

## Ejecutar un workflow (run)
- Desde el Space: hover en la tarjeta del WF → **"Run agent"**. (O abre el WF y "Run/Test".)
- Pasos **File upload**: "Drag and drop / Choose file" → **lo hace el abogado** (la automatización no
  puede; el diálogo es del SO).
- Pasos **Freeform/Selection**: sí aceptan tu tecleo/selección. **"Send"** avanza.
- Paso 1 de WF-2 ("Aporta el estado tras WF-1"): tiene además **"Paste your text in here"** → pega el
  bloque (se guarda como `.txt` adjunto) → Send.
- **"Finished in N steps" + un cuadro pidiéndote algo = NO ha terminado**: es un **checkpoint humano**
  (confirmar huecos / validar issues / validar número). Responde en el campo y Send.
- Para leer una salida larga (bloque parseable): `get_page_text` del tab; usa el botón **Copy** de la
  respuesta para llevar el bloque al portapapeles y pegarlo en WF-2 (`cmd+v`).

## Borrar workflows (lo ejecuta el usuario)
1. **Build → Manage** (`/workflows/manage`).
2. Marca el/los **checkbox(es)** (columna izquierda). Aparece barra inferior **"N selected · Unpublish ·
   Delete"**; cada fila tiene también un icono papelera al hover.
3. **El usuario** pulsa **Delete** y **confirma** en el diálogo.
4. ⚠️ Tras hacer `scroll`, clica el **checkbox exacto** — si clicas el cuerpo de la fila, navegas al
   builder. Mejor: borra por tandas lo visible sin scroll. Recablea los Spaces (quitar tarjetas
   obsoletas) **antes** de borrar globalmente, para no dejar Spaces sin herramientas.

## Space: Customize, Vaults, Tools, View as
- **Customize** (lápiz ✎ del Space): **Appearance** (logo / accent color / header image con Replace),
  **Welcome** (Título + Contenido + toggle **Visible** + **Preview**; **solo externos/invitados**),
  **About** (Name + Description).
- **View as** (arriba dcha.): solo **External collaborators** / **Invited guests** (no hay "miembro
  interno"). Útil para ver el Welcome como lo verá un externo.
- **Crear/añadir Vault:** Data → **"+ Vault"** → **"Create vault"** (nuevo) o seleccionar uno existente.
  Nuevo: fuente **"Upload files or folders"** → Next → nombre + descripción → **Create** → **Select** →
  **Add to space**. El abogado sube luego los ficheros (Upload files / Upload from computer).
- **Tools:** `+ Workflow Agents` (buscar y `Add to space`) y `+ Playbooks`. Quitar: hover tarjeta → `⋯`
  → **Remove** (sale del Space; reversible).

## Lectura en el dominio Harvey
- El **JS está bloqueado** ("Cookie/query string data"): usa `read_page` (a11y), `get_page_text`, `find`,
  screenshots y `zoom`. No dependas de `javascript_tool` para leer valores.
