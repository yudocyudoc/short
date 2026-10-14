# C4 — Constructor SD con verificación y una revisión acotada

**Diseño registrado antes de inferencia:** 2026-10-13. **Estado inicial:** pendiente de prueba.

## Hipótesis acotada

¿Un LLM que propuso un grafo de stocks/transiciones inconsistente puede producir una versión estructuralmente válida después de recibir **una sola devolución tipada de errores**, sin recibir las respuestas numéricas correctas?

C4 **no** compara dos modelos independientes. Usa un mismo GLM-4.7-Flash: propuesta inicial → verificador → como máximo una revisión. Se reportan ambos estados por separado, sin convertir la revisión en desempeño inicial del modelo.

## Controles

- [Escenario](scenario.md), [contrato JSON](prompts/contract.md), [instrucciones de construcción](prompts/build.md), [instrucciones de revisión](prompts/revise.md).
- [Hechos estructurados](evaluation/facts.json): se emplean **solamente en el verificador**, nunca se suministran al LLM.
- [Protocolo y rúbrica](evaluation/protocol.md): congelados antes de obtener respuestas.
- `scripts/c4_validator.py`: diez puertas con balances independientes y sin modificar jamás las salidas.
- `scripts/run_c4_cloudflare.py`: máximo dos inferencias y ahorro controlado.
- `tests/test_c4_validator.py`: casos de control antes de gastar tokens.

## Decisiones predefinidas

Se acepta JSON puro o **exactamente un envoltorio** de triple fence Markdown con idioma `json` opcional. El original queda sin tocar; la normalización de transporte sólo retira esos fences y se registra. No se recuperan objetos desde texto libre.

Si la primera salida falla, se envían a GLM solamente códigos de errores y explicaciones generales del verificador, junto con **su salida inicial sin modificar** y el escenario/contrato. Ni la clave ni las cantidades esperadas se revelan.

Si la revisión pasa las diez puertas, se registra `ACCEPT_AFTER_REPAIR` (no `FIRST_PASS`). En caso contrario, `REJECT`. Nada se repara por código.

**Límite de validez:** prueba sintética de consistencia con evidencia suministrada, no inferencia causal sobre cafeterías reales. El validador conoce parte importante del modelo esperado, por diseño. No confundir validez con descubrimiento autónomo.
