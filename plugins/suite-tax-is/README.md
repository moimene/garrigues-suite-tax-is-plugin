# Suite Tax IS — plugin

Copiloto de la **campaña del Impuesto sobre Sociedades** (Modelos 200/202/222) de Garrigues. Empaqueta la
superficie de skills y comandos que operan el **motor fiscal Python canónico** (ADR-001), que es quien firma
el número y genera la base de importación AEAT: `.200` DR200 + XML mod200 validado contra XSD.

La versión del plugin (**1.18.1**, 2026-07-01) consolida el motor tras las iteraciones reales de OpenWeb:
perfiles de estados contables **normal / abreviado / PYMES**, ECPN coherente, página 20 de gastos financieros,
precarga N-1 exhaustiva, lectura de Balance/PyG formulado, proxy de importabilidad foral desde N-1,
SOCIMI, validación de importabilidad y datos fiscales AEAT como bloque de intake HITL. Para Garrigues Windows,
el paquete recomendado es **thin**: excluye expedientes reales, salidas, PDFs, Excels, `.200`, zips con posible
PII y no incluye el motor Python embebido.

La `1.18.1` incorpora el fix de precarga formal N-1 completo: administradores, participadas B.1, socios B.2,
titulares reales y registros complementarios; además no arrastra el carácter `00027` porque depende del
resultado fiscal de 2025.

Esta release no sustituye el gate real: Sociedades WEB/OpenWeb sigue siendo la verdad final de importabilidad.
Los datos fiscales en PDF imagen quedan marcados como `requiere_vision/OCR`; el OCR se opera como fase de
intake, no como dependencia obligatoria del motor congelado.

## Qué incluye

**Skills (conocimiento que Claude carga bajo demanda):**

- `harvey-sociedades` — manual operativo para preparar el Modelo 200 dentro de Harvey: patrón
  expediente = 1 Space + 2 Vaults, correr/editar WF-1 y WF-2, el handoff por bloque parseable, el
  gating, los 2 checkpoints humanos y los entregables como TEXTO sobre plantillas Garrigues.
- `harvey-architect` — arquitecto genérico de Harvey (Spaces, Vaults, Workflow Agents, Playbooks) para
  cualquier dominio: patrones de diseño, tipos de paso y mecánica probada de operación por navegador.
- `suite-is-motor` — el cerebro fiscal canónico: endpoints del `engine_service`, el puente Python, el
  oráculo de no-regresión GIP 2024/2025 y el contrato del bloque parseable. Es la vía del taller y el
  doble-check del número por servicio.
- `descubrir-expediente` — Fase 0 de intake por carpeta: inventario, dossier por bloques, N-1, modelo de
  cuentas, grupo fiscal/mercantil, administradores, B.1/B.2, titular real, apertura ECPN y **datos fiscales
  AEAT 2025** con clasificación de pagos, retenciones, arrastres, ajustes HITL y gestión.
- `suite-is-export-aeat` — genera la **base de importación a la AEAT** (`.200` BOE conforme al
  **DR200** + **XML mod200** validado contra XSD) desde SyS, Balance/PyG formulado o carpeta de expediente,
  1 a 1 o en **lote**. Consume `/exportar-aeat` (ADR-001); el motor firma el número (fail-closed); corre en
  local por la PII; el `.200` es provisional hasta la importación real en Sociedades WEB.

**Comandos (acciones que el abogado dispara con `/`):**

- `/harvey-nueva-declaracion` — monta el Space + Vaults del expediente y arranca WF-1.
- `/harvey-sanity-gip` — corre el sanity de no-regresión y compara contra las cifras-ancla GIP.
- `/harvey-publicar-wf` — mecánica de publicación de un workflow (con OK humano explícito).
- `/suite-is-salud` — comprueba la salud del motor en producción (`/salud`).
- `/suite-is-export-aeat` — genera la base de importación AEAT (`.200` BOE + XML) de una carpeta de
  sociedades y resume el informe de excepciones.

**Sub-agente:**

- `campana-is-orquestador` — corre una declaración de punta a punta (WF-1 → pausa cliente → WF-2),
  respetando los 2 checkpoints humanos, el gating y los guardarraíles (los ficheros los sube el abogado;
  publicar/borrar requiere OK del usuario).

## Requisitos

- **Claude/Cowork en entorno Garrigues Windows**.
- **Motor Suite Tax IS** disponible de una de estas formas:
  - recomendado: servicio Windows local en `http://127.0.0.1:8000`;
  - alternativa IT: URL interna Garrigues configurada como `SUITE_IS_ENGINE_URL`.
- El motor demo cloud no debe usarse con datos reales.

## Reglas duras (heredadas del proyecto)

1. **Confidencialidad.** NIF, razón social, contabilidad e importes del cliente viven solo en el
   Vault/Space del expediente — nunca en git, ni en los nombres/descr. de workflows. Este plugin
   contiene **0 PII** (solo cifras-ancla agregadas del oráculo, ya públicas en `PROGRESO.md`).
2. **El motor Python firma el número** (ADR-001/ADR-002): no se reescribe lógica fiscal en otra parte.
3. **Lo irreversible lo ejecuta el usuario:** publicar o borrar workflows requiere OK explícito.
4. **GIP 2024/2025 = no-regresión:** las cifras-ancla no cambian sin tests verdes.

## Instalación

- **Directa:** instala el fichero `suite-tax-is.plugin` o `suite-tax-is-thin-v1.18.1.plugin` desde Cowork
  (botón "Save plugin" del preview).
- **Por marketplace interno:** añade el marketplace Garrigues (`marketplace-garrigues/`) y selecciona
  el plugin `suite-tax-is` desde él.
- **Windows Enterprise:** antes de ejecutar `/is-nueva`, IT debe haber arrancado el motor local o configurado
  `SUITE_IS_ENGINE_URL`. El self-contained Linux/aarch64 no es el paquete operativo de Garrigues Windows.
- **No-enterprise/autocontenido:** usar un bundle portable Windows separado
  (`suite-tax-is-portable-win64-v1.18.1.zip`, pendiente de build) con plugin thin + motor + runtime Python +
  scripts PowerShell. El `.plugin` sigue siendo thin; el motor portable corre en `127.0.0.1:8000`.

Consulta `VERSION_MATRIX.md` antes de instalar: el plugin thin y el motor Windows/portable deben ir alineados
en la misma release funcional.

## Origen y trazabilidad

Construido a partir del repo `is200transmittalApp`. Estado y cifras verificables en
`harvey-suiteis-live-findings.md`, `PROGRESO.md`, `DECISIONES.md` (D1–D18) y `docs/memoria/INDEX.md`.
Para re-empaquetar tras editar las skills canónicas (`.claude/skills/harvey-*`): `bash build-plugin.sh`
(en la raíz del repo) — re-sincroniza las skills en el plugin y genera `dist/suite-tax-is.plugin` +
`dist/suite-tax-is-thin-v<version>.plugin`, con guardrail anti-PII.
