# Piloto IGC de moléculas y evidencia — primera ejecución real

**Fecha local:** 2026-10-16 (America/Mexico_City).  
**Ejecución de Cloudflare + GitHub Actions:** [#38988377874](https://github.com/yudocyudoc/short/actions/runs/38988377874).  
**Artefacto íntegro:** [12083938465](https://github.com/yudocyudoc/short/actions/runs/38988377874/artifacts/12083938465) — 24 solicitudes, respuestas originales, salida del proveedor, scores, manifiesto y hashes.  
**Versión sometida a prueba:** commit `1bcf658f253b6f11677082d7cad074a3e39a204d`.  

## Protocolo completado

- Doce casos empresariales cualitativos sintéticos, sin cifras ni datos reales; cuatro mecanismos posibles. No se ejecutó OpenModelica, no se formularon ecuaciones y ningún LLM recibió parámetros numéricos.
- Enfoque A: reglas deterministas transparentes sobre los hechos públicos.
- Enfoque B: Llama 3.3 70B (Cloudflare, temperatura 0) con prompting SD cualitativo general y nombres de las mismas cuatro opciones.
- Enfoque C: mismo Llama y hechos, con contratos enriquecidos de las cuatro moléculas: mecanismos, señales, requisitos, exclusiones y nivel de madurez.
- Una inferencia por brazo y caso; 24/24 respuestas recibidas; sin reintentos. Orden de brazos alternado por caso. Máximo 1,250 tokens de respuesta.
- Se exigieron citas literales con ID de hecho y se cotejó, por separado, si el hecho citado estaba anotado como respaldo de la molécula. Esa última anotación es un juicio humano preregistrado para esta muestra, NO un verificador semántico general.

## Resultados observados

| Métrica | Reglas | Llama SD general | Llama con moléculas |
|---|---:|---:|---:|
| Casos evaluados | 12 | 12 | 12 |
| Selección exacta de moléculas/abstención | **12** | 9 | **11** |
| Citas literales válidas | **12** | 11 | **12** |
| Citas apoyadas por la clave de evidencia | **12** | 9 | **11** |
| Criterio estricto (selección + respaldo) | **12** | 9 | **11** |
| Moléculas elegidas sin respaldo esperado | 0 | 3 | 1 |
| Falsas abstenciones | 0 | 0 | 0 |

La diferencia pareada entre B y C es **2 casos favorables al andamiaje y 0 favorables al prompt general**. Este número es demasiado pequeño para concluir superioridad; una prueba exacta binomial bilateral sobre esos dos casos discordantes produciría p = 0.5, sin ajuste por diseño exploratorio.

### Fallos concretos

**P01 — Fabricante para almacén.**  
El SD general eligió `BACKLOG_FLOW + MTO_S2_PATTERN` pese a que F1 dice que fabrica para almacén *antes* de compras, e ignoró `CAP_UTIL` pese a evidencia explícita de producción deseada y capacidad. Con moléculas enriquecidas eligió la combinación correcta `BACKLOG_FLOW + CAP_UTIL`. Ejemplo de selección causal corregida al contar con exclusiones semánticas.

**P07 — Mercancía en tránsito hacia inventario comercial.**  
El SD general eligió `MATERIAL_DELAY + BACKLOG_FLOW + MTO_S2_PATTERN`. Añadió una cola de producción bajo pedido sin respaldo; además una cita pretendía sostener backlog en un hecho que sólo describía recepción de inventario. El andamiaje eligió correctamente `MATERIAL_DELAY + BACKLOG_FLOW` y aportó citas respaldadas.

**P11 — Ajuste de plantilla.**  
Ambos prompts escogieron equivocadamente `CAP_UTIL` a partir de contratación hacia dotación objetivo. Aunque las citas eran literales, **esas afirmaciones NO prueban un mecanismo de producción deseada frente a capacidad nominal productiva**. El catálogo no contenía la molécula adecuada de ajuste de plantilla; el comportamiento esperado era abstenerse. Este error muestra que los contratos de exclusión no bastan aún para controlar analogías excesivas.

Los otros nueve casos pasaron en ambos brazos. El criterio de literalidad por sí solo no salva el fallo P11: la selección fue causalmente inapropiada con cita existente.

## Limitaciones decisivas

1. **Techo no ciego:** la misma colaboración redactó los casos y el baseline de expresiones regulares en el mismo trabajo. **Antes de llamar al LLM**, el baseline ya había obtenido 12/12. Es evidencia de que el conjunto es demasiado sencillo o demasiado alineado con sus reglas, no de generalización determinista. No debilitamos el baseline después.
2. **Muestra pequeña:** doce parejas, dos mejoras netas, sin potencia confirmatoria. No se puede afirmar superioridad poblacional del andamiaje molecular.
3. **La intervención cambia el volumen y el detalle de instrucciones:** B recibe nombres de opciones; C además los contratos funcionales. No se puede aislar si la mejora es por estructura formal, información adicional o ejemplos implícitos de exclusión.
4. **Selección, no construcción abierta:** sólo cuatro mecanismos: tres Hines con fuente y paridad, y un patrón IGC S2 ya ejecutado, pero todavía no empaquetado como molécula independiente. Los casos no verifican compatibilidad de conectores, formulaciones, parametrización ni observaciones.
5. **Citas literales vs inferencia:** las comprobaciones exactas bloquean atribuciones inexistentes, pero no demuestran semántica ni verdad empírica. Se necesitó una clave anotada humanamente.
6. **No observaciones reales:** ninguna puntuación valida causalidad de una empresa o identifica parámetros.

## Decisión recomendada

**Mantener IGC-SL como diseño, NO escalar todavía a una biblioteca grande ni a 30 intentos de reparación.** El siguiente estudio debería congelar ambos clasificadores antes de obtener los casos nuevos y crear una muestra ciega por un autor independiente. Debe incluir negaciones, analogías superficiales (como workforce/capacity), variantes de lenguaje y composición de mecanismos, y usar idénticas instrucciones base y presupuesto informativo controlado para comparar el aporte del contrato.

Un piloto reproducible ya existe: commit, prompts, outputs, etiquetas y scripts están archivados. Las tres cifras relevantes son: baseline 12/12, Llama SD general 9/12 y Llama con andamiaje 11/12; **resultado exploratorio favorable al catálogo en dos casos, no prueba de ventaja general**.
