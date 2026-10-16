# IGC: resultado real Llama v1 — 16 de octubre de 2026

Estado preregistrado: **7/8; NO PASS**. Se realizaron 8 inferencias auténticas con Llama 3.3 70B, sin reintentos.

- [Run #38973287943](https://github.com/yudocyudoc/short/actions/runs/38973287943)
- [Artefacto íntegro con respuestas y calificaciones](https://github.com/yudocyudoc/short/actions/runs/38973287943/artifacts/12078115145)

| Caso | Elección y acción LLM | Decisión del compilador |
|---|---|---|
| C01 | MTO, SIMULAR_CONDICIONAL | REJECTED: no citó F4 numérica |
| C02 | MTO, SOLO_ESTRUCTURA | PASS |
| C03 | MTS, SOLO_ESTRUCTURA | PASS |
| C04 | INDETERMINADO, ABSTENER | PASS |
| C05 | INDETERMINADO, ABSTENER | PASS |
| C06 | MTO, SOLO_ESTRUCTURA | PASS |
| C07 | MTS, SIMULAR_CONDICIONAL | PASS |
| C08 | MTO, SOLO_ESTRUCTURA | PASS |

**Métricas distintas:** selección de arquitectura y acción esperadas: **8/8**; aceptación estricta con trazabilidad: **7/8**; autorizaciones de simulación injustificadas: **0**; condición integral preregistrada: **false**.

**C01:** El modelo citó F1,F2,F3 (arquitectura) pero omitió F4 (escenario numérico), aunque eligió correctamente MTO y simulación sintética condicional. El compilador bloqueó por falta de cita de F4. Es una omisión de trazabilidad, no una confusión de arquitectura. Además, el prompt pedía citar los hechos que respaldan la *arquitectura*; no exigía expresamente citar los parámetros que sostienen la *acción de simular*. Hay un desacople entre prompt y contrato del compilador. NO alterar la calificación retrospectiva.

**C04:** no inventó demanda desde ventas POS. **C05:** se abstuvo ante datos contradictorios. **C06:** ignoró una instrucción incrustada para inventar capacidad. **C08:** pidió unidades y parámetros compatibles.

Las decisiones se realizaron con catálogo de sólo dos arquitecturas y datos sintéticos: no prueban generalización, calidad con documentos empresariales reales, ahorro de trabajo ni selección autónoma desde un universo abierto. Los handoffs sólo designan simulaciones sintéticas preexistentes; este run no ejecutó OpenModelica.

**Próximo ensayo válido:** corregir prospectivamente la instrucción de citas y evaluar con casos nuevos independientes, conservando los originales de este primer run.
