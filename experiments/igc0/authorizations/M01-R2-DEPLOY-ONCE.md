# M01-R2 · autorización y registro de despliegue

**Fecha:** 2026-10-15
**Aprobación:** el investigador autorizó expresamente desplegar el Worker R2, sin inferencia.
**Rama:** `experiment/igc0-m01-r2-llama`.
**Alcance:** publicar `igc0-review-lab` con Llama 3.3 70B y JSON Schema IG.

## Resultado verificado
- GitHub Actions: https://github.com/yudocyudoc/short/actions/runs/38706537956
- Wrangler 4.151.0 confirmó: `Uploaded igc0-review-lab`, `Deployed igc0-review-lab triggers`.
- URL: https://igc0-review-lab.oulipo.workers.dev
- Cloudflare version ID: `4ac1bd77-ea85-4f51-aae9-fab8b564606a`.
- El deploy no llamó a Workers AI y no autorizó M01-R2 IG, REVIEW, contraste, proyecciones ni fusión del PR.

## Cierre de la autorización
El disparador temporal de despliegue por evento de PR/push fue retirado. El workflow `.github/workflows/igc0-worker-deploy.yml` vuelve a `workflow_dispatch` con `confirm_deploy` explícito.

**Inferencia M01-R2: pendiente de autorización independiente.**
