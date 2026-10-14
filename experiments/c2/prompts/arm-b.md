# Brazo B — Reglas FORMALIZADAS de dinámica de sistemas (SD)

Modela con las siguientes reglas generales de SD, basadas en *Business Dynamics* cap. 6 (stocks y flujos, notación, snapshot test, conservación, unidades y vínculos informativos). Son reglas de **estructura**, no datos del negocio ni respuestas correctas.

**R1. Prueba de la fotografía:** una cantidad que persistiría si el tiempo se detuviera puede ser un stock. Un número de eventos ocurridos *a lo largo de un periodo* no es por ello un stock. Una actividad no es un stock.

**R2. Firma de stock:** cada stock declarado debe incluir nombre, material/entidad que acumula, unidad, valor inicial (si se conoce), entradas, salidas y regla general de balance `final = inicial + entradas acumuladas - salidas acumuladas`. Si falta un valor, poner `desconocido` y no completar por intuición.

**R3. Firma de flujo:** cada flujo debe declarar `origen → destino`, `unidad/tiempo` y estado/stock al que modifica. Distinguir un total acumulado del periodo de una tasa instantánea; no declarar una tasa uniforme sin datos de tiempos.

**R4. Conservación:** transferir una unidad entre dos acumulaciones resta una de origen y suma una en destino; un flujo de conversión puede requerir coeficientes técnicos justificados. Un elemento no cambia de naturaleza (p. ej. solicitud/material/producto terminado) sin una transformación definida.

**R5. Stock sólo cambia por flujo:** prohibido alterar directamente un stock mediante flechas informativas. Las flechas de información sólo afectan la regulación de flujos y deben marcarse `información`; las de materia/entidades, `transferencia`.

**R6. Transiciones:** cada entidad que cambie de estado debe seguir una ruta temporal admisible. Dibujar un evento como entrada/salida sólo del estado al que efectivamente entra o del que efectivamente sale; no hacer pasar una entidad por estados incompatibles sólo para cerrar el dibujo.

**R7. Capacidad frente a resultado:** restricciones de máquina, suministro y horizonte establecen cotas, NO observaciones ni pruebas de utilización plena. Para un stock final deducido utiliza únicamente cambios observados o explícitamente inferidos del balance.

**R8. Revisión estructural final:** antes de responder revisa cada stock: (i) tiene entradas y salidas explícitas, (ii) unidades compatibles, (iii) final concuerda con datos y balance, (iv) ninguna salida desaparece sin destino, (v) ninguna retroalimentación aparece como hecho sin mecanismo sustentado. Ante contradicción, señálala; no la ocultes.

Representa la estructura en Mermaid pero **no confundas la sintaxis Mermaid con la notación formal SD**: etiqueta tipos `[STOCK]`, `[FLUJO]`, `[AUX]` y los conectores `transferencia` frente a `información`.

No agregues nuevos hechos, umbrales ni valores propios del negocio.
