# IGC — piloto de evidencia y selección de moléculas (v1)

**Hipótesis acotada:** ¿Los contratos de moléculas funcionales aportan algo a Llama por encima de (a) instrucciones SD cualitativas generales con nombres de mecanismos y (b) un clasificador determinista de reglas, cuando se exige evidencia textual literal? **El LLM no recibe datos numéricos, no genera ecuaciones ni toca OpenModelica.** Ningún resultado de este experimento constituye simulación.

## Diseño concreto

- 12 relatos empresariales **inventados cualitativos**, nuevos respecto de G01–G04 y C01–C08, en `cases_public.json`. Contienen afirmaciones positivas, ausencia de datos, ámbitos sin molécula autorizada y contradicción.
- Cuatro mecanismos disponibles: `CAP_UTIL`, `BACKLOG_FLOW`, `MATERIAL_DELAY` (originales Hines SHA/PySD verificados) y `MTO_S2_PATTERN` (patrón de seis componentes SystemDynamics/MSL validado en el S2; **no es molécula nativa independiente**). Esta limitación de madurez aparece en el catálogo.
- **A: baseline determinista:** `deterministic.py` inspecciona los hechos públicos y usa reglas de palabras clave. No lee `gold_private.json`.
- **B: Llama, SD general:** secuencia cualitativa inspirada en sd-ai (variables, stocks, flujos, límites y contradicciones). Recibe los mismos hechos y los IDs/títulos de las cuatro opciones, sin sus contratos enriquecidos.
- **C: Llama, moléculas:** mismo prompt base, las mismas opciones y los mismos hechos; adicionalmente recibe funciones, entradas/salidas conceptuales, requisitos, exclusiones y madurez de cada mecanismo.
- Las dos variantes usan el mismo modelo Cloudflare (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`), temperatura 0, un intento por caso y 1,250 tokens máximos de salida. Para minimizar tendencias de orden, se alterna qué variante se envía primero por caso.

Cada respuesta debe devolver `decision`, `molecules`, `citations` (`target`, `fact_id`, `quote`) y `unresolved`. La cita debe ser **substring literal de un hecho**. Para considerarla evidencia compatible, también debe corresponder al hecho preregistrado como respaldo de la molécula. Si una molécula no aplica, se espera `ABSTAIN` y una cita pertinente sobre límites/contradicción.

**Clave independiente de los prompts:** `gold_private.json` fija la selección y los hechos que realmente respaldan cada mecanismo. El evaluador consulta la clave **después** de obtener las respuestas; nunca se entrega al modelo. Esto no supone validación semántica automática general: el respaldo está etiquetado manualmente para estos casos sintéticos.

## Métricas distintas

1. `exact_selection`: coincidencia exacta de conjunto de mecanismos y abstención.
2. `literal_quote_pass`: citas que aparecen realmente en el hecho referido y cubren cada molécula seleccionada.
3. `source_supported_citation_pass`: además de literalidad, al menos una cita permitida por la anotación independiente para cada molécula.
4. `strict_pass`: selección exacta **y** citas correctamente respaldadas.
5. `unsupported_molecules`, `false_abstentions`: falsos positivos y abstenciones que pierden mecanismos fundamentados.

Una cita que aparece literalmente no demuestra verdad causal: sólo comprueba trazabilidad textual. No se fabrican parámetros ni ecuaciones, y ninguna clase se declara compatible con otras por selección conjunta.

## Advertencias metodológicas previas a la ejecución LLM

**Esta muestra NO es un estudio ciego.** El investigador creó tanto los doce casos como el baseline de expresiones regulares durante el mismo trabajo. Antes de lanzar ningún LLM el baseline alcanzó **12/12 de selección exacta y citas estrictas**. Ello es una señal clara de **casos demasiado fáciles/efecto de diseño conjunto**. No modificamos retrospectivamente los casos ni debilitamos las reglas para producir un resultado favorable a Llama. El piloto puede descubrir defectos de formato, extracción y abstención, pero **no puede establecer una ventaja estadística de Llama** sobre esta línea base con un techo perfecto.

Las cuatro opciones están cerradas de antemano. La selección no implica que puedan componerse por sus conectores Modelica. Cuatro Hines en el catálogo anterior no equivalen a cuatro moléculas OM ejecutables. Con solo 12 casos, diferencias de acierto son exploratorias, sin potencia formal preespecificada. Un estudio confirmatorio exigiría nueva muestra independiente y dimensionamiento apropiado, preferiblemente evaluación pareada y estratificada por casos ambiguos/negaciones/composiciones.

## Reproducibilidad y límites de herramientas

```bash
python -m unittest discover -s experiments/evidence-molecules-pilot-v1 -p 'test_*.py' -v
python experiments/evidence-molecules-pilot-v1/deterministic.py \
  --out /tmp/baseline.json --score-out /tmp/baseline_score.json
python experiments/evidence-molecules-pilot-v1/run_llm.py --prepare-only --out /tmp/prompts
```

La CI de PR ejecuta únicamente baseline, tests y generación de prompts (cero llamadas pagadas). Las inferencias auténticas se ejecutan mediante un **push de autorización de una sola vez** o `workflow_dispatch` explícito, con secretos Cloudflare del repositorio. Se archivan las solicitudes sin secretos, respuestas originales, manifiesto, hashes y scores incluso si hay errores del proveedor. Un error de formato o una respuesta ausente NO se sustituye por un ejemplo humano ni se reintenta para mejorar la nota.

## Decisión después del piloto

- Si Llama no supera siquiera el baseline simple, documentar tipos de error antes de construir un parser completo IGC-SL.
- Si supera algunas limitaciones no captadas por reglas simples en casos posteriores, redactar un conjunto **nuevo y ciego**, congelar implementaciones antes de conocerlo y evaluar con muestra suficiente.
- No pasar todavía a entrenamiento de parámetros, integración BSL ni reparaciones múltiples: eso pertenece a otros experimentos.
