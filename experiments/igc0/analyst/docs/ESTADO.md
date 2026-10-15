# Registro de ejecución

- Paquete público verificado: 8/8 mundos; 336 registros POS; 112 cierres diarios.
- Hashes SHA-256 de fuentes, referencias tipadas e índice verificados.
- Grafos de ingeniería de referencia: 8/8 creados y renderizados desde JSON.
- Comprobaciones automatizadas: 9/9 PASS.
- Motor SD agregado inicial: ejecutado sobre 8 mundos; se detectó y corrigió doble cargo de insumos y se añadió prueba de regresión. Sigue **no calibrado** para reproducir todas las trayectorias observadas.
- Inferencias LLM: **0**, aún no se ejecutó analista externo.
- Evaluación mediante oráculo oculto: **no realizada**; ZIP reservado permanece sin abrir.
- Política de entrega: separar `output/inputs`, `output/models`, `output/diagrams` del motor agregado de prueba.
