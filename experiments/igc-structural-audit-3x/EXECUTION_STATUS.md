# Estado de ejecución — IGC structural audit 3x

- Rama experimental GitHub: `experiment/igc-structural-audit-3x` derivada de `experiment/breadbasket-hines-scenarios`.
- Protocolo y rúbrica comprometidos antes de inferencia. Evaluador reservado fuera de GitHub; solo se registra su hash SHA-256.
- Comprobaciones locales del paquete: siete pruebas PASS y seis solicitudes preparadas, sin LLM.
- Control aritmético: BB01 139 y 79 ventas, dos series de 96 intervalos; seis producciones de CapUtil reproducibles; baseline de fluido y dos casos de reposición.
- GitHub CI: el PR ejecuta únicamente pruebas y preparación; **sin llamadas externas**, incluso si se abre un PR.
- Ejecución real: solo desde el `workflow_dispatch` con elección explícita `RUN_SIX_CASES`, o con `runner.py --execute` en entorno autorizado. No asumir éxito sin un run/artifact verificable.
- Si falla el modelo en un caso, conservar salida original; no reintentos automáticos ni reparaciones.
