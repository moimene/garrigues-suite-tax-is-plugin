---
name: gestion-errores-is
description: >-
  Ayuda al abogado a resolver ERRORES y avisos al preparar o importar el Modelo 200 (Impuesto sobre Sociedades)
  con Suite Tax IS. Cubre: mensajes del MOTOR (Fase A «No se detectó la cabecera», «No se pudo proyectar el SyS»,
  descuadre «TOTAL ACTIVO ≠ TOTAL PN+PASIVO», «N cuentas sin mapear», fail-close sin_contabilidad/OCR/régimen),
  validación XSD del XML contable, y errores/avisos de importación en Sociedades WEB (00001, EMALP311 estados,
  EMALR31-34 socios B.2, casillas dependientes de otros modelos). ÚSALA cuando el usuario pegue un error o aviso,
  o diga «no me importa el .200», «da error», «XSD inválido», «no cuadra», «sin mapear», «EMAL…», «no detecta la
  cabecera», o pregunte qué significa un mensaje y cómo arreglarlo. Si la duda es de CRITERIO fiscal (a qué
  casilla va un ajuste, una deducción, un régimen), pásalo a la skill `analisis-respuestas-is` (consulta +
  análisis sobre el Manual de Sociedades 2025 empaquetado).
metadata:
  version: "1.3.0"
---

# Gestión de errores — Modelo 200 (Suite Tax IS)

Cuando el abogado reporte un error o aviso: **identifícalo, explica la causa en una frase y da la acción
concreta.** No inventes. Si es mecánico → acción directa; si es criterio fiscal → abre el Manual (§4).
**PII:** no reproduzcas NIF/razón social/importes; usa codename.

Memoria canónica de errores reales:

```
docs/memoria/2026-07-02-registro-errores-openweb-modelo200.md
```

Cuando el usuario pegue errores OpenWeb, consulta ese registro antes de improvisar. Si el error no existe,
clasifícalo como hallazgo nuevo y devuelve un handoff corto para el hilo de motor.

## 1. Errores del MOTOR (antes de generar el `.200`)
| Mensaje | Causa | Acción |
|---|---|---|
| `No se detectó la cabecera (Cuenta / Descripción)` | El Sumas y Saldos no tiene una cabecera reconocible. Típico: TB de ERP en otro idioma o con cabecera desplazada/columnas atípicas. | El motor reconoce ES **y EN** (Account/Description/Actual Debit/Credit/YTD). Si aún falla: comprobar que la **hoja correcta** tenga una fila con columna de cuenta + descripción; re-guardar con cabecera estándar (Cuenta·Descripción·Debe·Haber·Saldo Final). |
| `No se pudo proyectar el SyS (pipeline: error)` | El Excel no es el balance esperado (p. ej. **libro multipestaña** cuya 1ª hoja no es el TB). | Aportar el fichero de **Sumas y Saldos** (una hoja con Cuenta/Descripción/Saldo), no un libro de trabajo con varias pestañas. |
| `TOTAL ACTIVO (…) ≠ TOTAL PN+PASIVO (…)` | La **proyección AEAT** no cuadra; casi siempre por cuentas sin mapear o por signo. | Resolver primero las cuentas sin mapear (fila siguiente) y revisar signos del TB. |
| `N cuenta(s) sin mapear` / `no identificada` | El plan puede no ser PGC (plan de grupo). El motor ya mapea por **código + descripción + inferencia** (v1.9.0); lo que queda suelen ser **cuentas-plug** («Not Applicable», «9999», «varios», «regularización») **con saldo**, que no se pueden inferir. | El abogado clasifica esas cuentas-plug (a qué cuenta/casilla real va su saldo); sin eso el balance no cuadra. Las marcadas **«inferida»** se revisan **tras importar** (Manual §4 si hay duda de casilla). |
| fail-close `sin_contabilidad` | No hay contable validada (Fase A no apta). | Arreglar Fase A primero (las filas de arriba). |
| fail-close OCR pendiente / régimen sin confirmar / HITL | El paso 2 tiene confirmaciones pendientes. | Completar el paso 2 y reintentar. **No** forzar. |

## 2. Validación XSD del XML contable
`valido_xsd = False` → el XML de datos contables no valida contra el XSD oficial. Pide el **detalle**
(elemento/casilla) y revísalo: suele ser un valor fuera de rango/formato o una casilla mal proyectada, que se
corrige en la **cuenta/mapeo de origen**, no a mano en el XML. (El XSD 2025 es provisional.)

## 3. Importación en Sociedades WEB
| Código | Significa | Acción |
|---|---|---|
| `00001 — No existen errores` | Importado. | Completar la liquidación en Sociedades WEB (recalcula) y cerrar. |
| `ECRLF` + `EMALREG` | OpenWeb no recibió un registro plano válido. Casi siempre es fichero equivocado/intermedio o `.200` con saltos de línea. | No diagnosticar fiscalidad. Verificar `LF=0`, `CR=0`, cabecera/cierre y subir solo `00_IMPORTAR_OPENWEB_*.200`. |
| `EMALNI1` / `EMALNO1` | NIF y/o razón social del **declarante** vacíos en el `.200`. | Aportar el `.200` del año anterior o los datos fiscales (la precarga los rellena, v1.8.0+) o indicar NIF + razón; re-generar. Los «NIF» que pueda llevar el fichero son de **socios** (B.2), no el principal. |
| `EMALP311` | Modelo de estados de cuentas no cumplimentado. | Indicar modelo **normal/abreviado/pymes** en el paso 2 (el plugin lo inyecta). |
| `EMALR31`–`EMALR34` | Socios (apartado B.2) incompletos. | Faltan **NIF + % de participación**; aportar fuente completa (`.200` previo / datos fiscales) o completar; no emitir registros parciales. |
| `16053` / `E254001xx` / `E254002xx` en balance | El perfil de estados contables no coincide con las casillas emitidas o hay subtotales normales en un modelo abreviado/PYMES. | Confirmar el modelo de cuentas al inicio del expediente. Regenerar con el perfil correcto; no parchear totales a mano. |
| `E25400705` | PyG abreviado/PYMES con casilla normal-only `00705` emitida. | Regenerar con motor que pliega `00705/00706/00707/00708` en `00255`; no tocar bytes. |
| `E25400632` / `E25400645` / ECPN | ECPN incoherente con balance N/N-1 o emitido cuando no procede. | En modelo normal, aportar apertura N-1 desde SyS/CCAA/`.200` N-1. En abreviado/PYMES, omitir ECPN salvo decisión expresa. |
| `15525` | Declaración con tributación conjunta foral (`00028`) sin página 26. | Aportar reparto territorial 2025 o usar proxy N-1 de importabilidad marcado como HITL; no emitir liquidación estatal pura. |
| `E25400599` / `E25400611` / `E25401586` / `E25400621` con foral | Liquidación solo-Estado o DID incompatible con reparto foral. | No copiar liquidación N-1. Generar página 26 y reparto 2025; marcar revisión humana fiscal. |
| `E25402369` / casillas página 20 | Límite de gastos financieros recalculado por OpenWeb distinto del importado. | Regenerar con regla de página 20 del motor; no poner `02369=0` si aplica suelo de 1.000.000. |
| `0200900` / `0200910` / `0200920` (`01501`-`01503`) | Totales B.1 de participadas rechazados. | Si B.1 es compleja o con continuaciones, no emitirla en el `.200`; entregar `b1_participadas_post_import.json`. |
| `Caracteres no válidos 'Casilla ...'` | Suele ser valor en casilla calculada/no aplicable o formato físico incompatible para esa página/modelo. | Revisar contra DR y perfil de estados; si la casilla es calculada o no aplicable, debe salir del emisor correcto, no editarse en bytes. |
| Casillas dependientes de otros modelos (retenciones, pagos a cuenta…) | Van a **cero**. | Completar desde su modelo de origen («Pendiente AEAT» en el manifiesto). |

## 4. Criterio fiscal → skill `analisis-respuestas-is`
Si la duda **no es un error mecánico** sino de **criterio fiscal** (a qué casilla va un ajuste/deducción, un
régimen especial, una operación vinculada, por qué sale una cifra, qué ajustes faltan), **pásalo a la skill
`analisis-respuestas-is`**: responde citando el Manual 2025 y, si hay liquidación, la explica/audita. Ambas
skills comparten el **mismo** Manual empaquetado en:

```
${CLAUDE_PLUGIN_ROOT}/engine/suite-is/Manual_Sociedades_2025_md/
```

Empieza por **`00_INDICE.md`** y abre **solo** el capítulo relevante (p. ej. `04_Cap04_Estados_contables…`,
`05_Cap05_Base_imponible`, `06_Cap06_Deuda_tributaria`, `08_Cap08_Operaciones_vinculadas`, `09/10` regímenes
especiales). **Cita el capítulo**; no vuelques el Manual entero (lectura on-demand).

## Reglas
- Causa → acción, en breve. Mecánico = acción directa; criterio fiscal = Manual citado.
- **PII local:** codename; nunca NIF/razón/importes fuera del expediente.
- Error nuevo no listado: pide **código + texto literal**, mapéalo a una acción y, si es del motor, escálalo
  como mejora del plugin para todo el equipo.
