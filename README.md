# Short — CEI / SD-AI

Repositorio de pruebas breves y verificables para estudiar si una IA puede construir modelos estructurales de **dinámica de sistemas**, distinguiendo balances y restricciones de mecanismos hipotéticos.

## Experimento C0

**[C0 — Cafetería mínima](experiments/c0/README.md)** compara dos brazos (sin/con gramática sistémica) sobre un mismo escenario.

**Estado al 2026-10-13:**
- ✅ Pruebas deterministas de la referencia C0 ejecutadas en GitHub Actions: https://github.com/yudocyudoc/short/actions/runs/38477449642
- ⛔ Comparativa A/B no ejecutada: el proveedor rechazó la primera inferencia Copilot CLI (`Access denied by policy settings`): https://github.com/yudocyudoc/short/actions/runs/38477259600
- El ejecutor instalado usa Copilot CLI como aproximación experimental; **no es el motor previo SD-AI**.
- Véase [registro de intento](experiments/c0/results/attempt-2026-10-13.md).

> La capacidad de identificar restricciones aritméticas no demuestra que la IA pueda descubrir mecanismos causales reales. Primero evaluamos coherencia estructural y después, si procede, dinámicas y decisiones.
