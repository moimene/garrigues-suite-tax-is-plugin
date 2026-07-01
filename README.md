# Suite Tax IS Plugin Marketplace

Repositorio privado para distribuir el plugin thin `suite-tax-is` en Claude/Cowork.

Este repo **no instala el motor fiscal Python**. Solo distribuye el marketplace, skills, comandos, agentes y
scripts ligeros. El motor `1.18.1` debe desplegarse aparte como servicio Windows Enterprise, URL interna
Garrigues o portable local Windows.

## Contenido

- `plugins/suite-tax-is/`: plugin thin `1.18.1` con skills, comandos, agentes y scripts ligeros.
- `.claude-plugin/marketplace.json`: marketplace interno `garrigues-suite-fiscal`.
- `VERSION_MATRIX.md`: compatibilidad entre plugin y motor.

No contiene motor Python, Manual, expedientes reales, PDFs, Excels, ficheros `.200`, zips ni salidas con PII.

## Instalacion por el equipo

```text
/plugin marketplace add https://github.com/moimene/garrigues-suite-tax-is-plugin
/plugin install suite-tax-is@garrigues-suite-fiscal
```

Para datos reales, el motor debe estar arrancado aparte como servicio Windows Enterprise, URL interna Garrigues
o portable local Windows en `http://127.0.0.1:8000`.

## Actualizaciones

1. En el monorepo del motor, cerrar tests y generar el thin con `bash build-plugin.sh entregables-piloto`.
2. Sustituir `plugins/suite-tax-is/` por el contenido del `.plugin` thin validado.
3. Actualizar `.claude-plugin/marketplace.json`, `plugins/suite-tax-is/.claude-plugin/plugin.json` y
   `VERSION_MATRIX.md` a la misma release.
4. Ejecutar el guardrail anti-PII antes de publicar.
5. Commit, tag y push del repo privado.

## Release actual

- Plugin: `1.18.1`
- Motor minimo: `1.18.1`
- Cambio funcional: precarga N-1 formal completa de pagina 1/2, administradores, participadas B.1, socios B.2,
  titulares reales y registros complementarios; `00027` no se arrastra por depender de 2025.
