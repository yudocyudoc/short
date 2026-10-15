# Protocolo de evaluación C0 · versión 0.1

**Pregunta primaria:** ¿la gramática sistémica (brazo B) mejora la corrección estructural frente a la línea base (brazo A)?

**Estado:** preregistro de la prueba, redactado antes de ejecutar los brazos. No se han obtenido resultados.

## Procedimiento

1. Usar exactamente el mismo proveedor/modelo, versión, temperatura, longitud máxima y herramientas para A y B.
2. Proporcionar sólo tres documentos: `scenario.md` + `prompts/common.md` + `prompts/arm-a.md` **o** `prompts/arm-b.md`. El agente **no debe tener acceso de lectura al repo** ni al directorio `evaluation/`.
3. Ejecutar primero un smoke test A/B una vez. Si el formato es comparable, completar tres corridas independientes por brazo, con contextos nuevos y orden alternado A–B / B–A / A–B; no introducir aprendizaje o feedback entre corridas.
4. Guardar los textos íntegros, modelo, fecha, parámetros, orden y hashes de prompts en `results/` cuando se ejecute. No modificar rúbrica después de ver respuestas sin registrar el cambio de versión.
5. Evaluar respuestas sin conocer su brazo cuando sea posible; si no, reconocer ausencia de cegamiento.

## Rúbrica (0–2 por criterio; máximo 16)

0 = ausente / incorrecto; 1 = parcial o ambiguo; 2 = correcto, explícito y consistente.

| ID | Criterio |
|---|---|
| C1 | Distingue stocks, flujos, auxiliares y sus unidades, sin mezclar tasas con cantidades. |
| C2 | Reconoce el límite operativo de la máquina en dos horas. |
| C3 | Reconoce el límite de insumos y su papel como restricción conjunta. |
| C4 | Maneja correctamente las solicitudes no resueltas sin tratarlas automáticamente como entregas o cancelaciones. |
| C5 | No impone un límite fisiológico inventado por cliente ni convierte los 10 humanos en «10 bebidas». |
| C6 | El diagrama respeta origen/destino, stocks y límites y no fabrica material. |
| C7 | Distingue bucles demostrados de posibles bucles que exigen observación adicional. |
| C8 | Explicita incertidumbres relevantes para pasar del esquema a dinámica cuantitativa. |

**Errores críticos (veto):** afirmar entregas superiores al mínimo entre capacidad e insumos; afirmar que las 30 solicitudes son 30 entregas; asegurar un límite biológico numérico no suministrado; inventar reposición durante las dos horas; presentar causalidad no dada como hecho confirmado.

## Umbrales orientativos de avance

- Respuesta individual aceptable: **≥12/16 y ningún error crítico**.
- Señal favorable a la gramática: mediana de B al menos **3 puntos** por encima de A, **sin más errores críticos**. Con tres corridas por brazo esto es sólo una señal exploratoria, **no evidencia estadística** de superioridad.
- No mejorar sólo por longitud: puntuar precisión, no verbosidad.
- No obligar a producir bucles: para este C0 reconocer que no están identificados puede obtener la puntuación máxima.

## Límites del experimento

El caso es artificial y pequeño. Éxito en C0 NO demuestra descubrimiento automático de mecanismos causales, calibración, identificación de campo, desempeño con datos reales ni decisiones empresariales correctas. Un segundo caso con reposición retardada sería necesario para evaluar al menos una retroalimentación comprobable.
