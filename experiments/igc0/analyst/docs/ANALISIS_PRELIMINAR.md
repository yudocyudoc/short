# IGC-0 · Lectura preliminar de los ocho paquetes públicos

Este documento procede exclusivamente de **agregados deterministas** de registros públicos; no revela la configuración del mundo ni el oráculo. No se hizo inferencia de LLM.

| Caso | Cumplimiento presencial (cohorte) | Cancelación delivery (cohorte) | Días caja negativa observados | Llegadas pico (14 días) |
|---|---:|---:|---:|---:|
| M01 | 98.7% | 0.9% | 0 | 335 |
| M02 | 79.1% | 14.0% | 0 | 725 |
| M03 | 98.4% | 18.8% | 0 | 332 |
| M04 | 94.3% | 4.6% | 0 | 308 |
| M05 | 99.3% | 0.9% | 0 | 351 |
| M06 | 10.9% | 82.7% | 11 | 335 |
| M07 | 99.1% | 15.2% | 0 | 328 |
| M08 | 98.4% | 18.8% | 0 | 332 |

Los dos ratios se obtienen exclusivamente de campos de **cohorte de llegada**, no de tiempos de atención. El volumen de pico no demuestra por sí solo saturación: el denominador de capacidad debe incluir días, recurso compartido y carga previa. No inferimos causas únicas ni identidades de mundos.

**No es una clasificación de desviaciones**. Un modelo puede mostrar cancelaciones o colas aún cuando sus mecanismos coincidan con la referencia, y dos mecanismos distintos pueden generar las mismas observaciones.

## Resultado de simulación preliminar

Se implementó un simulador agregado independiente con paso de dos horas; se ejecutó con parámetros de referencia, sin leer el oráculo. La primera corrida mostró un error de contabilidad interno: cobraba los insumos al adquirirlos y nuevamente al prepararlos. Tras corregirlo, el error de caja final oscila entre 437.4 y 46,384.4 MXN. M01 pasó de 24,546.6 a 701.4 MXN, mientras M06 sigue muy alejado. En otros mundos también divergen materialmente las entregas e inventarios. Este hecho **bloquea el uso de esas trayectorias para adjudicar decisiones**. La causa del error aún no está localizada: puede involucrar supuestos de compras, cancelaciones, reparto y mecanismos operativos ocultos.

## Siguiente compuerta técnica

1. Ejecutar LLM externo con **un mundo**, sólo público y sin grafo de referencia adjunto; congelar JSON bruto y su SHA-256.
2. Verificar fuentes, epistemología, stocks/pipes y abstención; generar Mermaid desde JSON.
3. Sin abrir oráculo: medir error de reproducción del escenario observado por el simulador SD y decidir si posee resolución suficiente.
4. Sólo entonces evaluar las intervenciones contra el oráculo, con ayuda de un revisor distinto del diseñador de mundos.
