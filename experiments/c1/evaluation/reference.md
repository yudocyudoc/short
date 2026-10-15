# C1 — Referencia de evaluación preregistrada

> **Prohibido suministrar al modelo.** Preparada antes de ejecutar C1, con criterios invariantes respecto de las respuestas que lleguen.

## Resultado esperado y cálculos

- Capacidad máxima **teórica** de máquina: 12/h × 2h = **24 bebidas**.
- Cota máxima de producción por insumos: **18 bebidas**.
- Cota conjunta de producción: **18**, pero la cantidad **real observada es 13**, no 18.
- Stock final de insumos: 18 − 13 = **5 unidades de bebida-equivalente**, porque no hubo recepción, merma ni otros usos.
- Solicitudes totales recibidas: 30; rechazadas 5; aceptadas 25; canceladas tras aceptación 4; entregadas 13; stock final de pedidos aceptados pendientes: **8** (30 − 5 − 4 − 13).
- Las 17 no entregadas se componen **exactamente** de 5 rechazadas + 4 canceladas + 8 pendientes. No afirmar que 17 son pendientes.
- La máquina no es límite vinculante para el total de 13 entregadas; su utilización efectiva y la presencia de cuellos transitorios **no** se puede inferir sin marcas de tiempo. El inventario disponible habría permitido 5 bebidas adicionales, pero no implica que pudieran prepararse a cualquier instante ni que existiera demanda aceptada en ese instante.
- Diez personas distintas no equivalen a diez bebidas ni permiten inferir máximos biológicos.
- La causalidad de rechazos y cancelaciones no se observa. No hay evidencia suficiente para un bucle endógeno probado.

## Rúbrica C1 predefinida (0–2 cada criterio, máximo 16)

0 = ausente o erróneo; 1 = parcial/ambiguo; 2 = explícito y correcto.

| ID | Criterio |
|---|---|
| C1 | Stocks y flujos bien diferenciados con unidades y destinos (pendientes, insumos) |
| C2 | Identifica capacidad teórica de máquina 24 y cota conjunta 18 sin confundirlas con producción real |
| C3 | Registra exactamente 13 producidas y entregadas como OBSERVADO, no como capacidad |
| C4 | Obtiene 5 de inventario final y justifica entradas/salidas |
| C5 | Reconstruye 8 pendientes y diferencia 5 rechazadas + 4 canceladas + 13 entregadas |
| C6 | Diagrama con stock(s), flujos entrantes/salientes, trazabilidad de unidades y destinos |
| C7 | Retroalimentaciones no asumidas como hechos; señala falta de series temporales/causas |
| C8 | Distingue hechos, cotas e incertidumbres sin inventar límite por persona u otros mecanismos |

Errores críticos (veto): declarar inventario final 0 o 18, pendientes 17, entregas 18/24/30, sumar el rechazo al stock de pedidos aceptados, tratar 5 rechazadas y 4 canceladas como un único flujo sin distinguir su secuencia, inventar causalidad como observada.

## Umbrales exploratorios, congelados antes del resultado

- Respuesta estructuralmente aceptable: **≥12/16, sin veto**.
- Mejora orientativa del brazo B: B ≥ A+3 puntos, sin más errores críticos.
- Sólo una corrida por brazo: aun con diferencia, **no** hay inferencia estadística; evaluar con la misma rúbrica y declarar que el evaluador conoce el brazo.
- No comparar los puntajes de C0 y C1 como si fueran estimaciones del mismo efecto: los escenarios y criterios C1 han cambiado. En C1 se prueban estados observados, no inferencia de estados latentes.

**Importante:** La clave anterior sólo puede verse después de registrar las respuestas. No modificarla para favorecer un brazo.
