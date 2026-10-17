# IGC — Resultados del primer ciclo molecular Llama → OpenModelica

**Fecha:** 2026-10-16 (México), ejecuciones del 17 de octubre UTC. **Veredicto:** PASS técnico en escenario sintético S2. **No** es descubrimiento de modelos generales ni validación de empresa real.

## Lo que efectivamente se construyó

El LLM recibe sólo una narración cualitativa y un catálogo de roles moleculares tipados; nunca recibe cifras operativas ni ecuaciones. Produce un AST declarativo con instancias, puertos y citas literales. El compositor admite conectores/instancias registradas y genera Modelica exclusivamente mediante plantillas confiables. OpenModelica resuelve las ecuaciones **ya definidas** en SystemDynamics 2.1.2, MSL 4.0.0 y los wrappers IGC; los parámetros cuantitativos provienen del escenario S2 que el LLM no ve.

Las tres clases moleculares IGC son AcceptedSource, BoundedQueue (reutilizada dos veces) y DeliveryCounter. Los cuatro roles son fuente de pedidos aceptados, cola de preparación, cola de pedidos preparados esperando despacho y entregas acumuladas. Son **wrappers propios**, no moléculas originales importadas de Hines o BSL. El catálogo v1 únicamente admite esta topología de cuatro roles, por lo que no prueba descubrimiento abierto.

## Control independiente de la IA

GitHub Actions [#38997637947](https://github.com/yudocyudoc/short/actions/runs/38997637947): 14 tests PASS, compilación y simulación del grafo humano PASS, igualdad exacta con el S2 preexistente a lo largo de 41 puntos y seis variables (error máximo 0), todos los invariantes dinámicos PASS. Este control **no** cuenta como acierto de Llama.

## Primera corrida Llama: fallo de formato del orquestador

[Run original #38997693854](https://github.com/yudocyudoc/short/actions/runs/38997693854), [archivo de cinco respuestas originales](https://github.com/yudocyudoc/short/actions/runs/38997693854/artifacts/12087153159). Llama devolvió cinco veces el mismo JSON de arquitectura íntegro, rodeado de un único bloque de código Markdown JSON. Los cinco outputs tienen SHA-256 231ee808fdb72dff8ba643bb8de58716a77ba5d49e90c4059950f46342ee44ee.

El primer lector Python esperaba JSON puro, así que produjo cinco JSONDecodeError. **Ninguna propuesta de Llama se ejecutó en esa primera corrida.** El workflow terminaba con status SUCCESS aunque el experimento decía NO_VALID_EXECUTED_DESIGN_IN_BUDGET; también se corrigió esa discrepancia de señalización.

## Reproducción del mismo archivo sin nueva inferencia

Se implementó un parser limitado a JSON puro o JSON envuelto en **un único** bloque Markdown JSON. No repara conexiones, hechos ni contenidos JSON. El workflow [#38998020947](https://github.com/yudocyudoc/short/actions/runs/38998020947) descargó exactamente la respuesta original del archivo del primer run, verificó SHA-256, comprobó tipos y citas y ejecutó el Modelica renderizado. **Cero llamadas nuevas a Llama.**

Resultado del original recuperado: STRUCTURALLY_VALID, 4 roles, 3 conexiones materiales justificadas, sin errores, OpenModelica PASS, 41 muestras, seis series idénticas a S2 (error máximo 0), todos los invariantes aprobados. Frente a la referencia independiente Euler, diferencia máxima aproximadamente 1.76e-8, dentro del límite 1e-6.

## Ejecución real prospectiva con orquestador corregido: PASS

[Run #38998095455](https://github.com/yudocyudoc/short/actions/runs/38998095455), [artefacto íntegro con la respuesta real, modelos, series y diagnósticos](https://github.com/yudocyudoc/short/actions/runs/38998095455/artifacts/12088455028). Las 15 pruebas estructurales pasan. Una inferencia real nueva de Llama produjo la misma estructura; el compositor devolvió STRUCTURALLY_VALID y OpenModelica COMPILED_SIMULATED_PARITY_PASS. El manifiesto registra PASS_SYNTHETIC_MOLECULAR_DESIGN_LOOP y accepted_attempt=1. No hubo reintentos.

| Métrica | Resultado |
|---|---|
| Propuestas necesarias | **1 de un máximo de 5** |
| Moleculas seleccionadas | 4 roles, 3 clases Modelica moleculares |
| Conexiones materiales | 3, sin incidencias de puertos |
| Ecuaciones escritas por el LLM | **0** |
| Compilación y simulación OpenModelica | **PASS** |
| Paridad con S2 preexistente | **error máximo 0** |
| Invariantes de escenario S2 | **PASS** |
| Reparaciones observadas Llama → feedback → Llama | **0: no hicieron falta** |

## Límites y siguiente experimento

Este es el primer acoplamiento completo **real y auditable** desde una propuesta molecular auténtica de Llama hasta simulación y contraste. No demuestra que Llama construya libremente otros sistemas. Los cuatro roles ofrecidos y la cadena aceptada ya estaban acotados por un contrato cerrado; las citas literales no certifican verdad causal ni se usaron datos de una empresa real.

El ciclo de diagnóstico existe para errores de esquema, citas y puertos, pero **no se probó reparación con un error real de la propuesta**: acertó en el primer intento. No presentar los cinco JSON iguales del primer run como cinco reparaciones, porque todos quedaron bloqueados en el parser.

**Siguiente prueba más informativa:** ampliar sólo con una segunda topología/mecanismo realmente ejecutable, presentar una situación cuya estructura no sea obvia y observar una reparación genuina de conexiones o una abstención justificada. No hace falta un nuevo benchmark ciego de clasificación en este paso.

**Conclusión:** el plano de Llama ya puede pasar a OpenModelica sin que el LLM genere ecuaciones. El alcance es deliberadamente reducido y la investigación sobre composición/selección causal abierta continúa.
