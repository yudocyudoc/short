# C0 — Copilot Free activation recheck (2026-10-13)

**Resultado:** primera inferencia bloqueada: **0 respuestas útiles**, no existe comparación A/B todavía.

1. Prueba con selección automática de modelo, brazos A/B, y límite de 1 AI Credit: terminó antes de inferencia porque CLI exige un mínimo de 30 AI Credits en `--max-ai-credits`. [GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38477822194).
2. Se actualizó a 30 AI Credits (mínimo admitido por esa versión de CLI). Primera inferencia A: `Access denied by policy settings`. El modelo no generó respuesta; el brazo B no se ejecutó. [GitHub Actions](https://github.com/yudocyudoc/short/actions/runs/38477877860).

GitHub publicó en 2026 que Copilot Free incluye CLI y acceso limitado a créditos de IA, pero ello **no garantiza** permiso en cada modo de autenticar GitHub Actions. El runner usó `GITHUB_TOKEN` con `copilot-requests: write`.

No se ha confirmado ninguna deducción de créditos por los intentos bloqueados. Sólo la sección de facturación de GitHub puede confirmar el consumo real.

Se deja Copilot sólo con disparador manual. Se preparó ruta alternativa de Cloudflare Workers AI que requiere secrets.
