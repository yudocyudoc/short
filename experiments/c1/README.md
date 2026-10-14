# C1 — Cotas, estados observados y destinos de solicitudes

**Diseño:** 2026-10-13 · **Estado:** congelado antes de la ejecución. C1 es una continuación acotada de C0: usa el mismo proveedor y modelo y los mismos principios de comparación A/B.

## Pregunta

¿Puede la IA distinguir entre (1) una cota de producción posible, (2) una producción/entrega efectivamente registrada y (3) el estado final de dos stocks cuando hay observaciones suficientes?

C0 demostró errores compartidos: «capacidad máxima = producción efectiva», «solicitudes no entregadas = necesariamente pendientes». C1 incluye resultados operativos observados y registra exhaustivamente los destinos de solicitudes. **No se cambiaron las reglas del brazo B para favorecerlo después de C0.**

## Archivos

- `scenario.md`: hechos entregados idénticos a A y B.
- `prompts/common.md`: instrucciones compartidas, misma estructura que C0.
- `prompts/arm-a.md`: línea base.
- `prompts/arm-b.md`: **copia del contenido de la gramática de C0** (sin cambios sustantivos).
- `evaluation/reference.md`: solución y rúbrica **excluidos de la inferencia**.
- `results/`: pruebas, respuestas íntegras y evaluación posterior.

El modelo no debe recibir el contenido de `evaluation/`, los resultados de C0 ni la referencia de C1. El runner sólo concatena los tres archivos de entrada correspondientes.

**Límite de gasto:** exactamente una corrida A y una B (2 solicitudes máximas), `@cf/zai-org/glm-4.7-flash`, `max_completion_tokens=2400`. Una sola pareja es exploratoria.

**Qué C1 no demuestra:** descubrimiento de mecanismos causales reales, buen desempeño con datos empresariales incompletos, o capacidad de modelar retroalimentaciones. C1 prueba contabilidad estructural bajo observaciones explícitas.
