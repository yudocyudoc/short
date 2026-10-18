# IGC · Estado y siguiente paso — P0 (borrador de continuidad)

**Corte:** 2026-10-18 · **Hoja rectora propuesta:** v5.1, **pendiente de aprobación**.  
**Estado:** auditoría documental y estática de código completada; **revisión independiente pendiente**. No se abrió PR ni se modificó el repositorio.

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

## Tres límites confirmados por inspección de código

1. **Red material limitada a cadena.** `composer.py:enumerate_material` y `check_graph` exigen sucesor físico único y camino `source → receipt`. Un split de clientes `atendidos + abandono` no se representa como bifurcación conservativa. El validador E0 impone grados análogos.
2. **Sin control/feedback tipado general.** `enumerate_signal` parte de un tap de tasa de recepción y construye una única cadena informacional. `backend.py` impone estímulos y observables de pedidos; el `maxThroughput` de `BoundedQueue` es parámetro, no entrada de política variable. `SENSE/GOVERN` permanecen documentales.
3. **Faltan IR causal/entidades y evidencia exigida.** E1 anota `FLOW<Order/ReadyOrder/Shipment>` y compara unidades por cadena literal; no vincula roles de `CUSTOMER`, `ORDER`, `PRODUCT` ni soportes `SUPPORT/HYPOTHESIS` por conexión. Un distractor formalmente compatible puede pasar como grafo válido sin justificar pertinencia causal; `NO_MATCHING_MOLECULE` no es salida estructurada de composición.

## Núcleo mínimo propuesto para cafetería (no admitido aún)

Tres mecanismos acoplables, sin cifras inventadas: **(A) llegadas y cola de personas** (stock `Waiting<Customer>`, frontera entrada), **(B) servicio con capacidad y una política de ajuste explícita** (salida `Served<Customer>/h`, capacidad, señal `CONTROL` distinta de flujo) y **(C) desistimiento/abandono** (salida `Left<Customer>/h`, cuya ley dependiente de espera se deja `POLICY_UNIMPLEMENTED` hasta verificarla). La bifurcación exige `arrivals = dWaiting/dt + served + left`, con balances y unidades coherentes. Un feedback opcional que mida cola y regule capacidad sólo se admite si el paquete de política tiene entrada y dinámica verificadas. No confundir personas, órdenes y porciones de pan.

**No se afirma que estas tres clases ya existan en Modelica.** Primero se definen contratos y pruebas de frontera; después P2 generaliza linter/IR y P3 admite moléculas ejecutables por verificación matemática/nativa.

## Paquete mínimo de P1: un positivo y tres negativos

| ID | Caso | Resultado deseado; refutación de la ampliación |
|---|---|---|
| POS-01 | Una entrada de clientes alimenta una sola cola con dos salidas distintas `served` y `left`, sin crear personas. Una lectura de cola puede regular servicio sólo por política verificada. | IR acepta split de conservación y feedback bien tipado, o declara implementación pendiente **sin fingir ejecución**. Falla si sigue imponiendo un solo destino o clona entidades. |
| NEG-01 (físico) | Se envía el mismo flujo de personas completo a `served` y `left` sin fracciones/split conservativo. | Rechazo `MATERIAL_DUPLICATION` o equivalente. Falla si se acepta por coincidir unidades. |
| NEG-02 (semántico) | Una molécula de contagio/adopción de personas/h se propone para explicar abandono en fila sólo por compatibilidad de puertos. | `HYPOTHESIS/MISSING_EVIDENCE` o descarte justificado, sin prohibir una transferencia válida cuando existe mecanismo causal común. Falla si pasa sólo por tipo o es rechazada sólo por nombre de origen. |
| NEG-03 (política ausente) | Se pide que espera reduzca tasa de servicio o produzca abandono sin ley ni política implementada. | `POLICY_UNIMPLEMENTED`/`NO_MATCHING_MOLECULE` y abstención ejecutable. Falla si inventa ecuación o valor. |

**Nota:** las etiquetas de fallo son objetivos de interfaz propuestos, no códigos que ya entregue E1. La especificación #20 fundamenta la familia de diagnósticos; el parser/IR deberá versionarlos.

## Siguiente acción ÚNICA

**Preparar la ficha P1 de límites, con los cuatro fixtures tipados y un paquete de crítica independiente sin gold; obtener la revisión antes de codificar P2/P3 ni abrir un PR nuevo.** Habilita una capacidad concreta: distinguir una **ramificación material legítima** de clonación y de coincidencia semántica falsa, conservando estados de insuficiencia.

**Costo/presupuesto:** una ficha de máximo una página, cuatro casos deterministas, ninguna llamada de LLM a Modelica, cero nuevas moléculas admitidas hasta superar el gate; reutilizar las CI E0/E1 como regresión. Revisión independiente adicional: una pasada adversativa, con objeciones localizadas y severidad. No hay aquí estimación monetaria verificada ni horas de desarrollo comprometidas.

**Puerta de salida:** revisor independiente examina los cuatro casos y propone al menos un contraejemplo propio; los requisitos quedan refinados sin fugas; los tests diseñados pueden fallar de verdad ante una regla actual demasiado estricta o demasiado laxa; se presenta al investigador una única modificación mínima de IR/linter que no rompa E0/E1. Si no aparece una nueva frontera falsable, **DETENER** sin codificar. **Revisión externa: PENDIENTE**; este documento no la simula.

**Riesgos:** ampliar tipos sin semántica, confundir contrato declarativo con clase admitida, diseñar negativos tautológicos, mezclar políticas con flujos, evitar la abstención y abrir demasiado el catálogo. Mitigaciones: negativos no filtrados, procedencia, invariantes, no gold para revisora, controles de regresión.

**Decisiones pendientes de aprobación:** aceptar v5.1 como rectora y cualquier posterior merge/cambio material de PR. Ninguno se ejecutó al elaborar este registro.
