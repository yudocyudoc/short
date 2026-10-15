# C4 — Cafetería, cuatro horas (mundo cerrado de prueba)

Se desea construir el modelo mínimo de stocks y flujos de una cafetería presencial durante **4 horas**.

- Acudieron **15 personas distintas** que formularon **43 solicitudes de bebidas**. Una persona puede pedir varias bebidas. No hubo delivery ni ventas a terceros.
- Una máquina puede preparar como máximo **9 bebidas por hora**.
- El turno comenzó con insumos equivalentes a **30 bebidas**. No llegó reposición ni hubo otras salidas de material o merma.
- El turno comenzó con **0 solicitudes aceptadas pendientes** y sin bebidas terminadas. Cada bebida consume exactamente una unidad de insumos-equivalentes y es entregada inmediatamente tras prepararse. No se almacenan productos terminados.
- Registros observados al cierre: **21 bebidas preparadas y entregadas**, **9 solicitudes rechazadas antes de aceptarse** y **5 solicitudes canceladas después de su aceptación, antes de la preparación**.
- El registro es exhaustivo: toda solicitud acaba como entregada, rechazada, cancelada después de aceptación o aceptada todavía pendiente al cierre.

No conocemos la distribución temporal de las solicitudes, las razones de los rechazos/cancelaciones, utilización efectiva de máquina por instante, comportamiento futuro, ingresos, precios ni límites de consumo por cliente.

Reconstruye únicamente el sistema respaldado por estos hechos. Las capacidades son cotas, no producción observada. No inventes feedback causal.
