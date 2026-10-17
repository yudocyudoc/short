# IGC — 24 casos nuevos, tres enfoques congelados: primera evaluación real

**Fecha:** 2026-10-16 (México) / 2026-10-17 (UTC).

- **[GitHub Actions real #38992494847](https://github.com/yudocyudoc/short/actions/runs/38992494847)**: 48 solicitudes recibidas; jobs deterministic y real-llm concluyeron SUCCESS.
- **[Artefactos íntegros de 48 respuestas, 48 solicitudes, manifiesto y evaluación](https://github.com/yudocyudoc/short/actions/runs/38992494847/artifacts/12085433836)**.
- **[Baseline y prompts preparados en la misma ejecución](https://github.com/yudocyudoc/short/actions/runs/38992494847/artifacts/12084739981)**.
- Revisión de integridad PR: [#38992458667](https://github.com/yudocyudoc/short/actions/runs/38992458667): ocho tests PASS.

## Qué está congelado

Los cuatro archivos de PR #21 se compararon por huella Git *antes* de toda ejecución: `deterministic.py`, `evaluate.py`, `run_llm.py`, `catalog_public.json`. El baseline de palabras clave, los prompts cualitativo SD y molecular, el evaluador y el catálogo de cuatro mecanismos no fueron modificados. Se redactaron 24 casos N01–N24 y la clave de respaldo textual, y se guardaron **antes de hacer consultas al modelo**. Se alternó el orden B/C por caso. Llama 3.3 70B Cloudflare, temperatura 0, 1 intento por par caso/brazo, sin reintentos ni correcciones de respuestas. Nunca se dieron valores numéricos ni se pidieron ecuaciones o código Modelica.

**Importante:** los 24 casos son nuevos respecto del piloto anterior y prueban cierta transferencia léxica y causal, pero los redactó el mismo asistente que elaboró las etiquetas: **no constituyen un conjunto independiente, ciego, creado por un evaluador externo**.

## Resultado agregado

| Brazo | Exact selection | Citas textuales válidas | Citas con hechos preregistrados que respaldan la selección | Strict pass | Moléculas sin respaldo | Abstenciones falsas |
|---|---:|---:|---:|---:|---:|---:|
| A: regex congelado | 10/24 | 24/24 | 24/24 | **10/24** | 0 | 13 |
| B: Llama SD general | 16/24 | 23/24 | 16/24 | **15/24** | 7 | 1 |
| C: Llama moléculas tipadas | 18/24 | 24/24 | 19/24 | **18/24** | 5 | 1 |

El baseline A tenía 12/12 en los casos originales; aquí cayó a 10/24 sin cambio de reglas. Su ausencia de falsos positivos procede en parte de **abstenerse excesivamente (13 casos con mecanismo respaldado que perdió)**, no de identificar todos los mecanismos.

**Comparación pareada B vs C, métrica strict pass:** C corrige **cuatro** casos que B falla (`N02`, `N09`, `N10`, `N17`); B corrige **uno** que C falla (`N24`). Discordantes = 5; diferencia neta C−B = **+3 de 24**. Prueba exacta McNemar bilateral descriptiva **p=0.375**. No permite inferir superioridad poblacional con significación convencional; datos artificiales y baja potencia para diferencias moderadas.

## Lectura de originales caso por caso

- **N02 (cámaras por encargo):** B añadió `BACKLOG_FLOW` a `MTO_S2_PATTERN`, duplicando semánticamente el stock de órdenes entregables; C seleccionó sólo MTO, con tres citas pertinentes.
- **N09 (plan de mezclas):** B se abstuvo por ausencia de inventario o pedidos; C seleccionó adecuadamente `CAP_UTIL` a partir del control deseado/capacidad, sin requerir backlog.
- **N10 (piezas listas por surtir):** ambos seleccionaron `BACKLOG_FLOW`. B falló por una cita que no era substring literal exacto; C citó correctamente stock, pedidos por surtir y despachos. Esto es principalmente **fidelidad de extracción de cita**, no diferencia de selección causal.
- **N17 (semillas en tránsito con inventario):** B añadió indebidamente MTO a `MATERIAL_DELAY + BACKLOG_FLOW`; C evitó inferir preparación a partir de despacho.
- **N24 (tránsito físico hacia comprador):** B identificó `MATERIAL_DELAY` con cita adecuada, C se abstuvo por falta de datos sobre inventario y fabricación **no requeridos** para representar el tránsito físico. El andamiaje fue excesivamente conservador.
- **N04 (contratación de personal):** B eligió retardo de material y C MTO, aunque el evento era contratación de personas. Ambos trataron términos de espera como mecanismos físicos o de trabajo por pedido.
- **N06 (capacidad de salas clínicas)** y **N21 (plantilla como capacidad):** ambos eligieron incorrectamente `CAP_UTIL` por semejanza verbal con «capacidad», sin evidencia de capacidad productiva de una planta vs producción deseada.
- **N11 (taller sin segunda acumulación):** ambos eligieron `MTO_S2_PATTERN` pese a que el relato niega explícitamente stock de trabajos preparados esperando despacho.
- **N15 (juguetes bajo pedido):** ambos eligieron `MTO_S2_PATTERN + BACKLOG_FLOW` cuando sólo estaba respaldada la cadena MTO; la existencia de un stock de preparados dentro de MTO no autoriza añadir toda la molécula de inventario terminado/órdenes de envío.

## Qué sí y qué no demuestra

**Sí:** el enriquecimiento con contratos moleculares mejoró descriptivamente la selección estricta de Llama frente al SD general en la misma muestra de 24 casos nuevos, usando código y prompts congelados; el baseline simple falló en sinónimos y descripciones alejadas de sus regex; las citas literales y las etiquetas humanas permiten localizar errores distintos de semántica.

**No:** superioridad estadística general, clasificación causal fiable en empresas reales, composición de puertos de Modelica, corrección de dinámica, calibración, identificación de variables latentes, capacidad autónoma de construir modelos ni valor económico de IGC. No se corrió OpenModelica en esta etapa. La validación de citas literales es condición de trazabilidad pero no de verdad causal.

## Próxima decisión metodológica

Evitar adaptar los prompts a N01–N24 o repetirlos hasta obtener mejor nota. Antes de crear un parser completo de IGC-SL, probar un conjunto **externo o independientemente anotado** con énfasis en contraejemplos difíciles: personal/capacidad, administrativos/materiales, dos colas MTO vs backlog shipping y el acto de abstenerse cuando sólo hay parte de la estructura. Añadir comparación pareada con intervalos de incertidumbre y un operador de observabilidad si se dispone de un dataset; preservar un baseline determinista transparente. No combinar p-valores de pilotos diseñados por el mismo equipo como si fueran evidencia confirmatoria.

**Referencia del estudio previo:** [PR #21](https://github.com/yudocyudoc/short/pull/21) produjo 9/12 para SD general, 11/12 molecular y 12/12 baseline en casos escritos junto a las reglas. Este nuevo resultado no cambia ni reetiqueta los resultados históricos.
