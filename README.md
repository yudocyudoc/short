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
