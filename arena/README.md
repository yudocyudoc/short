# Arena CEI–IGC — núcleo GitHub v0.1

La Arena **no es** el antiguo probe de Cloudflare: el expediente, las tres vías y los artefactos viven en GitHub o en el entorno local. Cloudflare se reserva para inferencia de IA mediante el adaptador existente que ya esté probado; este núcleo no necesita tokens de Cloudflare, callbacks, D1, R2 ni HMAC.

## Flujo reproducible

1. Autor registra problema, agente focal (controla / influye / observa) y evidencia con tipo epistemológico, fuente y `as_known_at`.
2. `prepare` genera un snapshot **visible** con hash distinto para cada vía: A convencional, B SD determinista, C IGC.
3. Cada constructor (humano, IA o Modelica según corresponda) produce una respuesta JSON: hipótesis rivales, refutadores, evidencia citada, incertidumbres, pruebas discriminantes y costo.
4. `validate` comprueba la respuesta y sella su contenido. No acepta campos `gold`, `holdout` ni adjudicaciones del propio constructor.
5. `adjudicate` emite resultado **solo de ingeniería**. G1/G2/G3 quedan `NOT_ADJUDICATED`; ninguna simulación ni prueba estructural demuestra verdad empírica. La evaluación ciega, contrafactual y comparación de costos se implementará en una fase posterior.

```bash
python -m unittest discover -s arena/tests -v
python -m arena.cli prepare arena/examples/cafeteria.json C_IGC output/visible.json
python -m arena.cli validate output/visible.json output/submission.json output/sealed.json
python -m arena.cli adjudicate output/visible.json output/sealed.json output/verdict.json
```

Los últimos dos comandos requieren que un constructor genere `output/submission.json`. No se fabrica ese resultado ni se asignan automáticamente PASS metodológicos.

## Fronteras

- Una anotación `HIPOTESIS` sigue siendo hipótesis; no convertirla en `OBSERVADO`.
- La reserva real debe permanecer fuera del directorio entregado al constructor; el chequeo de claves no sustituye un custodio ni una auditoría de aislamiento.
- No se ha implementado todavía compositor, linter L0–L6, evaluación ciega real, comparación A/B/C ni puente de IA. Son próximas capas, no éxitos atribuidos a esta versión.
- No ejecutar el antiguo `igc-arena-probe.yml` como si fuera una Arena.
