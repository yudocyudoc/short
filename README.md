# Short — CEI / SD-AI

Repositorio de pruebas pequeñas para investigar si una IA puede construir modelos estructurales de dinámica de sistemas distinguiendo balances, restricciones, stocks y flujos de causalidad hipotética.

## C0 — Cafetería mínima

[Descripción y protocolo](experiments/c0/README.md). Primera ejecución A/B con **Cloudflare Workers AI GLM-4.7-Flash**, 2026-10-13.

- **2/2 inferencias correctas técnicamente**, [GitHub Actions #38480082589](https://github.com/yudocyudoc/short/actions/runs/38480082589).
- **Evaluación estructural:** A = **11/16**, B = **11/16**, según [rúbrica original](experiments/c0/results/cf-2026-10-13-evaluation.md).
- **Hallazgo:** las dos respuestas reconocieron el máximo de 18 bebidas, pero confundieron esa cota con producción efectiva y asumieron resultados no observados: inventario agotado y solicitudes necesariamente pendientes.
- **Costo estimado:** US$0.0008609 antes de franquicia, 78.3359 neuronas y 3,647 tokens combinados.
- [Resultados, respuesta y artefacto completo](experiments/c0/results/README.md).

**Límite:** una ejecución por brazo no demuestra mejora ni fracaso general de la gramática; este ejecutor Cloudflare no es el motor previo SD-AI.
