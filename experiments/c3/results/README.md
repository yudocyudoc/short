# C3 — Resultados registrados

- [Informe primario + diagnóstico post hoc](c3-2026-10-13-report.md)
- [Inferencia A/B en Workers AI](https://github.com/yudocyudoc/short/actions/runs/38493093296): ambas respuestas rechazadas, **0/10**, por JSON envuelto en Markdown (fallo de interfaz de salida).
- [Artefactos originales sin modificar](https://github.com/yudocyudoc/short/actions/runs/38493093296/artifacts/11862835762).
- [Diagnóstico de contenido sin nuevas inferencias](https://github.com/yudocyudoc/short/actions/runs/38493235639): tras eliminar exclusivamente cerco Markdown exterior, **A 4/10, B 5/10**, ambos REJECT por errores estructurales.
- **15 pruebas del validador superadas**, con casos positivos y negativos.
- **Coste estimado** A+B: US$0.0006235 antes de franquicia; 56.7216 neuronas.

**Interpretación:** el verificador sí detectó stocks ficticios, saldos incorrectos y unidades/rutas problemáticas; **ningún grafo de IA fue aceptado**. El diagnóstico posterior es explícitamente exploratorio y no reemplaza la nota de la rúbrica preregistrada.
