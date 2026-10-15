# IGC-0 · GitHub ↔ Cloudflare ↔ GitHub (infraestructura inicial)

**Estado (2026-10-14 México):** Worker, contratos, pruebas y workflows de despliegue/inferencia publicados en la rama experimental. **No se ha desplegado un Worker ni llamado a DeepSeek mediante esta nueva ruta.** Todos los tests actuales son sin costo ni conexión a Cloudflare.

## Diseño

```text
GitHub: código / prompts / M01 público / validador Python
   | Actions (manual, permisos mínimos)
   +--> Wrangler despliega Worker `igc0-review-lab`
   |       GET /health    (sin inferencia)
   |       POST /v1/infer (Bearer IGC_API_KEY requerido)
   |           |
   |           +-- binding AI: @cf/deepseek-ai/deepseek-r1-distill-qwen-32b
   |
   +--> GitHub Actions M01 audit (manual):
           prepara evidencia, llama IG, archiva respuesta cruda
           valida JSON con igc_split_gate.py
           si falla con JSON legible: envía JSON+errores a REVIEW
           valida otra vez; guarda v0/v1, hashes y uso
           propone PR de resultados sin modificar código/validador
```

**No es aún Cloudflare Workflows**: es un Worker invocado por GitHub Actions. Cloudflare conserva cero estado entre llamadas. GitHub envía explícitamente el JSON anterior y los errores en mensajes de la revisión. Mantener esta separación permite auditar revisiones sin depender de memorias implícitas.

## Archivos

- `src/index.mjs` — Worker autenticado y limitado a M01, etapas IG/REVIEW/C; cada request hace como máximo una llamada al binding AI. Sin GitHub token, R2, D1 u oráculo.
- `wrangler.jsonc` — Worker `igc0-review-lab` con un binding `AI`; ningún secreto versionado.
- `tests/worker.test.mjs` — tests Node nativos, sin Cloudflare.
- `../analyst/src/cloudflare_bridge.py` — intermediario GitHub que guarda respuesta original, prompt, evidencia y validación; máximo una revisión automática si el primer grafo es JSON válido pero incorrecto.
- `../analyst/tests/test_cloudflare_bridge.py` — tests con mocks, sin IA.
- `.github/workflows/igc0-worker-ci.yml` — tests automáticos en GitHub; **no despliega ni consume inferencias**.
- `.github/workflows/igc0-worker-deploy.yml` — **sólo manual**; Wrangler deploy desde GitHub.
- `.github/workflows/igc0-worker-audit.yml` — **sólo manual**, exige confirmación explícita, máximo dos inferencias, crea rama y propone PR con resultados.

## Configuración necesaria, sólo cuando se autorice desplegar

En **GitHub → Settings → Secrets and variables → Actions**:

| Nombre | Tipo | Fuente |
|---|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | secreto existente | ID de cuenta Cloudflare |
| `CLOUDFLARE_API_TOKEN` | secreto existente | Token de cuenta: **debe autorizar desplegar Workers**; las inferencias REST previas no acreditan este permiso |
| `IGC_WORKER_API_KEY` | **secreto nuevo** | Clave aleatoria de 24+ caracteres para proteger `/v1/infer`; no es una API key de Cloudflare ni GitHub |
| `IGC_WORKER_URL` | variable nueva | URL HTTPS del Worker obtenida después del despliegue, sin `/v1/infer` |

El workflow de despliegue usa `cloudflare/wrangler-action@v4`, se ejecuta sólo si se marca `confirm_deploy=true`, y transfiere `IGC_WORKER_API_KEY` al Worker como **secret binding `IGC_API_KEY`**. Si el Worker se despliega sin ese secreto, devuelve HTTP **503** a las solicitudes de inferencia. GET `/health` es público y no consume IA.

**Seguridad:** no colocar claves ni mensajes con datos sensibles en código, JSON de resultados o logs. Este piloto sólo recibe información pública de mundos **sintéticos** M01. Al desplegar, usar un token Cloudflare con el ámbito más limitado que permita Worker deploy.

## Secuencia manual prevista

1. Revisar y aprobar PR del código; los workflows `workflow_dispatch` pueden requerir estar presentes en la rama por defecto para aparecer en el selector de GitHub.
2. Crear el secreto nuevo `IGC_WORKER_API_KEY`, conservar los dos secretos Cloudflare existentes, y verificar que el token Cloudflare tenga permiso de edición de Workers.
3. Ejecutar **IGC0 manual Cloudflare Worker deploy** con confirmación desde Actions. Este paso modifica infraestructura Cloudflare; no se ejecuta por push.
4. Copiar el Worker URL en la variable `IGC_WORKER_URL`; verificar GET `/health` y un rechazo HTTP 401 sin credencial.
5. Ejecutar **IGC0 M01 audited Worker inference** en la rama `experiment/c0-cafeteria` con opción `RUN_M01_ONE_REVIEW`. Es el **único paso con coste potencial de Workers AI**, hasta dos llamadas.
6. GitHub Actions prepara los datos, ejecuta I/G → validador → posible REVIEW; crea el artefacto, rama `igc0/audit-<run_id>-<attempt>` y, si GitHub permite a Actions crear PRs, un PR separado hacia `experiment/c0-cafeteria`.

Si el permiso `contents: write` está restringido, **el artefacto de Actions permanece** pero la creación de rama fallará. Si la organización impide que `GITHUB_TOKEN` cree pull requests, quedará disponible la rama de resultados y la acción lo indicará sin esconder el problema. Un PR no implica validación científica ni debe fusionarse automáticamente.

## Qué se registra

Cada intento guarda `input.json`, `prompt.md`, `summary.json`, carpeta `IG/` y, si corresponde, `REVIEW/`. Cada carpeta incluye `request.json` **sin Authorization**, `worker_response.json`, `raw_response.txt`, `reasoning.txt` si existe, `model.json` cuando es JSON completo, `validation.json` y `transport.json` con SHA-256, consumo reportado, estado y cero reintentos. **Nunca se sobrescribe el modelo original con la revisión.**

No hay ejecución de la etapa C, proyecciones numéricas ni lectura del oráculo en este circuito inicial. Aunque un JSON apruebe las compuertas, la estructura causal y el comportamiento temporal aún requieren evaluación independiente.

## Riesgos que siguen abiertos

- El Worker no almacena ni coordina pasos duraderos. Si GitHub Actions falla entre llamadas, no reanuda desde un checkpoint como Cloudflare Workflows.
- El `request_id` correlaciona entrada/salida, **no garantiza idempotencia** en Workers AI ante reenvíos externos. No automatizar reintentos con el mismo ID.
- Una única M01 no demuestra eficacia. El conjunto C0–C5 y M01 v1–v3 sigue siendo exploratorio.
- Los resultados se versionarán en rama separada, no se promueven a `main` sin revisión.
