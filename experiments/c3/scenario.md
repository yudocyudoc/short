# C3 — Cafetería, turno observado

Una cafetería presencial atiende durante **3 horas**. Ofrece una sola bebida; cada bebida preparada consume exactamente una unidad de insumos equivalentes, y se entrega inmediatamente. No hay bebidas terminadas almacenadas, merma ni otros consumos de insumos.

- Entraron **12 personas distintas** y registraron **33 solicitudes de bebidas**; alguien puede solicitar más de una.
- La máquina puede preparar **como máximo 10 bebidas por hora**.
- Había insumos al inicio para preparar **24 bebidas**. No hubo entregas de proveedores ni reposición de insumos durante el turno.
- Al inicio había **cero solicitudes aceptadas pendientes**.
- Registros al cierre: **16 bebidas fueron preparadas y entregadas**; **8 solicitudes fueron rechazadas ANTES de aceptarse**; **3 solicitudes fueron aceptadas y posteriormente canceladas ANTES de preparación**.
- El registro es exhaustivo: todas las solicitudes quedan clasificadas como entregadas, rechazadas, canceladas después de aceptar o aceptadas que continúan pendientes al cierre. No existen otros destinos en este turno.

No se dispone de momentos exactos de solicitudes, causas de rechazo o cancelación, políticas de precios, efectos sobre visitas futuras ni utilización temporal de la máquina. No infieras un máximo fisiológico por persona.

Construye un modelo estructural mínimo y registra únicamente información deducible. No presupongas retroalimentaciones observadas.
