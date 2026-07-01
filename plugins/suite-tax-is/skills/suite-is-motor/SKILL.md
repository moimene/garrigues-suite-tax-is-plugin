---
name: suite-is-motor
description: >-
  Referencia operativa del motor fiscal Python canónico de Suite Tax IS (ADR-001). Úsala para comprobar salud,
  entender endpoints, reglas firmadas, cadena de liquidación del Modelo 200, perfiles contables
  normal/abreviado/PYMES, ECPN, gastos financieros, tributación foral, SOCIMI, precarga N-1, datos fiscales y
  validación de importabilidad. El motor firma el número; el plugin solo lo orquesta.
metadata:
  version: "1.18.1"
---

# Suite IS — motor fiscal

El motor fiscal Python es la fuente canónica de cálculo y emisión. El plugin no calcula casillas por su cuenta:
prepara el expediente, llama al motor, muestra el manifiesto y ayuda a iterar errores de importación.

## Release 1.18.1

- Perfiles contables `normal`, `abreviado` y `pymes`.
- ECPN coherente con saldos de balance N/N-1 cuando procede.
- Página 20 de gastos financieros y casillas calculadas por OpenWeb.
- Tributación foral con página 26 obligatoria y proxy N-1 marcado como revisión humana.
- SOCIMI con cuota 0 del Modelo 200 cuando procede.
- Precarga N-1 formal completa: administradores, B.1/B.2 con complementarias, titulares reales adicionales.
- Carácter `00027` no arrastrado por depender del resultado fiscal del ejercicio.
- Datos fiscales AEAT como intake HITL.

Sociedades WEB/OpenWeb sigue siendo el gate final de importabilidad.

## Salud

Motor local esperado:

```text
http://127.0.0.1:8000/salud
```

En Windows Enterprise puede existir una URL interna en `SUITE_IS_ENGINE_URL`. No uses motores demo con datos
reales.

## Endpoints habituales

- `/salud`: disponibilidad del servicio.
- `/precarga-anterior`: lectura de `.200` N-1 y datos formales recurrentes.
- `/resolver-contable` / `/fase-a-sys`: normalización contable.
- `/liquidar-orquestado`: liquidación firmada.
- `/expediente/export-base`: emisión `.200` + XML desde expediente.
- `/exportar-aeat`: exportación directa/lote desde contabilidad.

Verifica la firma exacta en el motor instalado cuando integres automatizaciones.

## Cadena de liquidación

Cadena principal del Modelo 200:

```text
00500 -> 00501 -> 00550 -> 00552 -> 01330 -> 00562 -> 00582 -> 00592 -> 00599 -> 00611 -> 01586 -> 00621
```

Reglas destacadas:

- `00550 = 00501 + 00417 - 00418`.
- BINs: límite art. 26 LIS / DA 15ª, con mínimo general de 1.000.000 euros si aplica.
- El motor redondea al céntimo con criterio fiscal configurado.
- Si el motor y una estimación manual discrepan, manda el motor y se abre incidencia.

## Importabilidad

El validador interno reduce iteraciones, pero no sustituye la importación real.

Familias cubiertas:

- Identificativos y caracteres de página 1.
- Modelo de estados contables.
- Balance/PyG/ECPN.
- Página 20 de gastos financieros.
- Tributación foral y página 26.
- SOCIMI.
- DID y cascada de liquidación.
- Errores OpenWeb pegados por el usuario.

## Seguridad

- PII solo en carpeta local/interna.
- No subir expedientes, PDFs, Excels, `.200` ni salidas reales al repo.
- No rellenar ceros para esquivar gates.
- No tocar casillas calculadas por OpenWeb salvo regla explícita del motor.

## Comprobaciones de desarrollo

En el monorepo del motor, antes de publicar una versión:

```bash
make test
python3 -m pytest engine_service/tests -q
python3 -m pytest Extractor-parseador/tests -q
git diff --check
```
