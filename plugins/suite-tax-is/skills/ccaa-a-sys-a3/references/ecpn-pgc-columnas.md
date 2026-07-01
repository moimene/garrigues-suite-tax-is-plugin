# ECPN del Modelo 200 (págs. 10000/11000) — reconstrucción desde el PGC y la CCAA

> Referencia canónica para que el SyS A3 alimente un ECPN que la AEAT acepte. **Regla de oro:** NO hay que
> rellenar a mano las ~140 casillas del ECPN; hay que dar al motor un SyS con **apertura (N-1) y cierre (N)
> correctos por cuenta de PN**, y `ecpn_sys` deriva las columnas y filas. La AEAT **recalcula** el ECPN desde el
> balance; si la apertura va a 0 o el PN va como movimiento/YTD (no saldo acumulado), rechaza con
> **E25400632 / E25400645** (FRECH). 0 PII.

## 1. Componentes de PN (columnas del ECPN) ← cuentas PGC

| Columna ECPN | Cuentas PGC |
|---|---|
| Capital escriturado | 100 |
| Capital no exigido (−) | 1030 / 1040 |
| Prima de emisión | 110 |
| Reservas | 112, 113, 114x, 115, 119 |
| Acciones y participaciones propias (−) | 108 / 109 |
| Resultados de ejercicios anteriores | 120, 121 |
| Otras aportaciones de socios | 118 |
| Resultado del ejercicio | 129 |
| Dividendo a cuenta (−) | 557 |
| Otros instrumentos de patrimonio | 111 |
| Ajustes por cambios de valor | 133, 134, 135, 136, 137 |
| Subvenciones, donaciones y legados | 130, 131, 132 |

## 2. Filas del ECPN (por año) y de dónde salen

- **Saldo final del ejercicio ANTERIOR** (apertura, casillas 00380–00393): saldo de **cierre N-1** de cada
  columna → **columna N-1 del Balance de la CCAA**. (00380 capital=100 N-1; 00382 prima=110 N-1; 00383
  reservas=Σ112..119 N-1; 00385 result. anteriores=120+121 N-1; 00387 resultado=129 N-1; 00388 dividendo=557 N-1;
  00390 ajustes=Σ133..137 N-1; 00392 subvenciones=Σ130..132 N-1; 00393 total).
- **Saldo ajustado, inicio del ejercicio** (00422–00435): apertura + ajustes por cambio de criterio (00394–00407)
  + ajustes por errores (00408–00421). **Sin ajustes → 00422..00435 = 00380..00393** (se copian).
- **Total ingresos y gastos reconocidos / Operaciones con socios / Otras variaciones**: descomposición de la
  variación del PN del ejercicio (PyG grupos 6/7 + cuentas de los grupos 8/9 imputadas a PN + movimientos con
  socios: 100/110/118/120/121/129/557/111 × 57x). Lo **deriva el motor** desde ΔPN (cierre − apertura) por
  columna; no se pican a mano.
- **Saldo final del ejercicio** (cierre, casillas 00632–00645): saldo de **cierre N** de cada columna → **columna
  N del Balance** (= el balance que ya emite el SyS). 00632 capital=100 N; 00634 prima=110 N; 00635 reservas N;
  00639 resultado=129 N; 00642 ajustes N; 00645 total. **Debe coincidir con el balance N** o la AEAT rechaza.

## 3. Qué debe cumplir el SyS A3 (y lo demás se deriva)

1. **Saldo Inicial ≠ 0** para toda cuenta de PN relevante (100, 110, 11x, 120/121, 129, 130–137, 118, 111, 557):
   = saldo de **cierre N-1** del Balance comparativo de la CCAA.
2. **Saldo Final = saldo acumulado N** del Balance para esas cuentas — **no** el YTD/movimiento del ERP (p. ej.
   un capital con YTD −12.264 NO es el saldo de capital; usa el nominal del balance).
3. Clasificación PGC correcta de PN + de los movimientos del ejercicio (PyG 6/7 + grupos 8/9 + operaciones con
   socios). Con eso, `ecpn_sys` rellena apertura/movimientos/cierre y el ECPN cuadra contra la AEAT.

## 4. Implementación en el motor (ya disponible, no hay que tocarla)

- `ecpn_sys.proyectar_desde_balance(comp_apertura, comp_cierre, resultado)` — proyecta el ECPN desde los
  componentes de PN (apertura N-1 + cierre N) reusando `_construir_paginas` (la misma matriz que importa limpia
  en TB PGC). Pliega dividendo a cuenta / resultados anteriores en `reservas` (el TOTAL de PN cuadra).
- `ecpn_sys.componentes_desde_ccaa_texto(texto)` — parsea el bloque de PN del Balance (columnas N y N-1).
- `engines.extraer_texto_ccaa(path)` — texto del Balance (soporta **PDF-portfolio** con la CCAA embebida).
- `engines.exportar_base(..., ecpn_ccaa_texto=…)` — **AUTO**: si el SyS no trae apertura y hay CCAA, toma la
  apertura de la columna N-1; si el SyS sí trae apertura (TB PGC), mantiene la proyección del canónico
  (GIP/ARIOSO byte-idénticos). Es la red de seguridad si el SyS inferido aún no trae el Saldo Inicial.

> **Doble vía (defensa en profundidad):** lo ideal es que la **inferencia** (esta skill) produzca el SyS con
> Saldo Inicial N-1 y PN acumulado; si aun así llega un SyS sin apertura, el **motor** la deriva de la CCAA.
> Probado contra REDEVCO RRE (2026-06-28): import «terminado con éxito» en Sociedades WEB Open.
