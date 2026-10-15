# C0 — Cafetería mínima

**Estado:** especificación lista para ejecutar; **ninguna corrida de IA realizada**.  
**Objetivo:** comprobar si dar una gramática estructural mínima mejora la capacidad de un modelo de IA para reconstruir stocks, flujos y restricciones sin inventar causalidad.

## Pregunta

¿Una IA produce una representación de SD más coherente cuando recibe reglas generales de conservación, capacidad, incertidumbre y stocks/flujos, comparada con la misma IA sin esas reglas?

No evaluamos calibración, predicción, optimización de precios, identificación de causalidad real ni viabilidad económica de una cafetería completa.

## Archivos

- [Escenario que recibe el modelo](scenario.md)
- [Instrucciones comunes, idénticas para ambos brazos](prompts/common.md)
- [A: instrucción sin gramática](prompts/arm-a.md)
- [B: instrucción con gramática sistémica](prompts/arm-b.md)
- [Protocolo de comparación](evaluation/protocol.md)
- [Referencia y rúbrica, **sólo para el evaluador**](evaluation/reference.md)
- [Registro de ejecuciones](results/README.md)

## Ejecución manual sin cambiar SD-AI

En una conversación **sin acceso al repositorio completo**, suministrar exclusivamente `scenario.md`, `prompts/common.md` y el archivo del brazo elegido; mantener idénticos motor, versión y parámetros de inferencia. No proporcionar al modelo `evaluation/`, otros resultados ni respuestas de corridas anteriores.

El escenario ofrece condiciones necesarias, no un modelo resuelto. Los valores y criterios esperados están en `evaluation/reference.md`, que debe mantenerse fuera del contexto de ambos brazos.

## Decisión posterior

Si el brazo B demuestra mejor coherencia sin errores críticos, añadir un segundo caso con reposición retardada y un bucle verificable. Si no, examinar errores específicos antes de programar cualquier motor matemático.
