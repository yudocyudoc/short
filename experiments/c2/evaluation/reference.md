# C2 — Clave y rúbrica selladas ANTES de inferencia

**No compartir con ninguna variante durante la generación.** Rúbrica 0–2 por criterio, total 16, creada antes de observar sus respuestas.

## Balance esperado

- Capacidad teórica máquina: 9×3 = **27 bebidas**. Insumos iniciales = 20 bebidas-equivalentes. Máximo físicamente producible dentro del turno `min(27,20)=20`.
- Producción/entrega observada = **14** bebidas. Inventario remanente = **20−14=6** unidades. No inventar bebida almacenada.
- 28 solicitudes totales: **6 rechazadas** antes de aceptación; **22 aceptadas**. De las aceptadas, **3 canceladas**, **14 entregadas** y **5 aceptadas pendientes** al cierre. `28=6+3+14+5`.
- 14 entregadas no implica máquina saturada, ni se conoce distribución temporal de solicitudes; nadie puede inferir demanda máxima biológica a partir de nueve personas.
- Stock clave 1: inventario de insumos (20→6, salida consumida 14).
- Stock clave 2: aceptadas pendientes de entrega (0→5; entrada 22 aceptadas, salidas 3 canceladas y 14 completadas/entregadas). Si se agrega preaceptación, debe separar su balance y evitar doble conteo. Rechazos no son salidas de aceptadas.
- No identificar bucles endógenos como observados. Diagrama sin productos terminados almacenados; no confundir transferencias de recursos físicos y estados de solicitud.

## Criterios congelados

| Código | Criterio (0–2) |
|---|---|
| F1 | Identificación correcta de stocks vs eventos/tasas, sin «bebidas listas pendientes» ni stocks instantáneos ficticios |
| F2 | Unidades compatibles en stocks y flujos y distinción entre totales del turno y tasas |
| F3 | Balance de inventario correcto (20 inicial, 14 consumidas, 6 final) |
| F4 | Solicitudes correctamente particionadas: 6 rechazo, 22 aceptación, 3 cancelación, 14 entrega, 5 pendientes |
| F5 | Distingue máximo máquina 27, máximo físico conjunto 20 y entregas reales 14 |
| F6 | Diagrama conserva material y entidades y no cruza estados incompatibles (rechazo antes de aceptación; cancelación desde aceptadas, nunca desde bebidas preparadas) |
| F7 | No presenta lazos causales como comprobados cuando sólo son hipótesis |
| F8 | Declara incertidumbres, supuestos y límites, sin inventar causas ni fisiología humana |

**Veto estructural:** inventario final ≠6, pendientes finales ≠5, producción real ≠14, preparados almacenados >0, o rechazo dibujado como salida de «aceptados». El veto se declara como tal aunque el puntaje total sea alto.

**Umbral exploratorio:** ≥12/16 sin veto es aceptable individualmente; diferencia B−A ≥3 con B sin veto es señal para nueva réplica. Con una sola pareja, jamás inferir robustez. Evaluador que conoce brazo declara ausencia de cegamiento. El escenario C2 fue diseñado después de ver errores en C1; es **prueba exploratoria iterativa**, no réplica preregistrada independiente del hallazgo original.
