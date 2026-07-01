---
name: is200-importabilidad-hitl
description: Diagnosticar y corregir en modo HITL ficheros `.200` del Modelo 200 hasta que sean importables en Sociedades WEB/Open, respetando siempre el Diseño de Registro oficial. Usar cuando el usuario aporte un `.200`, errores/avisos de importación AEAT/Open, pida "arreglar importación", "validar importabilidad", "evitar picar datos", "corregir E254/EMAL/EPOR/FRECH", o quiera iterar parches con revisión humana antes de reimportar.
metadata:
  version: "1.1.0"
---

# IS200 Importabilidad HITL

## Secuencia (orden duro, no se solapa)

**FASE 1 — Importabilidad (automática, esta skill): PRIMERO conseguir un import positivo.** El motor emite el
`.200` como vehículo de carga con liquidación BASE cosmética coherente; este validador es un **pre-vuelo
automático** que solo resuelve lo `auto_seguro` (mecánico, DR) y señala lo **estructural** que impediría
importar. **No se pide criterio fiscal al abogado en Fase 1** (no improvisar liquidación ni rellenar a mano:
eso rompió la importación en la incidencia document-6).

**GATE = resultado POSITIVO de importación** en Sociedades WEB (aceptado; idealmente «00001 — no existen errores»).

**FASE 2 — HITL fiscal: SOLO DESPUÉS del import positivo.** El abogado completa la liquidación fiscal real
(ajustes 00417/00418, deducciones/DDI, BINs, régimen/tipo, GF art. 16, distribución, foral) en Sociedades WEB,
que recalcula. Es juicio fiscal (ADR-001, cubo 3); el motor no lo automatiza. Ver
`docs/memoria/2026-06-28-secuencia-importabilidad-luego-hitl-fiscal.md`.

## Principios

1. Respetar siempre el DR. Parsear y emitir solo con `DR200e25_modelo_registro.json` / `dr200.py`; no inventar posiciones, longitudes ni páginas.
2. Tratar la identidad real como `pagina_hoja + casilla`. Nunca aplanar casillas homónimas sin página.
3. Separar tres estados:
   - `dr_ok`: el fichero cumple la estructura de ancho fijo.
   - `importabilidad_probable`: las reglas locales conocidas no anticipan rechazo.
   - `validado_en_open`: evidencia real de Sociedades WEB/Open.
4. Separar fase y gate:
   - `fase=pre_import`: estructura o mecanica necesaria para cargar el fichero.
   - `fase=post_import_fiscal`: juicio fiscal diferido hasta import positivo.
   - `bloquea_importacion`: unico flag que decide el gate local de Fase 1.
5. No hacer autofix ciego. Proponer parches con categoría:
   - `auto_seguro`: derivado mecánico del DR/manual y sin juicio fiscal.
   - `hitl_requerido`: requiere dato o criterio del abogado.
   - `no_local`: depende de validación censal o motor AEAT no replicado.

## Flujo

1. Ejecutar diagnóstico:

```bash
python3 Extractor-parseador/scripts/validacion_importabilidad_200.py \
  "/ruta/declaracion.200" \
  --errors "/ruta/errores_aeat.txt" \
  --ejercicio 2025 \
  --out-json "/tmp/is200_importabilidad.json" \
  --out-md "/tmp/is200_importabilidad.md"
```

Tambien se conserva el wrapper historico de la skill:

```bash
python3 suite-tax-is-plugin/skills/is200-importabilidad-hitl/scripts/diagnosticar_importabilidad.py \
  --file "/ruta/declaracion.200" \
  --errors "/ruta/errores_aeat.txt" \
  --ejercicio 2025 \
  --out-json "/tmp/is200_importabilidad.json" \
  --out-md "/tmp/is200_importabilidad.md"
```

2. Revisar el informe por capas:
   - Estructura DR.
   - Errores AEAT pegados, cruzados con el valor real del `.200`.
   - Reglas locales conocidas (`autocontrol_200.py`).
   - Propuestas de parche y preguntas HITL.

3. Clasificar por fase (orden duro de arriba):
   - **Fase 1 (resolver AHORA, para importar):** `auto_seguro` + estructural de importabilidad (páginas
     obligatorias, modelo de cuentas DP200001B, cuadres, casillas que el importador rechaza por estructura).
     Aplicar por el emisor DR; no pedir criterio fiscal.
   - **Fase 2 (DIFERIR a post-import positivo):** todo `hitl_requerido` **fiscal** — criterio de régimen/tipo,
     ajustes extracontables, distribución del resultado, limitación de gastos financieros (art. 16),
     deducciones/DDI, liquidación firmada. NO se solicita ni bloquea la importación; se lista como pendiente
     para que el abogado lo complete en Sociedades WEB una vez el `.200` haya importado.

4. Aplicar parches solo mediante emisor DR (`dr200.emitir_registro` o pipeline existente). No editar bytes a mano salvo inspección puntual.

5. Revalidar localmente y pedir nueva importación en Open. Incorporar el nuevo texto de errores al siguiente ciclo.

## Recursos

- Leer `references/reglas-importabilidad.md` cuando haga falta explicar cobertura, severidades o diseñar nuevas reglas.
- Usar `Extractor-parseador/scripts/validacion_importabilidad_200.py` como diagnostico canonico.
- Usar `scripts/diagnosticar_importabilidad.py` solo como wrapper compatible de la skill.
- Usar `Extractor-parseador/scripts/modelo200_parser.py`, `dr200.py` y `autocontrol_200.py` como núcleo canónico de parseo/validación.

## Límites

- El diagnóstico local no garantiza importación limpia: Sociedades WEB puede aplicar reglas censales o internas no publicadas.
- Si el manual contradice el DR, prevalece el DR y la regla queda bloqueada hasta revisión.
- Si el usuario aporta errores reales de Open, tratarlos como evidencia prioritaria para ampliar el catálogo local.
