# CEI–IGC v0.2: runner independiente

`cei-igc-workbench-v02` mantiene Cloudflare Access y todas sus rutas de usuario. El ejecutor GitHub usa el Worker independiente `cei-igc-runner-v02`; el Workbench ya no ofrece rutas `/api/runner/*` en el código fuente.

El Worker runner solo acepta:

- `GET /api/runner/jobs/:id/snapshot`
- `POST /api/runner/jobs/:id/result`

Ambas rutas verifican la firma HMAC temporal con método, path y SHA-256 del body antes de consultar D1 o R2. El snapshot conserva su hash y `job_id`. El callback conserva la validación del contrato y los estados terminales. R2 usa escritura condicional de creación única; callbacks repetidos reciben HTTP 409 y no sustituyen el resultado.

El runner no tiene rutas de administración, formularios ni consultas generales, y no usa Cloudflare Access Service Auth. No se modifica la política `Allow` del investigador ni la protección del Workbench. No se crea un secreto nuevo: `IGC_RUNNER_HMAC_SECRET` del runner debe tener el mismo valor existente que usan el Workbench y GitHub Actions.

## Bindings y despliegue

El archivo `platform/cei-igc-runner-v02/wrangler.jsonc` conecta el Worker nuevo solo con el D1 `cei-igc-lab-v02` y el bucket R2 `cei-igc-lab-v02`. El secreto se administra fuera del archivo de configuración.

Desde `platform/cei-igc`, con Wrangler autenticado:

```powershell
npx wrangler deploy --config ..\cei-igc-runner-v02\wrangler.jsonc --keep-vars
npx wrangler secret put IGC_RUNNER_HMAC_SECRET --config ..\cei-igc-runner-v02\wrangler.jsonc
```

Al introducir el valor, usa la fuente segura del HMAC existente. Wrangler no permite leer de vuelta el valor guardado en el Workbench, así que no se puede copiar automáticamente desde ese Worker. No lo pegues en el repositorio, el workflow ni el chat.

Configura la variable del repositorio `yudocyudoc/short`:

```text
IGC_SERVICE_ORIGIN=https://cei-igc-runner-v02.oulipo.workers.dev
```

El workflow sigue usando `IGC_RUNNER_HMAC_SECRET` como secreto de Actions y no envía cabeceras Cloudflare Service Auth.

## Comprobaciones y única sonda

Antes de lanzar una sonda:

1. Enviar un `GET` sin firma a una ruta snapshot con UUID y comprobar HTTP 401 sin contenido del snapshot.
2. Enviar una firma HMAC inválida y comprobar que no se devuelven datos.
3. Si aparece HTTP 403, detenerse: no rotar tokens ni cambiar políticas. Revisar protección global de Workers y reglas de borde.
4. Con ambas comprobaciones aprobadas, lanzar exactamente una sonda sintética `CAF-DEMO-001` desde el Workbench autenticado.
5. Verificar el resultado firmado en el artefacto de GitHub, el estado y `result_key` en D1, el objeto correspondiente en R2 y el resultado mostrado en Workbench.

No habilitar IA ni Modelica durante esta prueba.

## Reversión

Para volver al recorrido anterior, restaura `IGC_SERVICE_ORIGIN` a `https://cei-igc-workbench-v02.oulipo.workers.dev` y revierte los commits de esta rama. Si el runner nuevo ya se desplegó, conserva el Worker mientras se revisan jobs pendientes; después se puede revertir a su versión previa con Wrangler o eliminar únicamente `cei-igc-runner-v02`. No reviertas ni despliegues cambios sobre ramas EPI-01 a EPI-06.
