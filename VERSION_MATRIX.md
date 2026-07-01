# Version Matrix — Suite Tax IS

Esta matriz fija la compatibilidad operativa entre el plugin thin y el motor que firma el numero.

| Plugin | Motor minimo | Fecha | Notas |
| --- | --- | --- | --- |
| 1.18.1 | 1.18.1 | 2026-07-01 | Precarga N-1 formal completa: administradores, B.1/B.2 con complementarias, titulares reales adicionales y `00027` no arrastrado. |
| 1.18.0 | 1.18.0 | 2026-07-01 | Importabilidad consolidada: normal/abreviado/PYMES, ECPN, pagina 20 GF, proxy foral, SOCIMI y datos fiscales como intake HITL. |

## Politica

- El plugin de Garrigues es **thin**: no contiene motor, Manual, expedientes, PDFs, Excels, `.200` ni salidas con PII.
- El motor se distribuye aparte: servicio Windows Enterprise, URL interna Garrigues o bundle portable Windows.
- Antes de usar `/is-nueva`, comprueba que el motor instalado corresponde a la version funcional indicada para el plugin.
- Mientras `/salud` no exponga la version semantica del motor, esta matriz es la fuente operativa de compatibilidad.
