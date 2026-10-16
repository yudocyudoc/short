# Autorización de archivo de resultados PySD — una sola ejecución

Guardar una copia **derivada y sin materiales originales** del experimento aprobado [GitHub Actions #38843656367](https://github.com/yudocyudoc/short/actions/runs/38843656367), artifact `12022676608` SHA-256 `4c646a55e6775a52a36056db676251b94e881d47ee197e3402acd35e28b971ab`.

- Rama destino: `igc0/audit-breadbasket-hines-38843656367-1`, separada del código experimental.
- Contenido: reportes JSON, series CSV derivadas, procedencia y SHA-256 individual de cada archivo.
- Incluir advertencia de producción excesiva bajo interpretación *make-to-order*, no ocultarla.
- No copiar originales de Jim Hines, el POS bruto ni modelos transitorios `.mdl`.
- **No ejecutar nuevamente PySD ni inferencias LLM al archivar**.
- Una vez verificado el archivo, borrar workflow temporal `breadbasket-hines-archive-once.yml`.
