# 1 expediente = 1 carpeta — convención, estado y manifiesto (F3, Cowork)

Cómo el plugin produce un `.200` admisible **por carpeta de expediente**, consumiendo el motor canónico
(ADR-001) por HTTP. Es la cara Cowork de la lanzadera: misma frontera fiscal y mismos gates que la app.

## Estructura de la carpeta
```
EXPEDIENTE_<codename>_<ejercicio>/
  entrada/        SyS / balance / mayores · .200 previo · justificante / datos fiscales (PDF)
  estado.json     estado del stepper (ExpedienteState-compatible) — reanudable
  salida/         <codename>_<ej>_modelo200.200 · _mod200.xml · _estados_contables.xlsx · _agrupado_4d.xlsx
                  canonico.csv · manifiesto.md
```
Si no hay subcarpeta `entrada/`, el pipeline busca los ficheros en la raíz de la carpeta. El SyS se elige por
nombre (sumas/saldo/balance/sys/tb) para no confundirlo con la estimación o la liquidación.

## `estado.json` (R2) — mismo contrato que la app
Mapea `ExpedienteState` (`src/data/expedienteStore.ts`) para **converger** con la web/app local: claves
`pasoActual · alcanceTrabajo · actualizado · contabilidadCargada · fuenteCanonico · a3Confirmado · faseA ·
precarga · liquidacion_firmada · exportBase · salida`. Reanudable: reabrir la carpeta continúa donde quedó.

## `manifiesto.md` (R4) — revisión por bandejas (5 estados)
Cuatro bandejas con su estado de responsabilidad (validado por motor · precargado/requiere confirmación ·
firmada/cosmética · no incluido) + la tabla de **casillas que dependen de otros modelos** (202/222→pagos,
216/210→retenciones, 242→00004) a cero, con su modelo origen + los avisos no bloqueantes del motor.

## El recorrido (6 pasos · 2 checkpoints)
Lo conduce el agente **`is-stepper-orquestador`**; el comando **`/is-nueva`** lo arranca. Pipeline determinista
en `scripts/expediente_carpeta.py`:
1. **Motor valido** (`/salud` + `/version`) → en Garrigues Windows debe responder el servicio local
   `127.0.0.1:8000` o una `SUITE_IS_ENGINE_URL` interna, con `version >= 1.18.3`.
2. **Contabilidad**: `/fase-a-sys` (cuadre `00180=00252`) → `canonico_csv`. Descuadre → **fail-close**, para.
3. **Precarga N-1 + datos fiscales 2025**: `/precarga-anterior` y dossier sobre `.200`/justificante/datos-fiscales
   → caracteres, página 1B, formales, identificativos (nif/razón) y bloque fiscal completo: retenciones/pagos
   fraccionados, arrastres, deducciones pendientes, sanciones/recargos/intereses y gestión/terceros. Todo
   **precargado, a confirmar** (✋ checkpoint del abogado). Los pagos/retenciones van a liquidación; los ajustes
   fiscales quedan HITL.
4. **Liquidación** (✋): si el cierre aporta la cascada **firmada** (`--liquidacion` JSON con `00621`), entra
   como `liquidacion_provisional` y activa el camino firmado (F1); si no, el motor aplica la base cosmética
   coherente (Borrador rápido). El **criterio GF** (leniente/estricto) lo decide el abogado, no el plugin.
5. **Exportar AEAT**: `/expediente/export-base` (fail-close) → `.200` + XML + estados → `salida/` + manifiesto.
6. **Seguimiento**: el abogado importa el `.200` en Sociedades WEB Open (su sesión AEAT) y registra el resultado.

## Uso
```bash
curl -s http://127.0.0.1:8000/salud          # motor Windows local/servicio IT arriba
curl -s http://127.0.0.1:8000/version        # version >= 1.18.3
# Una carpeta (stepper por expediente):
python3 ${CLAUDE_PLUGIN_ROOT}/skills/suite-is-export-aeat/scripts/expediente_carpeta.py \
  --carpeta /ruta/local/EXPEDIENTE_ACME_2025 --codename ACME --ejercicio 2025
# con liquidación firmada del cierre (JSON {casilla:importe}):
  ... --liquidacion /ruta/local/cierre_ACME.json
# Muchas carpetas/sociedades a la vez: usa lote_export_aeat.py (modo lote).
```

## Guardarraíles
- **El motor firma el número** (ADR-001); el plugin no inventa casillas.
- **Fail-close**: descuadre/OCR/HITL/régimen/XSD → para y escribe el motivo; no se parchea el dato.
- **PII local**: engine en local; carpeta y salidas **gitignored**; nombres en **codename**, nunca el NIF;
  la consola no imprime NIF/razón/importes.
- **Push/PR y Supabase = humano.** El `.200` es BORRADOR: la validez la confirma el import real en Sociedades WEB.
