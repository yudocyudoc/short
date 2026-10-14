# Short — CEI / SD-AI

Proyecto experimental: modelación de stocks, flujos, restricciones y estados de sistemas físicos y empresariales, antes de intentar identificar ecuaciones dinámicas complejas.

## C0 — Capacidades vs posibles resultados

[Experimento C0](experiments/c0/README.md) · [Evaluación](experiments/c0/results/cf-2026-10-13-evaluation.md): **A 11/16, B 11/16**. Ambas IA confundieron cotas posibles con estados no observados.

## C1 — Estados observados y destino de solicitudes

[Experimento C1](experiments/c1/README.md) · [Evaluación](experiments/c1/results/c1-2026-10-13-evaluation.md): **A 5/16, B 9/16**. La gramática B identificó correctamente 13 entregas y 5 insumos restantes, pero declaró 11 pendientes en vez de 8 y presentó flujos mal conectados.

Las puntuaciones C0 y C1 provienen de escenarios/rúbricas distintos; **no son comparables entre sí como medidas de progreso estadístico**.

**Modelo/proveedor:** GLM-4.7-Flash mediante Cloudflare Workers AI. Ningún ensayo prueba que el antiguo SD-AI pueda recuperar mecanismos causales.

## Costos C0 + C1

Cuatro inferencias: **7,819 tokens**, **172.012 neuronas**, estimación **US$0.0018904** antes de franquicia (no un cargo confirmado).

## Siguiente hipótesis

La IA podría proponer diagramas, pero la **contabilidad de estados y transiciones requiere validación independiente**. En vez de seguir modificando prompts, introducir un validador determinista mínimo de balances antes de escalar a mecanismos y retroalimentaciones.


## C2 — Reglas formales de SD

[Experimento](experiments/c2/README.md) · [Evaluación](experiments/c2/results/c2-2026-10-13-evaluation.md): **A 4/16**, **B 6/16**, ninguna variante aceptable. Las reglas formales mejoraron un saldo de inventario, pero B todavía ubicó mal rechazos y calculó mal pendientes. **No hay prueba robusta de modelado SD autónomo.**

## C3 — Grafo tipado y verificador independiente

[Experimento](experiments/c3/README.md) · [Informe completo](experiments/c3/results/c3-2026-10-13-report.md). **15 pruebas del validador OK**. Dos respuestas de GLM: **REJECT 0/10** en la regla original de JSON puro; análisis exploratorio que quita sólo el cerco Markdown: **A 4/10, B 5/10**, ambos rechazados por stocks/transiciones inconsistentes. C3 costó US$0.0006235 estimados antes de la cuota diaria. No se alteraron datos ni se otorgó crédito a las IA por correcciones de código.

## C4 — Construir, verificar y revisar una vez

[Protocolo](experiments/c4/README.md) · [Informe de resultados](experiments/c4/results/c4-2026-10-13-report.md) · [GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38499957498).

Validador estructural con **20 pruebas positivas/negativas aprobadas**. Misma GLM-4.7-Flash: **6/10 primera propuesta → 6/10 tras una revisión**. **REJECT_AFTER_ONE_REPAIR**. La revisión agravó el anclaje al mundo observado: corrigió un saldo de inventario que era verdadero para que concordara con un consumo equivocado. Sin automatización adicional de inferencias.

C4 consumió 4,042 tokens y 55.7884 neuronas; costo estimado US$0.00061324 antes de franquicia. Nada de esto demuestra modelación SD autónoma validada en datos reales.

## C4.1 — DeepSeek-R1-32B y JSON Mode

[Protocolo](experiments/c4.1/README.md) · [Informe](experiments/c4.1/results/c41-2026-10-13-report.md) · [Run original](https://github.com/yudocyudoc/short/actions/runs/38510170508).

Se probó `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b` con prompting normal y JSON Mode nativo. En ambas respuestas, `response` incluyó razonamiento `<think>...</think>` y un bloque JSON Markdown: **0/10 en contrato estricto de salida completa**. El diagnóstico posterior aisló JSON final válido: **6/10 en estructura SD** en ambos modos, porque faltó el flujo material `inventory → consumed`. Esta inspección no reemplaza el resultado original.

Costos C4.1: **4,601 tokens**, **1,060.4033 neuronas**, ~**US$0.01166407** estimados antes de franquicia gratuita.

## C4.2 — Separación estricta de razonamiento y cobertura de stocks

[Protocolo](experiments/c4.2/README.md) · [Informe de adjudicación](experiments/c4.2/results/c42-2026-10-13-report.md) · [GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38511091953).

Mismo DeepSeek R1 Distill Qwen 32B y mismo escenario C4.1. A = contrato anterior, **9/10, REJECT** (stock pendiente 5 vs flujos que implican 8). B = mismo contrato más reglas de cobertura por stock, **10/10 + P11 PASS, ACCEPT**. Separación de `<think>…</think>` y JSON verificada; originales conservados sin reparación. **40 pruebas del verificador PASSED.**

Consumo C4.2: **5,113 tokens, 1,124.9833 neuronas, US$0.01237448 estimados** antes de franquicia. **N=1 por brazo**, señal adaptativa prometedora, no capacidad causal/generalizable demostrada.
