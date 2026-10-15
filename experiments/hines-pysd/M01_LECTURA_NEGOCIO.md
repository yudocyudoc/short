# M01 · ¿Puede la cafetería abrir delivery con la cocina actual?

**Lectura para el negocio — no es una recomendación de apertura.**

Esta cafetería es **sintética**: sus datos fueron generados para probar un método, no provienen de un establecimiento real. La pregunta y la manera de explicar los resultados sí sirven como ejemplo de una conversación con un negocio pequeño.

## Lo que sabemos

La capacidad de referencia es **16 pedidos por hora en cocina** y **15 pedidos por hora en despacho**. Son capacidades nominales documentadas, no mediciones del rendimiento efectivo en cada hora. El inventario inicial era de **92 comidas equivalentes** y la caja comenzaba en **$4,600 MXN**.

En 14 días se registraron **789 pedidos aceptados** entre presencial y delivery. Los registros también contabilizan **780 completados en ventanas reales de servicio**, pero las aceptaciones están agrupadas por *ventana de llegada*, mientras que los completados se registran por *ventana de ejecución*. No debemos restar ambas cifras para calcular automáticamente una cola o decidir dónde se perdieron pedidos.

De las 42 ventanas de dos horas, **solo una excedió la capacidad nominal de cocina por número de pedidos aceptados**: el **día 2, ventana pico, 34 aceptados frente a 32 nominales**. Esto *podría* justificar investigar presión de trabajo, pero no demuestra que la cocina se saturó. Además, una capacidad nominal puede admitir sobreutilización temporal.

## Lo que todavía no podemos asegurar

No sabemos cuánto tardó individualmente cada pedido en pasar por cocina, en quedar listo y en entregarse a despacho. Tampoco sabemos cuántas comidas equivalentes consumió cada pedido, cuántos pedidos preparados había ya en espera o cómo se efectuaron efectivamente las entregas del proveedor.

No hay suficiente evidencia para atribuir las cancelaciones a la cocina, a los repartidores, al inventario o a los pagos. **Por eso no tenemos una proyección confiable de ingresos, tiempos de espera ni servicio si se abre delivery.**

## El mapa del negocio, sin exigirle aprender SD

1. **Pedidos pendientes:** clientes que ya ordenaron, pero cuya solicitud todavía no se completó.
2. **Pedidos preparados:** trabajos que la cocina terminó, pero que aún no han salido hacia el cliente.
3. **Inventario de ingredientes:** capacidad de producir, medida en comidas equivalentes. No es el mismo inventario que los pedidos preparados.
4. **Abastecimiento:** compras que están en tránsito desde el proveedor.
5. **Caja y cobros por recibir:** dinero disponible y dinero que puede entrar después; no son comida ni pedidos.

Son estructuras conocidas del modelado de sistemas, no figuras improvisadas por una IA. Las relaciones precisas entre ellas dependen de datos y supuestos que debemos declarar.

## La mínima información adicional que pediríamos

Registrar por pedido **hora de aceptación, hora en que cocina lo deja listo y hora de salida/entrega a despacho**, además de cancelación si ocurrió. Para vincular esto con inventario, anotar comidas equivalentes o ingredientes por pedido, y las cantidades/fechas de abastecimiento.

Con esas mediciones podríamos contrastar si el límite relevante aparece antes de cocina, en cocina, en despacho o en la reposición. Sin ellas, distintas explicaciones pueden generar registros agregados parecidos.

## ¿Qué decisión está pendiente?

Comparar tres alternativas originales del ejercicio: **seguir solo presencial**, **abrir delivery en todas las ventanas**, o **abrir únicamente en valles con un máximo de nueve pedidos delivery por ventana**.

**Ninguna queda recomendada todavía**. Primero necesitamos un modelo que reproduzca suficientemente la operación observada y que distinga mecanismos alternativos. La pregunta útil, de momento, no es «¿qué modelo propone la IA?», sino **«¿qué tendría que observar el negocio para tomar esta decisión con menos incertidumbre?»**

---

**Auditoría:** [código y composición, PR #7](https://github.com/yudocyudoc/short/pull/7) · [resultado verificado y hashes, PR #8](https://github.com/yudocyudoc/short/pull/8) · [PySD con originales Hines, PR #5](https://github.com/yudocyudoc/short/pull/5).  
**Estado:** propuesta estructural verificada; inferencias de IA = 0; simulación calibrada M01 = bloqueada.
