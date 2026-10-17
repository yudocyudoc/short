# IGC — Selección MTO vs MTS con igual firma de puertos: resultados de la primera corrida

**Fecha de trabajo:** 16-oct-2026 en México / ejecuciones UTC 17-oct-2026. **Estado:** exploratorio. NO existe todavía un grafo auténtico aceptado de Llama para simular en este experimento.

## Qué se cambió respecto del PR #25

Claude había demostrado que el PR anterior era prácticamente resoluble con unificador de puertos. Este experimento ofrece **DOS** arquitecturas distintas y verificadas —MTO de S2 y MTS de S1— con la **MISMA firma abstracta** `FLOW<Order> -> FLOW<DeliveredOrder>`. El validador no utiliza las etiquetas esperadas y acepta **cualquiera** de las dos si entrega estructura y evidencia formalmente correctas. `COMPOSE`, `PARTIAL`, `ABSTAIN` son decisiones de primer orden. No se enviaron cifras, ecuaciones ni condiciones numéricas de simulación al LLM.

**Límite:** son alternativas completas de arquitectura reutilizadas, no ocho moléculas Hines conectables libremente. Los cuatro señuelos están explícitamente NO_EJECUTABLES, para evitar inventar compatibilidad.

## Resultado confirmado del backend, independiente de las propuestas Llama

**[CI #39001909102 — 13 tests PASS y comportamiento OM](https://github.com/yudocyudoc/short/actions/runs/39001909102)**. El contenedor OpenModelica v1.26.5 con SystemDynamics 2.1.2 y MSL 4.0.0 ejecutó dos experimentos `no accepted orders` sobre S1 y S2, con parámetros fijados en la biblioteca y fuera de Llama:

- **MTO/S2**: sin nuevos pedidos y sin trabajo inicial, no hay preparación ni despacho y ambas colas quedan vacías.
- **MTS/S1**: sin pedidos nuevos, pero con programa de producción exógeno, la fabricación continúa y crece el inventario terminado.
- Resultado `POLICY_BEHAVIOR_DISCRIMINATION: PASS`, con dos firmas de comportamiento genuinamente distintas.

Esto prueba un **contraste contrafactual de políticas en modelos sintéticos existentes**, no ajuste a observaciones reales ni validación causal de una empresa. S1 conserva sus curvas Hines y limitaciones conocidas.

## Corrida real con Llama

**[Run #39001963771](https://github.com/yudocyudoc/short/actions/runs/39001963771)** · [24 respuestas y hasta dos intentos por caso, diagnósticos y scores originales](https://github.com/yudocyudoc/short/actions/runs/39001963771/artifacts/12089821237).

Se fijaron previamente 12 casos T01–T12, con cuatro MTO, cuatro MTS, dos sin evidencia de política y dos contradicciones. Las referencias fueron redactadas por el equipo —no son adjudicación independiente externa—. Los dos baselines se mantuvieron congelados.

| Enfoque | Resultado en contrato estricto de admisión de la prueba |
|---|---:|
| Baseline unificador de tipos (empate de interfaces, opta por indeterminado) | **2/12** etiquetas coincidentes |
| Baseline lexical de reglas, sin LLM | **8/12** etiquetas coincidentes |
| Llama, exigido AST y evidencia estructurada para COMPOSE | **3/12** respuestas aceptadas con etiqueta correcta |

Estos valores no son una comparación exactamente homogénea de ingeniería: los baselines sólo clasifican la política, mientras Llama además debía emitir un AST completo con citas que pasaran el compilador. Se incluyen como controles operativos, pero no debe afirmarse superioridad/inferioridad cognitiva basándose únicamente en la tabla.

Las tres aceptaciones de Llama fueron **ABSTAIN** en T09, T11 y T12. **Ninguna** propuesta de COMPOSE pasó el checker: ocho positivos y el falso positivo T10 fallaron el contrato. El job GitHub fue SUCCESS porque el experimento terminó correctamente y archivó fallos individuales, **no** porque Llama lograse nueve composiciones.

## Auditoría forense EXPLÍCITAMENTE POST-HOC de las respuestas originales

Tras observar el 3/12 se hizo una revisión diagnóstica de las mismas respuestas de intento 1, sin ajustar ni etiquetas, ni mensajes, ni casos, ni scores. [Código de auditoría](https://github.com/yudocyudoc/short/blob/experiment/igc-mto-mts-choice-v1/experiments/policy-choice-v1/forensic_original.py), [CI de reproducción #39002236307](https://github.com/yudocyudoc/short/actions/runs/39002236307).

- En T01–T04, la **intención de selección** de Llama fue MTO, en consonancia con los hechos.
- En T05–T08, la intención de selección fue MTS.
- En T09, T11 y T12, Llama se abstuvo con motivo correcto (`EVIDENCE_MISSING` o `CONFLICTING_POLICIES`).
- En **T10** —agenda de una clínica sin fabricación de bienes—, Llama propuso **MTO** a partir de lenguaje de solicitudes y esperas, aun cuando el problema no sustentaba una política productiva. **Éste es un fallo semántico real**.

Como interpretación **post-hoc** de la etiqueta `decision` y `policy` en el texto crudo, **11/12** coincidieron con la respuesta esperada (8/8 positivos y 3/4 no-compose). **No reemplaza el resultado estricto 3/12 ni demuestra modelos ejecutables.** Las 12 muestras, su redacción y etiquetas son sintéticas y del mismo proyecto.

### Por qué el validador rechazó COMPOSE

El esquema exigía `support` y `counterevidence` como arrays de objetos `{fact_id,quote}`, y cada `links[].evidence` también como objeto. En la primera salida de los nueve casos COMPOSE, Llama produjo **arrays de cadenas y strings de evidencia**, no esos objetos. El segundo intento no corrigió las evidencias de enlace. El checker hizo bien en detenerse.

Además, en algunos casos `counterevidence` contenía frases **no presentes literalmente** en los hechos, por ejemplo «No se menciona producción especulativa sin pedidos» (T01) o «No hay evidencia de que la producción se inicie después de recibir un pedido» (T05). Son inferencias lingüísticas de ausencia, no citas; **no deben admitirse como citas positivas de hechos**. El fallo no es puramente de formato.

## Importancia metodológica

1. **La elección no está forzada por puertos:** ambos modelos nativos pueden ser declarados para el mismo grafo abstracto. El checker admite incluso MTS en un caso cuyo gold dice MTO; la evaluación separada lo contaría como fallo causal.
2. **El mecanismo matemático puede diferir realmente:** sin pedidos, MTO no procesa y MTS puede producir. Es una discriminación dinámica observada en OM, no paridad consigo mismo.
3. **La interpretación causal cruda fue mayoritariamente correcta en este conjunto**, pero hubo confusión servicio/producción en T10.
4. **La estructura de salida no es todavía robusta**: 0/9 propuestas de composición pasaron el contrato y por ello no hubo modelo Llama ejecutado en OM.
5. **Se necesitan métricas separadas** para política elegida, traza literal y artefacto ejecutable. Responder correctamente MTO/MTS no equivale a construir una casa completa.

## Qué conviene hacer después

Para un protocolo v2 *prospectivo* con casos nuevos, simplificar y tipar las referencias como identificadores de hechos en el AST y resolver su texto literal exclusivamente en el backend (sin permitir que el LLM fabrique negaciones como supuestas citas). Distinguir explícitamente `positive_support` de `rival_excluded_because` y de `unknown`; el último no es un extracto textual. Conservar casos nuevos y reservar los 12 actuales como depuración de ingeniería. Ofrecer dos módulos completos es todavía sólo **selección arquitectónica**, no composición abierta de Hines.

**No ejecutar otra vez los mismos casos después de ajustar el prompt para reclamar una segunda 'validación'.**
