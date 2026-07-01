# Referencia — cadena de liquidación IS y mapa del Manual 2025

Uso interno de la skill `analisis-respuestas-is`. **Toda cifra concreta la firma el MOTOR** (ADR-001); esta
referencia sirve para EXPLICAR la mecánica y ENRUTAR al Manual, no para calcular a mano. La semántica está
validada contra el Manual de Sociedades 2025 (Cap 05/06) y la skill `suite-is-motor`.

## Cadena de casillas del Modelo 200 (oficial, validada Cap 05/06)
```
00500  resultado contable del ejercicio
 → 00501  resultado antes de impuestos  (= 00500 + corrección por el IS)
 → 00550  BASE IMPONIBLE PREVIA          (= 00501 + (00417 − 00418))
 → − 01032 reserva de capitalización  − 00547 BINs compensadas
 → 00552  BASE IMPONIBLE
 → 01330  base tras reserva de nivelación
 → 00562  CUOTA ÍNTEGRA                  (= 00552 × tipo)
 → 00582  cuota íntegra ajustada positiva
 → 00592  cuota líquida                  (tras bonificaciones y deducciones)
 → 00599  cuota del ejercicio
 → 00611  cuota diferencial
 → 01586  …
 → 00621  LÍQUIDO A INGRESAR / a devolver
```
El esqueleto que más se cita (`00550 → 00547 → 00552 → 00562 → 00621`) es correcto pero **salta**
01032/00582/00592/00599/00611/01586.

### Composición de la base previa 00550 (D8)
`B12 = B2 + B3 + B4 + B5`, donde:
- **B2 = resultado contable (00500)**
- **B3 = corrección por el IS = 00301 − 00302** (+ `00004` si hay Impuesto Complementario)
- **B4 = ajustes permanentes**, **B5 = ajustes temporarios**
- **Control:** `B2 + B3 = resultado antes de impuestos = 00501` (Manual Cap 05; art. 15.b LIS).

## Tope de compensación de BINs (art. 26 LIS / DA 15ª)
Por **INCN individual** (casilla **00255** del Modelo 200 anterior), sobre la base previa:
| INCN | Límite |
|---|---|
| < 20 M€ | **70 %** (mínimo **1.000.000 €** siempre compensable) |
| 20–60 M€ | **50 %** |
| ≥ 60 M€ | **25 %** |

Esencia: `compensable = min(BINs_pendientes, max(1.000.000 € prorrateado, límite% × base_previa))`.

**Cautelas (no en la fórmula base):** (1) los tramos **50/25 %** de la DA 15ª tienen **vigencia acotada**
(no son atemporales); (2) el **mínimo de 1 M€ se PRORRATEA** si el período < 12 meses; (3) **excepciones** al
límite (quitas/esperas, extinción, entidad de nueva creación art. 26.3 → casilla **00070**, reversión de
deterioros pre-2021); (4) **no confundir** con el límite homónimo del **art. 11.12 LIS** (deterioros art. 13.1:
mismos 70/50/25 % y misma DA 15ª, concepto distinto).

## Límite de gastos financieros (art. 16 LIS) — página 20 (DP200020)
30 % del beneficio operativo, con **suelo de 1.000.000 €** (casilla **02369** = límite total). En **grupo
fiscal** la limitación se calcula a nivel de grupo (Modelo 220): el **miembro NO lleva la página 20** (caracteres
de configuración 00009 dominante / 00010 dependiente).

## Mapa tema → capítulo del Manual 2025
| Tema | Cap. |
|---|---|
| Cuestiones generales, plazos, obligados | 01 |
| Identificación, tipo de declaración, autoliquidación | 02 |
| Administradores; participaciones (B.1 participadas / B.2 socios) | 03 |
| Estados contables (balance, PyG, ECPN; casillas contables) | 04 |
| **Base imponible**: ajustes, amortizaciones, deterioros, provisiones, BINs, reserva de capitalización/nivelación, exención art. 21 | 05 |
| **Deuda tributaria**: tipo, cuota, bonificaciones, deducciones (doble imposición, I+D+i, donativos) | 06 |
| Consolidación fiscal / grupos (y art. 16 a nivel grupo) | 07 |
| Operaciones vinculadas | 08 |
| Regímenes especiales (I / II) | 09 / 10 |
| Cooperativas | 11 |
| Canarias (RIC, ZEC, DIC) | 12 |
| Illes Balears | 13 |
| Tributación conjunta / Forales | 14 |
| Pago fraccionado (Modelos 202/222) | 15 |
| IRNR | 16 |
| Anexos, apéndice, glosario | 17 |

Rutas (plugin instalado):
- Manual: `${CLAUDE_PLUGIN_ROOT}/engine/suite-is/Manual_Sociedades_2025_md/` (empieza por `00_INDICE.md`).
- Mapeo PGC→casilla: `${CLAUDE_PLUGIN_ROOT}/skills/ccaa-a-sys-a3/reference/pgc_mapeado.md`.
