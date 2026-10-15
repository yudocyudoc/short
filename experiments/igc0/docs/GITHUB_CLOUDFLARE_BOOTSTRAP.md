# IGC0 · Bootstrap de auditoría GitHub ↔ Cloudflare

Este documento describe la **estructura implementada**, no un despliegue ya realizado.

## Contratos

**Entrada HTTP** a `POST /v1/infer` (Bearer obligatorio):

```json
{
  "schema_version": "igc0.worker.v1",
  "case_id": "M01",
  "stage": "IG",
  "request_id": "igc0-123456789-1-ig",
  "messages": [
    {"role": "system", "content": "Contrato de grafo versionado en GitHub"},
    {"role": "user", "content": "{... evidencia pública M01 ...}"}
  ]
}
```

**Salida HTTP**: `schema_version, case_id, stage, request_id, model, provider_result`. En modo REVIEW los mensajes tienen secuencia `system → user → assistant` (JSON anterior completo) `→ user` (errores deterministas), lo cual da continuidad sin suponer memoria del proveedor.

**Roles:** Worker sólo protege endpoint y ejecuta Workers AI; Python del repo verifica, prepara, guarda respuestas inalteradas y compara; GitHub Actions versiona evidencia y propone PR a auditoría. El Worker no tiene credenciales GitHub, no consulta fuentes adicionales ni evalúa el modelo.

**Límites:** un intento I/G, máximo una revisión. Si el primer JSON es ilegible, sin segunda llamada. Si el primer grafo es aceptado, no se llama a revisión. Si es rechazado por unidades, fuentes, stocks o enlaces, el mismo grafo + diagnóstico se entregan a REVIEW. No hay reparaciones deterministas invisibles.

**Estado:** configuración de Wrangler y workflows manuales disponibles, CI con pruebas locales. **Se requiere secreto de acceso del Worker** y autorización explícita antes de modificar Cloudflare o consumir IA.
