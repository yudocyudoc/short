# IGC · prueba mínima: exploración restringida + crítico causal (v1)

**Objetivo inmediato:** comprobar que un generador determinista puede enumerar y ejecutar arquitecturas compatibles, y que Llama, actuando **sólo como revisor**, puede proponer una condición que permita discriminar sus comportamientos a partir de un relato.

## Protocolo, sin reinventar la biblioteca

Reutilizar **las dos arquitecturas ya verificadas** en los PR #25–26:
- `MTO` → S2, fabricación sólo tras encargo aceptado.
- `MTS` → S1, fabricación según plan exógeno con inventario terminado.

Las dos tienen **idéntica firma abstracta de puertos**. El enumerador `explorer.py` no ve los casos ni su gold: inspecciona el catálogo existente, compone `SOURCE → (MTO | MTS) → SINK` y devuelve **ambas** opciones tipadas. Sin LLM ni programación matemática nueva.

El workflow ejecuta de nuevo en **OpenModelica 1.26.5** los modelos originales bajo la intervención *sin nuevos pedidos* y obtiene de los CSV dos firmas dinámicas: `MTO:STOPS`; `MTS:CONTINUES`. Si el resultado numérico cambia o falla, el experimento aborta; **no se sustituyen simulaciones por etiquetas escritas a mano**.

El crítico Llama recibe todos los candidatos, sus contratos/limitaciones, sus firmas **cualitativas** y el relato. No necesita diseñar grafos ni copiar citas. Sólo propone:
```json
{"case_id":"R01","test_id":"NO_ACCEPTED_ORDERS",
 "expected":"STOPS","fact_ids":["F1","F2"],"next_question":""}
```
El linter comprueba el esquema, el ID del ensayo y que los IDs de hechos realmente existen. El motor compara el resultado **propuesto por Llama** contra las firmas **calculadas en OpenModelica**, conservando los candidatos que coinciden.

**Crítica importante:** el linter NO prueba que el texto citado implique semánticamente STOPS o CONTINUES; esa interpretación la hace Llama. El resultado son alternativas condicionadas a una premisa propuesta, no un modelo empiricamente validado. Para `UNKNOWN` o `CONFLICT`, no se descarta ninguna arquitectura y se solicita información adicional. La pregunta del crítico no se ejecuta automáticamente si no forma parte de los ensayos registrados.

## Cuatro casos nuevos fijados previamente

`cases.json` y `gold.json` contienen cuatro situaciones sintéticas: **no producir sin pedido** (R01), **producir para inventario sin pedidos** (R02), **solamente registros de ventas** (R03) y **documentos contradictorios** (R04). Los autores son los mismos del experimento, por lo que el puntaje NO representa evidencia independiente de generalización.

## Qué se mide

1. El enumerador sin LLM mantiene dos candidatos válidos: el unificador por tipos no puede elegir.
2. Las dos simulaciones se ejecutan y muestran resultados diferentes para el mismo ensayo.
3. Si el crítico identifica STOPS o CONTINUES sustentado en los hechos, el motor puede eliminar un candidato **condicionalmente**. Si encuentra desconocimiento/contradicción, debe preservar ambas opciones.
4. El esquema y los IDs se validan determinísticamente sin pedir a Llama un JSON enorme de nodos, puertos y citas.
5. Ninguna cifra de capacidad, tasa o periodo ni ninguna ecuación se envía a Llama.

**Resultado esperado como prueba de ingeniería:** una demostración reproducible del encadenamiento búsqueda → linter → simulación → crítica → selección condicionada. No se busca un efecto estadístico con cuatro casos.

## Qué NO demuestra

No es aún *Compositional Modeling* arbitrario: **hay dos modelos completos S1/S2** y ninguna biblioteca heterogénea de piezas ensamblables. El generador no descubre nuevos mecanismos; sólo enumera opciones registradas. Tampoco es CEGIS formal: las propuestas causales del LLM no son pruebas y ninguna medición del mundo real valida el supuesto.

La ejecución de cientos de arquitecturas es una extensión posible del generador, pero sería prematuro antes de contar con más moléculas **realmente ejecutables**, adaptadores probados y pruebas dinámicas discriminantes. No contemos variaciones numéricas de un mismo modelo como si fueran nuevas arquitecturas.

## Trazabilidad

- `explorer.py`: generador y linter determinista; sólo firmas reales derivadas de CSV OMC.
- `run_critic.py`: prompts de Llama, respuestas originales, códigos de error y poda condicionada.
- `test_explorer.py`: pruebas de equivalencia de puertos, abstención, contratos, falsificación de hechos y ausencia de valores/equaciones.
- `cases.json`, `gold.json`: casos y etiquetas previas a las llamadas.
- Workflow `.github/workflows/igc-constraint-critic-min-v1.yml`: control sin IA y una ejecución real autorizada como segundo paso, con artefactos.
