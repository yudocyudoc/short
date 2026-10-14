# C1 — Primera evaluación A/B: Cloudflare GLM-4.7-Flash

**Fecha:** 2026-10-13 (UTC 2026-10-14 00:30).  
**GitHub Actions:** https://github.com/yudocyudoc/short/actions/runs/38490556407  
**Respuestas originales y métricas del proveedor:** https://github.com/yudocyudoc/short/actions/runs/38490556407/artifacts/11862055168  
**Referencia preregistrada:** [reference.md](../evaluation/reference.md), creada **antes** de ejecutar los modelos.  
**Evaluador:** asistente ChatGPT, no ciego al brazo. **1 corrida por brazo, sólo smoke test**. Ningún modelo recibió la referencia.

## Consumo real registrado (no es facturación)

| Brazo | Tokens entrada | Tokens salida | Tokens totales | Neuronas | USD estimados antes de franquicia |
|---|---:|---:|---:|---:|---:|
| A | 792 | 1,167 | 1,959 | 46.8348 | 0.0005147 |
| B | 1,091 | 1,122 | 2,213 | 46.8413 | 0.0005148 |
| **Total** | **1,883** | **2,289** | **4,172** | **93.6761** | **0.0010295** |

Modelo `@cf/zai-org/glm-4.7-flash`; temperatura 0.1; límite de 2 llamadas y 2400 tokens de salida por respuesta. La estimación de tarifa no confirma cargo real tras franquicia diaria.

## Referencia estructural

- **Capacidad potencial:** 12/h × 2 = **24 bebidas**; insumos 18 → cota conjunta **18**.
- **Observación:** 13 preparadas y entregadas (no 18).
- **Inventario al cierre:** 18 − 13 = **5** unidades equivalentes.
- **Solicitudes:** 30 = **13 entregadas + 5 rechazadas + 4 canceladas + 8 pendientes**.
- **Aceptadas:** 30 − 5 = **25**, de las cuales 4 se cancelaron, 13 se entregaron y 8 quedan pendientes.

## Evaluación preregistrada: 0–2 por criterio (máximo 16)

| ID | Criterio | A | B | Justificación |
|---|---|---:|---:|---|
| C1 | Tipos, unidades y destinos | 0 | 1 | A representa «pendientes» como bebidas ya preparadas, imposible en el caso; B reconoce pedidos pendientes, pero mezcla flujos (unidades en vez de unidades/h) y cantidades |
| C2 | Cota máquina 24 / conjunta 18 | 1 | 1 | Ambos calculan 24. Ninguno fija explícitamente la cota conjunta de 18 al describir resultados |
| C3 | Las 13 entregas observadas no son la capacidad | 1 | 2 | A reconoce 13 entregadas pero luego inventa 15 preparadas; B conserva 13 preparadas y entregadas |
| C4 | Inventario final correcto: 5 | 0 | 2 | A resta dos bebidas fantasma adicionales y concluye que quedan 3; B calcula 18−13=5 |
| C5 | Solicitudes: 5 rechazo, 4 cancelación, 13 entrega, 8 pendientes | 0 | 0 | A produce 2 pendientes inventando stock terminado; B produce 11 pendientes y afirma erróneamente sólo 17 aceptadas |
| C6 | Diagrama SD compatible con balance y destinos | 0 | 0 | Los dos diagramas contienen flujos/inventarios mal conectados; B muestra rechazos saliendo de aceptadas cuando el rechazo ocurre antes |
| C7 | No atribuye bucles causales no observados | 2 | 2 | Ambos señalan la ausencia de evidencia de retroalimentación endógena |
| C8 | Separa hechos, límites e incertidumbres | 1 | 1 | Ambos identifican algunos datos ausentes, pero hacen afirmaciones de estado no sustentadas |
| **Total** | | **5/16** | **9/16** | **B mejoró 4 puntos, pero no superó 12/16** |

### Errores materiales

**A:** construye un stock de dos bebidas terminadas «pendientes» contradiciendo el hecho de entrega inmediata y ausencia de producto terminado almacenado; declara 15 preparadas cuando sólo se observaron 13; inventa 3 de inventario remanente y 2 pedidos pendientes. Confunde material con solicitudes.

**B:** acierta stock de insumos (5) y total preparado (13). Sin embargo, informa «17 aceptadas» cuando fueron 25, y «11 pendientes» cuando son 8, pese a que sus categorías están disponibles. Su diagrama muestra rechazos como salida de aceptación y pendientes como salida de preparación, relaciones incompatibles con los hechos. Un error aparece incluso con categorías enumeradas exhaustivamente.

**Ninguna** incorporó un bucle endógeno ficticio, correctamente.

## Decisión metodológica

- **Mejora relativa inicial B vs A:** +4 puntos, que satisface el criterio orientativo de diferencia, pero no el umbral absoluto de respuesta aceptable (**12/16**). Por tanto, **no declaramos éxito estructural**.
- **No extrapolable:** el escenario y la rúbrica C1 son distintos de C0, no se deben comparar puntuaciones entre escenarios como una estimación estadística.
- Los criterios de «error crítico» habían enumerado valores erróneos concretos (inventario 0/18, pendientes 17). Los errores observados (A inventario 3 / pendientes 2, B pendientes 11) **son tan sustanciales como aquellos, pero no fueron añadidos retroactivamente a la lista de veto**. Registrarlos como hallazgos que sugieren mejorar la próxima rúbrica.
- **Siguiente paso recomendado:** no refinar el prompt buscando la respuesta. Introducir un **validador determinista de estados y transiciones** fuera del LLM: entradas → aceptación/rechazo → cancelación/entrega/pendiente; insumos iniciales − preparación. Pedir a la IA estructura y explicación; contrastar su propuesta contra invariantes.

### Limitación

Se probó un único par A/B en GLM-4.7-Flash, no el antiguo SD-AI. No hay inferencia de que la gramática mejore consistentemente ni de que la IA reconstruya mecanismos causales nuevos.
