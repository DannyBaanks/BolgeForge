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
| `hello_world.mal` | 89 B | 88 B | `c8a95363dbe2e997192834cf42a6f317be4a3bef93263e026300bc8243e77601` | Andrew Cooke (2000) |
| `rot13.mal` | 33,383 B | 33,031 B | `3fa5d20f955265cc6a4dd28b5571a2a310c99d24b29077cfc4d654aa4ed88578` | Sakai & Iizawa / Nagoya Univ (2006) |
| `99_bottles.mal` | 22,807 B | 22,561 B | `f82723aa7a957f2986f554bf7f421498880bd9ee59a613861868c5c2f0741e0c` | Hisashi Iizawa / Nagoya Univ (2005) |

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
- **`hello_world.mal`**: Emisión canónica de `"Hello, world."` y parada limpia (`v`).
- **`rot13.mal`**: Cifrador/descifrador ROT13 interactivo de flujo stdin $\to$ stdout en ~30 ms.
- **`99_bottles.mal`**: Emisión completa de las estrofas de *99 Bottles of Beer on the Wall*.
