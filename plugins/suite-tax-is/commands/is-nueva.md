---
description: Arranca una nueva declaración del Impuesto sobre Sociedades (Modelo 200) en modo stepper contra la carpeta del expediente, sobre el motor local (ADR-001).
---

Arranca el **stepper del Impuesto sobre Sociedades** para UN expediente, contra su **carpeta**, consumiendo el
**motor local** (`engine_service`, ADR-001). Delega la conducción en el agente **`is-stepper-orquestador`**.

Pasos de arranque:
1. **Motor valido:** `curl -s http://127.0.0.1:8000/salud` y `curl -s http://127.0.0.1:8000/version`.
   Exige `ok:true` y `version >= 1.18.3` (o `SUITE_IS_MIN_ENGINE_VERSION`). En Garrigues Windows Enterprise,
   si no responde o la version es antigua, ejecuta la skill `suite-tax-is:arrancar-motor` para diagnosticar:
   debe existir un servicio Windows local o una `SUITE_IS_ENGINE_URL` interna actualizada. No uses `make dev` ni
   intentes instalar el motor dentro del plugin thin. Si falta el servicio o esta desfasado, para y pide
   arranque/actualizacion IT.
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

**Muchas declaraciones a la vez:** no saltes directamente a lote salvo grupo homogeneo o patron ya probado.
Primero procesa en individual la sociedad mas compleja/representativa del grupo; si pasa OpenWeb o solo devuelve
errores conocidos, usa `suite-is-export-aeat` para el resto. En grupos con foralidad, SOCIMI, B.1/B.2 relevante,
ECPN sensible, perfil abreviado dudoso o anexos pesados, mantén el carril individual.
