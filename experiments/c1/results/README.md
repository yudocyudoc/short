# C1 — Resultados (2026-10-13)

- [Evaluación A/B preregistrada](c1-2026-10-13-evaluation.md): A = **5/16**, B = **9/16**; +4 relativo B, pero ambos < 12 y errores materiales.
- [Ejecución GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38490556407): completada con éxito, una inferencia por brazo.
- [Artefacto con respuestas originales, archivos JSON y métricas](https://github.com/yudocyudoc/short/actions/runs/38490556407/artifacts/11862055168).
- **Costo estimado antes de franquicia:** US$0.0010295 por ambas inferencias, 4,172 tokens y 93.6761 neuronas.

**Hallazgo:** la gramática resolvió mejor el saldo del inventario (5 unidades), pero falló en el stock de pedidos pendientes: B dice 11, el registro exhaustivo implica 8. A inventó dos bebidas terminadas pendientes cuando estaba prohibido almacenarlas. No hay validación de modelado SD automático en esta prueba.
