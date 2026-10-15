# IGC-0 · Criterios de evaluación propuestos, pendientes de adjudicación independiente

Los ocho mundos constituyen un **piloto de desarrollo**, no una campaña confirmatoria. Congelar la colección permite evaluar versiones futuras, pero no transforma el conjunto en una muestra aleatoria no intervenida.

Se propone registrar cuatro ejes **sin sumarlos en un único 11/11**:

1. **Estructura identificada:** stocks/pipes/retardos/fuentes correctos y falsos elementos; exactitud por clase y cobertura sobre la ontología del problema, con adjudicación independiente.
2. **Contraste:** localización de diferencias operativas/de campo que están sustentadas; falsos positivos en los mundos nulos; abstención cuando dos mecanismos son observacionalmente equivalentes. Se debe distinguir detección de discrepancia de identificación de su causa.
3. **Proyección:** error por ventana y por día de pedidos entregados, saldo de inventario, caja y cuentas por cobrar bajo políticas reservadas; siempre con modelo, parámetros y hash de corrida. Si no hay datos suficientes, reportar `DESCONOCIDO` en lugar de una cifra.
4. **Utilidad decisional:** acción elegida, factibilidad y arrepentimiento económico respecto a la mejor acción factible del oráculo bajo la función de pérdida sintética. Las acciones no viables requieren un marcador aparte: un beneficio aparente obtenido con caja negativa no es admisible.

**Controles futuros** (no ejecutados): regla determinista/hoja de cálculo sin LLM; LLM con tabla y sin formalización SD; IGC con pipes y simulación reducida. Cada brazo debe recibir **las mismas observaciones** y no tener acceso a configuraciones ocultas. Las puntuaciones deben conservar intervalos de incertidumbre y costo, y los umbrales deberían fijarse por un revisor distinto del autor del generador.

Cuidado con un problema de puntuación: múltiples puertas que dependen de la misma arista no son observaciones independientes. Los errores estructurales y epistémicos deben reportarse por tipo raíz, además de cualquier veto de aceptación.
