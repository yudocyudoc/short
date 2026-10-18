# IGC v3 — E1 composición molecular

PR encadenado sobre [E0 / #33](https://github.com/yudocyudoc/short/pull/33), no fusionado a main. Consulte [CONTRACT.md](CONTRACT.md), [registro base](registry.base.json), [registro extendido](registry.extended.json) y la [hoja de ruta v3](../../docs/IGC_SD_HOJA_DE_RUTA_CONSOLIDADA_v3_2026-10-18.md).

Un motor de puertos abiertos deriva cadenas de flujo y ramas informativas desde clases registradas; el backend sólo instancia componentes publicados de SystemDynamics/MSL y los conecta. No hay código de respuesta por ID de escenario, oráculo, etiquetas precalculadas ni IA.

Comandos:

    python -m unittest discover -s experiments/e1 -p 'test_*.py' -v
    python experiments/e1/composer.py --registry experiments/e1/registry.base.json --out /tmp/base.json
    python experiments/e1/composer.py --registry experiments/e1/registry.extended.json --out /tmp/extended.json
    python experiments/e1/backend.py --registry experiments/e1/registry.base.json --out experiments/e1/generated/base
    python experiments/e1/backend.py --registry experiments/e1/registry.extended.json --out experiments/e1/generated/extended

Los registros se pueden cambiar sin editar composer.py ni backend.py. El nuevo componente Gain modifica señales únicamente; no se le atribuye descubrir una nueva ley física. **Una CI verde sólo puede probar composición de ingeniería acotada**, no IGC completo.
