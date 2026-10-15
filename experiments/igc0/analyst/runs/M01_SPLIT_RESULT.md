# IGC-0 · M01 v3 — Primera ejecución de I/G → compuerta → C

**Estado:** ejecutado y adjudicado. **IG: REJECT. C: NO EJECUTADO**.
Fecha: 2026-10-14 México / 2026-10-15 UTC. Este intento es **adaptativo** posterior a M01 v1/v2; no constituye réplica independiente.

## Fuentes permanentes

- [Protocolo congelado antes de inferir](M01_IGC_SPLIT_PROTOCOL.md)
- [Contrato I/G](../prompts/ig_graph_v3.md) · [Contrato C](../prompts/ig_contrast_v3.md)
- [GitHub Actions #38684669725](https://github.com/yudocyudoc/short/actions/runs/38684669725) — **una llamada real**, sin reintento
- [Respuestas crudas, provider JSON, razonamiento, entrada, SHA y compuerta](https://github.com/yudocyudoc/short/actions/runs/38684669725/artifacts/11949757660)
- [Inspección posterior sin IA](https://github.com/yudocyudoc/short/actions/runs/38684843230) · [artefacto diagnóstico](https://github.com/yudocyudoc/short/actions/runs/38684843230/artifacts/11949428230)

## Ejecución

Antes de inferir: **60 tests del analista PASS** (incluidos casos de compuerta positiva/negativa y la prueba de que C nunca se consulta si I/G falla), además de cuatro tests del generador. Input público M01 inalterado: `3ede7ef04e172c04f9ab5564c57bc1b1e5d88ba63c19b76660e9941f13dec6df` (42 filas POS, 14 cierres). Se conservaron los contratos previos, sin acceso al oráculo ni al SD agregado no calibrado.

DeepSeek `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b`, temperatura 0.1, máximo 4500 tokens de salida, una petición I/G con `stream=false`. API: OK. Transporte: `think_fenced`, JSON final **completo y parseable**.

**Compuerta I/G: REJECT**, con dos fallos explícitos:
- `MISSING_DOMAIN_STOCK`: ninguna acumulación de pedidos (`orders`) fue declarada; el modelo sólo incluyó `cash` (MXN), `inventory` (meals_equivalent) y `receivables` (MXN).
- `DANGLING_INFO_LINK`: conexión informativa `orders → inventory` apuntó a `orders`, que **no existe** como stock o pipe declarado.

**Por definición de la compuerta, C quedó `SKIPPED_IG_REJECT`.** No se realizó una segunda llamada ni se generó un contraste o proyección.

## Inspección sustantiva posterior

Los dos errores son los identificados por el validador, **no un inventario exhaustivo de fallas de modelación**. El grafo propuesto se redujo a cuatro componentes de operación:

- Stocks: `cash`, `inventory`, `receivables`; los tres `initial=null` con `DESCONOCIDO`, **aunque el paquete público sí incluía saldos iniciales observados de caja e inventario**.
- Pipes: `sales_to_cash: orders → cash` con unidad MXN/day e `inventory_to_orders: inventory → orders` con unidad meals_equivalent/day. Las etiquetas de ambos fueron `HIPÓTESIS`, sin citas.
- Cuatro roles (cocina compartida, cola, despacho, liquidación): **todos marcados `unknown`**. Debe distinguirse entre ausencia de evidencia del comportamiento del virtual y ausencia de información de la referencia: **la referencia sí proporciona una capacidad calibrada de cocina**.
- Se declararon tres incógnitas: cocina, cancelaciones y ventanas de servicio; ninguna conexión de cocina compartida ni pipe de colas fue modelada.

No afirmamos que los dos pipes sean correctos porque pasaron un chequeo elemental de unidad de borde: `orders` se utilizó como **estado de frontera no declarado**, por lo que la representación sigue siendo ambigua. No existe modelo operativo IGC completo.

## Uso

| Métrica | Valor |
|---|---:|
| Llamadas reales al LLM | **1** |
| Tokens entrada | **18,377** |
| Tokens salida | **1,402** |
| Tokens totales | **19,779** |
| Neuronas reportadas | **1,452.2338** |
| USD estimados, antes de franquicia | **0.01597653** |
| Llamadas C | **0** |
| Reintentos | **0** |

El costo se estimó con tarifas por token utilizadas en los experimentos previos (DeepSeek R1 Distill Qwen 32B, $0.497/M input y $4.881/M output). No es una factura ni confirma cobro.

## Interpretación

**La infraestructura dividida funciona y evita gastar en un contraste sobre un grafo rechazado.** Además, a diferencia de v2, I/G produjo JSON completo. Esto **no demuestra que la separación haya causado la mejora de formato**, porque también cambió la longitud y el contenido del prompt.

**Identificación y graficación sustantiva siguen sin validarse**: el modelo omitió la acumulación de pedidos y trató como desconocidos saldos disponibles en la evidencia. No es honesto aumentar el puntaje agregando automáticamente `orders` o convirtiendo `unknown` en `observed`: eso sería repararlo con código.

### Siguiente decisión (no ejecutada)

Analizar la decisión de cómo representar entidades y conversiones sin sobre-dirigir la ontología. Antes de ensayar otro prompt, conviene evaluar si el input completo, de ~18k tokens, está saturando la tarea I/G. Sería lícito preparar una **ficha pública determinista y trazable de stocks y caudales** (sin sugerir nodos ni flujos obligatorios), con fuentes preservadas, para reducir carga de lectura; eso constituiría otro experimento, explícitamente distinto.

M02–M08 permanecen sin ejecutar. No se consultó el oráculo ni se autorizó una proyección contrafactual.
