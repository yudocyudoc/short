# IGC S2 — trabajo pendiente, preparación y entrega usando SystemDynamics

**Propósito:** prueba realmente distinta de S1. ¿Podemos modelar el flujo de pedidos *bajo pedido* reutilizando componentes `Level`, `Level1a`, `Rate_1` y `RRate`, sin programar integradores, balances ni topes de capacidad?

Este caso es **100 % sintético**, no tiene registros de clientes ni mediciones operativas. No usa los archivos Vensim de Hines.

## Pregunta práctica y límites

Una cocina recibe pedidos aceptados, los mantiene como **trabajo sin preparar**, los transforma en **pedidos preparados** a capacidad acotada y los **despacha**, acumulando **entregas completadas**. Se requieren tres estados distintos: sin preparar, preparados sin entregar y entregados. El caso S1 no tenía retroalimentación del trabajo sin preparar a la preparación; aquí sí.

En el escenario supuesto: 0–2 horas entran 6 pedidos/h, 2–4 horas sube a 16 pedidos/h y después de cuatro horas no entra ningún pedido nuevo. Capacidad de preparación 10/h, capacidad de entrega 8/h, tiempos de respuesta hipotéticos 0.5 h, stocks iniciales 0, simulación Euler 0–10 h con dt=0.25.

Comportamientos previstos, **sin usar números observados del negocio**:
- Si no queda trabajo sin preparar, la preparación es 0 (la tasa depende del backlog); un pedido que llega hoy no está «preparado» antes de existir.
- Una vez cerrada la aceptación, todavía pueden prepararse pedidos pendientes; preparación y despacho no dependen solamente de los pedidos que entran ahora.
- Los stocks no deben ser negativos, no debe excederse la capacidad instantánea, y la masa se conserva: aceptados acumulados = sin preparar + preparados + entregados.
- En las dos horas de pico la cola de preparación debe aumentar, y después de cortar llegadas debe disminuir.

## Estructuras reutilizadas, no inventadas

La versión `Components` conecta 6 clases preexistentes: **2 × `SystemDynamics.Levels.Level`**, **1 × `Level1a`**, **1 × `Rates.Rate_1`** y **2 × `Rates.RRate`** (restricción de máximos). Se especifican **5 conexiones de stock/flujo**. En esta versión **no se escribe ninguna ecuación diferencial de stocks**; los integradores y limitadores de tasas son de la biblioteca BSD 2.1.2.

Persisten elecciones de diseño que la biblioteca no resuelve: definir **qué significa cada stock**, interpretar aceptaciones como flujo de entrada real, elegir una política de preparación proporcional al trabajo por atender, y una política de despacho proporcional a los preparados, junto con límites y tiempos de respuesta. Son **supuestos propios de este escenario**, no hallazgos empíricos ni garantías de la biblioteca.

La versión `Equations` escribe explícitamente tres ecuaciones diferenciales y dos mínimos de capacidad con la misma política. Es una referencia independiente del cableado de componentes, no la metodología recomendada para generar modelos de negocio.

## Tres motores/representaciones cotejados

1. Python Euler independiente con balances y límites (`verify.py`). **No es PySD**: aquí no hay un equivalente Vensim que debamos portar.
2. OpenModelica 1.26.5 con ecuaciones `der()` (`IGCS2MakeToOrder.Equations`).
3. OpenModelica 1.26.5 con componentes `SystemDynamics` (`IGCS2MakeToOrder.Components`).

Se cotejan 41 tiempos × 6 variables (`acceptedRate`, `preparationRate`, `dispatchRate`, `unpreparedOrders`, `preparedOrders`, `deliveredOrders`) para los tres pares y **10 controles físicos/operacionales**. Tolerancia absoluta 1e-6; cualquier diferencia visible, anomalía de masa o divergencia de capacidades invalida el PASS.

La prueba también registra cuántas instancias de biblioteca se usaron y cuántas líneas de `der()` fue necesario escribir en cada variante. **No se mide tiempo de desarrollo ni facilidad subjetiva:** no inferir superioridad general de OpenModelica de ese conteo.

## Ejecución

`python -m unittest discover -s experiments/openmodelica-mto-s2 -p 'test_*.py' -v`

`python experiments/openmodelica-mto-s2/verify.py --reference-out experiments/openmodelica-mto-s2/output/independent_euler.csv`

GitHub Actions instala la **misma** imagen oficial OpenModelica `v1.26.5-minimal` y descarga etiquetas exactas `v4.0.0` de MSL y `v2.1.2` de SystemDynamics desde repositorios oficiales. La variable correcta es `OPENMODELICALIBRARY`. Ejecuta ambos modelos, almacena CSVs de resultados, y compara contra Euler independiente.

**Veredicto permitido:** `PASS` significa reproducibilidad numérica de los 3 enfoques y cumplimiento de invariantes para este escenario, no identificación de demanda real ni mejor estrategia operativa. Un error de instalación/compilación es bloqueo técnico; una divergencia de ecuaciones/datos es discrepancia, no ventaja de modelo.
