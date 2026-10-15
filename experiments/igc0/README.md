# IGC-0 — Piloto de ocho mundos (artefactos preparados externamente)

**Fecha:** 2026-10-14. **Estado:** generador, paquetes públicos y oráculo de ocho casos ya creados y validados localmente; **aún no están incorporados como archivos en esta rama**. El material íntegro se entregó como tres ZIP separados en la conversación de ChatGPT del proyecto.

## Pregunta

¿Puede un sistema IGC asistido por LLM identificar y graficar una estructura mínima SD, contrastar operación virtual con una referencia factible y examinar tres decisiones sobre abrir delivery con la cocina existente, sin convertir hipótesis en datos?

## Diseño implementado

- **8 mundos sintéticos, 14 días, tres ventanas intradía (valle/pico/valle).**
- **Mundo generador por eventos discretos, distinto de un eventual motor SD agregado:** pedidos individuales, cocina compartida, inventarios, despacho, cancelaciones, compras, caja y liquidación diferida.
- **Ocho paquetes de observación ciegos**, con 42 filas POS y 14 cierres diarios cada uno, unidades, IDs de fuente y SHA-256.
- **Controles:** casos sin desviación de mecanismo; pico de demanda; liquidación diferida; frontera omitida; despacho restringido; y dos mecanismos alternativos con evidencia pública idéntica pero distintas respuestas a intervención.
- **Decisiones:** no abrir; abrir todas las ventanas; abrir sólo valles con máximo 9 pedidos delivery aceptados por ventana.
- **Oráculo separado:** semillas, inyecciones, trazas ocultas y comparaciones contrafactuales; no dar acceso al analista antes de fijar respuestas.
- **15 pruebas automatizadas PASS:** 4 tests divulgables + 11 reservados, incluyendo conservación, repetibilidad, dos mundos nulos exactos y equivalencia observacional de dos mecanismos rivales.
- **Criterio financiero sintético:** minimización de pérdida con límites de servicio presencial, cancelaciones delivery y déficits de caja; cifras y umbrales son supuestos del piloto, no datos sectoriales.

## Precaución metodológica

Los ocho casos se ajustaron durante el desarrollo para ensayar los mecanismos buscados: **no son benchmark independiente ni preregistro confirmatorio**. No se han ejecutado inferencias LLM sobre ellos. El protocolo exige evaluar estructura, falsos positivos, abstención ante no identificabilidad, proyección por horizonte y utilidad decisional por separado. El siguiente trabajo es integrar los paquetes desde los ZIP al repositorio sin mezclar oráculo y observaciones y ejecutar un analista ciego sobre el paquete público.

## Integridad de los ZIP generados

- Paquete analista SHA-256: `b7c635aa3954cf4dd5f24cdc36274646cf28b18b9ac1a82fe5b19db523c0d934`
- Paquete motor/pruebas SHA-256: `2bce0a5bdcb84b6aa68541d19a4f23a9caeb1c26b4bc7457e9c94e986abe644f`
- Paquete reservado al evaluador SHA-256: `34bab2940469c0a9c3e5fcfec221b458fe786fe543fc14db5fdfddc5742a08d8`

**No poner públicamente el ZIP del oráculo ni el mapa de casos.** Los ZIP están adjuntos en la conversación, no en este commit.
