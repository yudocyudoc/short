# Resultados C2 (2026-10-13)

**Ejecutado** con Cloudflare GLM-4.7-Flash, una respuesta por brazo.

- [Evaluación A/B, rúbrica preregistrada](c2-2026-10-13-evaluation.md): A **4/16**, B **6/16**. Ninguna respuesta pasó el umbral; ambas violaron invariantes críticos.
- [GitHub Actions #38491772902](https://github.com/yudocyudoc/short/actions/runs/38491772902).
- [Respuestas íntegras y usage del proveedor (ZIP)](https://github.com/yudocyudoc/short/actions/runs/38491772902/artifacts/11861538966).
- **Costo estimado antes de cuota gratuita:** US$0.0017667, 6,334 tokens, 160.7545 neuronas.

**Conclusión:** las reglas SD explícitas ayudaron parcialmente a distinguir inventario y producción pero no evitaron calcular mal pendientes, ubicar mal rechazos y declarar retroalimentaciones inexistentes. El siguiente experimento no debería afinar prompts, sino **separar propuesta de grafo tipado y validación independiente**.
