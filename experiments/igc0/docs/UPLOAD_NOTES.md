# IGC-0 v0.1 — Código y datos públicos versionados

Código íntegro, pruebas y ocho casos públicos importados desde los archivos de desarrollo de IGC-0.

- `analyst/`: ingestión, grafo SD de ingeniería, validación, render Mermaid y runner optativo del LLM. **Aún no hay resultados del LLM.**
- `generator/`: simulador discreto de evaluación y pruebas públicas, **sin oráculo ni semillas/configuraciones secretas**.
- `public/`: ocho paquetes de observación, índice y fuentes. **Nunca contiene las etiquetas del oráculo.**
- `aggregate/`: motor SD agregado experimental y sus errores de ajuste. **No calibrado; no autoriza decisiones económicas.**
- `analyst/inputs/IGC0_8_mundos_analista.zip`: empaquetado público original para ejecutar scripts sin modificar rutas.

## Comandos

```sh
cd experiments/igc0/analyst
python src/prepare.py --public-zip inputs/IGC0_8_mundos_analista.zip --out output
python src/igc.py --inputs output/inputs --out output
python -m unittest discover -s tests -v
```

El evaluador reservado (`IGC0_oraculo_evaluador.zip`) **no se publica**. El paquete generado de modelos iniciales y diagramas no se incluye como respuesta del LLM: se regenera desde código. Los tests deben pasar antes de ejecutar cualquier inferencia.
