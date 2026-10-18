# E1 — Contrato mínimo de composición molecular

**Estado prospectivo.** Este experimento depende de E0 (PR #33). Aún no prueba descubrimiento causal, identificación de mundos ni valor de IA.

| Aspecto | Regla |
|---|---|
| Hipótesis S2 | ¿El compositor deriva enlaces válidos desde contratos de puertos, sin programar topologías particulares? |
| Entradas | Registros JSON base y extendido, clases Modelica fijadas en E0; ninguna respuesta de mundos ocultos |
| Salidas | AST con instancias/enlaces, canonicalización, compilación y simulación nativa |
| Prueba principal | Intercambiar el registro JSON, sin cambiar compositor ni backend: 6 grafos de referencia y 15 cuando se añade la ganancia informativa existente en MSL |
| Pruebas negativas | Tipos y unidades incompatibles, grafo material desconectado, parámetros fuera de rango, presupuesto exhausto, isomorfismos renombrados |
| Baseline | Generador de cuatro interruptores del PR #29, archivado y no importado. Los seis casos de E0 son controles, no respuestas que el compositor deba leer |
| Métrica | Número de grafos válidos/canónicos/compilados; diferencia por intercambio; rechazos; pruebas de no alteración física |
| Fallo genuino | Necesitar editar código del compositor para aceptar una clase registrada, conectividad incorrecta, AST no compilable, variantes precableadas o falsa novedad |
| Límites | Máximo dos instancias de tránsito, un filtro, una ganancia opcional. Extensión informacional, no mecanismo físico nuevo |
| Estado posible | TECHNICAL PASS/FAIL y COMPOSITION_ENGINEERING_PASS/FAIL acotado; I1–I4, S3–S5 siguen NOT_RUN |

La extensión se apoya en Modelica.Blocks.Math.Gain (MSL 4.0.0). No escribe ecuaciones diferenciales nuevas y no acredita identificación causal.

El conteo 15 contra 6 **no es por sí solo un éxito metodológico**. La evidencia necesaria incluye inspección de que el compositor usa resolución de puertos abiertos, pruebas de intercambio de roles y unidades, y compilación independiente. La ausencia de un mundo oculto impide declarar E2 aprobado.

## Diagrama

~~~mermaid
flowchart LR
  R["Registro molecular intercambiable"] --> P["Puertos y tipos"]
  P --> G["Composición acotada"]
  G --> L{"Linter: conexiones, unidades, materiales"}
  L -->|Válido| A["AST + canon"]
  L -->|Inválido| X["Fallo registrado"]
  A --> OM["Compilador de instancias y OpenModelica"]
  OM --> V["Regresión numérica, no identificación"]
~~~

Pruebas contra el diseño: sustitución del registro manteniendo código fuente inmutable; cambio de nombre de rol; límites de instancias modificados; conexión ilegal rechazada; canon idéntico tras renombrar nodos; no usar tablas de firmas ni verdad del evaluador.

**Decisión de parada:** si el intercambio requiere tocar el motor o si falla el backend, S2 queda pendiente/fallida en este alcance. No resolverlo con nuevos tipos de datos, sensores o extensiones no preregistradas.
