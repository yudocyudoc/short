# Manifiesto de migración IGC v3

| Archivo importado | Fuente histórica | SHA-1 de objeto Git |
|---|---|---|
| src/modelica/IGCMolecules.mo | PR #25: experiments/molecular-design-loop-v1/IGCMolecules.mo | 2f83de72d38d0b8f5e866295b806d19067c5194d |
| src/modelica/IGCInformationMolecules.mo | PR #29: experiments/dual-mechanism-v1/IGCInformationMolecules.mo | 36d97a7e9de4d7ee80bf884beec6094a9bb1cf98 |

Ambos contenidos fueron copiados sin modificación; foundation/test_foundation.py calcula su objeto Git a partir de los bytes y verifica los SHA originales.

## Ramas históricas

- archive/igc-pre-v3-2026-10-17 (commit 75e9706b0761fb0920e1a1bb90171d87b88ad74d)
- archive/igc-evidence-pre-v3-2026-10-17 (commit f10510816701f0853102fbfd12065f4197007079)

Estas dos ramas guardan distintos linajes; ninguna es una fusión de todas las ramas históricas. Los PR y ramas de auditoría originales permanecen conservados.

## Frontera de confianza

Las dos clases de archivos importadas constituyen una base de ejecución verificada. El fixture nuevo es regresión de ingeniería, no mundo de evaluación ciego. No se ha migrado un mecanismo de búsqueda, ni se han adjudicado H1/H2 o ninguna hipótesis de IGC v3.

La decisión v3 posterior al texto de §9 de la hoja de ruta es abrir el PR fundacional contra main en lugar de encadenarlo a PR #29. No se cambia la normativa experimental.
