# X1-b — Resultados reales del ciclo integrado (2026-10-18)

**Corrida completa, con API corregida:** [GitHub Actions #39109063285](https://github.com/yudocyudoc/short/actions/runs/39109063285). [Adjudicación y apertura de mundos](https://github.com/yudocyudoc/short/actions/runs/39109063285/artifacts/12129348566), [peticiones y respuestas de IA al elegir medida](https://github.com/yudocyudoc/short/actions/runs/39109063285/artifacts/12129517023), [respuestas de IA al revisar decisión](https://github.com/yudocyudoc/short/actions/runs/39109063285/artifacts/12129388478). **Corrida original X1-a preservada:** [REAL_RESULTS_X1a.md](REAL_RESULTS_X1a.md), con C no evaluable por fallo del adaptador Cloudflare. La segunda corrida usó entropía nueva, sin modificar mundos candidatos, costos, instrumentos, umbrales ni heurísticas A/B.

## Resultado adjudicado sin seleccionar el caso favorable

La comprobación previa numérica de OpenModelica confirmó que **la ampliación preferible cambia** entre un cuello de botella en preparación y otro posterior al despacho. Se efectuó un ciclo de información, decisión y pronóstico reservado, con un mundo sellado que se abrió después de los compromisos. Ambos mecanismos aparecieron en las asignaciones finales: M_A en cinco casos y M_B en uno. **Los casos repiten prácticamente la misma información inicial y no constituyen seis muestras conceptualmente independientes**.

| Resultado sobre seis casos | A: revisión operativa simple | B: SD numérico sin IA | C: mismo SD + crítica Llama |
|---|---:|---:|---:|
| Acción óptima identificada | 5/6 | 5/6 | 5/6 |
| Abstención (caso sin inspección permitida) | 1 | 1 | 1 (forzada por validador) |
| Excluyó indebidamente el verdadero mundo | 0 | 0 | 0 |
| Intervalo comprometido contiene respuesta reservada | 6/6 | 6/6 | 6/6 |
| Costo de inspecciones | 4.0 | **1.0** | 5.5 |
| Arrepentimiento agregado frente al óptimo omnisciente | 19.6420 | **16.6420** | 21.1420 |
| Respuestas conceptuales C admitidas | N/A | N/A | 5/6 en fase de decisión |

**Valor incremental de C frente a B:** `-4.5` unidades de arrepentimiento agregado; C **no añadió valor decisional**, y costó más en mediciones. Ni siquiera se incorporó el costo de tokens del LLM, que sólo ampliaría la desventaja de C. Se advierte que el arrepentimiento incluye una oportunidad perdida relevante en el caso sin inspección: no es una comparación pura de costos de modelos.

## Hallazgo de proceso: escoger una observación verdadera NO basta

- B escogió `inspect_dashboard` (costo 0.2 por caso permitido), que en este mundo ideal separaba ambos mecanismos bajo la prueba autorizada. No eligió la medición físicamente más rica: eligió la **más barata que cambiaba la decisión**.
- C escogió `measure_in_route` (costo 1.1), que también separaba correctamente los rivales, pero no justificó el gasto adicional. Los cinco casos con medición produjeron decisiones estructuralmente compatibles y recomendaciones óptimas.
- En C06, donde las mediciones estaban prohibidas, el LLM intentó elegir `measure_in_route` y más tarde recomendar `upgrade_distribution` dejando fuera un mundo compatible. **El validador bloqueó ambos intentos** y registró abstención. Es un límite real de respeto a la observabilidad, no un éxito independiente de Llama.
- La diferencia de costo 5.5 - 1.0 = **4.5** coincide con toda la diferencia de arrepentimiento C-B: **ambos eligieron las mismas acciones**, C compró información más cara.

## Límite más importante: ¿cuánto enseña esto sobre IGC?

**No es una demostración del método.** Es un circuito integrado técnico con una prueba pequeña de valor decisional que aquí resultó **NEGATIVA PARA LA APORTACIÓN INCREMENTAL DE IA**.

1. **Techo predefinido para la IA.** B tenía en su catálogo ambos modelos correctos y sus consecuencias calculadas con precisión sobre el mismo motor del evaluador. Con sólo dos mundos válidos y una inspección que basta para separarlos, B puede optimizar exactamente el costo de información. C no tenía espacio legítimo para descubrir un mecanismo omitido, criticar un supuesto falso del motor ni mejorar su conjunto de hipótesis. Por construcción es un entorno muy favorable a B: **no permite juzgar la función investigadora más ambiciosa del IGC**.
2. **La transferencia propuesta conceptual → restricción tipada → composición todavía NO está implementada.** C escogió observaciones y acciones de un menú cerrado, pero no pudo plantear una variante que el motor convirtiera en estructura. Este es precisamente el hueco reconocido en la hoja v4. No debemos inventar que X1 lo resolvió.
3. La verdad sintética y las alternativas comparten la misma biblioteca Modelica y parámetros elegidos. Las predicciones reservadas dentro del intervalo son esperables en un universo cerrado, no una validación prospectiva empresarial.
4. El caso C06 muestra que la garantía de abstención vino del motor de reglas, no de la IA. Cuando la información no discrimina, el método conjunto supo no ejecutar una inversión arbitraria, pero C por sí solo no.
5. Los cinco casos con observación recibieron el mismo planteamiento y ofrecieron sólo dos tipos de respuesta. No inferir frecuencias, robustez estadística ni comparaciones de modelos a partir de 5/6.

**Adjudicación:** `PIPELINE_TECHNICAL_PASS`; `DECISION_TRIAL_EXECUTED`; `AI_INCREMENTAL_VALUE_NOT_DEMONSTRATED`; `IGC_METHOD_NOT_VALIDATED`. **Siguiente decisión:** no escalar el universo cerrado ni seguir repitiendo el selector de observaciones. Si se continúa, debe ser sobre una discrepancia causal que no esté representada en B, y sólo después de construir y verificar el puente conceptual tipado. Si no existe esa brecha real, parar X1 y reconsiderar la contribución esperada de IA.

Esta interpretación adversa se registró sin solicitar una tercera corrida.
