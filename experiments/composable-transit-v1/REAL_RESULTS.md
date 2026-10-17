# IGC — una molécula opcional, dos ensayos y Llama como crítico

**Fecha:** 2026-10-17. **Veredicto:** ejecución técnica satisfactoria; **3/4** revisiones admitidas bajo el linter original. No es validación empírica.

## Evidencia reproducible

- [PR #28](https://github.com/yudocyudoc/short/pull/28), borrador.
- [CI sin inferencias #39010993655](https://github.com/yudocyudoc/short/actions/runs/39010993655): 13 tests PASS, cuatro simulaciones Modelica PASS.
- [CI con Llama #39011077087](https://github.com/yudocyudoc/short/actions/runs/39011077087): 13 tests, cuatro solicitudes y respuestas originales, ejecución técnica PASS.
- [Artefacto completo #12091989426](https://github.com/yudocyudoc/short/actions/runs/39011077087/artifacts/12091989426): Modelica generado, grafos tipados, cuatro CSV OpenModelica, prompts, respuestas y score.

## Lo que hizo el motor (sin LLM)

Partiendo de la cadena de trabajo S2, el enumerador insertó opcionalmente una instancia de la molécula real `IGCMolecules.BoundedQueue` entre despacho y entrega. Se generaron y compilaron **dos grafos físicamente conectados de forma diferente**:

- **Direct:** SOURCE → PREPARATION → DISPATCH → DELIVERY.
- **Buffered:** SOURCE → PREPARATION → DISPATCH → TRANSIT → DELIVERY.

Todos los cálculos de niveles y tasas proceden de bloques ya existentes, no de ecuaciones escritas por Llama. El tipado acepta ambas alternativas.

OpenModelica, usando SystemDynamics 2.1.2 y MSL 4.0.0, produjo dos firmas cualitativas:

| Prueba | Direct | Buffered |
|---|---|---|
| Sin pedidos y sin stocks iniciales | STOPS | STOPS |
| Diferencia entre despachos y recepciones con pedidos variables | SYNC | LAG |

El motor seleccionó la segunda prueba porque separó las alternativas en **dos grupos**, mientras la primera sólo produjo uno. Los valores medidos del escenario sintético fueron: diferencia máxima entre tasas de despacho y entrega **0** (Direct) frente a **4.6735153885** (Buffered), y stock máximo en tránsito **0** frente a **11.5841946547** unidades. No se entregaron cifras al LLM.

## Cuatro respuestas originales del crítico

| Caso | Crítica de Llama | Linter original | Resultado operativo |
|---|---|---|---|
| C01: entrega posterior a transporte | LAG | Válido | Buffered |
| C02: entrega al retirar de ventanilla | SYNC | Válido | Direct |
| C03: sólo registro de despachos | UNKNOWN | Válido | Se conservan ambos |
| C04: manuales incompatibles | CONFLICT (F1/F2) | **Inválido** | Sin poda autorizada |

**Resultado operativo original: 3/4.** En C04, la respuesta raw sí reconocía el conflicto, citaba F1 y F2 y hacía una pregunta pertinente, pero tenía **250 caracteres** donde el linter permitía un máximo arbitrario de **240**. Su código fue `QUESTION_REQUIRED`. Leer las respuestas originales indica **4/4 elecciones semánticas coincidentes con el gold**, pero esto es una **auditoría posterior**, no un nuevo resultado estricto.

La corrección del límite de pregunta a 400 caracteres y la prueba de regresión se añadieron después de conocer el fallo. **No se solicitó una segunda inferencia ni se reetiquetó la ejecución original.**

## Qué demuestra y qué no

Sí: generación determinista de dos grafos distintos usando un módulo opcional; tipado; renderizado Modelica de enlaces alternativos; cuatro simulaciones reales; selección automática de ensayo discriminante; crítica LLM sin escribir ecuaciones; preservación cuando falta evidencia.

No: cientos de grafos, composición general de las moléculas originales de Hines, verdad semántica garantizada por fact_ids, ajuste contra datos observados, método CEGIS formal, generalización estadística. Los cuatro casos fueron redactados y etiquetados por el mismo equipo.

**Siguiente prueba recomendada:** una segunda molécula opcional realmente distinta (no sólo otra cola), combinaciones que sobrevivan más de una prueba, deduplicación de grafos equivalentes y diagnóstico conductual de mecanismos para evitar multiplicar arquitecturas únicamente por combinatoria.
