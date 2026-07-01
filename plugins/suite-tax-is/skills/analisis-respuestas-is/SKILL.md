---
name: analisis-respuestas-is
description: >-
  Copiloto de CONSULTA y ANÁLISIS del Impuesto sobre Sociedades (Modelo 200) para el abogado: responde dudas de
  CRITERIO fiscal citando el Manual de Sociedades 2025 empaquetado, y EXPLICA/AUDITA una declaración concreta (la
  liquidación que firma el motor). ÚSALA cuando el usuario pregunte «¿a qué casilla va…?», «¿cómo se calcula el
  límite de BINs / los gastos financieros / la cuota?», «¿qué dice el Manual sobre…?», «explica esta liquidación /
  la casilla 00552», «¿por qué sale esta cuota?», «¿qué ajustes faltan?», «revisa/audita la declaración», o
  consulte un régimen, una deducción, la exención del art. 21, operaciones vinculadas, la reserva de
  capitalización/nivelación, la DA 15ª, etc. El número lo firma el MOTOR (ADR-001): esta skill explica y razona,
  CITA la fuente y MARCA lo no soportado; NO inventa casillas ni doctrina. Para errores de IMPORTACIÓN del .200
  (EMAL…, XSD, «no me importa») usa antes `gestion-errores-is`; para GENERAR el .200 usa `is-nueva` /
  `suite-is-export-aeat`.
metadata:
  version: "1.1.0"
---

# Análisis y respuestas — Impuesto sobre Sociedades (Suite Tax IS)

Dos modos: **CONSULTA** (dudas de criterio, citando el Manual) y **ANÁLISIS** (explicar/auditar una declaración
concreta). Elige por la pregunta; a menudo se combinan (explicar una casilla = análisis + cita del criterio).

## Frontera (no negociable)
- **El número lo firma el MOTOR** (ADR-001): cualquier cifra concreta sale del motor (`/liquidar`, `/auditoria-*`)
  o del `.200`/`estado.json` del expediente — **nunca la inventes ni la recalcules a mano**.
- **Toda afirmación de criterio CITA el Manual 2025** (capítulo/epígrafe). Si el Manual no lo cubre o es ambiguo,
  **dilo** («no verificado en el Manual») y deja la decisión al abogado. No rellenes con doctrina de memoria.
- **No es asesoramiento definitivo:** es apoyo a la decisión del abogado.
- **PII local:** codename; nunca NIF/razón social/importes fuera del expediente.

## Modo CONSULTA (dudas de criterio)
1. Identifica el tema y enruta al capítulo (mapa en `references/cadena-y-mapa-manual.md`).
2. Abre **solo** ese capítulo: `${CLAUDE_PLUGIN_ROOT}/engine/suite-is/Manual_Sociedades_2025_md/` (empieza por
   `00_INDICE.md`). **Cita** capítulo/epígrafe; no vuelques el Manual entero (lectura on-demand).
3. Si la duda es «¿a qué casilla va X?», cruza con el mapeo PGC→casilla:
   `${CLAUDE_PLUGIN_ROOT}/skills/ccaa-a-sys-a3/reference/pgc_mapeado.md`.
4. Responde: criterio en breve + **cita** + casilla(s) si aplica + cautelas (vigencia, prorrateo, excepciones).
   Marca lo no soportado.

## Modo ANÁLISIS (de una declaración concreta)
1. **Consigue el número del motor** (arráncalo con `arrancar-motor` si no responde en `127.0.0.1:8000`):
   - liquidación completa → `POST /liquidar` (o lee el `estado.json` / `.200` del expediente ya generado);
   - read-only → `POST /auditoria-mayores`, `POST /auditoria-propuestas`, `POST /auditoria-informe`,
     `GET /auditoria-checklist`;
   - explicación de una casilla → `GET /explicar/{casilla}`; reglas activas → `GET /reglas-activas`; triaje
     art. 15 → `POST /triaje`. El motor también expone `/gf-criterio` y `/juez-normativo` (criterio): verifica su
     contrato en `engine_service/` antes de usarlos.
2. **Explica la cadena** `00500 → 00501 → 00550 → 00552 → 00562 → … → 00621` (detalle en la referencia): qué
   entra en cada eslabón y de dónde sale el saldo (cuenta/ajuste).
3. **Audita** (señala, no corrijas a ciegas):
   - ¿cuadran el resultado contable (00500) y el control `B2 + B3 = 00501`?
   - **límites**: BINs (art. 26 / DA 15ª por INCN, casilla 00255), gastos financieros (art. 16, suelo 1 M€,
     casilla 02369), reserva de capitalización/nivelación, tipo aplicado. En **grupo fiscal** la página 20 va al
     Modelo 220, **no** al miembro.
   - **ajustes que faltan**: contrasta con el Manual Cap 05 (amortizaciones, deterioros, provisiones; vinculadas
     → Cap 08).
   - **casillas dependientes de otros modelos** (retenciones / pagos a cuenta) a cero → «Pendiente AEAT».
   - cuentas **«inferida»** / HITL del expediente → revisión tras importar.
4. Conclusión: qué está **soportado** (motor + Manual), qué es **criterio del abogado**, qué queda **pendiente**.

## Cadena de liquidación y límites
Detalle verificado (cadena de casillas, tope de BINs, art. 16, mapa tema→capítulo) en
`references/cadena-y-mapa-manual.md`. Si algo discrepa, mandan el **motor** y el **Manual**, no la memoria.

## RAG de reglas (importabilidad + experiencia Open)
Para «¿qué significa este error / por qué bloquea / qué hago?» y para enrutar por **casilla o código de error**,
consulta la **RAG de reglas** (3 capas: Manual/norma · Diseño de Registro · experiencia Open):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/engine/suite-is/scripts/rag_reglas.py" <casilla|error|familia|texto>
# p. ej.: E25402369 · 00562 · grupo_fiscal · micropyme · ECPN
```

Cada regla trae `fuente`, `fase` (pre_import / post_import_fiscal), `modo` (auto_seguro / hitl_requerido /
no_local), las **casillas** y **códigos de error** implicados, el **módulo** que la implementa y el **test** que la
protege. Úsala para EXPLICAR (no para decidir el número): la cifra la firma el motor; el criterio lo cita el
Manual; la RAG dice qué exige el importador y dónde está implementado. Dataset: `engine/suite-is/rules/rag/reglas_open.yaml`.

## Reglas
- Cifra → del **motor**. Criterio → del **Manual**, citado. Lo no cubierto → marcado «no verificado»; decide el abogado.
- **No inventes** casillas, importes ni doctrina. No dupliques `gestion-errores-is` (errores de importación) ni
  `is-nueva` / `suite-is-export-aeat` (generar el .200).
- **PII local** (codename). Si detectas un criterio recurrente no soportado, propónlo como mejora del motor/Manual.

## Fuentes
- Manual AEAT 2025: `${CLAUDE_PLUGIN_ROOT}/engine/suite-is/Manual_Sociedades_2025_md/` (`00_INDICE.md`).
- Mapeo PGC→casilla: `${CLAUDE_PLUGIN_ROOT}/skills/ccaa-a-sys-a3/reference/pgc_mapeado.md`.
- Motor (ADR-001): endpoints `/liquidar`, `/auditoria-*`, `/explicar/{casilla}`, `/reglas-activas`, `/triaje` en
  `127.0.0.1:8000`.
- `references/cadena-y-mapa-manual.md` — cadena de casillas + límites + mapa del Manual.
- **RAG de reglas:** `${CLAUDE_PLUGIN_ROOT}/engine/suite-is/scripts/rag_reglas.py` + `engine/suite-is/rules/rag/reglas_open.yaml` (consulta por casilla/error/familia).
