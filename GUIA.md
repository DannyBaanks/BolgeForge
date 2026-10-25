# GUIA.md — BolgeForge para el operador

Guía de operación en español. El contrato técnico y las etiquetas de cada claim están en
[README.md](README.md), [docs/CLAIMS.md](docs/CLAIMS.md) y [docs/ROADMAP.md](docs/ROADMAP.md)
(en inglés). Esta guía no amplía claims: solo dice cómo se opera el repo.

## 1. Qué es y qué está certificado

Sintetizador y laboratorio de Malbolge Clásico. El núcleo verificado:

- cinco quines byte-exactos (el menor, m=281, 53.562 B);
- el corpus histórico de referencia;
- cuatro benchmarks comprimidos que se reconstruyen byte a byte (`cat`, `digital_root`,
  `adder`, `99_bottles`);
- **un Cat compacto de 7.690 celdas** (`artifacts/cat_compact.mal`), artefacto aparte del
  rebuild de los cuatro.

Todo lo demás (MicroCat, pilotos `candidate_cat_*`, variantes) está etiquetado como REFUTADO,
RETIRADO o ABIERTO en el ledger. No se promociona por conveniencia.

## 2. Requisitos

Linux con `gcc`, `make` y `python3` ≥ 3.10. Sin red. `mb_ref` (el oráculo estricto en C) se
compila local con `make`; no se versiona.

## 3. Comandos

| comando | qué hace | tiempo |
|---|---|---|
| `make` | compila `mb_ref` | segundos |
| `make test` | certificación completa: 52 tests, corpus, 4 comprimidos, 5 quines, espejo independiente (236 comparaciones) | ~10 s |
| `make test-rebuild` | reconstruye los 4 comprimidos publicados y exige bytes idénticos | ~5 min |
| `make test-oracle` | solo los unit tests de `tests/` | ~5 s |
| `make test-independent` | solo el espejo Olmstead independiente | ~5 s |
| `python3 tools/build_compact_cat.py --check` | reconstruye el Cat compacto y compara con lo publicado | ~2 s |
| `python3 tools/build_compact_cat.py` | reconstruye, verifica y **publica** `cat_compact.mal` | ~2 s |
| `make test-tm` / `make test-fizzbuzz` | Truth Machine / FizzBuzz | segundos |
| `make synth-cat` / `make microcat` | sintetizadores experimentales | variable |
| `make audit` / `make analyze-corpus` | auditoría de bloat / análisis del corpus | variable |

## 4. Inventario de artefactos

| archivo | celdas | SHA-256 | se genera con |
|---|---:|---|---|
| `reference/malbolge_org/cat.mal` | 9.382 | `ce04a6f2…` | referencia histórica |
| `artifacts/cat_compressed.mal` | 8.254 | `b4ddd5ec…` | `tools/resynthesize.py cat` |
| `artifacts/cat_compact.mal` | **7.690** | `0e14c807…` | `tools/build_compact_cat.py` |
| `artifacts/digital_root_compressed.mal` | 26.308 | `69c668a8…` | `tools/resynthesize.py digital_root` |
| `artifacts/adder_compressed.mal` | 44.914 | `5177cb74…` | `tools/resynthesize.py adder` |
| `artifacts/99_bottles_compressed.mal` | 21.809 | `9710e8c4…` | `tools/resynthesize.py 99_bottles` |

Los pilotos `artifacts/candidate_cat_*.mal` están **gitignorados** y **no son válidos**; se
conservan como evidencia. No confundirlos con `cat_compact.mal`.

## 5. El Cat compacto (7.972 celdas)

Plan determinista: `k=15` (`delta=1.410 = 15×94`), semilla 47, penalización de préstamo 2,
saltos directos de ventana. Preámbulo de 7.443 operaciones que termina en la celda 7.541, handoff
en 7.593, sufijo desde 9.004. Reproduce el estado de handoff de la referencia: **124/124**
variables, `a=29.524`, `d=58.975`.

Verificación manual (las tres deben pasar):

```bash
python3 tools/build_compact_cat.py --check
python3 tools/verify_handoff_state.py --reference reference/malbolge_org/cat.mal \
    --reference-cell 9067 --candidate artifacts/cat_compact.mal --delta 1410 --value-floor 9003
python3 -m unittest tests.test_compact_cat -v
```

Evidencia completa: `docs/evidence/2026-10-24-compact-cat-k15/REPORT.md`.

## 6. Reglas que no se rompen

1. **No regenerar a ciegas un artefacto publicado.** Primero `--check`; si difiere, se investiga,
   no se sobrescribe.
2. **Los informes de evidencia no se reescriben.** Se anexan erratas fechadas (ver la errata del
   2026-10-24 en `docs/evidence/2026-10-23-compact-cat-diagnosis/REPORT.md`).
3. **Un PASS es test finito, no prueba universal.** Los comprimidos se certifican sobre vectores
   documentados; así se dice en el README y en el ledger.
4. **Si tocas `tools/resynthesize.py`**, `make test-rebuild` tiene que seguir pasando byte a byte
   para los cuatro publicados. Los parámetros nuevos (`borrow_penalty`, `direct_gap`, `rng`) tienen
   valores por defecto que preservan el comportamiento histórico.
5. **La puerta de handoff tiene dos modelos.** `keep-high` (por defecto) es el que usa el
   compresor; `shift-all` solo reproduce el análisis del piloto de 2026-10-19. El control es
   `cat_compressed.mal`: 124/124 con `keep-high`, 0/124 con `shift-all`.

## 7. Mapa del repo

```
reference/malbolge_org/   programas históricos (fuente de los comprimidos)
artifacts/                publicados + candidatos (algunos gitignorados)
tools/                    sintetizadores, verificadores, puertas y tests de artefactos
oracle/mb_ref.c           VM de referencia en C (oráculo estricto)
docs/audits/…/olmstead_strict_mirror.c   espejo independiente (segunda implementación)
tests/                    unit tests (unittest)
docs/evidence/            evidencia fechada, con hashes y claims por experimento
docs/CLAIMS.md            ledger de claims (DEMONSTRATED / REFUTED / RETIRED / OPEN)
docs/ROADMAP.md           frente abierto y cerrado
```

## 8. Problemas conocidos

- Este archivo faltaba desde el inicio aunque el README lo enlazaba; esta es su primera versión.
- El generador histórico `tools/generate_compact_cat.py` no está en el repo (scratch gitignorado).
  El plan reproducible del Cat compacto es `tools/build_compact_cat.py`.
- `make test-rebuild` tarda ~5 minutos porque reconstruye `adder` y `99_bottles` desde cero.
