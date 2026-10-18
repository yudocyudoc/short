# E0 — REAL_RESULTS (primera corrida, sin inferencia IGC)

**Referencia:** [GitHub Actions #39102876405](https://github.com/yudocyudoc/short/actions/runs/39102876405) · [Artefactos nativos y matriz](https://github.com/yudocyudoc/short/actions/runs/39102876405/artifacts/12126973452).  
**Commit ejecutado:** ea63c9fb72e0776efd1c792ddbb2cc0e29dff64f.  
**Fecha registro UTC:** 2026-10-18.  
**Alcance:** pruebas prospectivas del contrato E0 y controles públicos del evaluador. **No se ejecutó ningún modelo de IA, mundo con gold oculto, ciclo de selección contra oráculo ni predicción reservada.**

## Evidencia real

| Control | Resultado |
|---|---|
| Validación declarativa y fuentes Modelica históricas | PASS |
| Tests Python del contrato (incluye grafo físico desconectado, tipos, canon, parámetros, leak y presupuesto) | **12/12 PASS** |
| Tests Python del comparador numérico, perfiles y compensación de parámetros | **7/7 PASS** |
| Expansión únicamente del evaluador de referencia | 6 estructuras × 2 capacidades × 4 estímulos = **48** |
| CSV de simulaciones OpenModelica | **48/48 producidos**; trabajo CI PASS |
| Matriz numérica por pares con capacidades **iguales** | P cap3 **15/15 separables**; Q cap3 **15/15**; P cap100 **15/15**; Q cap100 **14/15**, **1 no resuelto** |
| Matriz estructural conservadora con capacidades **cruzadas** | P **15/15 pares separables en la rejilla P0**; Q **14/15 pares separables, 1 no resuelto** |
| Filtro informacional: diferencia máxima física sobre escenarios pareados | **8.953399692757102e-7**, bajo umbral operativo **1e-5**, no exactitud matemáticamente demostrada |
| Pulso alto con capacidad de tránsito 3 unidades/h | Saturación observada: **true** en CSV |
| Veredicto técnico | **PASS** |
| Veredicto metodológico | **ENGINEERING_ONLY** |

### Interpretación estricta

- Los 15 pares son combinaciones entre **seis modelos construidos expresamente en el evaluador**. El sistema **no los descubrió**, ni eligió cuál representa el mundo.
- P conserva información física e informacional; Q ve únicamente el tablero. El par que permanece sin resolver en Q es una limitación de identificabilidad **bajo estas observaciones, estímulos y rejilla numérica**, no una afirmación de equivalencia estructural global.
- La matriz fuerte compara cada par también con *distintas* capacidades admisibles en cada modelo. Es deliberadamente más conservadora que cotejar sólo candidatos con exactamente los mismos parámetros. Sigue limitada al grid P0 {3, 100} unidades/h y residencia total 1.6 h.
- Se usaron diferencias de **series numéricas reales**, no etiquetas manuales SYNC/LAG ni firma de respuesta conocida.
- El parámetro error_bound = 1e-5 es un **umbral operacional declarado**, **NO una cota de error de solver certificada**. La etiqueta UNRESOLVED no prueba equivalencia.
- Aun cuando las 48 simulaciones sean correctas, ningún resultado implica que un compositor futuro genere libremente esas estructuras, ni que un LLM interprete documentos o proponga causalidad.

## Lo que habría hecho fallar este control

Un grafo desconectado con aristas tipadas, un filtro que modifica flujos físicos más allá del umbral, una conexión material/señal sin adaptador, matrices calculadas con columnas ocultas por el perfil Q, rejillas temporales diferentes o más consultas de oráculo de las presupuestadas. Los tests negativos dan evidencia de que el resultado **no está garantizado por la lógica del gate**. El contraste de mundos secretos aún no ha ocurrido.

## Estado y decisiones pendientes

**E0 contrato implementado, verificación técnica superada. E0 no se declara demostración metodológica ni autorización automática de E2.**

1. Revisión adversativa del PR #33: linter, observabilidad física/tap, compensación de parámetros, independencia evaluador/constructor y si hay falsificadores aún tautológicos.
2. Caracterizar error de solver independientemente y fijar una tolerancia justificada **antes de E2**. Si el umbral cambia, se versiona el contrato y no se reetiquetan los resultados anteriores.
3. Sellar la verdad E2 con sal privada y un ejecutor que impida realmente el acceso desde el constructor; no usar las seis referencias públicas como clave secreta.
4. Abrir E1 e IA-1 en PR distintos **tras** revisión del contrato. Las pruebas de extensibilidad del registro e inferencia LLM siguen **NOT_RUN**.

**Referencias:** [CONTRACT.md](CONTRACT.md), [catalog.json](catalog.json), [protocol.json](protocol.json), [hoja de ruta v3](../../docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md).
