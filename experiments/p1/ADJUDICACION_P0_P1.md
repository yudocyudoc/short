# IGC v5.1 · P1 — Adjudicación y revisión adversativa

**Corte:** 2026-10-18. **Alcance:** P0/P1; no se modificó el linter E1 ni se admitieron clases Modelica nuevas. **Hoja v5.1 no sustituida.** PR #38 mantiene la ficha y estado; esta rama parte del PR #34 para ejecutar sondas sobre código real.

## Auditoría independiente: insumos originales y respuesta

1. **Observaciones independientes O1–O4 proporcionadas al investigador**, recibidas antes de construir las sondas. O1: `CONTROL` real frente a parámetro fijo; O2: incluir transferencia legítima; O3: custodio/aislamiento de gold; O4: condición temporal de parada. Las cuatro se incorporaron al paquete conceptual P1 en [PR #38](https://github.com/yudocyudoc/short/pull/38).
2. **Segunda IA:** Llama 3.3 70B ejecutada una vez con [entrada sin gold](review_input_no_gold.json), independiente de los casos numéricos; [Actions #39177394513](https://github.com/yudocyudoc/short/actions/runs/39177394513), [texto original y request](https://github.com/yudocyudoc/short/actions/runs/39177394513/artifacts/12154896948). Su respuesta **no pasó JSON estricto**: JSON inicial más una nota adicional fuera del objeto. El original se conserva; la CI del formato es **FAIL**. No repetir llamadas para obtener aprobación.
3. El objeto inicial del revisor tenía veredicto `REPAIR_BRIEF`, un hallazgo R1, y propuso como contraejemplo propio una cadena de inventarios multiproducto/proveedores con política de reposición omitida. Es una idea genuinamente distinta de Q1–Q5, pero **demasiado amplia y sin un falsador pequeño** para ser prueba P1; queda como candidato a un límite futuro, no supuesto resuelto.

### Adjudicación localizada de las objeciones

| ID | Objeción | Severidad para P1 | Decisión verificable |
|---|---|---|---|
| O1 | Parámetro fijo puede disfrazar política dinámica | BLOQUEABA | **Resuelto en contrato P1:** ninguna política se ejecuta; la falta de `CONTROL` queda evidenciada en NEG-03. Pendiente implementar política nativa para gate ejecutable posterior |
| O2 | Falta positivo de transferencia semántica | BLOQUEABA | **Resuelto en diseño P1:** POS-02 conserva transferencia condicional, sin afirmar que se puede compilar hoy |
| O3 | Custodio de gold no designado | NO BLOQUEA P1 SIN MUNDOS | Los casos P1 son contratos estructurales públicos, sin verdad de mundo; **bloquea P5** hasta asignar custodio |
| O4 | Sin límite temporal/parada | BLOQUEABA | Ficha P1 define una ronda de revisión, dos iteraciones de documento y siete días; al exceder, BLOCKED |
| R1 (segunda IA) | Exigir inmediatamente ley de abandono | NO BLOQUEA P1 | **Rechazada como instrucción técnica**: P1 debe reconocer `POLICY_UNIMPLEMENTED`; inventar la ley antes de medir el límite anularía NEG-03. Podrá ser gate P3 con mecanismo justificado |
| R2 (segunda IA) | Inventario con varios productos y proveedores | FUERA DE P1 | Conservar como pista para expansión heterogénea futura, sin forzar vocabulario nuevo ahora |

**Cierre administrativo de la revisión del diseño P1:** `ADJUDICATED_WITH_LIMITS`. Las objeciones O1–O4 fueron respondidas con evidencias y estados diferenciados; la salida de segunda IA tuvo fallo de formato y poca especificidad, por lo que **no se presenta como auditoría de código completa ni firma científica**. La revisión independiente del **código nuevo de P2** sigue pendiente por separado.

## Primera campaña P1: frontera observada contra E1 SIN MODIFICACIONES

[GitHub Actions #39177612268](https://github.com/yudocyudoc/short/actions/runs/39177612268) · [fuente reproducible](probe_limits.py) · [resultados crudos](https://github.com/yudocyudoc/short/actions/runs/39177612268/artifacts).

**Regresión E1: 11/11 tests PASS.** Se construyeron seis sondas descriptivas **en memoria**. Las moléculas sintéticas no son clases Modelica admitidas y **no se ha simulado** una cafetería.

| Sonda | Resultado del código actual | Significado limitado |
|---|---|---|
| POS-01: dos salidas independientes desde un stock | `ValueError:MATERIAL_MULTICAST` | **Falso rechazo estructural** por camino único; aun si lo admitiese faltarían ley de abandono y parámetros |
| NEG-01: misma tasa duplicada | `ValueError:MATERIAL_MULTICAST` | Rechazo válido de este clon concreto, **diagnóstico incapaz de distinguirlo del anterior** |
| NEG-02: cambiar semántica declarada conservando los puertos | `ACCEPTED` | El linter ignora la descripción de mecanismo; **no demuestra** que un selector IA elegiría contagio |
| NEG-03: política dinámica desconocida | sin `CONTROL`; sin estado semántico de abstención | Ausencia de representación y diagnóstico, no un PASS de abstención |
| POS-02: reutilizar `BoundedQueue` para `Customer` | `ROLE_NOT_SUPPORTED:customer` | No hay binding/modelo nativo verificado; **no prueba** que la transferencia sea imposible |
| NEG-04 (suplemento del implementador): `Person/h` con dominio cliente vs empleado | `ACCEPTED` | Tipos generales y unidades iguales no verifican identidad semántica. Es un contraejemplo añadido por el implementador, **no por la IA revisora** |

## Veredicto y única siguiente acción

- `P0_AUDIT_CONFIRMED` para inventario/limitaciones; licencias Hines/BSL aún sin gate, **bloquea admisión de terceros P3, no P1**.
- `P1_LIMITS_CONFIRMED` para la necesidad de abandonar la regla de camino único e introducir diagnóstico semántico específico.
- `P1_EXPERIMENT_EXECUTED`; **ninguna capacidad P2 fue validada** y ningún modelo causal fue identificado.
- `P2_IMPLEMENTATION_PENDING`; para iniciar P2, usar sólo el subconjunto tipado `LINK/SENSE/GOVERN/SUPPORT/HYPOTHESIS/UNRESOLVED` de PR #20 y los contraejemplos anteriores.

**Siguiente acción única:** implementar un **IR tipado/linter de redes mínimo** en rama aislada, que acepte POS-01 sólo como estructura, rechace NEG-01, exija evidencia en NEG-02, no sobre-rechace POS-02, distinga entidades en NEG-04 y devuelva `POLICY_UNIMPLEMENTED` en NEG-03; nunca generar leyes o puertos numéricos faltantes. Conservar 11 regresiones E1. Tras implementar, nueva **auditoría de código independiente**, no asumir que la revisión del diseño equivale a verificación técnica.

**No realizados:** merge, cambio de hoja v5.1, P3/P4/P5, ruido, validación de cafetería real, ejecución Modelica de nuevas redes o política dinámica.
