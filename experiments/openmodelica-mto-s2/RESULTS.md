# Resultado S2 — composición *make-to-order* mediante componentes existentes

**Estado: PASS** (primer resultado verde reproducible). Se conserva la evidencia íntegra en [GitHub Actions #38857429074](https://github.com/yudocyudoc/short/actions/runs/38857429074), artefacto [12027667533](https://github.com/yudocyudoc/short/actions/runs/38857429074/artifacts/12027667533). GitHub workflow `igc-openmodelica-mto-s2.yml`. Commit ejecutado `467c7b6dfba0e3da0a3531474332d50b0fe6b240`.

## Datos del ensayo

**Sintético, no calibrado.** Pedidos aceptados = 6/h (0–2 h), 16/h (2–4 h), 0/h (4–10 h). Capacidad de preparar = 10/h; entregar = 8/h. Respuesta proporcional: tasa solicitada = stock / 0.5 h. Ningún pedido se prepara antes de estar en backlog. Euler explícito dt=0.25, 41 instantes, 44 pedidos hipotéticos aceptados en total.

## Números cotejados contra el oráculo Euler independiente

| Comparación | Error absoluto máximo en seis variables | Veredicto |
|---|---:|---|
| Python Euler vs OMC ecuaciones | 1.759843826e-8 | PASS |
| Python Euler vs OMC componentes SystemDynamics | 1.759843826e-8 | PASS |
| OMC ecuaciones vs OMC componentes | **0.0** | PASS |

Tolerancia predeclarada 1e-6, revisión puntual de todos los 41 tiempos para `acceptedRate`, `preparationRate`, `dispatchRate`, `unpreparedOrders`, `preparedOrders` y `deliveredOrders`. Se verificaron **10 invariantes por cada una de las tres series**; todos aprobados. El mayor error de balance de stocks en Modelica fue 8.803922924e-9, y en la referencia Python 0.

**Nota de registros:** OpenModelica emitió 46 filas, incluyendo duplicados de evento justo a las horas 2, 4 y 10. `verify.py` conserva los CSV brutos y utiliza, exclusivamente en esas horas autorizadas, el último valor (estado posterior al evento) al obtener la malla de 41 tiempos. No interpola ni modifica valores. El listado de eventos adicionales consta en los logs del run.

### Interpretación temporal (referencia independiente)

| Hora | Trabajo sin preparar | Preparados sin entregar | Entregados |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 2 | 2.988281 | 2.894531 | 6.117188 |
| 3 | 9.994141 | 4.985352 | 13.020508 |
| 4 (fin de nuevas aceptaciones) | 15.994141 | 6.985352 | 21.020508 |
| 6 | 0.436768 | 6.542725 | 37.020508 |
| 10 | 0.000006665 | 0.000268493 | 43.999724843 |

Todo es resultado de **supuestos**. El backlog persiste y la preparación continúa cuando cesan llegadas; luego disminuye. La producción es cero cuando el trabajo por preparar es cero. No representa observaciones de tiempos de espera ni pedidos perdidos.

## Reutilización comprobada y límites

- Reutilizados desde la biblioteca BSD `SystemDynamics 2.1.2`: **2 `Levels.Level`, 1 `Levels.Level1a`, 1 `Rates.Rate_1`, 2 `Rates.RRate`**.
- Cinco enlaces estructurales mediante `connect()`.
- **Cero** `der()` personalizados en `Components`, **tres** en `Equations`. El acumulador y los límites de tasa provienen de bloques ya existentes.
- **No reutilizados:** interpretación de estados, perfil exógeno de aceptaciones, reglas de preparación y despacho proporcionales al stock, tiempos de respuesta y límites de capacidad. Estas **políticas son decisiones del modelador**, no una consecuencia automática de la librería.
- No se midió el tiempo total de modelado, la calidad de selección de políticas por un LLM, ni correspondencia causal con un negocio. Esto **no** prueba que la composición automática por IA sea correcta.

**Conclusión acotada:** en dos sistemas diferentes, el motor abierto es numéricamente operativo, y en S2 logró representar un flujo de pedidos con componentes de stock y tasa ya disponibles sin programar nuevas ecuaciones diferenciales. El siguiente gate para IGC no es repetir paridad: es comprobar **selección causal correcta de componentes y políticas** a partir de evidencia real e incompleta, sin confundirla con simulación calibrada.
