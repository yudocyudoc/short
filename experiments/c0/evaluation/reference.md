# C0 — Referencia independiente para evaluación

> **NO suministrar este archivo al modelo durante las pruebas A ni B.** El repositorio es público: para evitar contaminación, las pruebas deben ejecutarse con sólo los archivos permitidos y sin acceso de lectura al repositorio completo. Este documento es una clave de evaluación, no datos de entrada.

## Consecuencias deducibles

- Capacidad teórica de producción de máquina en dos horas de funcionamiento continuo: `12 bebidas/h × 2 h = 24 bebidas`.
- Insumos iniciales permiten como máximo `18 bebidas` en el periodo sin reposición.
- El máximo posible de bebidas terminadas y entregables es **min(24,18)=18** en el periodo, suponiendo que no haya otras restricciones. Es una **cota superior**, NO producción/venta observada y NO garantía de que se hayan entregado 18.
- Hay **30 solicitudes**; por tanto, al menos **12 solicitudes no pudieron culminar en una entrega dentro del horizonte**. Su destino exacto —rechazadas, pendientes, canceladas, no aceptadas— **no es identificable** con estos datos. No afirmar «12 pedidos pendientes».
- La máquina NO es el cuello de botella del volumen total de este horizonte bajo la cota de insumos; pueden existir cuellos transitorios por la distribución desconocida de solicitudes.
- Que existan 10 personas distintas NO impone un máximo exacto de 10 bebidas ni un máximo fisiológico calculable a partir del escenario.

## Una representación razonable (no única)

**Stocks/estados relevantes:** insumos disponibles (bebidas-equivalentes); solicitudes pendientes de resolución (si la definición y aceptación se explicitan); pedidos aceptados pendientes de entrega (si se quiere separar aceptación); personas presentes (si se modela ocupación temporal; aquí no es indispensable para calcular la cota).

**Flujos:** solicitudes recibidas; aceptación o rechazo; terminación y entrega (limitada por máquina e insumos); cancelaciones (posibles, magnitud desconocida); consumo de insumos por preparación. «30 solicitudes» es un total en el periodo, no una tasa constante de 15/h **observada**.

**Acoplamiento:** el flujo de preparación/entrega consume 1 unidad de insumos equivalente por bebida; no se generan insumos; no se supone producción adelantada. Si se agregan compradores/caja/finanzas, han de rotularse extensiones no sustentadas por los datos C0.

**Retroalimentación:** C0 no identifica un ciclo endógeno cuantificable. Espera → cancelaciones, ventas → reposición, satisfacción → demanda futura, etc. pueden rotularse sólo como hipótesis para otro escenario; la reposición está explícitamente excluida en las dos horas.

## Fallas típicas a vigilar

- Usar `30` como ventas observadas, `24` como producción efectiva o `18` como venta garantizada.
- Suponer 15 solicitudes por hora uniformes cuando sólo conocemos el total del periodo.
- Mezclar «solicitudes» y «pedidos aceptados» en un stock sin definición.
- Tratar posibles cancelaciones como observadas.
- Forzar un bucle «ventas → caja → compras → inventario» contradiciendo la ausencia de reposición en C0.
- Atribuir límites fisiológicos numéricos a los diez consumidores sin ninguna exposición, dosis o preferencia observada.

**Origen de esta clave:** deducción independiente de balances y límites explícitos del escenario; no es el output de una corrida SD-AI. Debe quedar congelada antes de puntuar respuestas.
