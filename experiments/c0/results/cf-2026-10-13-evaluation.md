# C0 — Evaluación del primer A/B Cloudflare (2026-10-13)

**Ejecución:** https://github.com/yudocyudoc/short/actions/runs/38480082589  
**Artefacto con salidas íntegramente preservadas:** https://github.com/yudocyudoc/short/actions/runs/38480082589/artifacts/11856993172  
**Motor:** Cloudflare Workers AI, `@cf/zai-org/glm-4.7-flash`, temperatura 0.1.  
**Método:** un smoke test A/B, sin acceso a `evaluation/reference.md` durante la inferencia. La evaluación posterior la hizo el asistente, **sin cegamiento** respecto al brazo. No es el motor anterior SD-AI.

## Uso registrado por Cloudflare

| Brazo | Entrada | Salida | Total tokens | Neuronas | US$ estimados antes de franquicia |
|---|---:|---:|---:|---:|---:|
| A | 731 | 880 | 1,611 | 36.0525 | 0.0003962 |
| B | 1,030 | 1,006 | 2,036 | 42.2834 | 0.0004647 |
| **Total** | **1,761** | **1,886** | **3,647** | **78.3359** | **0.0008609** |

Estimación de costo basada en los precios escritos en el ejecutor, no en una factura; pueden aplicar las neuronas gratuitas diarias. Los valores `usage` provienen de las respuestas del proveedor.

## Evaluación con rúbrica 0.1 (sin cambios posteriores)

0 = incorrecto/ausente, 1 = parcial, 2 = correcto y explícito.

| Criterio | A | B | Evidencia |
|---|---:|---:|---|
| C1 Stocks, flujos, auxiliares y unidades | 1 | 1 | Ambos nombran stocks relevantes, pero confunden totales de periodo con niveles y/o tasas: A usa unidades para flujos, B usa unidades para entregas |
| C2 Límite máquina | 2 | 2 | Ambos calculan 12 × 2 = 24 bebidas |
| C3 Límite de insumos | 2 | 2 | Ambos establecen cota de 18 bebidas |
| C4 Solicitudes no resueltas | 0 | 0 | Ambos afirman que las >=12 solicitudes no entregadas quedan necesariamente pendientes |
| C5 No inventa límite por humano | 2 | 2 | Ninguno infiere 10 bebidas a partir de 10 personas ni impone límite biológico |
| C6 Diagrama estructural | 0 | 0 | Ambos muestran auxiliares/actividades como cajas conectadas, sin representar entradas/salidas de stocks como tasas de SD trazables; los 30 eventos se presentan como stock sin distinguir aceptación |
| C7 Retroalimentaciones | 2 | 2 | Ambos dicen correctamente que C0 no identifica bucles endógenos |
| C8 Información faltante | 2 | 2 | Ambos mencionan distribución temporal, tiempos operativos o tratamiento de solicitudes |
| **Total** | **11/16** | **11/16** | **Sin mejora observada en el smoke test** |

No hay ningún veto de los **cinco errores críticos definidos inicialmente**: no se afirmó producción >18, no se llamó entregas a las 30 solicitudes, no se inventó máximo biológico numérico, no se añadió reposición, ni se presentó una causalidad externa como demostrada. **Sin embargo, aparecen dos errores materiales que la rúbrica inicial no incluyó explícitamente como veto**. Se documentan, pero no se redefine retroactivamente la rúbrica.

### Errores materiales comunes

1. **Agotamiento falso de insumos:** A y B aseguran que inventario final = 0. La cifra 18 representa una **capacidad máxima** del inventario, no producción observada. Podrían quedar insumos.
2. **Falso destino de solicitudes:** A y B aseguran que quedan al menos 12 solicitudes **pendientes**. Lo deducible es que **al menos 12 no fueron entregadas en el horizonte**; pudieron ser rechazadas, canceladas o no aceptadas, además de pendientes.
3. **Stock incorrectamente identificado:** los 30 pedidos solicitados durante dos horas son un total de eventos, no necesariamente el stock de solicitudes pendientes en una fecha.

### Particularidades

- A invierte la intuición de una cola cuando dice que si la producción fuese más rápida que la llegada, las solicitudes se acumularían.
- B mantiene las mismas conclusiones incorrectas de estado final, pese a la instrucción explícita de separar solicitudes, aceptación, producción, entregas y cobros.
- Ningún gráfico es un diagrama formal SD de niveles y tasas suficientemente riguroso para simular directamente.

## Veredicto

- La corrida **sí se ejecutó** y verificó integración Cloudflare con gasto muy reducido.
- Ambos lograron la aritmética de cotas pero fallaron al distinguir **posibilidad máxima** de **estado observado**, precisamente la competencia principal que queremos adquirir.
- Con un único par, no puede inferirse superioridad general, y aquí el puntaje fue igual. Se incumple el umbral de avance individual (>=12/16) y no hay señal de mejora B sobre A (+3).
- **No ejecutar automáticamente más repeticiones idénticas.** Antes conviene diseñar C1 que cambie deliberadamente el inventario remanente y la política de aceptación/cancelación, y luego volver a comparar con respuestas independientes. La rúbrica 0.1 se conserva; cualquier ampliación en un experimento nuevo debe preregistrarse por separado.

**No es un resultado sobre el antiguo sistema SD-AI; es un resultado sobre dos instrucciones al mismo GLM-4.7-Flash mediante Workers AI.**
