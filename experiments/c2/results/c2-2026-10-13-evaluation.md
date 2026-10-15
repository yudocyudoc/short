# C2 — Primer A/B: reglas formales SD vs gramática conceptual

**Fecha:** 2026-10-13.  
**Workflow:** https://github.com/yudocyudoc/short/actions/runs/38491772902  
**Artefacto crudo A y B (JSON, texto, uso):** https://github.com/yudocyudoc/short/actions/runs/38491772902/artifacts/11861538966  
**Clave/rúbrica preregistrada:** [reference.md](../evaluation/reference.md).  
**Modelo:** `@cf/zai-org/glm-4.7-flash`, temperatura 0.1, una respuesta por brazo, sin acceso a la clave. Evaluador conoce brazo (no ciego).

## Balance real del escenario

- Capacidad máxima máquina: 9 bebidas/h × 3 h = **27**.
- Insumos iniciales 20, por tanto capacidad máxima conjunta **20**.
- Bebidas preparadas y entregadas observadas **14**.
- Inventario final **6**.
- 28 solicitudes: rechazadas **6**, aceptadas **22**, canceladas tras aceptación **3**, entregadas **14** y **pendientes finales 5**.

## Resultados cualitativos

**A — Gramática anterior:** 
- Acierta la capacidad de máquina 27 y techo de insumos 20, y reconoce 14 entregas.
- Declara **inventario final 20** al no descontar los 14 insumos utilizados.
- Declara **pendientes finales 0** porque equipara solicitudes pendientes con bebidas ya preparadas.
- Interpreta las 5 solicitudes restantes como no clasificadas, a pesar de existir la categoría exhaustiva de aceptadas pendientes.
- Afirma una «retroalimentación demostrada» desde la restricción de capacidad, sin evidencia de un bucle causal cerrado.

**B — Reglas formales SD:**
- Reconoce correctamente el inventario final **20−14=6**.
- Declara incorrectamente **3 pendientes finales**, cuando son **5**.
- Redacta un balance inconsistente: `0+28−19=9`, pero sostiene que final es 3; intenta «repararlo» atribuyendo 5 cancelaciones en lugar de las 3 observadas.
- Dibuja el rechazo como salida de solicitudes ya pendientes/aceptadas, pese a que se rechazan **antes** de la aceptación.
- Presenta un «límite de insumos» como retroalimentación demostrada; eso no constituye por sí solo un bucle causal.
- La salida es más formal y etiquetada, pero la verificación verbal no impidió una inconsistencia en los estados.

## Rúbrica preregistrada (0–2; máximo 16)

| ID | Criterio | A | B | Observación |
|---|---|---:|---:|---|
| F1 | Stocks frente a eventos/tasas | 0 | 1 | A equipara pedidos pendientes con bebidas ya listas; B los define mejor pero falla el estado final |
| F2 | Unidades de stock/flujo y totales/tasas | 1 | 1 | Ambos separan parcialmente tasas de totales; B mezcla «unidades», materiales concretos y bebidas equivalentes |
| F3 | Balance inventario (20−14=6) | 0 | 2 | A declara 20; B obtiene 6 |
| F4 | Partición 28 = 6+3+14+5 | 0 | 0 | Ninguno reconstruye 5 pendientes |
| F5 | Cotas 27/20 vs observado 14 | 2 | 1 | A menciona 27, 20 y 14; B menciona 9/h, 20, 14 pero no explicita 27 |
| F6 | Diagrama conserva rutas/estados | 0 | 0 | Ambos tienen transiciones erróneas, B coloca rechazo después de aceptación |
| F7 | No atribuir feedback comprobado sin evidencia | 0 | 0 | Ambos declaran retroalimentaciones como hechos que no cierran circuito |
| F8 | Reconoce incertidumbre sin inventar causas | 1 | 1 | Ambos identifican datos faltantes pero contradicen estados/atribuyen explicaciones |
| **Total** | | **4/16** | **6/16** | +2 relativo B, ambos por debajo de aceptación |

**Vetos preregistrados:** A falla inventario final y pendientes; B falla pendientes y rechazo estructural posterior a aceptación. **Ninguno es aceptable** conforme a la regla ≥12/16 sin veto.

Las puntuaciones las asignó el asistente conociendo el brazo; no son una evaluación ciega o estadística. No se comparan directamente las puntuaciones C0, C1 y C2 porque los escenarios y rúbricas difieren.

## Consumo del proveedor

| Brazo | Entrada | Salida | Total tokens | Neuronas | US$ estimados antes de franquicia |
|---|---:|---:|---:|---:|---:|
| A | 932 | 2,004 | 2,936 | 78.0716 | 0.0008580 |
| B | 1,327 | 2,071 | 3,398 | 82.6829 | 0.0009087 |
| **Total** | **2,259** | **4,075** | **6,334** | **160.7545** | **0.0017667** |

No es una factura ni confirma gastos netos tras la cuota gratuita. El modelo B consumió más tokens porque recibe un prompt más largo.

## Conclusión y próxima decisión

**Las reglas de Sterman sí mejoraron la presentación formal y el saldo de insumos, pero no bastaron para garantizar los balances de estados.** Se detecta incluso una contradicción explícita entre la comprobación escrita y la respuesta final.

En vez de insistir con cambios de prompt, siguiente ensayo propuesto: la IA produce un grafo tipado de stocks/transiciones en un formato procesable y un validador externo comprueba la partición, las direcciones, las unidades y los balances. El validador debe **rechazar** la salida si falla, no completar silenciosamente el diagrama ni adjudicar al LLM una respuesta corregida por código.

El caso es artificial y fue diseñado después de ver fallas de C1: evidencia exploratoria, no evaluación independiente de dominio real ni del antiguo SD-AI.
