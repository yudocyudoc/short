# IGC — 2 moléculas opcionales, 4 grafos y observabilidad: resultados reales

**Fecha:** 2026-10-17. **Estado:** ensayo técnico completado; **15 tests**, **8 simulaciones OM**, **8 revisiones Llama**. No se utilizaron hechos de una empresa real.

## Evidencia

- [PR #29](https://github.com/yudocyudoc/short/pull/29), borrador.
- [Ejecución técnica sin LLM #39070228180](https://github.com/yudocyudoc/short/actions/runs/39070228180), 15 tests y OMC PASS.
- [Ejecución con Llama #39070298956](https://github.com/yudocyudoc/short/actions/runs/39070298956), mismo OMC PASS y revisión real de 8 casos.
- [Artefacto completo #12114922102](https://github.com/yudocyudoc/short/actions/runs/39070298956/artifacts/12114922102): 8 series OMC, código Modelica generado, 8 prompts, respuestas originales, diagnósticos y puntuación.

## 1. Cuatro composiciones ejecutables, no sólo nombres de modelos

El generador determinista `construct.py` compone un upstream MTO existente con dos **mecanismos de naturaleza diferente**:

- `TRANSIT`: almacén físico de productos enviados pendientes de recepción; clase ya verificada `IGCMolecules.BoundedQueue` (SystemDynamics). Modifica la tasa de entrega física y la acumulación material.
- `REPORT_FILTER`: filtro informacional `IGCInformationMolecules.FirstOrderReportFilter`, implementado con `Modelica.Blocks.Continuous.FirstOrder`. Suaviza **la tasa mostrada en el tablero**, **no** el material entregado, **ni** una cola de transacciones contables.

Se enumeraron y compilaron `Direct`, `TransitOnly`, `ReportOnly`, `TransitAndReport`. Hay cables de tipo `FLOW<Shipment>` para material y `SIGNAL<DeliveryRate>` para observación; los enlaces y las instancias son generados por reglas, no por Llama. El informe de OMC verifica que el filtro informacional **no cambia `deliveryRate`, `deliveredOrders`, `dispatchRate` ni `inTransit`** cuando se compara el mismo modelo físico con/sin filtro.

## 2. Tres observaciones distinguen lo que una sola no distingue

Las ocho simulaciones (cuatro arquitecturas × entrada cero/variable) pasaron los controles. Las firmas binarias se calcularon desde CSV **reales**; `SYNC` exige diferencias numéricas despreciables y `LAG` diferencias no triviales:

| Grafo | Tablero vs despacho | Recepción física vs despacho | Tablero vs recepción física |
|---|---|---|---|
| Direct | SYNC | SYNC | SYNC |
| TransitOnly | LAG | LAG | SYNC |
| ReportOnly | LAG | SYNC | LAG |
| TransitAndReport | LAG | LAG | LAG |

Con **sólo** el atraso entre tablero y despacho permanecen **tres** hipótesis. El motor eligió **`OBSERVED_VS_PHYSICAL`** como siguiente observación que particiona esas tres alternativas. Pero si allí aparece `LAG`, aún sobreviven **ReportOnly y TransitAndReport**: hace falta además conocer despacho frente a recepción física. La desambiguación requiere *observabilidad real*; simular las variables latentes no significa que la empresa las haya medido.

**Advertencia:** estas son clases binarias cualitativas. `LAG` compartido **no demuestra** series temporales idénticas o equivalencia matemática entre los grafos.

## 3. Ocho casos sintéticos, Llama exclusivamente como crítico

El modelo leyó los hechos D01–D08 y las firmas cualitativas de los cuatro grafos. No eligió conexiones ni generó matemáticas; emitió expectativas para las tres comparaciones y referencias por `fact_id`. El linter sólo verificó tipos y existencia de IDs, no la verdad semántica.

| Caso | Lectura del crítico y resultado | Estado |
|---|---|---|
| D01: transporte y reporte inmediato | Conserva TransitOnly | Válido |
| D02: entrega inmediata, tablero suavizado | Conserva ReportOnly | Válido |
| D03: transporte y tablero suavizado | Conserva TransitAndReport | Válido |
| D04: entrega y medición inmediatas | Conserva Direct | Válido |
| D05: reporte retrasado, recepción desconocida | Conserva ReportOnly, TransitOnly y TransitAndReport | Válido |
| D06: recepción física posterior, reporte desconocido | Conserva TransitOnly y TransitAndReport | Válido, desacuerdo con gold en una dimensión |
| D07: documentos contradictorios sobre recepción | Conserva los cuatro | Válido, clasificó UNKNOWN en lugar de CONFLICT |
| D08: ningún observable disponible | Conserva los cuatro | Válido |

**Puntuación estricta: 6/8 vectores exactos con el gold; 8/8 respuestas admitidas por el linter.** Frente a las cuatro alternativas iniciales de cada caso (32 candidaturas hipotéticas), las decisiones condicionadas conservaron **17** entre los ocho casos. Esta reducción NO certifica 17 arquitecturas empíricamente viables.

### Dos discrepancias originales, sin reetiquetar la campaña

**D06** — El gold esperaba `UNKNOWN` para `OBSERVED_VS_DISPATCH`, porque la forma del reporte informático no estaba documentada. Llama respondió `LAG`, respaldándose en la recepción física posterior al despacho. **Dentro de nuestro catálogo cerrado** ambas topologías con tránsito tienen `OBSERVED_VS_DISPATCH=LAG` aun si se añade el filtro, así que esta inferencia es compatible con las dos alternativas sobrevivientes. Pero **fuera** de esos supuestos, una política de reporte desconocida no justifica automáticamente cómo se comportará el tablero. Lo correcto es conservar esta diferencia como *ambigüedad entre razonamiento condicionado al catálogo y evidencia real disponible*, no declararla un acierto ni una falla causal inequívoca.

**D07** — Dos manuales vigentes afirmaban para el mismo proceso una recepción física inmediata y otra posterior a transporte. El gold era `CONFLICT` para `PHYSICAL_VS_DISPATCH`; Llama respondió `UNKNOWN` para esa dimensión, aunque incluyó los IDs F1 y F2. **Aquí omitió identificar explícitamente la contradicción.** La consecuencia operacional fue conservadora: no eliminó ninguna arquitectura, pero tampoco diagnosticó la naturaleza del conflicto.

Las ocho respuestas fueron parseadas y pasaron el linter. No se modificaron el gold, los relatos, los prompts ni las reglas después de observar estos dos fallos.

## 4. Veredicto y límites

**Sí se logró:** dos moléculas opcionales de tipos y dinámicas distintas, enumeración de cuatro grafos, pruebas Modelica repetibles, medición del efecto independiente del filtro, búsqueda de señales discriminantes y crítica semántica sin generación de ecuaciones. La poda conservadora mostró comportamiento útil en situaciones informativamente insuficientes.

**No se logró ni se afirma:** cientos de grafos, composición Hines arbitraria, deducción semántica formal, validación con datos observados de empresa, estimación estadística con 8 textos sintéticos, ni demostrar que la próxima medición seleccionada efectivamente exista en la organización. La elección de pruebas es una heurística sobre firmas binarias, no un diseño experimental óptimo continuo.

**Recomendación siguiente:** antes de añadir más moléculas, incorporar una **capa explícita de observabilidad/procedencia** por variable. Por ejemplo `dispatch_timestamp=observado`, `physical_receipt_timestamp=no observado`, `reported_rate=observado`. El motor podrá calcular qué experimento distinguiría alternativas y decir cuáles requieren instrumentación que aún falta. Un LLM propondría preguntas a partir de hechos, sin poder inventar que una variable ya está medida.
