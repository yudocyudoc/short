# IA-1 — Contrato preregistrado de interpretación y propuesta molecular

**Alcance:** I1 (extracción de evidencias para familias de mecanismos) e I2 (propuesta de un AST molecular *hipotético y ejecutable*). **No es E2 ni identifica un mundo oculto.** Base técnica: E0 #33 y E1 #34, todavía sin fusionar. Revisión adversativa aplazada por el investigador.

| Variable | Contrato |
|---|---|
| Población | 12 viñetas operativas originales, redactadas por el equipo; no son documentos independientes ni datos de empresas |
| Entradas para IA y baseline | Contexto + 3 hechos con IDs F1–F3; contrato público de roles/puertos de E1; ni gold, ni mapa de mundos, ni lista de arquitecturas correctas |
| Lo que debe separar | Evidencia física **después del despacho**; transformación de la tasa informacional; insuficiencia de observación y contradicción |
| Lo que **NO** debe inferir | Cantidad exacta de etapas, ecuaciones, parámetros verdaderos, causalidad única, mundo oculto, equivalencia dinámica |
| Salida obligatoria | JSON estricto: 2 clasificaciones SUPPORT/UNRESOLVED con IDs; un AST tipado ilustrativo; límites de lo desconocido; declaración literal de no-identificación |
| LLM inicial | `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, temperature=0, una llamada por caso, 2,600 tokens máximos de salida. No repetición a temperatura 0 como muestra independiente |
| Control | Baseline léxico declarado antes de la corrida: reconoce patrones sencillos y produce siempre un AST físico mínimo válido |
| Puntuación | Admisión estricta, citas existentes, correspondencia con decisiones de referencia codificadas por autores, AST aceptado por E1 + backend Modelica, resultados por caso |
| Penalizaciones | Cita inexistente, apoyo sin hecho, estructura de respuesta alterada, AST inválido, atribuir certeza topológica, no declarar incertidumbre |
| Gold | Archivo separado del prompt (`evaluation_gold.json`); **no constituye juicio humano independiente ni oráculo**. El LLM sólo recibe texto de hechos y registro |
| Medidas | `n`, `strict_admitted`, `valid_ast`, `strict_physical`, `strict_information`, `strict_both_evidence`, todos separados |
| Comparación justa | Mismos 12 hechos y decisiones de referencia para ambos brazos; baseline no obtiene crédito por compilar su AST fijo como causalidad identificada |
| Gate de factibilidad | Al menos una construcción AST IA válida, con justificación respaldada y sin afirmación de unicidad; informar todos los rechazos y el baseline |
| Interpretación permitida | Demostración descriptiva acotada de capacidad I1/I2 en ejemplos de autores; NO superioridad estadística ni recuperación verdadera de mecanismos |
| Interpretación prohibida | “La IA descubrió el modelo real”, “Llama valida/no valida toda la IA”, “El registro contiene la respuesta”, “12 variaciones son pruebas independientes de generalización” |

## Límite central

Si un caso únicamente informa que *el tablero aparece tarde*, la respuesta epistémica defendible es **UNRESOLVED tanto para tránsito físico como para filtro del tablero**. Una topología ilustrativa puede proponerse como hipótesis, pero no reivindicarse como verdad del mundo.

Si se registraron unidades físicamente fuera del centro y todavía no recibidas, eso respalda la familia de **almacenamiento físico posterior al despacho**. No demuestra cuántas colas existieron ni que sean exactamente BoundedQueue.

Si la recepción física está medida separadamente y el tablero aplica una transformación temporal documentada, eso respalda la **familia informacional**. No demuestra un filtro continuo concreto de primer orden.

Estos criterios evitan confundir la inferencia de una familia de mecanismos con la recuperación de una arquitectura única.

## Separación y límites de evidencia

La petición al modelo se genera exclusivamente desde `cases.json`, `registry.base.json` y reglas generales, nunca desde `evaluation_gold.json`; hay controles negativos que fallan ante fugas o claims categóricos. Pero ambos archivos están en la misma carpeta del runner: esto **no equivale al aislamiento físico exigido para E2**, cuyo mundo oculto necesita permisos y sal secreta.

La puntuación de los autores no debe transformarse en prueba adversativa independiente. Se pospone esa revisión, no se declara realizada.

## Decisión posterior

Si las respuestas muestran potencial en I1/I2, preparar comparación en las mismas condiciones con un modelo más capaz, previa autorización/acceso disponible; si Llama fracasa, reportarlo sin cancelar exploración IA. No incorporar nuevos mecanismos ni ruido para rescatar puntuación. El siguiente experimento causal E2 sólo se abrirá cuando el mundo sellado y el contraste independiente estén listos.
