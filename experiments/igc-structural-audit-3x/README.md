# IGC structural audit 3x — prueba A/B de correspondencia

Tres elementos: **(1)** diagnóstico Bread Basket sin pistas (**A**); **(2)** mismo diagnóstico con salidas de herramientas deterministas (**B**); **(3)** dos controles sintéticos inéditos W17/W18, uno con defecto y otro internamente consistente, para medir falsos positivos y transferencia. Seis solicitudes independientes al mismo modelo, sin reparación.

## Archivos

- [protocol.md](protocol.md): diseño y puntuación comprometidos antes de inferir, con hash de evaluación reservada.
- [cases.json](cases.json): un caso derivado de resultados observacionales/simulaciones anteriores y dos controles de inventario.
- [probes.py](probes.py): integración de capacidad, baseline fluido, mutaciones algebraicas y trayectoria de inventario.
- [runner.py](runner.py): 6 llamadas aisladas a DeepSeek por Cloudflare con respuestas originales preservadas.
- [test_experiment.py](test_experiment.py): siete verificaciones deterministas.
- [Workflow](../../.github/workflows/igc-structural-audit-3x.yml): CI inocuo para PR y ejecución manual explícitamente autorizada.

## Comprobar sin gastar ni usar API

Desde la raíz del repositorio:

~~~sh
cd experiments/igc-structural-audit-3x
python3 -m unittest -v test_experiment.py
python3 runner.py --dry-run --out ./prepared
~~~

El `--dry-run` solo prepara prompts y reporta hashes; no llama al LLM. Los resultados del modelo aún no existen hasta una ejecución autorizada.

## Ejecutar las seis llamadas

Una vez que GitHub reconozca el workflow en la rama principal, ir a Actions → «IGC structural audit 3x» → Run workflow, elegir rama y `RUN_SIX_CASES`. La cuenta debe tener los secretos de GitHub `CLOUDFLARE_ACCOUNT_ID` y `CLOUDFLARE_API_TOKEN` ya configurados. En la rama de PR, la compilación y las verificaciones se ejecutan sin credenciales.

Alternativa desde un entorno propio autenticado:

~~~sh
python3 runner.py --execute --out ./audit-results
~~~

Las seis respuestas originales y hashes quedan en el artifact de Actions durante 90 días. **No publicar credenciales ni la clave privada de evaluación.** No alterar prompts entre brazos ni evaluar W17/W18 antes de recibir respuestas.

## Interpretación

BB01 utiliza una fuente atribuida a ventas reales, pero las salidas de Hines son simulaciones condicionales. No estiman capacidad, cola o pérdidas reales. Los controles W17/W18 son completamente sintéticos. Los informes aritméticos entregados a B no constituyen uso autónomo de herramientas. Una victoria en tres casos no valida modelado causal general.
