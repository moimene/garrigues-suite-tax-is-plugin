---
description: Arranca una nueva declaración del Impuesto sobre Sociedades (Modelo 200) en modo STEPPER contra la carpeta del expediente, sobre el motor local (ADR-001). Sin Harvey.
---

Arranca el **stepper del Impuesto sobre Sociedades** para UN expediente, contra su **carpeta**, consumiendo el
**motor local** (`engine_service`, ADR-001). Delega la conducción en el agente **`is-stepper-orquestador`**.

Pasos de arranque:
1. **Salud del motor:** `curl -s http://127.0.0.1:8000/salud` → espera `{"ok":true,...}`. En Garrigues Windows
   Enterprise, si no responde, ejecuta la skill `suite-tax-is:arrancar-motor` para diagnosticar: debe existir un
   servicio Windows local o una `SUITE_IS_ENGINE_URL` interna. No uses `make dev` ni intentes instalar el motor
   dentro del plugin thin. Si falta el servicio, para y pide arranque/configuración IT.
2. **Identidad del expediente** (de `$ARGUMENTS` o pregúntala): **codename** + ejercicio + ruta de la carpeta.
   El NIF/razón reales son **solo locales** (nunca en tu salida); usa el codename para nombrar todo.
3. **Estructura** (créala si no existe): `EXPEDIENTE_<codename>_<ejercicio>/{entrada,salida}/` + `estado.json`
   (`{"pasoActual":0}`). La carpeta es local y **gitignored**.
4. **Precarga N-1:** si en `entrada/` hay `.200` previo / justificante / datos fiscales, ejecuta
   `POST /precarga-anterior` y guárdala en `estado.json` como **"precargado, a confirmar"** (no firmado).
5. **Lanza el agente** `is-stepper-orquestador` para conducir los 6 pasos (Expediente · Contabilidad · ✋ Datos
   Modelo 200 · ✋ Revisión rápida · Exportar AEAT · Seguimiento), con sus 2 checkpoints humanos.

**Guardarraíles:** el motor **firma** el número (no inventas casillas) · paras en los checkpoints · fail-close
(no esquives un gate) · PII local (codename, carpeta gitignored) · push/PR y Supabase = humano.

**Muchas declaraciones a la vez:** usa la skill `suite-is-export-aeat` (lote por carpeta de sociedades).
