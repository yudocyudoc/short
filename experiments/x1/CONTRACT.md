# X1 — Decisión operativa bajo dos cuellos de botella rivales

**Único experimento integrado de la hoja de ruta v4** ([PR #36](https://github.com/yudocyudoc/short/pull/36)); parte del código de E1 #34, nunca de IA-1 #35. **No prueba comprensión abierta de empresas ni una teoría causal universal.**

## Frontera de decisión

Agente: responsable de una pequeña operación que prepara, despacha y entrega pedidos. Campo: capacidad y ubicación de una restricción física, inventarios fuera de su vista directa, costos de auditoría y capacidad de una única inversión. Objetivo: maximizar unidades **físicamente entregadas** durante una jornada de ocho horas, menos dos unidades equivalentes de costo de ampliación, y menos costo de una inspección opcional. No se monetiza el tablero por sí solo.

**Acciones reales:** ninguna ampliación; ampliar capacidad de preparación hasta al menos 12 unidades/h; ampliar capacidad de distribución hasta al menos 12 unidades/h. Cada ampliación cuesta dos unidades equivalentes; no se permiten las dos. El día hipotético siguiente repite la misma demanda y reinicia sus stocks en cero. Éste es un supuesto ideal explícito, no una previsión de operación continua.

**Mecanismos rivales:** misma topología molecular de E1 (fuente, cola de preparación, cola de despacho, cola física de tránsito, contador), pero distinta localización del cuello de botella. Un mundo tiene preparación limitada a 3 unidades/h y tránsito holgado (20); otro tiene preparación holgada (20) y tránsito limitado a 3. Despacho tiene capacidad 20. La arquitectura causal relevante está en **dónde se acumula inventario**, no en adivinar el nombre de una clase.

**Información inicial:** patrón de demanda alto conocido, sin tiempo individual de salida/recepción ni stocks desagregados. El constructor ve *ambos mecanismos como hipótesis*, no cuál rige cada caso. No cuenta con tabla de clasificación de mundos verdaderos.

## Intervención de información

Máximo una inspección autorizada por mundo: tasa de salidas a las 4h (0.8 unidades), stock en tránsito a las 4h (1.1), o indicador de recepción reportada a las 4h (0.2). Un caso no permite ninguna inspección. En cada caso se otorgan hasta tres respuestas del entorno: contexto inicial + observación opcional + resultado reservado de la siguiente jornada. El nombre de la inspección se fija antes de conocer su resultado.

**Freno de viabilidad antes de experimentar:** OpenModelica, solamente en evaluador, debe confirmar que las inversiones óptimas **difieren** entre mecanismos y ofrecen un beneficio neto superior a 0.5 unidades respecto a las segundas mejores acciones; al menos una inspección debe distinguirlos numéricamente. Si alguna condición falla se detiene X1 como `UNINFORMATIVE_UNIVERSE` sin ejecutar IA, no se cambia el objetivo para fabricar PASS.

## Comparadores simultáneos

A: análisis operativo simple, siempre intenta auditar salidas si está permitido y decide según esa evidencia; se abstiene si dos decisiones permanecen válidas. B: motor numérico sin IA, considera todas las hipótesis y optimiza **valor esperado de información neto del costo**; no es una línea base deliberadamente débil. C: mismo catálogo y consecuencias simuladas que B, IA sólo **critica, elige conceptualmente una inspección y propone una recomendación**. Jamás escribe AST, conexiones, ecuaciones ni Modelica; si su salida es inválida se registra el error, sin parche invisible.

Las salidas C de Llama (versión `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, temperatura 0) se guardan íntegras; no se presenta más de una prueba por caso como iteración independiente.

## Ceguera y adjudicación

La selección secreta por caso se genera con entropía de sistema en el job evaluador; el manifiesto se compromete mediante SHA-256 de sal privada y asignaciones, antes de las peticiones a IA. El participante, tanto en elección como en revisión, opera en **jobs distintos sin descargar `private_truth.json`**. El evaluador sólo devuelve la medida elegida; un tercer proceso califica después de que todos los brazos comprometen elección, recomendación y predicción reservada. Las verdades se revelan finalmente en el informe de adjudicación. La separación por jobs no equivale a protección frente a un administrador que altere permisos o workflows; aquí se evalúa una IA sin herramientas para leer secretos.

Las seis asignaciones se sortean de forma independiente. Si por azar aparece un solo tipo de mundo, se informa `INCONCLUSIVE_ONLY_ONE_TRUE_WORLD`; no se repite para conseguir diversidad. El caso sin inspección debe aceptar abstención cuando las inversiones rivales difieren.

## Métricas y posibilidad de refutación

- Cobertura honesta de rivales compatibles; exclusiones falsas.
- Acción preferida / abstención, arrepentimiento respecto a óptimo con verdad conocida, costo por inspección.
- Diferencia C frente a B y A con igual información inicial y mismo máximo de consultas, costo de llamadas a IA anotado; una ventaja de C no es automática.
- Predicción del resultado reservado expresada como intervalo por los modelos supervivientes, comprometida antes de abrir verdad.
- Preflight negativo, error de arquitectura si IA intenta modelar, probe fuera del menú, más consultas o recomendación sin supervivientes: `FAIL`.

**Interpretación de resultados:** este universo tiene dos candidatos conocidos y ambos comparten las matemáticas de OpenModelica con el evaluador. Una predicción dentro de la banda bajo el modelo correcto es esperable, **no descubrimiento causal**. La pregunta es si el sistema puede decidir, medir, actualizar y reconocer la falta de identificabilidad sin consumir más valor del que genera. Si B o A resultan mejores que C, **declarar ausencia de valor incremental de IA para este caso**. No extender a otros sistemas sin transferencia auténtica.

No se ejecutan más tests separados de capacidad del LLM o conteos de grafos. Éstos son controles regresivos, no el resultado del experimento.
