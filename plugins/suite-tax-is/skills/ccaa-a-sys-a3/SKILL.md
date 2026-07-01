---
name: ccaa-a-sys-a3
description: >-
  Convierte las CUENTAS ANUALES (Balance + Cuenta de Pérdidas y Ganancias, o un balance resumido) en un
  SUMAS Y SALDOS en cuentas del PGC de 4 dígitos, cuadrado y listo para el motor SuiteIS, CUANDO el cliente
  NO ha entregado un Sumas y Saldos. La lectura de la CCAA la hace Claude por VISIÓN (también
  escaneados/imagen) — sin OCR/Docling. Úsala siempre que para un expediente del Impuesto sobre Sociedades /
  Modelo 200 solo haya CCAA / estados financieros / balance + PyG (PDF, imagen, Word o Excel) y falte el SyS.
  Genera 3 tablas (Sumas y Saldos A3 · Comprobación · Mapeo PGC), guarda el .xlsx y lo VERIFICA por el motor:
  sus totales deben coincidir con los TOTALES DECLARADOS de la CCAA (TOTAL ACTIVO, TOTAL PN+PASIVO,
  resultado). Si existe SyS, usa ese. Triggers: "solo tengo las cuentas anuales", "no hay sumas y saldos",
  "CCAA", "cuentas anuales", "balance y PyG", "balance de situación", "generar sumas y saldos", "SyS desde el
  balance", "convertir el balance a A3".
---

# CCAA → Sumas y Saldos A3 (el LLM lee la CCAA; el motor verifica y firma)

## Para qué es esto
Muchos clientes entregan **solo las Cuentas Anuales** (Balance + PyG) y **no** un Sumas y Saldos. El motor
SuiteIS arranca desde un **Sumas y Saldos** (formato A3). Esta skill **infiere** un Sumas y Saldos en cuentas
PGC de 4 dígitos, cuadrado, que reproduce el balance y la PyG, para alimentar el flujo normal del expediente.

## Método (LLM-visión primario — sin OCR)
**Claude lee la CCAA directamente por visión**, incluida en PDF escaneado o imagen. No hace falta OCR/Docling
(que era frágil con escaneados): el modelo ve el balance y la PyG y transcribe las partidas y los totales.
La fiabilidad **no se asume**: se comprueba en el Paso 3 contra los **totales declarados** de la propia CCAA.

**Doctrina (no negociable):** el LLM **propone** el SyS; **el número lo firma el motor** (ADR-001). La
declaración se completa y recalcula en **Sociedades WEB Open** de la AEAT. Lo inferido es **carga asistida**:
el abogado la revisa.

## Cuándo usarla / cuándo NO
- **Úsala** cuando para el expediente solo hay CCAA / balance + PyG y falta el SyS.
- **No la uses** si el cliente entregó un Sumas y Saldos real **en plan PGC español** → ese es la fuente
  (flujo normal: `descubrir-expediente` → `arrancar-motor` → pipeline). El SyS real (PGC) siempre gana.

### Variante: SyS en plan AJENO (SAP / extranjero / inglés)
Si el cliente sí entregó un SyS **pero en un plan no-PGC** (códigos SAP de 6 díg., descripciones en inglés —
típico de multinacionales), el motor determinista **no lo mapea** (ni prefijo PGC ni descripción española
casan). Aplica **el mismo método**: el LLM lee ese SyS y lo **normaliza a PGC 4 díg.** (traduce/mapea cada
cuenta a su PGC por la descripción), excluyendo la 129 (resultado = grupos 6/7), y el motor verifica. El
**cross-check** aquí es el **resultado contabilizado del cliente** (su cuenta 129): el resultado que deriva el
motor de los grupos 6/7 debe coincidir con él (en vez de los totales de la CCAA). Validado en un caso retail
SAP real (codename CYA, 2026-06-26): cuadre + 0 sin regla + resultado al céntimo + XSD válido.

## Paso 1 — Leer la CCAA e inferir el Sumas y Saldos
Lee el Balance (Activo y PN+Pasivo) y la Cuenta de PyG del cliente (con la herramienta de lectura de PDF/
imagen; si es escaneado, léelo igual por visión). Anota desde la CCAA, para el Paso 3, **tres totales
declarados**: **TOTAL ACTIVO**, **TOTAL PATRIMONIO NETO + PASIVO** y **Resultado del ejercicio**.

Luego infiere el SyS con estas reglas (mismas que validaron GIP al céntimo):
> Genera un **Sumas y Saldos** ficticio, contablemente razonable, con el **menor número de cuentas únicas**:
> - Cuentas del PGC de **4 dígitos**, cada una **una sola vez**, con el **prefijo en**
>   [`reference/pgc_mapeado.md`](reference/pgc_mapeado.md) (si una partida no encaja en ningún prefijo de esa
>   lista, usa la cuenta razonable más cercana que **sí** esté y anótalo).
> - **Total Debe = Total Haber** y **Σ deudores = Σ acreedores**.
> - Activo → **deudor**; Pasivo y PN → **acreedor**; Gastos → deudor; Ingresos → acreedor. No conviertas un
>   pasivo positivo en activo ni un activo negativo en pasivo.
> - **El resultado del ejercicio NO es una cuenta propia (no uses 129).** Incluye las cuentas de los **grupos
>   6 y 7** (gastos/ingresos) de la PyG: el motor deriva el resultado y lo lleva al PN. El PN del SyS =
>   capital + prima + reservas + ajustes (SIN la línea de resultado).
> - **Aportaciones de socios / Aportación de socios** no es prima de emisión: usa **1180**, no 1100. La cuenta
>   1100 queda reservada para una línea explícita de **Prima de emisión**. Si se usa 1100 para aportaciones, el
>   balance va a `00190` y el ECPN puede chocar con Sociedades WEB (caso RHVS).
> - **Impuesto sobre beneficios** → grupo 63 (p. ej. 6300), respetando signo (gasto deudor / ingreso acreedor).
> - Para cuadrar, usa cuentas razonables de la lista mapeada (reservas, bancos, clientes, proveedores,
>   acreedores, Hacienda Pública).
>
> Presenta **tres tablas**, sin texto adicional:
> - **Tabla 1 "Sumas y Saldos A3"**: Cuenta / Descripción / Saldo Final / Debe / Haber / Saldo Inicial.
>   - **Saldo Final** = saldo de cierre del ejercicio **N** (columna N del Balance). Para las cuentas de
>     **patrimonio neto** usa el **SALDO ACUMULADO** del balance (capital nominal, reservas, etc.), **NO** el
>     movimiento/YTD del ERP (un YTD de capital ≈ 0 o pequeño NO es el saldo). Debe = Saldo Final si deudor y 0
>     si no; Haber = −Saldo Final si acreedor y 0 si no.
>   - **Saldo Inicial** = saldo de cierre del ejercicio **N-1** (columna del ejercicio anterior del Balance de la
>     CCAA), **NO cero**. Es la **APERTURA** que necesita el ECPN. ⚠️ Con `Saldo Inicial = 0` el ECPN sale con
>     apertura 0 y la AEAT lo recalcula como cierre N-1 ≠ 0 → rechaza con **E25400632/E25400645** (FRECH). Si la
>     CCAA no trae la columna N-1, márcalo **HITL** (no lo inventes a cero). Detalle del mapeo PN→ECPN por
>     columnas y por año en **[references/ecpn-pgc-columnas.md](references/ecpn-pgc-columnas.md)**.
> - **Tabla 2 "Comprobación"**: Total Debe | Total Haber | Total Saldo Deudor | Total Saldo Acreedor |
>   Resultado contable | Nº de cuentas | Confirmación de cuentas únicas.
> - **Tabla 3 "Mapeo PGC"**: Partida del balance o PyG | Cuenta utilizada | Descripción | Importe.

## Paso 2 — Guardar el SyS A3 como .xlsx
Vuelca la Tabla 1 a un Excel con la cabecera exacta en la fila 1
(`Cuenta | Descripción | Saldo Final | Debe | Haber | Saldo Inicial`) y guárdalo en la carpeta del
expediente como `SyS_<codename>_<ejercicio>.xlsx`. Es la entrada estándar del motor.

## Paso 3 — VERIFICAR por el motor (gate obligatorio)
Con el motor disponible (`arrancar-motor`), corre el guardarraíl con los **tres totales que leíste de la CCAA**:

```bash
python3 scripts/verificar_sys_vs_ccaa.py \
  --sys RUTA/SyS_<codename>_<ejercicio>.xlsx --ejercicio <ejercicio> \
  --total-activo <TOTAL ACTIVO de la CCAA> \
  --total-pn-pasivo <TOTAL PN+PASIVO de la CCAA> \
  --resultado <Resultado del ejercicio de la CCAA>
```

Exige (si no, **HITL**):
- `dif (00180 − 00252) = 0` → el balance **cuadra** en el motor.
- `0 cuentas sin regla` → todas las cuentas tienen casilla (si no, corrige su prefijo por uno de
  `reference/pgc_mapeado.md`).
- **`00180 == TOTAL ACTIVO`, `00252 == TOTAL PN+PASIVO`, `resultado == Resultado del ejercicio`** de la CCAA.
  Esto es lo que confirma que **el LLM leyó/transcribió bien**. Si alguno no cuadra, revisa la Tabla 3
  (importe/cuenta de esa partida) y repite.

**🟢 VERDE** → el SyS inferido entra en el flujo normal del expediente (export a la base AEAT: XML mod200 +
`.200` borrador). **🔴** → carga asistida a revisar por el abogado antes de seguir.

## Fallback (excepcional) — OCR si la visión no basta
Solo si la CCAA es ilegible por visión (escaneo pésimo): usa el OCR del ecosistema
(`ccaa_a_casillas`/`ocr_client` → persona_tax, `OCR_SERVICE_URL`). Es el camino antiguo y frágil; con visión
casi nunca hace falta.

## Cross-check opcional (determinista, sin OCR)
Para una verificación fina por partida, `Extractor-parseador/scripts/ccaa_casillas.py::mapear` casa las
etiquetas de la CCAA (las que ya leíste) contra el rótulo de cada casilla del catálogo (exacto + alias +
fuzzy). Útil para detectar una partida mal clasificada; secundario frente al gate de totales del Paso 3.

## Notas
- **Caso conocido validado (GIP 2025):** SyS inferido de 31 cuentas PGC; el verificador dio **🟢 VERDE** con
  los 3 totales de la CCAA coincidiendo al céntimo (dif 0, 0 sin regla).
- **Guardarraíl = el motor:** si la inferencia elige una cuenta fuera del mapeo o transcribe mal un importe,
  el Paso 3 lo señala (no cuadra / total no coincide) en vez de firmar un número malo.
- La 4ª cifra del PGC afina dentro del prefijo (p. ej. deterioro de participaciones de grupo 696→00315 vs
  otras→00316): matiz de revisión humana que **no** cambia totales ni cuadre.
