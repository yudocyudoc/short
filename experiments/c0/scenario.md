# C0 — Escenario idéntico para ambos brazos

Se desea representar con un modelo **mínimo de dinámica de sistemas** una cafetería presencial durante **dos horas**.

**Hechos del caso:**

- En esas dos horas entran **10 personas distintas**. No hay ventas a terceros, pedidos para llevar ni delivery.
- Estas personas registran en total **30 solicitudes de bebidas** durante el periodo. Una persona puede solicitar más de una bebida. No sabemos cuándo se produjo cada solicitud.
- Se vende un único tipo de bebida preparada al momento. La máquina puede terminar, como máximo, **12 bebidas por hora** durante funcionamiento continuo.
- Hay insumos iniciales para producir **18 bebidas**. No se reciben más insumos durante las dos horas.
- Al inicio hay **cero bebidas ya preparadas** y **cero solicitudes pendientes**.
- Las bebidas se entregan después de prepararse; no se almacenan bebidas terminadas.
- No se informa cuántas solicitudes fueron aceptadas, rechazadas o canceladas, ni cuántas bebidas se entregaron efectivamente.

**No se proporciona:** precio, ingreso, caja, intensidad de deseo de consumo, umbrales fisiológicos individuales, frecuencia por persona, distribución temporal de llegadas, tiempo de espera tolerado ni tasa de cancelación.

**Tarea:** construir una representación estructural mínima, explicitar restricciones y consecuencias lógicas, distinguir hechos de hipótesis y señalar lo que no se puede inferir con los datos dados.

No agregues otros hechos de la cafetería.
