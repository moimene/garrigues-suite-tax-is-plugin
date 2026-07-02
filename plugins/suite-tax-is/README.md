# Suite Tax IS — Guia de usuario

Plugin thin para preparar declaraciones del Impuesto sobre Sociedades con Suite Tax IS.

El plugin no calcula por si solo. Orquesta el proceso y llama al motor fiscal Python, que genera la base de
importacion AEAT: `.200` DR200 + XML mod200. El motor debe estar arrancado en local o en infraestructura interna.

## Version

- Plugin: `1.18.3`
- Motor minimo: `1.18.3`
- Cambio clave: las skills verifican `/salud` y `/version` antes de generar declaraciones. Si el motor es antiguo
  (por ejemplo un servicio Cowork/Windows no actualizado), el flujo aborta antes de producir `.200`. Se conserva la
  consolidacion SUN/OpenWeb, B.1 selectivo, datos fiscales AEAT, secretario/titulares reales y pagina 26 foral.

## Requisitos antes de empezar

1. Plugin instalado en Claude/Cowork o Codex.
2. Motor disponible en `http://127.0.0.1:8000` o `SUITE_IS_ENGINE_URL`.
3. Expediente en carpeta local, con datos reales fuera de git.
4. Si existe, `.200` del ejercicio anterior para precargar configuracion formal.
5. Validacion final en Sociedades WEB/OpenWeb.

## Instalacion

### Claude/Cowork

```text
/plugin marketplace add https://github.com/moimene/garrigues-suite-tax-is-plugin
/plugin install suite-tax-is@garrigues-suite-fiscal
```

### Codex

El mismo repo incluye soporte Codex:

```text
.agents/plugins/marketplace.json
plugins/suite-tax-is/.codex-plugin/plugin.json
```

## Arrancar o comprobar el motor

Comprueba salud y version:

```text
http://127.0.0.1:8000/salud
http://127.0.0.1:8000/version
```

Debe responder `ok:true` y `version >= 1.18.3` salvo que IT configure otro umbral en
`SUITE_IS_MIN_ENGINE_VERSION`.

Opciones:

- **Servicio Windows Enterprise:** gestionado por IT.
- **URL interna:** variable `SUITE_IS_ENGINE_URL`.
- **Portable Windows:** descargar de `downloads/motor/win64/`, descomprimir y ejecutar:

```powershell
.\scripts\start-suite-tax-is.ps1
```

No uses motores demo o cloud con datos reales.

## Flujo de una declaracion

Para abrir una conversacion nueva de fabrica, usa el prompt versionado:
`prompts/activar-fabrica-declaraciones-v1.18.3.md`.

1. Crear o localizar la carpeta del expediente.
2. Incluir contabilidad, estados contables, `.200` N-1, datos fiscales y anexos disponibles.
3. Ejecutar `/is-nueva` con la ruta del expediente.
4. Revisar el intake: modelo de cuentas, N-1, CNAE, administradores, participadas B.1 post-import, socios, titulares reales,
   datos fiscales, foralidad, regimenes especiales y anexos.
5. Generar `.200` + XML.
6. Leer el manifiesto de salida.
7. Importar el `.200` en Sociedades WEB/OpenWeb.
8. Si OpenWeb devuelve errores, iterar con `gestion-errores-is` e `is200-importabilidad-hitl`.

## Flujo de lote

Usa `/suite-is-export-aeat` sobre una carpeta con varias sociedades. El resultado queda en salidas locales por
sociedad, con informe de excepciones.

## Skills principales

- `descubrir-expediente`: inventario e intake fiscal-contable previo.
- `ccaa-a-sys-a3`: normalizacion de estados contables a SyS parseable.
- `suite-is-export-aeat`: generacion `.200` + XML desde expediente.
- `is200-importabilidad-hitl`: diagnostico e iteracion de errores de importacion.
- `gestion-errores-is`: clasificacion de errores OpenWeb y propuesta de correccion.
- `arrancar-motor`: comprobacion del motor local/interno.
- `suite-is-motor`: referencia operativa del motor fiscal.

## Comandos

- `/is-nueva`: preparar una declaracion individual por carpeta.
- `/suite-is-export-aeat`: generar en lote.
- `/suite-is-salud`: comprobar disponibilidad del motor.

## Reglas de seguridad

- No subir expedientes, PDFs, Excels, `.200` ni salidas reales a git.
- El motor firma el numero; no se inventan casillas fuera del motor.
- El `.200` generado es provisional hasta importacion real en Sociedades WEB/OpenWeb.
- La informacion fiscal aportada por el usuario debe conservarse en la carpeta del expediente y reflejarse en
  el manifiesto.
