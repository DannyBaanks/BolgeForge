# reference/quine_lutter.malbolge

- **Qué es**: la quine clásica de referencia de Matthias Lutter (59,852 bytes;
  59,032 caracteres de programa), la línea base histórica pública del ecosistema
  Malbolge.
- **Por qué está aquí**: `synthesize.py` la usa como referencia arquitectónica —
  extrae de ella el prefijo (1,473 caracteres) y el loop slice (467 caracteres)
  de la arquitectura Lutter, y calcula contra ella los 215 objetivos de síntesis
  (paso 27,190 de la ejecución de referencia). Sin este archivo el sintetizador
  no puede correr; es un dato de entrada, no un artefacto generado.
- **sha256**: `dca8476f8b70c8462c32f661f63c5f8b1ad6c33946b3c7a9a35186c824117d98`
- **Procedencia**: copia exacta de `workspace/assembly/malbolge/quine_lutter.malbolge`
  del monorepo ISyCo (2026-10-17), que a su vez proviene de la distribución pública
  original de la quine de Lutter. Se incluye con fines de análisis y reproducción,
  con atribución; el crédito de la quine de referencia es de su autor.
