# C5 — Transferencia de reglas SD a una biblioteca de préstamo

**Pre-registro antes de inferencia.** Un dominio nuevo: ejemplares físicos circulan entre tres stocks reversibles; las reservas son entidades de otro tipo y no se pueden sumar a los ejemplares.

Se usa un mismo escenario y contrato JSON para dos inferencias independientes de DeepSeek R1 Distill Qwen 32B, ambas con la capa estricta `<think> + JSON` de C4.2 y la misma verificación determinista. El **único cambio del brazo B** es la adición **verbatim** de `experiments/c4.2/prompts/flow-coverage.md`. Ni se edita ni se reescribe esa gramática después de mirar C5.

A — instrucciones generales compartidas. B — esas instrucciones + gramática C4.2 sin editar.

**Limitación importante:** para que las transiciones sean comprobables mecánicamente, el contrato proporciona nombres candidatos de stocks y estados. Por tanto C5 **no prueba que el LLM descubra una ontología completamente nueva sin ayuda**. Prueba si conserva balances, rutas y tipos materiales en un dominio distinto al café, sin adaptar la regla B.

[Escenario](scenario.md) · [Contrato común](prompts/contract.md) · [Criterios congelados](evaluation/protocol.md).
