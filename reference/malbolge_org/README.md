# Corpus de Referencia malbolge.org

Programas canónicos de Malbolge clásico publicados en [malbolge.org](https://malbolge.org/) por Matthias Lutter y colaboradores, integrados en BolgeForge para pruebas de conformidad, benchmarking y reproducción.

## Inventario de Artefactos

| Archivo | Bytes totales | Caracteres de programa | SHA-256 | Autor / Origen |
|---|---|---|---|---|
| `cat.mal` | 9,503 B | 9,382 B | `ce04a6f27b7045b6e0010d6c97873ad8b34ba87c7be6e16d53be0b97a7224a52` | Matthias Lutter (2012) |
| `digital_root.mal` | 32,596 B | 32,136 B | `d23023b73b16d86a8bfd2a470f4d9f4cfc531a78abfd7ce431eae3d2197c1e6d` | Matthias Lutter (2012) |
| `adder.mal` | 57,283 B | 56,476 B | `f7a23ea3d55d943489653d17ff0f4e048f81bb952bc81f1d313a0a26151dcf7a` | Matthias Lutter (2012) |
| `quine-2012.mal` | 59,032 B | 59,032 B | `419e274e3fa7f6356473a17058571cf3bcca9b0652063c27acebce064a800a4f` | Matthias Lutter (2012) |
| `quine.mal` | 59,852 B | 59,032 B | `dca8476f8b70c8462c32f661f63c5f8b1ad6c33946b3c7a9a35186c824117d98` | Matthias Lutter (2015) |

## Ejecución y Verificación

Todos los artefactos se ejecutan contra el oráculo independiente en C de BolgeForge (`mb_ref`):

```bash
make
python3 test_corpus.py
```

### Comportamiento Verificado:
- **`cat.mal`**: Eco interactivo de stdin en stdout hasta EOF.
- **`digital_root.mal`**: Calcula la raíz digital de un entero positivo en base 10 (ej: `42 -> 6`, `12345 -> 6`, `99 -> 9`).
- **`adder.mal`**: Lee dos enteros separados por salto de línea y emite su suma (ej: `12 + 34 -> 46`, `999 + 1 -> 1000`).
- **`quine.mal` / `quine-2012.mal`**: Autorreproducción exacta bit a bit (0 bytes de diferencia).
