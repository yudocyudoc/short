# C3 — Grafo tipado + validación determinista

**Estado:** ejecutado; ambas respuestas rechazadas por el validador original. El diagnóstico secundario también rechazó ambos grafos.\n\n**Pregunta:** ¿un modelo de IA puede convertir la descripción de un turno de cafetería en un grafo SD tipado que supere comprobaciones de conservación, transiciones, unidades y límites, sin que el verificador corrija la salida?

Se contrasta **A** (gramática conceptual anterior, misma estructura JSON) contra **B** (reglas formales SD, misma estructura JSON). Ambos usan GLM-4.7-Flash en Cloudflare Workers AI y reciben idéntico escenario y contrato de JSON. Sólo cambia el conjunto de reglas del brazo. Se realizó un smoke test de una inferencia por brazo. [Ver reporte](results/c3-2026-10-13-report.md).

**Control de sesgo:** esta es una prueba *exploratoria adaptativa*, diseñada después de los fallos C0–C2. El escenario y criterios del validador se escriben ANTES de pedir las respuestas. La clave estructurada se lee sólo después de generar salida.

## Archivos

- `scenario.md`: escenario que recibe la IA
- `prompts/contract.md`: estructura JSON exacta que ambas variantes deben entregar
- `prompts/arm-a.md` y `arm-b.md`: las dos condiciones
- `evaluation/facts.json`: hechos estructurados **sólo para validador**, no enviados a la IA
- `evaluation/criteria.md`: criterios y límites preregistrados
- `scripts/c3_validator.py`: verificador determinista, no repara salidas
- `tests/test_c3_validator.py`: pruebas positivas y negativas, sin servicios externos
- `results/`: respuestas originales, reportes y consumo

El modelo debe devolver un grafo en JSON y no una imagen Mermaid. El dibujo será una proyección posterior del grafo, no un sustituto de estructura formal.

## Qué demuestra y qué no

El validador puede establecer coherencia **respecto a los hechos del experimento**. No puede probar que los hechos del mundo sean verdaderos, ni descubrir por sí solo estructuras faltantes. Tener un grafo válido no prueba identificación causal, precisión predictiva ni corrección de decisiones.
