# C1 — Cafetería con registros de cierre (dos horas)

Una cafetería presencial vende un solo tipo de bebida. Se quiere construir un modelo estructural mínimo de sus stocks, flujos y restricciones durante **dos horas**.

**Condiciones físicas:**
- Durante las dos horas entraron **10 personas distintas**, sin pedidos para llevar, intermediarios ni delivery. Cada persona puede solicitar varias bebidas.
- Se registraron **30 solicitudes** de bebidas distintas durante el periodo; no se conoce su distribución temporal.
- Una máquina prepara como máximo **12 bebidas por hora** en funcionamiento continuo.
- Al comienzo existían insumos equivalentes para **18 bebidas**; no se recibieron insumos nuevos durante el periodo.
- Al inicio no había solicitudes pendientes ni bebidas terminadas. Cada bebida preparada utiliza una unidad de insumos equivalente y se entrega inmediatamente. No hay merma, preparación descartada ni otras salidas del inventario.

**Registros al cierre (hechos, no estimaciones):**
- Se prepararon y entregaron **13 bebidas**.
- **5 solicitudes** fueron rechazadas antes de ser aceptadas.
- **4 solicitudes** fueron aceptadas y después canceladas antes de empezar su preparación.
- El registro es exhaustivo: todas las solicitudes pertenecen a una y sólo una de estas cuatro categorías al cierre: **entregadas, rechazadas, canceladas o aceptadas pendientes de entrega**. No hay otros destinos.

**No consta:** hora exacta de cada solicitud, precios, caja, motivos de rechazo o cancelación, satisfacción, probabilidad de volver a comprar, ni tasas de comportamiento futuras.

**Tarea:** Representa estructuralmente stocks, flujos y restricciones; distingue cantidades potenciales de resultados observados y calcula sólo lo que la información permite. No añadas causas ni observaciones nuevas.
