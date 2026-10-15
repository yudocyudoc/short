# C0 — Registro de resultados

## Primera inferencia A/B: 2026-10-13

**Completada con éxito:** Cloudflare Workers AI, dos respuestas GLM-4.7-Flash, [workflow #38480082589](https://github.com/yudocyudoc/short/actions/runs/38480082589).

- [Evaluación con rúbrica preregistrada](cf-2026-10-13-evaluation.md): A = **11/16**, B = **11/16**.
- [Uso de tokens y estimación de precio](cf-2026-10-13-usage.json): 3,647 tokens y 78.3359 neuronas; US$0.0008609 estimados antes de franquicia.
- [Respuesta original A](cf-2026-10-13-run-1-A.md).
- [Artefacto ZIP original, incluidas ambas respuestas y datos del proveedor](https://github.com/yudocyudoc/short/actions/runs/38480082589/artifacts/11856993172).

Ambos modelos aciertan el límite de 18 bebidas, pero ambos declaran sin evidencia que el inventario termina en 0 y que las solicitudes no entregadas siguen pendientes. **No se observó mejora por agregar la gramática en este único smoke test.**

## Incidencias anteriores

- [Primer intento Cloudflare: token incorrecto](cloudflare-auth-2026-10-13.md).
- [Intentos Copilot: bloqueos de política](copilot-retry-2026-10-13.md).
- [Primera prueba fallida Copilot](attempt-2026-10-13.md).

**Los siete controles deterministas pasaron**, pero no se confunden con desempeño de IA. No se han ejecutado las tres repeticiones por brazo previstas en el protocolo para después del smoke test.
