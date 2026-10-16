# IGC — Llama 3.3 70B versus DeepSeek R1 Distill Qwen 32B (3 casos × 2 brazos)

**Fecha:** 2026-10-15 (hora local México) / 2026-10-16 UTC.  
**Llama:** [Actions #38849431675](https://github.com/yudocyudoc/short/actions/runs/38849431675), [artifact #12023804317](https://github.com/yudocyudoc/short/actions/runs/38849431675/artifacts/12023804317).  
**DeepSeek anterior:** [Actions #38848438175](https://github.com/yudocyudoc/short/actions/runs/38848438175), [artifact #12024337590](https://github.com/yudocyudoc/short/actions/runs/38848438175/artifacts/12024337590).  
**Protocolo y rúbrica original:** [protocol.md](../protocol.md).  
**Réplica:** [llama-replication.md](../llama-replication.md).

## Integridad

- Se recibieron **6/6 respuestas Llama** y **6/6 DeepSeek** con `api_success=true`, JSON interpretable y originales archivados en Actions.
- El CI de Llama verificó **los seis SHA-256 exactos de prompt** contra la corrida DeepSeek, sin variación de casos, de inputs, de probes, de temperatura (0.1) ni de límite de generación (3500 tokens).
- El único cambio planificado fue el modelo: `@cf/meta/llama-3.3-70b-instruct-fp8-fast` frente a `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`.
- Rama separada, sin retroalimentación entre inferencias, sin reintentos ni edición de respuestas.
- Elección de Llama **posterior a la observación de DeepSeek**. Evaluación exploratoria de N=1 por celda, no generalización estadística.

## Comparación semántica conservadora

| Caso/brazo | DeepSeek R1 Distill Qwen 32B | Llama 3.3 70B |
|---|---|---|
| BB01-A, sin probes | Rechaza decisión por falta de datos POS→llegadas y parámetros no calibrados; no identifica sobreproducción del lookup ni backlog detenido sin ventas. | Declara condicional y describe ecuaciones como correctas; no identifica los dos defectos del mecanismo. |
| BB01-B, con probes | Menciona lookup y realimentación ausente, pero sin descubrir f(r)>r ni paralización del backlog. | Afirma que parámetros de capacidad son adecuados y ventas observadas representativas de demanda real; ambas afirmaciones son injustificadas. No identifica mecanismos. |
| W17-A, defecto de retardo | Advierte discrepancia del retardo, pero se equivoca en un día y añade un problema de stock inexistente. | No identifica la recepción inmediata incompatible con el contrato de dos días. |
| W17-B, defecto de retardo | Reconoce entrega contractual día 3, pero acusa equivocadamente una existencia correcta. | **Falso negativo estructural**: sostiene que la simulación sí incorpora retardo de dos días, cuando su código recibe el pedido el mismo día 1. |
| W18-A, control consistente | Describe trayectoria y recepción día 3 sin descubrir falla estructural, aunque rechaza decisión comercial. | No inventa defecto concreto; dice que la decisión es condicional por falta de observaciones reales. |
| W18-B, control consistente | Describe correctamente recepción día 3 y el saldo; ausencia de defecto interno reconocido, etiqueta YES. | Aprueba implementación y afirma ausencia de falla, aunque sin explicar con precisión el día 3; etiqueta YES. |

### Mecanismos discriminantes

**BB01 — sobreproducción del lookup:** ninguno de los dos modelos (con o sin probes) deriva explícitamente `Production/Desired > 1` cuando el ratio es bajo, ni lo distingue como artefacto de la curva de Hines.  
**BB01 — backlog congelado:** ninguno identifica explícitamente que la producción queda en 0 cuando POS=0 a pesar de mantener backlog sin preparar/despachar. DeepSeek B alude vagamente a ausencia de feedback, insuficiente para considerar resuelto el mecanismo.  
**W17 — retardo:** DeepSeek reconoce el fallo sin precisión perfecta; Llama falla en ambos brazos y B describe como correcta una implementación que recibe la compra sin retraso.  
**W18 — ausencia de defecto:** ambos evitan acusaciones internas claramente demostrables; persiste la distinción entre corrección *interna* y datos suficientes para una promesa de entrega *real*.

**Veredicto acotado:** en esta única pareja de experimentos DeepSeek fue más sensible al defecto de W17, aunque cometió errores de precisión. No se sustenta que Llama sea mejor para auditoría estructural IGC; tampoco puede sostenerse superioridad general de DeepSeek a partir de N=1 por caso.

## Uso informado por Cloudflare

| Métrica | DeepSeek | Llama |
|---|---:|---:|
| Tokens entrada | 11,162 | 10,595 |
| Tokens salida | 7,771 | 2,611 |
| Tokens totales | **18,933** | **13,206** |
| Neuronas informadas | **3,952.6177** | **817.2907** |

Los recuentos de tokens provienen del proveedor y pueden diferir por tokenizador. La métrica neuronas no equivale automáticamente a coste facturado ni es una medida directa de calidad. No se ha reconstruido factura de Cloudflare.

## Auditoría y próxima decisión

Este experimento está cerrado: **no reintentar ninguna de las doce inferencias ni modificar puntuación para favorecer un modelo**. Evitar nuevas iteraciones de prompts sobre estos tres mismos casos como supuesto nuevo descubrimiento. Si se quisiera adjudicar una puntuación numérica, aplicar estrictamente el rubric `protocol.md` a las doce respuestas originales por un revisor que no conozca las etiquetas de modelo, registrando desacuerdos y abstenciones.

La siguiente pregunta de IGC sigue abierta: detectar mecanismos cuya salida es internamente conservativa y reproducible pero no se corresponde con el contrato operacional o evidencia real. Aquí la capacidad no quedó demostrada de forma fiable por ninguno de los modelos.
