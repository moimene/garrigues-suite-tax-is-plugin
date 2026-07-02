# Version Matrix — Suite Tax IS

Esta matriz fija la compatibilidad operativa entre el plugin thin y el motor que firma el numero.

| Plugin | Motor minimo | Fecha | Notas |
| --- | --- | --- | --- |
| 1.18.3 | 1.18.3 | 2026-07-02 | Guardrail obligatorio de version (`/salud` + `/version`) en skills/scripts. Evita ejecutar motores antiguos en Cowork/Windows. Refuerzo abreviado/PYMES para no emitir partidas normal-only como `00705`. |
| 1.18.2 | 1.18.2 | 2026-07-01 | SUN/OpenWeb: B.1 simple se emite; B.1 complejo con continuaciones queda como `b1_participadas_post_import.json`. Datos fiscales AEAT, secretario/titulares reales, foral página 26 y validador reforzados. |
| 1.18.1 | 1.18.1 | 2026-07-01 | Precarga N-1 formal completa: administradores, B.2 con complementarias, titulares reales adicionales y `00027` no arrastrado. B.1 simple se emite; B.1 con continuaciones queda como post-import local. |
| 1.18.0 | 1.18.0 | 2026-07-01 | Importabilidad consolidada: normal/abreviado/PYMES, ECPN, pagina 20 GF, proxy foral, SOCIMI y datos fiscales como intake HITL. |

## Politica

- El plugin de Garrigues es **thin**: no contiene motor, Manual, expedientes, PDFs, Excels, `.200` ni salidas con PII.
- El motor se distribuye aparte: servicio Windows Enterprise, URL interna Garrigues, bundle portable Windows/macOS o
  `engine-slim` verificado para Cowork/Linux.
- Antes de usar `/is-nueva`, comprueba que el motor instalado corresponde a la version funcional indicada para el plugin.
- Desde `1.18.3`, las skills y scripts fallan cerrado si `/version` es inferior al minimo de esta matriz.
