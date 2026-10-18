# X1-a — Corrida real original (2026-10-18)

**Run:** [GitHub Actions #39108593065](https://github.com/yudocyudoc/short/actions/runs/39108593065). [Informe de adjudicación sin filtros](https://github.com/yudocyudoc/short/actions/runs/39108593065/artifacts/12129337864) · [respuestas originales C al elegir](https://github.com/yudocyudoc/short/actions/runs/39108593065/artifacts/12129228366) · [respuestas originales C al decidir](https://github.com/yudocyudoc/short/actions/runs/39108593065/artifacts/12129627064).

**Estado real:** evaluación A/B y control integrado de presupuestos: **VALID**. Evaluación del brazo IA C: **NO EVALUABLE — PROVIDER ADAPTER FAILURE**, no derrota de Llama, aunque la primera tabla mecánica del juez lo cuente como abstención/costo. El PASS de CI sólo acredita que el pipeline llegó al final con los resultados disponibles; no acredita el resultado científico completo de X1.

## Lo que pasó

- OpenModelica generó las alternativas reales; el preflight confirmó que la inversión preferible difiere según qué cuello de botella limita la entrega.
- Se selló la identidad del mundo antes de las decisiones y se ejecutaron seis casos independientes con una asignación secreta de mecanismos, incluidos ambos tipos. Uno no permitía medición.
- A (auditoría simple): 5/6 inversiones óptimas, una abstención justificada, costo agregado de observación 4.0, arrepentimiento agregado frente al óptimo omnisciente 19.642042840903233.
- B (motor determinista con valor esperado de información): 5/6, una abstención justificada, costo agregado de observación 1.0, arrepentimiento agregado 16.642042840903226.
- C: 12 solicitudes HTTP hicieron `ValueError` sin obtener texto parseable en el archivo de resultados. La IA **no emitió decisiones medibles**. El juez contabilizó seis abstenciones por fallo de infraestructura y arrepentimiento 79.00854970472155; **esa cifra NO puede usarse como prueba de calidad de Llama**.

## Diagnóstico independiente, sin reejecutar los casos

Una petición de control ajena a los seis mundos [GitHub Actions #39108895235](https://github.com/yudocyudoc/short/actions/runs/39108895235) obtuvo HTTP 200, success true, result con `choices`, pero `response` NO era string. El cliente X1 original sólo utilizaba `result.response` y abandonaba. En IA-1 #35 sí existía fallback a `result.choices[0].message.content`. Se restableció esa adaptación, con test de regresión, sin modificar mundo, acciones, costos ni reglas de adjudicación.

La corrida X1-a **permanece inmutable**. Una siguiente corrida con nuevo mundo sellado se distingue como **X1-b**, no se presenta como el primer intento ni sustituye este fallo.

## Límite de inferencia

A y B comparan decisiones condicionales a dos mecanismos ya conocidos; no prueban descubrimiento estructural abierto. La predicción reservada es interna al mismo universo Modelica usado para generar contrafactuales. El caso sin acceso a medición muestra la abstención prevista, no capacidad de actuar bajo datos externos. Tampoco hay demostración de valor incremental de IA hasta que C pueda emitir salidas verificables.
