# C2 — Una cafetería: registros de un turno

Representa con dinámica de sistemas una cafetería que prepara un único tipo de bebida durante **3 horas**.

- Durante el turno entran **9 personas distintas** que emiten en total **28 solicitudes de bebidas**; una persona puede solicitar más de una.
- La máquina puede preparar como máximo **9 bebidas por hora**; no se conoce la distribución temporal de solicitudes.
- El turno empieza con insumos suficientes para preparar **20 bebidas**; no hay reposiciones, mermas ni otros usos de los insumos.
- Al comienzo no hay solicitudes pendientes ni bebidas preparadas. Toda bebida preparada se entrega inmediatamente; no hay bebidas terminadas almacenadas.
- **Registros completos al cierre:** se prepararon y entregaron **14 bebidas**; **6 solicitudes** se rechazaron antes de ser aceptadas; **3 solicitudes** se aceptaron y luego cancelaron antes de su preparación.
- El registro de solicitudes es exhaustivo: al cierre toda solicitud pertenece exactamente a una de cuatro categorías: entregada, rechazada, cancelada tras aceptación o aceptada pendiente de entrega.

No se conocen horas individuales de llegada, motivos de cancelación/rechazo, precios, pagos, preferencias, cantidades máximas de consumo por persona ni tasas futuras.

**Tarea:** entregar modelo mínimo de stocks y flujos, representar sus transiciones y límites, distinguir lo observado de lo deducido, reconocer retroalimentaciones demostradas frente a hipótesis y explicar qué no podemos identificar. No inventar hechos.
