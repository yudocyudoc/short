# IGC · Ensamblaje causal basado en sd-ai + componentes OpenModelica (prueba v1)

## Decisión de arquitectura

**El LLM NO produce ecuaciones.** Su única salida evaluable es un **grafo SD** de roles, stocks, flows, relaciones causales, polaridades, bucles con evidencia, información faltante y autorización propuesta.

La identificación causal sigue y **adapta** las instrucciones del motor cualitativo de [UB-IAD/sd-ai](https://github.com/UB-IAD/sd-ai/blob/main/engines/qualitative/QualitativeEngineBrain.js): extraer variables neutrales, causalidad con polaridades +/−, identificar acumulaciones y tasas, examinar feedback e incorporar el contexto empresarial. **No utilizamos su generador cuantitativo para crear ecuaciones**; tampoco replicamos su prompt literalmente o pretendemos haber verificado sus benchmarks. Inspiración y fuente: repositorio [sd-ai](https://github.com/UB-IAD/sd-ai), consultado el 16-oct-2026.

El componedor `compile_graph.py` no interpreta código del modelo; verifica un contrato cerrado y genera **declaraciones de bloques y conexiones Modelica de un catálogo permitido**. Las fórmulas de acumulación y las funciones de respuesta/limitación pertenecen a **`SystemDynamics` y `Modelica.Blocks.Math.Gain`**. Las señales externas y los alias de observación son uniones internas deterministas; **no se debe decir que OpenModelica descubre o selecciona políticas económicas automáticamente**.

## Lo que está genuinamente reutilizado

**Bloques existentes:**
- `SystemDynamics.Levels.Level` ×2 (stocks),
- `SystemDynamics.Levels.Level1a` ×1 (entregas acumuladas),
- `SystemDynamics.Rates.Rate_1` ×1 (pedidos entrantes),
- `SystemDynamics.Rates.RRate` ×2 (preparación y despacho limitados),
- `Modelica.Blocks.Math.Gain` ×2 (políticas lineales de respuesta).

**Marco ya validado:** `IGCS2MakeToOrder.Scenario`, que define entrada exógena de prueba, parámetros hipotéticos y variables observadas. Ese marco **contiene ecuaciones de entrada temporal previamente escritas**; no se presenta como una función que Modelica infirió de una empresa. Para la versión v1, OpenModelica ejecuta un ensamblaje de conexiones y bloques aprobados, sin `der()` propio ni fórmula libre generada por IA.

**Límite notable:** tenemos un **andamiaje de seis roles conocido y validado**. La IA elige si existe ese mecanismo en la evidencia y construye su grafo (incluidos dos lazos de balance), pero todavía no descubre un mecanismo totalmente nuevo entre cientos de componentes de OpenModelica. Los grafos no soportados quedan **REJECTED**, sin generar código. Ese comportamiento es una frontera deliberada y no un fallo que haya que resolver inventando clases.

## Rutas relevantes

- `catalog.json`: clases/roles/puertos predefinidos, módulos de política, origen de parámetros.
- `cases_public.json`: cuatro narraciones independientes (dos con estructura conocida, un caso solo POS, un caso contradictorio con instrucción adversarial).
- `run_llm.py`: prompting de seis pasos adaptado del motor SD cualitativo, salida JSON estricta (no Modelica), una llamada por caso si se autoriza.
- `compile_graph.py`: validaciones de nodos, cinco vínculos materiales, dos relaciones de control, evidencias y lazos de balance; emisor determinista de `.mo` únicamente para patrón completo con parámetros hipotéticos verificados.
- `oracle_graph_G01.json`: **construcción humana**, solo usada para verificar ensamblaje de código y compilación. No cuenta como respuesta del LLM.
- `assembled.mos`, `baseline.mos`: ejecución de OpenModelica, ambas sobre la misma condición sintética S2.
- `test_assembly.py`: casos de fallos seguros, evidencia, grafo, clases no admitidas y garantía de cero `der()` generado.
- `output/`: reportes y series derivados de CI; no se redistribuyen bibliotecas ni archivos Hines.

## Criterio de evaluación (etapas independientes)

**E1 · SD causal:** nodos con tipo, conexión, causalidad, polaridad, respaldo y abstención. Un LLM puede fallar aquí aunque un grafo manual simule.

**E2 · Composición OM:** compilador reconoce topología y reutiliza componentes y funciones de biblioteca; código generable contiene cero `der()` o ecuaciones provenientes del LLM. OM debe compilar y ejecutar. El generador de confianza inserta señales, conexión de puertos y alias de observación.

**E3 · Numérico:** serie Euler independiente vs modelo S2 prevalidado vs nuevo modelo ensamblado, 41 puntos × seis variables; tol 1e-6, misma política S2. Es **paridad de escenario sintético**, nunca ajuste empírico ni predicción empresarial.

La CI de PR ejecuta E2/E3 contra `oracle_graph_G01.json`, **no demuestra que el LLM haga E1**. El experimento LLM real está aislado y solo se dispara mediante decisión explícita; no hay reintentos ni remediaciones de respuestas, y conserva originales. Si falla el primer caso, se detiene el paso de simulación del LLM; los artefactos siguen guardados.

## Uso offline

```bash
python -m unittest discover -s experiments/sdai-om-scaffold-v1 -p 'test_*.py' -v
python experiments/sdai-om-scaffold-v1/compile_graph.py --case G01 --proposal experiments/sdai-om-scaffold-v1/oracle_graph_G01.json --out experiments/sdai-om-scaffold-v1/output/oracle_result.json --model experiments/sdai-om-scaffold-v1/IGCAutoAssembled.mo
python experiments/sdai-om-scaffold-v1/run_llm.py --prepare-only --out experiments/sdai-om-scaffold-v1/output/prepared
```

CI descarga MSL 4.0.0, SystemDynamics 2.1.2 y OpenModelica 1.26.5. No utiliza PySD ni los originales protegidos de Hines para esta nueva etapa.

## Cambios prospectivos

Si la biblioteca no ofrece un componente para políticas de cola, realimentación, memoria, retraso o reglas específicas, ese hueco se declara. No usar generación de ecuaciones como salida alternativa. Para superar esta v1 se requerirá **catalogar otros componentes abiertos y sus puertos**, no convertir al LLM en autor libre de Modelica.
