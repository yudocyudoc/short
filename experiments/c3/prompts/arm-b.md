# Brazo B — Reglas formales SD

Aplica el **mismo contrato JSON** y escenario que A, pero usa estos principios formales de SD, basados en la distinción de stocks y flujos de Sterman, *Business Dynamics*, cap. 6:

1. **Prueba de fotografía:** un stock permanece si el tiempo se congela; los eventos del periodo no son por sí solos stocks.
2. **Firma de cada stock:** inicial + entradas acumuladas − salidas acumuladas = final, respetando su unidad.
3. **Firma de cada flujo:** una entidad, origen y destino definidos y total del periodo en unidad compatible. No inferir tasas instantáneas uniformes.
4. **Rutas válidas:** cada tipo de entidad pasa por estados temporalmente admisibles; una transición no debe cambiar el tipo de entidad sin una transformación explícita.
5. **Conservación:** no se fabrican unidades, las salidas tienen destino y no puede existir material preparado almacenado sin un proceso que lo permita.
6. **Restricciones:** distinguir capacidad de proceso, recursos y horizonte de resultados realmente observados.
7. **Retroalimentación:** un límite no es por sí solo un bucle causal; declarar sólo lazos con mecanismo observable, de lo contrario marcar `hypothesis`.
8. **Autoauditoría:** antes de enviar el JSON, comprobar todos los balances y que los totales observados no se vuelvan capacidades ni estados ficticios. Si falta un dato, no inventarlo.

No se proporcionan valores finales correctos ni un grafo resuelto.
