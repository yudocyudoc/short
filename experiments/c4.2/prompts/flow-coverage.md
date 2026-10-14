# C4.2 — Reglas adicionales de completitud formal SD

Trabaja con el **mismo escenario y el mismo contrato JSON** anteriores. Se agrega una obligación general de modelación, **sin darte ninguna cantidad correcta**:

- Para **cada stock**, explica su cambio desde el nivel inicial hasta el final **mediante flujos incidentes declarados en `flows`**, sin excepciones tácitas.
- Revisa stocks de naturalezas distintas por separado: una transacción de servicio no es automáticamente una transferencia física de insumo; cuando ambas ocurren, sus flujos requieren trazabilidad propia.
- Para todo stock, suma los `flows.total` con destino en ese stock y resta los `flows.total` cuyo origen sea ese stock. Esa variación neta debe coincidir con `final - initial`.
- Cada transferencia debe tener `entity`, `from`, `to`, `unit` y `total` compatibles. Las flechas informativas no transportan cantidades ni sustituyen flujos.
- Comprueba que ningún consumo real quede representado únicamente por un cambio de cifra en el inventario. No crees flujos ficticios para cerrar balances: usa únicamente los mecanismos autorizados por el escenario.
- La presencia de stock preparado sólo se justifica si la operación permite realmente que permanezca producto terminado.
- Antes de responder, verifica cobertura de todos los stocks y coherencia con **los registros observados**, no sólo con las ecuaciones entre cifras que tú inventaste.

Devuelve exactamente la forma JSON definida en el contrato anterior. No agregues campos de auditoría: el certificado de stock-flujo lo construirá un verificador externo.
