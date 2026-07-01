# Reglas de Importabilidad Modelo 200

## Fuentes

- DR fisico: `docs/info soporte/DR200e25_modelo_registro.json`.
- Parser/emisor: `Extractor-parseador/scripts/modelo200_parser.py` y `Extractor-parseador/scripts/dr200.py`.
- Autocontrol existente: `Extractor-parseador/scripts/autocontrol_200.py`.
- Manual 2025: `suite-is/Manual_Sociedades_2025_md/`.

## Capas

1. **DR fisico**: tags, longitudes, constantes, tipos, signos monetarios. Bloqueante.
2. **Campos obligatorios y grupos**: bloques parcialmente rellenos, páginas exigidas, páginas incompatibles. Bloqueante o HITL.
3. **No importables/calculadas**: casillas que Open recalcula o no permite importar con contenido. Bloqueante; correccion usual: dejar a cero/omitida y alimentar sus componentes.
4. **Rollups contables**: subtotales de balance/PyG/ECPN. Bloqueante si el importador recalcula distinto.
5. **Liquidacion de carga**: cadena cosmetica `00500 -> 00501 -> 00550 -> 00552 -> 01330 -> 00562 -> 00582 -> 00592 -> 00599 -> 00611 -> 01586 -> 00621 -> DID`. Bloqueante solo si rompe la importacion mecanica.
6. **Fiscal post-import**: consolidacion, cooperativas, Canarias, Illes Balears, forales, GF art. 16, deducciones/DDI, BINs y distribucion. `fase=post_import_fiscal`; no bloquea el pre-vuelo local.

## Gate de fase

- `fase=pre_import` + `bloquea_importacion=true`: resolver antes de subir a Sociedades WEB.
- `fase=post_import_fiscal`: listar como pendiente para despues del import positivo. No pedir criterio fiscal en Fase 1.
- Si un error real de Open se aporta en el texto pegado, se conserva como evidencia de rechazo de ese intento aunque la familia sea fiscal.

## Reglas habituales

### Identificativos y formales

Familias vistas en tandas reales:

- `196`: CNAE ausente. Tratar como aviso HITL; pedir CNAE validado, no inventarlo.
- `7011`: tramo INCN ausente o multiple. Debe quedar exactamente uno de los campos 102-104 de `DP200001`.
- `10034` / `21200`: matriz ultima incompleta o incoherente. Si `00082` esta marcado, completar `DP200001B` campos 9-13; si no aplica, desmarcar.
- `2830`: titular real incompleto. Completar el bloque de `DP200002B` o marcar exencion si procede.
- `153` / `154` / `155`: representantes parcialmente rellenos. Completar nombre, NIF, fecha de poder y notaria/otros, o vaciar el bloque.

Estas reglas son `hitl_requerido`: el motor puede localizar el hueco y preparar el parche, pero los datos deben venir del humano o de fuente documental.

### Estados contables y ECPN

- `16053`: `DP200004/00180` debe coincidir con `DP200006/00252`.
- `E25400632` / `E25400645`: contenido ECPN incompatible o no recalculado por el modelo de cuentas marcado en `DP200001B`.
- `11712`, `11716`, `209xx`: avisos de coherencia contable. No bloquear automaticamente si Open los presenta como aviso, pero dejarlos en cola HITL.

Correccion: recalcular desde componentes o confirmar modelo de balance/ECPN/PyG; no forzar solo el total.

### EMAL00501

`DP200012/00501 = 00500 + 00301 - 00302 + 00004`.

Fuente: Manual Cap. 5, formula `[00501] = [00500] + [00301] - [00302] + [00004]`.

Correccion: calcular `00501` desde pagina 12. Si `00301/00302` vienen de gasto/ingreso por impuesto, confirmar signo.

### EMALP13_2

`DP200014/00550 = DP200012/00501 + DP200013/00417 - DP200013/00418`, salvo regimenes que alteren la regla.

Correccion: recalcular cadena de liquidacion completa, no parchear solo `00550`.

### Correcciones de pagina 13 y liquidacion

Familia `E25400417`, `E25400418`, `E25400420`, `E25400426`, `E25400474`, `E25400476`, `E25400494`, `E25400496`.

Correccion: no importar totales aislados si Open los calcula; mover el importe a la casilla de detalle soportada por el DR y recalcular la cadena. Si el ajuste es gasto/ingreso por impuesto, revisar `00301/00302`.

### Cascada de liquidacion comun

Modo comun sin reservas, BINs, deducciones ni forales:

- `00552 = 00550 - 01032 - 00547`
- `01330 = 00552 + 01033 - 01034`
- `00558 = tipo aplicable` (generalmente 25; HITL si régimen especial)
- `00562 = max(0, 01330 * 00558 / 100)`
- `00582 = 00562` si no hay bonificaciones/deducciones previas
- `00592 = 00582` si no hay deducciones aplicadas
- `00599 = 00592 - retenciones`
- `00611 = 00599 - pagos fraccionados`
- `01586 = 00611 + incrementos/intereses/abonos`
- `00621 = 01586`
- `DP200DID 00552/00562/01586/00621` debe repetir la liquidacion.

Marcar como `post_import_fiscal` + `hitl_requerido` si hay reservas, BINs, deducciones, retenciones, pagos fraccionados, forales o regimen especial.

### E254 calculada/no puede tener contenido

Si el error real dice "La Casilla XXXXX no puede tener contenido", proponer borrar/poner cero esa casilla y revisar sus componentes.

No crear una regla global por casilla sin página: muchas casillas se reutilizan en páginas distintas.

### Rollups contables

Open recalcula subtotales desde componentes. Si `E254xxxxx` da "se ha calculado un valor", usar el valor calculado como evidencia, pero revisar si el error raíz es:

- subtotal importado a mano;
- componente en casilla no importable;
- signo contrario;
- página de estados contables incorrecta para el modelo de cuentas marcado.

### Participaciones B.2

Si una fila de `DP200002` B.2 tiene algún dato significativo, exigir el bloque completo: NIF, F/J/Otra, razon social, codigo provincia/pais, nominal y porcentaje. La marca RPTE no activa por sí sola el bloque.

### Gastos financieros art. 16

Reglas frecuentes:

- `01249 = 30% * beneficio operativo`.
- `02369 = max(max(0, 01249) + 01255, suelo 1.000.000 prorrateable)`.
- `01256 <= 02369`.
- `01248 = 01256 + 01257` si se emite.
- `01257 = 01248 - 01256`.
- `01260 = 01243 + 01257`.
- `01214/03585 = 01256`; `03587/01216 = 01257`.
- `00364 = 01258 + 01259`.
- Avisos de conciliacion: `00363` vs `01260`, `01250` vs `00296`, `01251` vs `00284`, `01253` vs `00287`.

Mantener como `post_import_fiscal` si depende de criterio de beneficio operativo, art. 16.5/83 LIS o arrastres.

### Tributacion conjunta foral

Reglas frecuentes:

- Si `DP200001/00028=1`, debe existir `DP200026`.
- Error `15525`: pagina 26 exigida por tributacion conjunta foral.
- Si hay importes o porcentajes forales (`00600`, `00602`, `00604`, `00606`, `00622`, `00626-00629`) sin `00028`, marcar incoherencia.
- `00625 + 00626 + 00627 + 00628 + 00629 = 100`.
- Los porcentajes deben derivar de volumenes `00050-00056`, aplicando redondeo del Manual.
- `00599 = (00625 / 100) * (00592 - 01766 - 01784)`.
- `00600 = ((00626 + 00627 + 00628 + 00629) / 100) * (00592 - 01766 - 01784)`.
- Los totales forales de `DP200014B` (`00602`, `00604`, `00606`, `00622`) deben cuadrar con `DP200026`.
- Familia `E25402301/02303/02306/02308/02310` y `EMALREGPAG26B`: revisar registros obligatorios y reparto territorial de pagina 26.

Mantener como `post_import_fiscal` si falta reparto territorial, normativa aplicable o pagina 26 confirmada por el abogado.

### Errores AEAT pegados

Al leer el texto pegado de Sociedades WEB/Open:

- conservar `Icono - Error` frente a `Icono - Aviso`;
- `FRECH` es rechazo global, no causa raiz;
- si `importado ~= calculado * 100`, clasificar como `unidades_x100` y normalizar a euros con dos decimales;
- si dice "no puede tener contenido", podar la casilla calculada/no importable y alimentar componentes;
- si Open aporta valor calculado, usarlo como evidencia pero revisar la formula local antes de parchear.

## Salida recomendada

Cada hallazgo debe incluir:

- `codigo`
- `severidad`
- `pagina`
- `casilla`
- `valor_200`
- `esperado_local` o `calculado_aeat`
- `fuente`
- `accion_propuesta`
- `modo`: `auto_seguro`, `hitl_requerido` o `no_local`
- `fase`: `pre_import` o `post_import_fiscal`
- `bloquea_importacion`: booleano usado por el gate local de Fase 1
