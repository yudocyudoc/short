# IGC · Prueba mínima de exploración restringida y crítico causal

**Fecha de ejecución:** 2026-10-17 UTC (2026-10-17, México). **Estado:** experimento técnico terminado, observación 4/4 en cuatro casos sintéticos propios. **No es una validación científica generalizable**.

## 1. Ejecución y artefactos

- [GitHub Actions #39009750448 — control sin LLM](https://github.com/yudocyudoc/short/actions/runs/39009750448): aprobado.
- [GitHub Actions #39009811701 — ejecución real con Llama](https://github.com/yudocyudoc/short/actions/runs/39009811701): aprobado, **12 tests PASS**, cuatro llamadas reales al crítico.
- [Artefacto completo de OM, solicitudes y respuestas originales #12091854880](https://github.com/yudocyudoc/short/actions/runs/39009811701/artifacts/12091854880).

## 2. Motor sin LLM

Usando el catálogo del PR #26, el enumerador generó **exactamente dos** arquitecturas completas y tipadas:

- `MTO`: `ORDER_SOURCE → MTO → DELIVERY` (`IGCS2MakeToOrder.Components`);
- `MTS`: `ORDER_SOURCE → MTS → DELIVERY` (`IGCS1Parity.Components`).

Las firmas de puerto son equivalentes; **unificación de tipos sola conserva MTO y MTS** en todos los casos.

OpenModelica 1.26.5 ejecutó las dos arquitecturas bajo la intervención contrafactual *sin pedidos nuevos*. La prueba `POLICY_BEHAVIOR_DISCRIMINATION` terminó **PASS**. Las firmas se derivaron de CSV numéricos reales, no se inventaron:

- **MTO → STOPS**: sin nuevos pedidos ni colas iniciales, no prepara ni despacha.
- **MTS → CONTINUES**: fabrica a partir de plan exógeno y acumula inventario terminado pese a ausencia de pedidos.

Sólo las etiquetas cualitativas de firma se incluyeron en el prompt; el LLM no recibió capacidad, paso de integración, series numéricas ni ecuaciones.

## 3. Llama como crítico, no como generador

En cada caso, el crítico recibió: descripción con hechos identificados F1, F2, F3; las dos arquitecturas enumeradas por la máquina; contratos/exclusiones; comportamiento cualitativo medido. Únicamente respondió con `expected ∈ {STOPS, CONTINUES, UNKNOWN, CONFLICT}`, `fact_ids` y, cuando corresponde, `next_question`.

El linter comprobó que el formato y los identificadores existieran y que el ensayo solicitado estuviera registrado. **No verificó la implicación semántica de los hechos**. El motor sólo aplica una poda condicional a la expectativa propuesta por el crítico, comparándola con resultados realmente simulados.

| Caso | Expectativa esperada previamente | Llama | Candidatos conservados |
|---|---|---|---|
| R01: fabrican sólo por encargo | STOPS | STOPS | MTO |
| R02: plan de producción anticipada | CONTINUES | CONTINUES | MTS |
| R03: sólo tickets de ventas | UNKNOWN | UNKNOWN | MTO, MTS |
| R04: manuales incompatibles | CONFLICT | CONFLICT | MTO, MTS |

**Coincidencia 4/4** con cuatro claves sintéticas propias. Las cuatro respuestas superaron el esquema estricto. No fue necesario reparar JSON ni fabricar citas literales; Llama sólo referenció IDs de hechos.

## 4. Qué sí se demostró

- Un motor convencional enumera opciones estructurales tipadas y no pide a Llama construirlas.
- OpenModelica calcula firmas de comportamiento discriminantes para dos políticas realmente distintas.
- El crítico puede proponer una restricción cualitativa sobre el resultado del ensayo usando sólo los hechos.
- El motor aplica esas restricciones a los resultados simulados sin permitir que el LLM modifique ecuaciones.
- La ausencia de hechos y las contradicciones **mantienen abiertas** ambas hipótesis, en lugar de forzar una respuesta.
- La auditoría de entradas y salidas es reproducible mediante GitHub Actions y sus artefactos.

## 5. Qué NO se demostró

- No tenemos cientos de configuraciones: sólo **dos arquitecturas completas**; la enumeración crece cuando incorporemos contratos ejecutables de mecanismos realmente combinables.
- No son cuatro observaciones empíricas independientes: todos los textos y etiquetas los creó el equipo. El 4/4 es una prueba de integración, no una medida de confiabilidad causal poblacional.
- El linter no puede demostrar que F1 respalde `STOPS` ni que dos hechos sean contradictorios sin anotación externa. La eliminación de MTS en R01 es **condicionada al juicio del crítico**, no una verdad deducida formalmente de la prosa.
- No es CEGIS formal: falta garantía de contraejemplos verdaderos, cobertura de restricciones y criterios de terminación probados.
- No validamos las arquitecturas con observaciones de una empresa real ni que representen adecuadamente su campo.
- El crítico vio las firmas cualitativas de ambas alternativas. No sería una evaluación ciega ni una prueba de descubrimiento de comportamientos.

## 6. Decisión de diseño

Este experimento ofrece un motivo práctico para continuar con la inversión de roles: **generador/linter/simulador deterministas como núcleo; Llama como crítico y proponente de restricciones o preguntas discriminantes**.

Siguiente paso pequeño recomendado: separar un mecanismo interno nuevo en componentes combinables (no sólo S1/S2 como macros) e incorporar un segundo ensayo contrafactual independiente. Probar que **dos grafos tipados distintos pueden sobrevivir el primer ensayo, pero divergen en el segundo**. La fuente de apoyo causal debe seguir separada de la simulación de modelo.

Mantener el PR en borrador; no declarar superioridad sobre modelos de lenguaje generadores ni replicación de resultados.
