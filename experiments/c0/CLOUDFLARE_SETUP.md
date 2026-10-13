# C0 en Cloudflare Workers AI — preparación

**Estado:** flujo y cliente REST preparados, **sin ejecutar** hasta que el propietario configure credenciales. No subir secretos al repo ni pegarlos en conversaciones.

## Costos esperados

Workers AI tiene una franquicia diaria de 10,000 neuronas (Free y Paid). En Workers Paid, el exceso se factura a US$0.011 / 1,000 neuronas. En 2026 la página del modelo `@cf/zai-org/glm-4.7-flash` anuncia tarifas equivalentes de **US$0.0605 / millón de tokens de entrada** y **US$0.40 / millón de salida**. Lo reportado por el script es **estimación antes de créditos gratuitos**, no gasto facturado.

Fuente: https://developers.cloudflare.com/workers-ai/platform/pricing/
Modelo: https://developers.cloudflare.com/workers-ai/models/glm-4.7-flash/

## Configuración (sólo una vez)

1. Cloudflare Dashboard → Workers AI → **Use REST API** → **Create a Workers AI API Token** y copiar **Account ID**. Restringir el token a ese uso; documentación: https://developers.cloudflare.com/workers-ai/get-started/rest-api/
2. En `https://github.com/yudocyudoc/short/settings/secrets/actions`, crear **dos Repository secrets**:
   - `CLOUDFLARE_ACCOUNT_ID` = identificador de cuenta.
   - `CLOUDFLARE_API_TOKEN` = token de Workers AI.
3. Abrir `https://github.com/yudocyudoc/short/actions/workflows/c0-cloudflare.yml` → **Run workflow**, seleccionando `experiment/c0-cafeteria`.

**Límites programados:** dos inferencias como máximo (A y B), `@cf/zai-org/glm-4.7-flash` fijado, máximo 2400 tokens de terminación por inferencia, ejecución manual, ninguna llamada extra por reintento automático.

Los resultados quedan como artefactos del workflow y los textos principales se imprimen en los logs para facilitar su recuperación. El diseño impide leer `evaluation/reference.md` y no concede permisos para editar GitHub.

## Resguardo metodológico

Ésta es una prueba de la gramática sistémica sobre **Cloudflare GLM-4.7-Flash**; no una reproducción del antiguo motor SD-AI ni prueba de capacidad causal o de adopción empresarial.

**Comparabilidad:** Las dos solicitudes comparten un escenario idéntico y un modelo idéntico. Si se cambia el proveedor o modelo, crear una nueva serie; no mezclar puntuaciones.
