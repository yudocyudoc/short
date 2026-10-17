# IGC — segunda molécula opcional: filtro informacional frente a tránsito físico

**Diseño y casos congelados antes de inferencias:** 17 de octubre de 2026. **Estado:** experimento mínimo de ingeniería.

## Pregunta

¿Puede un generador determinista de mecanismos tipados crear cuatro grafos distintos incorporando dos funciones diferentes —una acumulación física y un filtro informacional— y encontrar qué mediciones distinguen explicaciones que parecen iguales cuando sólo se observa el tablero?

Este experimento profundiza los PR #27 y #28. No busca cien arquitecturas por combinatoria: busca demostrar que **mecanismos causalmente distintos pueden producir la misma clasificación cualitativa observada** y que una segunda medición cambia la identificabilidad.

## Dos mecanismos verdaderamente diferentes

1. **TRANSIT**, opcional: stock físico de unidades enviadas y no recibidas; reutiliza `IGCMolecules.BoundedQueue` sobre SystemDynamics (del PR #25). Cambia el instante de la recepción física y conserva flujos de material.
2. **REPORT_FILTER**, opcional: filtro continuo de primer orden de una **tasa informada**, implementado en `IGCInformationMolecules.FirstOrderReportFilter` usando el componente preexistente `Modelica.Blocks.Continuous.FirstOrder`. Altera sólo el valor informado del ritmo de entregas: **NO mueve unidades materiales, NO añade existencias físicas y NO representa una cola de transacciones administrativas pendientes de registro**.

El programa `construct.py` enumera los cuatro subconjuntos de `{TRANSIT,REPORT_FILTER}`, valida conexiones tipadas de `FLOW` y `SIGNAL`, y genera Modelica con instancias realmente distintas a partir de un upstream S2 fijo. Ni las ecuaciones ni los valores numéricos provienen del LLM.

| Grafo | Tránsito físico | Suavizado de reporte |
|---|---|---|
| Direct | No | No |
| TransitOnly | Sí | No |
| ReportOnly | No | Sí |
| TransitAndReport | Sí | Sí |

## Pruebas de comportamiento y observabilidad

Se ejecutan las cuatro arquitecturas con dos entradas sintéticas (cero pedidos y pedidos variables) en OpenModelica 1.26.5, SystemDynamics 2.1.2 y MSL 4.0.0: **ocho simulaciones reales**.

El analizador calcula de los CSV tres comparaciones cualitativas:

- `OBSERVED_VS_DISPATCH`: tasa mostrada en tablero frente al despacho.
- `PHYSICAL_VS_DISPATCH`: recepción física frente al despacho.
- `OBSERVED_VS_PHYSICAL`: tasa mostrada frente a recepción física.

**Hipótesis fijada antes de ejecutar OMC:**

| Grafo | Observado vs despacho | Físico vs despacho | Observado vs físico |
|---|---|---|---|
| Direct | SYNC | SYNC | SYNC |
| TransitOnly | LAG | LAG | SYNC |
| ReportOnly | LAG | SYNC | LAG |
| TransitAndReport | LAG | LAG | LAG |

Un observador que solamente nota que **el reporte va retrasado respecto del despacho** no puede elegir entre TransitOnly, ReportOnly y TransitAndReport: las tres firmas cualitativas son LAG. Eso **no afirma igualdad numérica de las curvas**. Una medición independiente de recepción física o del filtro informacional permitiría discriminar más, **si realmente está disponible en el negocio**.

El motor selecciona el siguiente ensayo calculando cómo particiona las alternativas aún compatibles, y registra si esa variable es observable en el problema, sin inventar datos ausentes. Se comprueba además que activar REPORT_FILTER **no altera** tasa ni total de entregas físicas en las dos comparaciones de pares apropiadas.

## Crítico Llama

Sobre **ocho situaciones cualitativas nuevas** D01–D08 fijadas antes de inferir, Llama recibe las cuatro alternativas y sus firmas binarias, nunca ecuaciones ni valores de simulación. Su única tarea es proponer `SYNC`, `LAG`, `UNKNOWN` o `CONFLICT` para cada dimensión, con IDs existentes de hechos.

El linter verifica forma/IDs. La selección es una **poda condicionada al juicio semántico del crítico, no un hecho deducido formalmente**. El motor no utiliza los labels esperados para aceptar una respuesta. Una contradicción bloquea la poda de manera conservadora; datos faltantes mantienen múltiples opciones. El humano o los datos reales deben resolver las preguntas de observabilidad.

## Límites

- Cuatro grafos comparten el mismo upstream S2 y dos piezas opcionales; no es una búsqueda de cientos de estructuras Hines.
- El filtro FirstOrder suaviza el indicador de ritmo, **no representa exactamente un retraso transaccional del sistema contable**.
- Las firmas cualitativas binarias agrupan salidas que pueden diferir numéricamente.
- Las ocho viñetas y su gold son sintéticos de los autores: prueba de integración, no estimación de rendimiento estadístico o causal empresarial.
- No se verifica semánticamente que un `fact_id` implique la expectativa, ni se ha encontrado evidencia de una empresa observada.

**Éxito mínimo:** enumera cuatro topologías, compila ocho corridas, comprueba independencia material de REPORT_FILTER, mide tres firmas y ejecuta un crítico que preserve incertidumbre cuando no hay observación suficiente.
