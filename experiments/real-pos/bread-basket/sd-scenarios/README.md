# The Bread Basket — Primera aplicación condicional de SD con PySD y moléculas Hines

**Experimento:** `BREADBASKET_HINES_PYSD_CONDITIONAL_V1`.

Pregunta limitada: **¿cómo responderían estructuras conocidas de SD ante un patrón temporal extraído de transacciones registradas, si imponemos distintas capacidades hipotéticas?**

No es un diagnóstico de la panadería, no descubre colas observadas y no calibra su productividad ni demanda potencial. La fuente pública está atribuida a un negocio real, pero procede de una copia secundaria sin auditoría independiente de autenticidad.

## Procedencia de tres tipos

| Componente | Procedencia | Carácter |
|---|---|---|
| Conteos por transacción/15 minutos | POS original atribuido a The Bread Basket, fijado por commit + SHA Git | `OBSERVADO_EN_FUENTE`; posibles clientes no atendidos no identificados |
| CapUtil + invbakf | Dos moléculas **originales** de Jim Hines, cotejadas previamente contra PySD | Estructura dinámica reutilizada, no modelo causal validado para este negocio |
| Capacidad 8/16/32 pedidos por hora, objetivo 0.5 h, despacho mínimo 0.25 h, acumulaciones iniciales 0 | `scenario_config.json` | `HIPÓTESIS_EXPLÍCITA`, no parámetros medidos |

Se usan fechas fijadas **antes** del primer cálculo: 2017-02-04 (máximo de transacciones por día, 139) y 2016-10-30 (máximo de transacciones por hora, 25; total diario 79).

Por cada fecha se crean 96 intervalos de 15 minutos, incluyendo ceros en intervalos sin ventas registradas. **Esos ceros no demuestran que el negocio estuviese abierto ni que la demanda fuera cero.**

Una serie de `n` ventas registradas en un intervalo de 15 minutos se transforma a `4n` transacciones por hora como señal exógena hipotética de entrada. No se usa cada artículo vendido como una transacción adicional.

## Reutilización efectiva de Hines

El workflow `breadbasket-hines-scenarios.yml` descarga de Vensim los archivos `CapUtil.mdl` e `invbakf.mdl`, tras cotejar SHA-256 contra los originales del Drive verificados en [PR #5](https://github.com/yudocyudoc/short/pull/5) / [PR #6](https://github.com/yudocyudoc/short/pull/6).

**Sólo en un directorio temporal**, se transforman las etiquetas de unidades genéricas (`Widgets/Week`, `Widgets/Month`) a `orders/Hour` y el reloj a horas. Las ecuaciones y puntos de sus curvas originales **no** se editan; los parámetros y stocks iniciales sí se sobrescriben mediante la API de PySD para definir escenarios explícitos. Ni las copias transformadas ni los `.mdl` del autor se suben al repositorio o artifacts.

1. `CapUtil.Production` recibe el patrón de ventas registradas como `Desired Production` y una capacidad **hipotética**.
2. Esa salida simulada alimenta el flujo `Producing` de `invbakf`; la molécula también recibe `Orders` como señal registrada transformada.
3. Se registran `Backlog`, `Inventory` de pedidos preparados y `Shipping`; todo eso son resultados **SIMULADOS**.

**Límite de composición:** el encadenamiento es unidireccional. `Backlog` no realimenta la decisión de producción de `CapUtil`; sin esta conexión endógena, no debe afirmarse que obtuvimos el modelo completo de una cafetería. La molécula original de inventario terminado no representa insumos, empaques ni costos.

## Pruebas y compuertas

- Conteos por día en 96 ventanas, sin doble conteo de artículos ni imputaciones.
- Fuente congelada, hashes originales de moléculas, versión PySD 3.14.3.
- Comparación de seis corridas (2 fechas × 3 capacidades), tiempos de 0 a 24h con paso 0.25h.
- Conservación determinista de pedidos pendientes y pedidos preparados, no negatividad numérica y reporte de escenarios.
- Las salidas son un JSON resumen, serie CSV por escenario e informe de procedencia. Datos POS brutos, fuentes de Hines y traducciones de modelos son transitorios y **no** se publican.

**Resultado admisible:** demostrar ejecución reproducible y sensibilidad **condicional** a capacidades arbitrarias. **Resultados inadmisibles:** declarar que la cola existió, que el comercio tiene esa capacidad, que se sabe cuánto espera un cliente, o que se identificó una causa de pérdidas.

## Auditoría

Este estudio es independiente de M01 sintético (cocina/delivery) y vive íntegramente en `experiments/real-pos/bread-basket/sd-scenarios/`, junto con sus scripts, tests y configuración.

Al aprobar Actions, el informe tendrá procedencia, modelo fuente, parámetros declarados, series y errores de balances. La auditoría se puede reconstruir desde los commits fijados, incluso después de que expire el artifact.
