CC ?= gcc
CFLAGS ?= -O2 -Wall

# Verification oracle: independent C implementation of Classic Malbolge
# (Olmstead semantics, whitespace skipped on load, no trailing conventions).
all: mb_ref

mb_ref: oracle/mb_ref.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f mb_ref

test-corpus: mb_ref
	python3 test_corpus.py

analyze-corpus: mb_ref
	@for f in reference/malbolge_org/*.mal; do \
		python3 tools/analyzer.py "$$f"; \
		echo ""; \
	done

synth-cat: mb_ref
	python3 tools/synthesize_cat.py

microcat: mb_ref
	python3 tools/microcat.py
	python3 tools/assemble_microcat.py

test-compressed: mb_ref
	python3 tools/test_compressed.py

test-tm: mb_ref
	python3 tools/verify_truth_machine_full.py

test-fizzbuzz: mb_ref
	python3 tools/test_fizzbuzz.py

test-oracle: mb_ref
	python3 -m unittest discover -s tests -v

test-quines: mb_ref
	python3 tools/test_quines.py

test-independent: mb_ref
	python3 tools/test_independent.py

# Strict certification never regenerates artifacts or treats rejected prototypes
# as working Classic programs. Negative loader controls are in test-oracle.
test: test-oracle test-corpus test-compressed test-quines test-independent

test-rebuild: mb_ref
	python3 tools/resynthesize.py all --check

audit: mb_ref
	python3 tools/audit_bloat.py

.PHONY: all clean test test-oracle test-quines test-independent test-rebuild test-corpus test-compressed test-tm test-fizzbuzz analyze-corpus synth-cat microcat audit

