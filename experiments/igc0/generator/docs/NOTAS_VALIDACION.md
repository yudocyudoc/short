# Validación técnica y advertencias del piloto IGC-0

**Pruebas locales:** 4 controles públicos + 11 controles privados, todos aprobados. Antes de un ensayo LLM, validar SHA-256, cantidad de filas y que el analista sólo recibió el ZIP público.

### Hechos comprobados del generador

- Las ocho ejecuciones son deterministas por semilla y escenarios congelados.
- Cada caso tiene 42 filas POS de ventanas y 14 registros diarios de inventario, efectivo y cuentas por cobrar.
- Balance de órdenes por cohorte: intentados = completados + rechazados + cancelados + pendientes al cierre.
- Balance de existencias: inicial + insumos recibidos = consumidos + inventario al cierre.
- Ninguna liquidación con fecha posterior a los 14 días se contabiliza anticipadamente como caja. El ingreso neto generado y no cobrado permanece en cuentas por cobrar.
- Las políticas comparten exactamente la misma secuencia potencial de llegadas dentro de cada mundo.
- Los dos mundos destinados a evaluar no identificabilidad tienen **idénticas referencias y evidencias observables**, pero divergen al modificar experimentalmente distintas restricciones ocultas.
- Los mundos nulos reproducen exactamente sus referencias con la misma demanda.
- Los archivos de observación no contienen claves de desviaciones inyectadas, semillas ni verdad del evaluador.

### Interpretación cuidadosa

La muestra fue ajustada mientras se diseñaba el piloto. No se debe presentar como prueba confirmatoria. En particular, la coincidencia por pares es **constructiva por diseño** para imponer una prueba de no identificabilidad; no valida por sí misma que un modelo la detectará.

**Registro POS:** `fulfilled` y `canceled` pertenecen a la **cohorte de llegada**. `service_window_completed` representa pedidos efectivamente completados durante la ventana. Estos no son campos intercambiables; son diferentes cortes de una misma bitácora.

**Liquidez:** los saldos negativos en el simulador significan faltante acumulado; no hay financiamiento externo modelado. Los escenarios con faltante se consideran inviables y las trayectorias posteriores requieren cautela.

**Limitación SD:** el generador es un sistema de eventos discretos; el IGC que lo analice debería construir una versión stock–flow agregada independiente. La igualdad numérica perfecta de una representación SD simplificada no es requisito si la reducción pierde resolución intradía; la brecha debe quedar trazada y evaluada contra una tolerancia declarada, nunca ocultarse.

**Datos sintéticos:** no son evidencia de que una cocina real pueda servir determinado número de pedidos ni de que los costos unitarios seleccionados sean realistas.
