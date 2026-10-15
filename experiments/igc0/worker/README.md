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
| `CLOUDFLARE_API_TOKEN` | secreto existente | Sólo inferencia REST de experimentos previos; **no se usará para desplegar** |
| `CLOUDFLARE_DEPLOY_TOKEN` | **secreto nuevo** | Token separado, con permisos para crear y actualizar Workers; restringir a una cuenta |
| `IGC_WORKER_API_KEY` | **secreto nuevo** | Clave aleatoria de 24+ caracteres para proteger `/v1/infer`; no es una API key de Cloudflare ni GitHub |
| `IGC_WORKER_URL` | variable nueva | URL HTTPS del Worker obtenida después del despliegue, sin `/v1/infer` |

El workflow de despliegue usa `cloudflare/wrangler-action@v4`, se ejecuta sólo si se marca `confirm_deploy=true`, y transfiere `IGC_WORKER_API_KEY` al Worker como **secret binding `IGC_API_KEY`**. Si el Worker se despliega sin ese secreto, devuelve HTTP **503** a las solicitudes de inferencia. GET `/health` es público y no consume IA.

**Seguridad:** no colocar claves ni mensajes con datos sensibles en código, JSON de resultados o logs. Este piloto sólo recibe información pública de mundos **sintéticos** M01. Al desplegar, usar un token Cloudflare con el ámbito más limitado que permita Worker deploy.

## Secuencia manual prevista

1. Revisar y aprobar PR del código; los workflows `workflow_dispatch` pueden requerir estar presentes en la rama por defecto para aparecer en el selector de GitHub.
2. Crear los secretos nuevos `IGC_WORKER_API_KEY` y `CLOUDFLARE_DEPLOY_TOKEN`, conservando `CLOUDFLARE_API_TOKEN` exclusivamente para inferencias anteriores. El nuevo token debe tener permiso de creación y despliegue sobre la cuenta elegida.
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


## Preflight real de credenciales (14 de octubre de 2026, México)

Se agregó [`igc0-worker-preflight.yml`](../../../.github/workflows/igc0-worker-preflight.yml) que corre con `push` en la rama experimental, **sin despliegue, sin tocar datos de cuenta y sin inferencias**.

[Resultado del preflight #38688147098](https://github.com/yudocyudoc/short/actions/runs/38688147098):

- Cuenta Cloudflare configurada con ID de longitud correcta.
- `CLOUDFLARE_API_TOKEN` presente y **activo**: el endpoint de token de **usuario** confirmó `active`; el endpoint de cuenta devolvió 401 porque es otro tipo de token.
- **No** se han verificado privilegios para crear Workers. Cloudflare requiere rol **Admin para el producto Workers** al crear `igc0-review-lab` (puede limitarse después a Editor del Worker concreto).
- `IGC_WORKER_API_KEY`: **aún no existe** como secreto GitHub (mínimo 24 caracteres).
- `IGC_WORKER_URL`: todavía vacía; se llenará sólo después de que el deploy real entregue la URL.
- Estado final: `ready_to_attempt_deploy=false`, sin intentos de despliegue.

**Operación humana mínima para desbloquear:**

1. En el equipo local generar una clave aleatoria nueva (por ejemplo, `python -c "import secrets;print(secrets.token_urlsafe(48))"`). No pegarla en un issue, comentario, PR ni chat.
2. En GitHub, `short → Settings → Secrets and variables → Actions → New repository secret`, guardar esa clave como `IGC_WORKER_API_KEY`. No confundirla con un token Cloudflare. El workflow de despliegue la copia como secret binding `IGC_API_KEY`.
3. En Cloudflare, crear **otro token**, separado del existente `Workers AI`, con alcance de creación de Workers (Workers product Admin o plantilla `Edit Cloudflare Workers` cuando aparezca) y recursos restringidos a la cuenta del experimento. Guardarlo en GitHub como `CLOUDFLARE_DEPLOY_TOKEN`.
4. Los workflows `workflow_dispatch` sólo aparecen normalmente en el selector de Actions cuando su definición está presente en la **rama predeterminada `main`**. Estos archivos siguen en la rama `experiment/c0-cafeteria`, por lo que **no hay botón de despliegue garantizado aún**. Revisar la PR y promover sólo el workflow necesario (o fusionar el código autorizado) a `main` antes de ejecutarlo. No se ha fusionado ni desplegado automáticamente.
5. Tras un despliegue autorizado, guardar `IGC_WORKER_URL` como variable de repositorio y verificar `/health`, rechazo HTTP 401 sin Bearer, y el ciclo M01 sólo después de revisar los artefactos de CI.

No se tiene en esta conexión una acción para editar GitHub Actions secrets ni administrar API tokens Cloudflare; por eso **ninguna credencial se ha creado, transferido ni revelado** durante esta preparación.

## Separación de credenciales, actualización 2026-10-14

El usuario confirmó en captura que el token actual llamado `Workers AI` concede sólo **Account → Workers AI → Read/Edit** y recursos `All accounts`. Ése es el token para invocar el modelo, **no** para desplegar código. No ampliar su alcance: crear **otro** token `IGC0 Worker Deploy` para Wrangler, preferiblemente desde la plantilla oficial **Edit Cloudflare Workers** y limitado a la cuenta deseada. El workflow `igc0-worker-deploy.yml` y el preflight utilizan ahora el secreto nuevo `CLOUDFLARE_DEPLOY_TOKEN` en lugar de `CLOUDFLARE_API_TOKEN`. La ejecución experimental vía REST previa permanece sin cambios. El preflight histórico #38688147098 validó únicamente el token anterior; se requiere nueva comprobación después de configurar el de despliegue.


## Despliegue y verificación final (2026-10-15 UTC)

**¡Desplegado y comprobado!** Este apartado supersede el estado inicial de «no desplegado» más arriba, conservado como registro de la preparación histórica.

- [Despliegue manual #38691612368](https://github.com/yudocyudoc/short/actions/runs/38691612368) desde `main` con el código congelado en `a25e2e42343c8f544fe7d37b1b5477a49b4f396a`.
- Worker creado: `igc0-review-lab` · URL: `https://igc0-review-lab.oulipo.workers.dev`.
- Wrangler 4.151.0 creó el secret binding `IGC_API_KEY` y desplegó correctamente el binding de Workers AI.
- [Prueba pública #38692026022](https://github.com/yudocyudoc/short/actions/runs/38692026022): GET `/health` = 200; POST `/v1/infer` sin bearer o con bearer incorrecto = 401.
- [Prueba de secreto real #38692244343](https://github.com/yudocyudoc/short/actions/runs/38692244343): POST autenticado con **contrato deliberadamente inválido** = 422 `INVALID_IGC_CONTRACT`. Esto comprueba que el secreto compartido funciona sin invocar Workers AI.
- Se corrigió `analyst/src/cloudflare_bridge.py` para enviar `User-Agent: IGC0-GitHub-Audit/1.0`. El `User-Agent` predeterminado de Python-urllib provocaba un 403 de Cloudflare `error code: 1010`, independiente de la autenticación del Worker.
- **Workers AI / DeepSeek: cero llamadas en todas las comprobaciones posteriores al despliegue.** No se ha ejecutado M01-R1.

El workflow [`igc0-worker-audit.yml` en `main`](https://github.com/yudocyudoc/short/blob/main/.github/workflows/igc0-worker-audit.yml) se instaló como lanzador **exclusivamente manual**, opción predeterminada `DO_NOT_RUN`; fija el commit probado del analista `2d4c686f6c79fc5cb30bcad05ddc1106cb4db25e`, usa la URL verificada y requiere cambiar deliberadamente a `RUN_M01_ONE_REVIEW` para permitir máximo dos llamadas. No se activó esta opción. La publicación automática del PR de resultados aún no se ha comprobado con una corrida real.
