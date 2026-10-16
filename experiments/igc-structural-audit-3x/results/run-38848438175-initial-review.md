# Auditoría IGC 3×2 — resultados originales y lectura inicial

**Run:** https://github.com/yudocyudoc/short/actions/runs/38848438175  
**Artefacto de respuestas originales:** https://github.com/yudocyudoc/short/actions/runs/38848438175/artifacts/12024337590  
**Modelo:** `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`  
**Estado técnico:** seis llamadas de seis con `api_success=true`, `status=OK`, objeto JSON parseable; CI preflight e infer PASSED.  
**Uso:** 11,162 tokens de entrada + 7,771 de salida = **18,933 tokens**, 3,952.6177 neuronas informadas por el proveedor. No se ha inferido de ello la facturación real.

## Resumen de las seis respuestas, sin reparaciones

| Caso | A — sin probes | B — con probes aritméticos |
|---|---|---|
| BB01 | `decision_supported=NO`. Advierte falta de validación POS→llegadas, parámetros arbitrarios y acoplamiento unilateral; declara no encontrar falla estructural demostrable. | `decision_supported=CONDITIONAL`. Menciona lookup y falta de retroalimentación, sin identificar `f(r)>r` como explicación de sobreproducción ni la paralización de backlog cuando POS=0. |
| W17 (retardo mal implementado) | `NO`. Detecta incompatibilidad de retardo, pero afirma equivocadamente recepción en día 2 (el código la recibe día 1) e inventa un problema de saldo en día 7. | `NO`. Acertó en la fecha contractual: orden día 1 → recepción día 3. Sin embargo, califica de incorrecto el inventario día 3=9; ese inventario es correcto en la trayectoria con retardo. |
| W18 (retardo consistente) | `NO`. Describe correctamente recepción en día 3 y agotamiento, sin demostrar un error estructural; el NO podría reflejar insuficiencia para promesas reales, no rechazo técnico. | `YES`. Identifica correctamente recepción día 3 y los stocks, y declara ausencia de fallas demostrables; YES puede sobreinterpretarse si se trata de promesas reales, no simple consistencia interna. |

## Adjudicación provisional (aún no puntuación ciega independiente)

- **BB01:** ninguno de los dos brazos identifica explícitamente los dos mecanismos discriminantes que motivaron esta prueba. La salida B contiene una alusión a lookup y a realimentación, pero no deriva el excedente del lookup ni la congelación por `DesiredProduction=0`.
- **W17:** A y B reconocen que existe un problema con el tiempo de recepción; B localiza el día contractual con mayor precisión. Ambos incluyen afirmaciones erróneas adicionales; B no queda exento de alucinación por recibir probes.
- **W18:** el control consistente no generó una acusación causal estructural específica en ninguno de los brazos. B explicita ausencia de falla, aunque su etiqueta global `YES` exige separar consistencia de utilidad para promesas de entrega.
- **No declarar superioridad general de B:** N=3 casos por brazo, sin replicación ni evaluación independiente y con pruebas realizadas sobre escenarios elaborados por el propio proyecto.

## Criterios antes de modificar el experimento

1. No retocar prompts ni hacer llamadas correctivas sobre esta muestra.
2. Si se adjudican puntos, puntuar *mecanismo exacto* y no similitud lingüística o mención genérica.
3. Separar `decision_supported` (decisión práctica) de `structural_fidelity` (consistencia del modelo con su contrato).
4. Mantener las respuestas originales, sus tokens/hashes y el paquete ZIP como referencia de esta corrida.

**Resultado central:** reproducibilidad de la inferencia confirmada; detección estructural específica en BB01 no conseguida, mientras la detección del retardo en W17 presenta errores de precisión. Por lo tanto, todavía no se demuestra auditoría estructural confiable ni autonomía de IGC.
