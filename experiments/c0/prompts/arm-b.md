# Brazo B — Gramática sistémica mínima

Resuelve la **misma tarea** de `prompts/common.md`, con el **mismo escenario** `scenario.md`, usando además estas reglas generales:

- **Separación conceptual:** un stock acumula una cantidad persistente; un flujo es una tasa que lo incrementa o reduce; una variable auxiliar condiciona una tasa sin ser necesariamente una acumulación.
- **Conservación y trazabilidad:** las cantidades no pueden surgir de la nada; considera entradas, salidas, acumulación, pérdida o transferencia con unidades consistentes.
- **Límites y restricciones:** identifica capacidades finitas, inventarios disponibles, horizonte temporal y otros límites explícitos. No conviertas promedios, umbrales normativos o preferencias en imposibilidades biológicas.
- **Propagación:** cuando una etapa no puede absorber la entrada, reconoce las salidas lógicamente admisibles (por ejemplo, acumulación, rechazo, cancelación o derivación), sin atribuir cantidades no observadas.
- **No confundir:** solicitudes ≠ pedidos aceptados ≠ producción ≠ entregas ≠ cobros.
- **Mecanismos:** una flecha plausible no demuestra causalidad. No inventes retroalimentaciones, comportamientos del consumidor ni relaciones con el campo externo. Indica qué necesitaríamos observar para justificarlos.
- **Minimalismo:** incorpora sólo los elementos que sirven para responder la pregunta; no formalices ecuaciones de demanda cuando las restricciones básicas basten.

No se suministra ninguna solución numérica ni diagrama resuelto.
