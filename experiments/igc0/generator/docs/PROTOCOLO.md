# IGC-0 · Protocolo del piloto de ocho mundos

**Propósito:** comprobar la aptitud de un sistema asistido por LLM, con cálculo y renderización deterministas, para **I**dentificar, **G**raficar y **C**ontrastar mecanismos de SD y **proyectar acciones** en una pregunta operacional.

## Frontera y mecanismos

**Agente focal:** restaurante que considera abrir canal delivery. **Campo:** mercado de pedidos, repartidores de una plataforma, proveedor de insumos, reglas de liquidación. **Sistema modelado:** demanda por canal, colas, recurso compartido de cocina, inventario y abastecimiento, etapa de despacho, cuentas por cobrar y caja. El modelo mínimo no presume que exista un feedback endógeno entre demanda y reputación: sólo se incluiría cuando se observe o se declare como hipótesis.

**Modelo fundamental:** tipos de acumulaciones, pipes y reglas de conservación. **Referencia factible:** capacidad compartida de cocina de 16 pedidos/h, despacho de referencia de 15 pedidos/h, liquidación de delivery tras un día, sin consumo oculto de catering. **Modelo virtual:** eventos operativos simulados con mecanismos específicos ocultos. La referencia no es una optimización y la operación virtual no se considera necesariamente «mala» sólo por divergir.

**Observación:** el mundo generador es un simulador de eventos discretos, no la misma integración stock-flow agregada que tendría que elaborar IGC. Cada día se abre de 09:00 a 15:00, dividido en tres ventanas de 120 minutos (valle, pico, valle). Los pedidos llegan individualmente, comparten cocina FIFO, pasan por preparación y eventualmente por despacho. Los pedidos pendientes pueden cancelarse tras 205 minutos. Los flujos financieros y el proveedor tienen retardos de días.

Los registros POS agrupan **por cohorte de llegada**, incluyendo el desenlace conocido al final del horizonte; para que no se confundan con tiempos de despacho, existe un campo separado con completados por ventana real de servicio. Esta diferencia debe respetarse en las proyecciones.

## Acciones simuladas

| ID | Política | Regla |
|---|---|---|
| `no_delivery` | No abrir | Sólo pedidos presenciales |
| `open_full` | Abrir | Pedidos de delivery admitidos en las tres ventanas |
| `open_offpeak_capped` | Apertura parcial | Sin delivery durante pico; admitir hasta 9 pedidos por ventana valle |

El mundo virtual mostrado al analista **corresponde a `open_full`**. Las otras dos acciones son contrafactuales simulados por el generador usando **la misma secuencia potencial de llegadas** de cada mundo. Si se pide una estimación de la acción contrafactual al LLM, éste no recibe la trayectoria verdadera de esa acción.

## Objetivo operacional y límites

La pérdida sintética de 14 días, que debe **minimizarse**, es:

\[
L=-M+220 C_p+20 C_d+9 T_{>65}+110 D_{caja}+3 P_f
\]

Donde `M` es margen económico neto: ingresos presenciales cobrados (120 MXN por entrega) + ingreso neto devengado por delivery (130 MXN por entrega menos 24% de comisión) − 32 MXN por unidad consumida − 9 MXN por paquete de delivery preparado − 1,650 MXN/día de operación − (para políticas con delivery) 900 MXN de configuración y 300 MXN/día. `C_p` y `C_d` son cancelaciones de pedidos presenciales y delivery, respectivamente; `T_{>65}` es número de servicios con espera superior a 65 minutos; `D_caja` días de insuficiencia de caja; y `P_f` pedidos aceptados todavía pendientes al cierre.

**Admisibilidad** independiente de minimizar `L`: fracción de pedidos presenciales completados ≥92%, cancelación del delivery ≤20% de los pedidos de ese canal aceptados, **cero días de déficit de caja**. Una política inviable se excluye aunque tenga un valor de pérdida menor. Ante varias viables se elige menor pérdida. Ante ninguna viable, no hay decisión numérica automática.

**Límite contable:** el simulador permite que el saldo neto de caja sea negativo para **registrar insuficiencia**, no para simular una línea de crédito real. Desde el primer déficit, las trayectorias deben tratarse como inadmisibles en una operación sin financiamiento. Esto impide interpretar como viable un crecimiento posterior que requeriría fondos no disponibles.

**Límite epistemológico:** todos los precios, costos, capacidades y penalizaciones son **supuestos sintéticos de prueba**, no valores de mercado, recomendaciones comerciales ni estimaciones del sector gastronómico.

## Contraste ideal–virtual

El evaluador ejecuta la referencia con las mismas condiciones iniciales y la misma secuencia de llegadas potenciales del mundo virtual cuando busca una diferencia **de mecanismo operativo**. Para evaluar una alteración de campo como el pico de demanda, también registra la diferencia en el perfil de entradas respecto a una referencia habitual. No se debe confundir choque externo de demanda con falla de capacidad.

**Casos nulos:** hay mundos en los que referencia y operación tienen idénticos mecanismos; incluso si aparecen esperas normales, la respuesta correcta no inventa desviaciones. **Casos no identificables:** hay mecanismos ocultos diferentes que generan exactamente la misma evidencia pública. Se espera reconocer equivalencia de observaciones y pedir una medición que permita discriminar las alternativas.

## Etiquetas y trazabilidad

Se preservan los seis tipos CEI-B v2: `OBSERVADO`, `CALIBRADO`, `INFERIDO`, `SIMULADO`, `HIPÓTESIS`, `DESCONOCIDO`.

Cada registro observacional lleva `source_id`, unidades por variable y `sha256` de la fila. Los parámetros de referencia y las condiciones iniciales numéricas llevan también tipo, fuente, unidad y huella. Un SHA comprueba **integridad del registro**, no autenticidad del mundo exterior.

**Regla para escenarios:** un número proyectado sólo puede presentarse con el ID de un modelo, su política, parámetros/calibración, origen de condiciones iniciales, horizonte, unidad y hash de corrida. Una cifra sin esa procedencia debe marcarse como hipotética/no verificada y no utilizarse para adjudicar una decisión.

## Lo que NO es una conclusión de este piloto

Los ocho mundos fueron seleccionados y parametrizados de forma adaptativa por el constructor mientras comprobaba los resultados. No son ocho muestras independientes representativas de negocios. La función de pérdida y los límites fueron ajustados durante la construcción; se consideran **congelados para futuras corridas sobre esta colección**, no preregistrados antes del diseño. El éxito de un modelo sobre los ocho no establecería validez externa ni robustez estadística.

El criterio de éxito confirmatorio, la selección de un conjunto nuevo y el juicio sustantivo de utilidad deben fijarse por un revisor distinto del autor del generador antes de cualquier campaña ampliada.
