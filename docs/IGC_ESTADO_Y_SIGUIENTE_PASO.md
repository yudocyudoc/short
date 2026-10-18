# IGC · Estado y siguiente paso — P0 (borrador de continuidad)

```yaml
fecha_corte: 2026-10-18
hoja_rectoria: v5.1-PROPUESTA-PENDIENTE-DE-APROBACION
fase_actual: P2
estado_fase: P0_CERRADO_P1_EJECUTADO_P2_IR_CONCEPTUAL_EN_REVISION
repositorio_base: main
main_sha: 725b3f23193dde326886bc8d35ded538d645e902
pr_relevantes: [20, 32, 33, 34, 35, 36, 37, 38, 39, 40]
capacidades_implementadas:
  - moleculas_modelica_base_en_main
  - validador_cadenas_E0_en_PR33_draft
  - compositor_backend_E1_en_PR34_draft
  - ciclo_X1_ejecutado_PR37_no_repetir
  - limites_P1_probados_PR39
  - IR_conceptual_P2_PR40_NO_EJECUTABLE
capacidades_solo_documentadas:
  - IGC_SL_v0_1_PR20
  - IR_causal_y_politicas_generales
  - linter_redes_general_L0_L6
limites_confirmados:
  - cadena_material_unica
  - sin_CONTROL_feedback_dinamico_general
  - sin_verificacion_semantica_y_evidencia_por_relacion
experimento_actual_pregunta: "P2: distinguir bifurcación conservativa y clonación con IR tipado; feedback nativo sigue faltando"
que_lo_refutaria: "pasar clonacion, confundir entidades o CONTROL con materia, simular sin politica, o romper regresiones E1"
resultado_verificable: "P1 CI 39177612268: 6 limites, 11 regresiones E1; P2 CI 39178234331: IR conceptual con tests; NO Modelica nativo en P2"
revision_externa_pendiente: true
revision_diseno_p1: ADJUDICATED_WITH_LIMITS
revision_codigo_p2_pendiente: true
siguiente_accion_unica: auditar_independientemente_codigo_p2_y_definir_gate_conservacion_nativa
prohibiciones:
  - repetir_X1
  - reabrir_LLM_AST
  - empezar_ruido_antes_de_limites_estructurales
  - mezclar_PASS_tecnico_y_causal
```

**Corte:** 2026-10-18 · **Hoja rectora propuesta:** v5.1, **pendiente de aprobación**.  
**Estado actualizado:** P0 auditado; revisión del diseño P1 **adjudicada con limitaciones**; P1 ejecutado [#39](https://github.com/yudocyudoc/short/pull/39); núcleo IR de P2 implementado [#40](https://github.com/yudocyudoc/short/pull/40), pero **aún no ejecutable nativamente**. El PR #38 contiene exclusivamente documentación, mientras #39/#40 son ramas experimentales separadas. No hay merges.

## Inventario verificado en GitHub

| Artefacto | Ref / estado | Capacidad verificable y límite |
|---|---|---|
| `main` | `725b3f23193dde326886bc8d35ded538d645e902` (#32 fusionado) | `src/modelica/IGCMolecules.mo` (`AcceptedSource`, `BoundedQueue`, `DeliveryCounter`) y `IGCInformationMolecules.mo` (`FirstOrderReportFilter`). Son modelos existentes, no motor causal autónomo. |
| PR #20 | `9794c01f56f8be65fc8da16f9443eeabf4134beb`, cerrado, no fusionado | `docs/IGC-SL-grammar-v0.1.md`: diseño ATOM/MOLECULE/SYSTEM, `LINK/SENSE/GOVERN`, evidencia, política y estados parciales. **No es parser ni linter ejecutable.** |
| PR #33 | `d5a9512e69b8e1f59ae1ea13c0e6fdb8c9472e72`, abierto/draft | `experiments/e0/catalog.json` y `check_contract.py`: tipos simbólicos y validador de cadena física. |
| PR #34 | `97a9ad3a3e13d5b04d85340a0907994e41c13518`, abierto/draft, basado en #33 | `experiments/e1/composer.py`, `backend.py`, `registry.base.json`, `registry.extended.json`: seis y quince composiciones pequeñas con simulación real [CI 39104098853], veredicto **ingeniería**, no inferencia. |
| PR #35 | `9303d99d28808a8a5609d2cba8bdf49f4019dbca`, abierto/draft | IA-1 exigió AST al LLM; conservar como límite histórico, no repetir. |
| PR #36 | `2ac35864b7e98cd69f1f608865ad4c389fb7e46e`, abierto/draft | v4 documental, no fusionada. |
| PR #37 | `a4b467cb311ab69054bb967bafdfbe1ba3573d5b`, abierto/draft | X1 ya adjudicado: B 16.642, C 21.142 de arrepentimiento agregado; C no añadió valor; no repetir. |

**Hines/BSL:** el PR #20 documenta fuentes originales y diversos estados de verificación, **pero no demuestra que BSL esté importada y compilada como catálogo E1**. Licencias, fuente, conectores y versiones siguen siendo comprobaciones por pieza, no permisos generales. La extensión E1 `Modelica.Blocks.Math.Gain` es un componente MSL distinto de una molécula física nueva.

## Trazabilidad capacidad → evidencia → límite → pieza próxima

| Capacidad actual | Evidencia concreta | Límite para cafetería | Pieza próxima, aún NO implementada |
|---|---|---|---|
| Fuente, acumulación y salida física | `main:src/modelica/IGCMolecules.mo`; E0 #33 `catalog.json` | Un solo tipo de trayectoria material, sin divisiones conservativas | IR de entidades y split conservativo verificable; P1 primero |
| Composición y validación de cadenas | E1 #34 `composer.py:enumerate_material/check_graph`; CI #39104098853 | Un único sucesor físico por nodo; rechaza bifurcación legítima | Linter de redes L0–L3, sin relajar la conservación |
| Información separada del material | E1 #34 `enumerate_signal`; `IGCInformationMolecules.mo` | Una cadena de reporte; ninguna política `GOVERN` dinámica general | Distinción `SENSE` vs `CONTROL`, política con puerto de control verdadero |
| Tipos sintácticos y papeles por rol | E0 #33 y E1 #34 `registry.base.json` | Sin `CUSTOMER/ORDER/PRODUCT` y soporte de hipótesis exigido por vínculo | Subconjunto `SUPPORT/HYPOTHESIS/UNRESOLVED` de IGC-SL #20 |
| Fuente de moléculas externas | IGC-SL #20 documenta Hines/BSL/MSL; MSL y SystemDynamics en CI #34 | Licencias/procedencia/adaptadores BSL-Hines **no auditados por pieza en P0** | Matriz origen–licencia–interfaz–verificación OMC, **gate P3**, no P1 |

## Tres límites confirmados por inspección de código

1. **Red material limitada a cadena.** `composer.py:enumerate_material` y `check_graph` exigen sucesor físico único y camino `source → receipt`. Un split de clientes `atendidos + abandono` no se representa como bifurcación conservativa. El validador E0 impone grados análogos.
2. **Sin control/feedback tipado general.** `enumerate_signal` parte de un tap de tasa de recepción y construye una única cadena informacional. `backend.py` impone estímulos y observables de pedidos; el `maxThroughput` de `BoundedQueue` es parámetro, no entrada de política variable. `SENSE/GOVERN` permanecen documentales.
3. **Faltan IR causal/entidades y evidencia exigida.** E1 anota `FLOW<Order/ReadyOrder/Shipment>` y compara unidades por cadena literal; no vincula roles de `CUSTOMER`, `ORDER`, `PRODUCT` ni soportes `SUPPORT/HYPOTHESIS` por conexión. Un distractor formalmente compatible puede pasar como grafo válido sin justificar pertinencia causal; `NO_MATCHING_MOLECULE` no es salida estructurada de composición.

## Núcleo mínimo propuesto para cafetería (no admitido aún)

Tres mecanismos acoplables, sin cifras inventadas: **(A) llegadas y cola de personas** (stock `Waiting<Customer>`, frontera entrada), **(B) servicio con capacidad y una política de ajuste explícita** (salida `Served<Customer>/h`, capacidad, señal `CONTROL` distinta de flujo) y **(C) desistimiento/abandono** (salida `Left<Customer>/h`, cuya ley dependiente de espera se deja `POLICY_UNIMPLEMENTED` hasta verificarla). La bifurcación exige `arrivals = dWaiting/dt + served + left`, con balances y unidades coherentes. Un feedback opcional que mida cola y regule capacidad sólo se admite si el paquete de política tiene entrada y dinámica verificadas. No confundir personas, órdenes y porciones de pan.

**No se afirma que estas tres clases ya existan en Modelica.** Primero se definen contratos y pruebas de frontera; después P2 generaliza linter/IR y P3 admite moléculas ejecutables por verificación matemática/nativa.

## Paquete mínimo de P1: un positivo, tres negativos y una contraprueba semántica

**Ficha de una página:** [`docs/IGC_P1_FICHA_LIMITES_v0_1.md`](IGC_P1_FICHA_LIMITES_v0_1.md). Los cuatro casos iniciales se conservan; se añade el **control de transferencia legítima POS-02** para evitar que `NEG-02` premie un rechazo indiscriminado. Ninguno supone que exista ya una política Modelica ejecutable. La crítica externa señaló además que un parámetro constante **no** prueba feedback `CONTROL`; esto es un gate propio.

| ID | Caso | Resultado deseado; refutación de la ampliación |
|---|---|---|
| POS-01 | Una entrada de clientes alimenta una sola cola con dos salidas distintas `served` y `left`, sin crear personas. Una lectura de cola puede regular servicio sólo por política verificada. | IR acepta split de conservación y feedback bien tipado, o declara implementación pendiente **sin fingir ejecución**. Falla si sigue imponiendo un solo destino o clona entidades. |
| NEG-01 (físico) | Se envía el mismo flujo de personas completo a `served` y `left` sin fracciones/split conservativo. | Rechazo `MATERIAL_DUPLICATION` o equivalente. Falla si se acepta por coincidir unidades. |
| NEG-02 (semántico) | Una molécula de contagio/adopción de personas/h se propone para explicar abandono en fila sólo por compatibilidad de puertos. | `HYPOTHESIS/MISSING_EVIDENCE` o descarte justificado, sin prohibir una transferencia válida cuando existe mecanismo causal común. Falla si pasa sólo por tipo o es rechazada sólo por nombre de origen. |
| NEG-03 (política ausente) | Se pide que espera reduzca tasa de servicio o produzca abandono sin ley ni política implementada. | `POLICY_UNIMPLEMENTED`/`NO_MATCHING_MOLECULE` y abstención ejecutable. Falla si inventa ecuación o valor. |

**Nota:** las etiquetas de fallo son objetivos de interfaz propuestos, no códigos que ya entregue E1. La especificación #20 fundamenta la familia de diagnósticos; el parser/IR deberá versionarlos.

## Avance registrado después de la ficha P1

- **P0 / revisión de diseño:** [adjudicación P0/P1](https://github.com/yudocyudoc/short/blob/experiment/igc-v5-p1-limit-probes-v1/experiments/p1/ADJUDICACION_P0_P1.md). O1–O4 respondidas; revisión con segunda IA produjo hallazgo débil y **salida no JSON estricta**. No se confunde con auditoría del código nuevo.
- **P1 / resultado medido:** [PR #39](https://github.com/yudocyudoc/short/pull/39), [Actions #39177612268](https://github.com/yudocyudoc/short/actions/runs/39177612268). Positivo split y negativo clon rechazados igual por E1; prueba semántica puede pasar al cambiar solo descripción; entidad `Person` no basta para distinguir rol. **No Modelica nuevo**.
- **P2 / implementación acotada:** [PR #40](https://github.com/yudocyudoc/short/pull/40), [Actions #39178234331](https://github.com/yudocyudoc/short/actions/runs/39178234331). IR conceptual y linter admiten un stock de dos salidas como **estructura no ejecutable**, prohíben clonación, distinguen entidades y `SENSE/GOVERN` y reportan `POLICY_UNIMPLEMENTED`. **Faltan conservación numérica, política y red ejecutable.**
- **Pendiente**: auditoría de código independiente P2 y verificación de licencias e interfaces para P3; sin aprobación de merge ni promoción de ingeniería a inferencia.

## Siguiente acción ÚNICA

**Auditar por una segunda IA el código P2 en su estado actual y preparar un contraejemplo de conservación dinámica que el IR estructural acepte, sin crear aún una política Modelica no verificada.** Habilita una capacidad concreta: distinguir una **ramificación material legítima** de clonación y de coincidencia semántica falsa, conservando estados de insuficiencia.

**Presupuesto de esta acción:** una revisión independiente del código P2 actual, sin datos de mundo oculto; al menos un caso nuevo sobre conservación/feedback; máximo una ronda de corrección y dos iteraciones documentales. Si no se encuentra evidencia reproducible, registrar `INCONCLUSIVE`, no inventar un PASS.

**Puerta de salida:** revisión con ruta/línea, severidad y contraejemplo propio; regresiones E1/P1/P2 verdes; conservar `executable:false` hasta verificar Modelica y política real. **La revisión de diseño P1 está cerrada con reservas; la revisión de implementación P2 no está cerrada.**

## Hallazgos de revisión P0/P1 ya adjudicados para avanzar a pruebas

| Hallazgo | Severidad propuesta | Respuesta en diseño, no veredicto experimental |
|---|---|---|
| O1: `CONTROL` puede confundirse con parámetro estático | **Bloquea P2** | La ficha diferencia `SENSE → POLICY → CONTROL` dinámico de un `parameter maxThroughput`; exige rechazo `POLICY_UNIMPLEMENTED` cuando no hay política verificada. |
| O2: solo rechazo semántico, sin transferencia válida | **Bloquea selección semántica P4** | Control emparejado POS-02 admite reutilización legítima de una molécula si preserva mecanismo y evidencia; no se decide por etiqueta sectorial. |
| O3: custodio y aislamiento de gold sin asignar | **Bloquea campañas con mundos ocultos** | P1 usa veredictos esperados de *contrato* visibles y conserva cualquier mecanismo verdadero reservado fuera de revisora/constructor; el investigador designará custodio antes de ejecutar experimentos con gold. |
| O4: presupuesto temporal sin parada | **Bloquea cierre de P1** | Máximo una ronda de revisión, una respuesta por hallazgo y **dos iteraciones de ficha**; si no se cierra, `BLOCKED` y elevar al investigador. No hay plazo de horas inventado. |

**Pendientes de progresión:** licencias/procedencia por pieza Hines/BSL/MSL (**bloquea admisión P3**), revisión independiente del código P2 (**bloquea considerar P2 terminado**) y aprobación formal de v5.1/D1–D7. Las objeciones O1–O4 ya se adjudicaron para diseño P1; no certifican el código nuevo.

**Decisiones pendientes de aprobación:** v5.1 rectora, decisiones D1–D7 y cualquier merge. Se abrieron ramas experimentales separadas #39 y #40, **sin fusionarlas**; el PR #38 sigue siendo exclusivamente documental.
