# C4.2 — Registro de evidencia cerrado (uso exclusivo del validador)

**Origen:** escenario sintético `experiments/c4/scenario.md`, que se entrega a ambas variantes sin modificación.

**Hechos explicitados por el escenario** (no inferidos del modelo):
- Duración: 4 horas; máquina: máximo 9 bebidas/hora.
- Insumos iniciales: 30 bebidas-equivalentes; sin reposición, merma ni otros consumos.
- Solicitudes iniciales pendientes: 0. No hay inventario de bebidas terminadas, que se entregan inmediatamente.
- Solicitudes recibidas: 43. Rechazos **previos** a aceptación: 9.
- Cancelaciones **posteriores** a aceptación: 5.
- Preparadas y entregadas observadas: 21, que consumen 21 unidades equivalentes.

**Deducciones del balance** (resultado del validador, nunca se suministran como respuesta):
- Total aceptado = 43−9 = 34.
- Aceptadas pendientes finales = 0+34−5−21 = 8.
- Inventario final = 30−21 = 9.
- Capacidad máquina = 4×9 = 36, capacidad de insumos 30; cota conjunta 30. **La cota 30 no es producción observada 21**.

**Frontera epistémica:** conocer estos hechos y comprobar conservación no identifica por sí solo causas, decisiones ni retroalimentaciones endógenas. No se incluye esta ficha en ninguna solicitud a Workers AI.
