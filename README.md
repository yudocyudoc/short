# Short — CEI / SD-AI

Repositorio de pruebas breves y verificables para estudiar si una IA puede construir modelos estructurales de **dinámica de sistemas**, distinguiendo balances y restricciones de mecanismos hipotéticos.

## Experimento C0

**[C0 — Cafetería mínima](experiments/c0/README.md)** compara dos brazos (sin/con gramática sistémica) sobre un mismo escenario.

**Estado al 2026-10-13:**
- ✅ Los siete controles de balance y el chequeo sintáctico de ambos runners pasaron en [GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38478172497).
- ⛔ Las solicitudes Copilot CLI fueron rechazadas por política de acceso, incluso después de activar Copilot Free y cambiar a selección automática. Ver [diagnóstico](experiments/c0/results/copilot-retry-2026-10-13.md).
- 🔧 **[Cloudflare Workers AI listo para configurar](experiments/c0/CLOUDFLARE_SETUP.md)**: dos llamadas máximas (A/B), modelo GLM-4.7-Flash, control por tokens, registro de respuestas y estimación de costos. Falta configurar secretos y ejecutar.
- Ninguna inferencia de modelo se ha completado; **todavía no existen puntuaciones A/B**.

> Identificar restricciones aritméticas no demuestra que la IA pueda descubrir mecanismos causales reales. Primero evaluamos coherencia estructural y sólo después dinámica y decisiones.
