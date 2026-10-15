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


## Analista IGC-0 v0.1 — prototipo preparado el 2026-10-14

Se construyó un paquete **público y reproducible**, separado de los motores de evaluación, y se entregó en los archivos de la conversación del proyecto:

- `IGC0_analista_minimo_v01.zip`: lector de las ocho observaciones públicas, verificación de SHA-256 en 336 filas POS y 112 cierres diarios, prompts para analista LLM, contratos tipados, validador de procedencia, grafo de ingeniería inicial, diagramas Mermaid derivables desde JSON y tests.
- `IGC0_SD_agregado_exploratorio_v01.zip`: **por separado**, primer motor SD agregado de dos horas, sus corridas contrafactuales de referencia y diagnósticos de reproducción de `open_full`. Sus números son **SIMULADO/no calibrado**, no un pronóstico válido de la operación virtual.
- `IGC0_oraculo_evaluador.zip`: sigue reservado al evaluador; **no se abrió durante este desarrollo**.

**Comprobaciones locales:** 9 tests PASS; 8/8 paquetes públicos con hashes correctos; 8 diagramas de ingeniería base. **0 consultas al LLM y 0 evaluaciones contra oráculo** realizadas para el nuevo analista.

Durante el desarrollo se detectó y corrigió un doble cargo de ingredientes en el motor SD agregado (al comprar y al consumir), y se añadió regresión contra ese fallo. Persisten desajustes de reproducción: por ejemplo caja final M01 error absoluto ~MXN 701.4 tras corrección; M06 ~MXN 46,384.4. Por tanto, **no aceptar decisiones contrafactuales de esta versión** y no incorporar sus simulaciones a los inputs del LLM ciego.

**Siguiente compuerta:** ejecutar un único caso público de IGC con un LLM externo, congelar respuesta JSON y fuentes, validar el grafo, contrastar frente a reglas de referencia y sólo luego verificar proyectabilidad con un SD agregado calibrado. El modelo no recibirá código del generador, decisiones ocultas ni el oráculo.

El código y los ocho paquetes públicos se incorporaron después al repositorio. El oráculo reservado permanece fuera. Los ZIP originales también siguen como adjuntos de conversación. Esta nota es el registro de estado y evita afirmar que GitHub contiene un ejecutor completo no comprometido.


## Código versionado y pruebas automáticas

- [Analista público y runner LLM](analyst/) (incluye ZIP público para ejecución reproducible).
- [Simulador discreto de prueba y generador](generator/) (sin configuraciones ni verdad oculta).
- [Ocho paquetes públicos](public/) accesibles individualmente.
- [Simulador SD agregado experimental](aggregate/) (**no calibrado**, sin decisiones automáticas).
- [Instrucciones reproducibles](docs/UPLOAD_NOTES.md).
- CI: `.github/workflows/igc0-public.yml` valida ambos módulos.

Las salidas de ingeniería se generan con código y **no se atribuyen al LLM**. No se incluyen los archivos del oráculo ni los resultados ocultos.
