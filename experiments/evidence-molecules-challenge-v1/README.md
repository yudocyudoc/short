# IGC · Prueba de desafío con los enfoques congelados (v1)

**Hipótesis exploratoria:** ¿la ventaja observada de Llama + contratos de moléculas en el piloto P01–P12 se mantiene en **24 narraciones nuevas** que incluyen descripciones alternativas, negaciones, mecanismos vecinos, evidencias insuficientes, combinaciones de tres moléculas y contradicciones?

## Congelación verificable

Los tres brazos son **idénticos** a los del [PR #21](https://github.com/yudocyudoc/short/pull/21). Este directorio no contiene un prompt nuevo, un regex nuevo ni una regla de puntuación reescrita; `run_challenge.py` importa las mismas funciones originales y rechaza cualquier modificación de las cuatro piezas mediante SHA de blob Git:

- `evidence-molecules-pilot-v1/deterministic.py` — reglas A;
- `evidence-molecules-pilot-v1/run_llm.py` — prompts SD B, moléculas C y proveedor;
- `evidence-molecules-pilot-v1/evaluate.py` — evaluación y citas;
- `evidence-molecules-pilot-v1/catalog_public.json` — catálogo y contratos.

**Nuevos materiales:** `cases_public.json` con N01–N24 y `gold_private.json` con decisiones y hechos que pueden sustentarlas, fijados **antes** de realizar cualquier llamada. La clave no se inyecta a ninguno de los prompts. Un `case_id` de Nxx no implica información semántica.

### Advertencia de independencia

Los casos son *nuevos respecto de P01–P12* y los brazos son previamente congelados, por lo que evalúan **transferencia a nuevos textos**. Sin embargo, **no son ciegos ni independientes del equipo investigador**: el mismo asistente diseñó casos y anotaciones humanas. No se puede presentar como replicación confirmatoria ni como benchmark externo. Se mantiene intacto el baseline anterior incluso si obtiene un mal resultado.

## Moléculas posibles

Las mismas cuatro opciones que en PR #21: `CAP_UTIL`, `BACKLOG_FLOW`, `MATERIAL_DELAY` y `MTO_S2_PATTERN`. Sus limitaciones y procedencias siguen siendo las mismas. La inclusión conjunta en una respuesta no implica que sus clases tengan conectores Modelica interoperables.

## Ejecución

**CI determinista sin inferencias:**

```sh
python -m unittest discover -s experiments/evidence-molecules-challenge-v1 -p 'test_*.py' -v
python experiments/evidence-molecules-challenge-v1/run_challenge.py --prepare-only --out experiments/evidence-molecules-challenge-v1/output/prepared
```

El baseline del PR anterior se ejecuta de forma inalterada sobre los 24 casos y se archiva la salida antes de llamar a ningún LLM. `--prepare-only` genera exactamente 48 prompts pero **NO envía llamadas al proveedor**.

**Inferencia auténtica:** workflow explícito de GitHub Actions `RUN_48_CASES`, o un commit de autorización con mensaje exacto `run(igc): execute frozen paired challenge 48 real calls`. Se utilizan los secretos Cloudflare del repositorio y el modelo anterior `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, temperatura cero, 1 respuesta/caso/brazo, cero reintentos. Todo se archiva aunque alguna respuesta falle.

## Métricas

Conservamos EXACTAMENTE los criterios anteriores: selección exacta, citas literales, citas con respaldo preregistrado, strict pass, falsos positivos y abstenciones erróneas. Agregamos descriptivamente la tabla de casos pareados y la p exacta McNemar exploratoria (sin afirmar potencia ni significación suficiente). Las respuestas faltantes puntúan **cero**.

No hay números para el LLM, ecuaciones, archivos Modelica generados ni ejecución de OpenModelica: se evalúa **reconocimiento causal y abstención** antes de programar IGC-SL.

### Riesgos

Los casos siguen siendo cualitativos y redactados manualmente. La cita literal protege trazabilidad textual pero no valida causalidad. El baseline simple puede ganar por vocabulario; una mejora C>B sobre 24 casos no prueba generalización. No modificar casos/clave/reglas después de observar respuestas para fabricar un resultado favorable.

### Criterio de salida

Registrar los 24×2 originales, baseline, score por caso, conteos y tipo de errores. Después decidir si conviene evaluar con un conjunto externo o ampliar la biblioteca; no construir ahora más reglas complejas ni un parser completo de IGC-SL.
