---
description: Genera la base de importacion AEAT (.200+XML) de una carpeta de sociedades
allowed-tools: Bash, Read, Write
argument-hint: "[carpeta-expedientes] [ejercicio]"
---

Genera la **base de importación a la AEAT** (`.200` BOE + XML mod200) para las sociedades de **$1** (ejercicio
**$2**, por defecto 2024), para no picar las declaraciones a mano. Carga la skill `suite-is-export-aeat` y
sigue sus reglas duras (el motor firma el número; PII en local; `.200` provisional).

1. **Motor valido (LOCAL/INTERNO, por la PII):** `curl -s http://127.0.0.1:8000/salud` y
   `curl -s http://127.0.0.1:8000/version` → debe dar `ok:true` y `version >= 1.18.3`. En Garrigues Windows
   Enterprise, si no responde o es antiguo, debe arrancarse/actualizarse el servicio Windows local o configurarse
   `SUITE_IS_ENGINE_URL`. No uses el cloud demo con datos reales.
2. **Decide si procede lote.** Por defecto, usa `/is-nueva` declaracion a declaracion. Corre lote solo si el
   grupo es homogeneo o si la sociedad mas compleja/representativa ya paso OpenWeb. No uses lote de entrada con
   foralidad, SOCIMI, B.1/B.2 relevante, ECPN sensible, modelo abreviado dudoso o anexos pesados.
3. **Corre el lote** sobre la carpeta (un SyS por sociedad). Si el abogado tiene identificativos y/o la
   liquidación firmada por sociedad, que aporte un `map.csv` (`--map`):

   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/suite-is-export-aeat/scripts/lote_export_aeat.py \
     --carpeta "$1" --ejercicio "${2:-2024}" --out "$1/_export_aeat_out"
   ```

4. **Resume el `informe_lote.md`**: cuántas OK, cuántas con incidencia y la lista de **excepciones**
   (SyS a revisar + casillas que dependen de otros modelos a cero). El resto queda listo para importar en
   Sociedades WEB, pero revisa individualmente cada manifiesto y cada `00_IMPORTAR_OPENWEB_*.200`. Recuerda:
   el `.200` es **provisional** hasta validarlo con una importación real.

No subas la carpeta de salida al repo (contiene PII). Los nombres usan codename, no el NIF.
