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

test: mb_ref test-corpus microcat
	@echo "Verifying committed quines..."
	@for f in artifacts/candidate_m*.mal; do \
		./mb_ref "$$f" > /tmp/out.mal && diff -q "$$f" /tmp/out.mal && echo "OK $$f"; \
	done

.PHONY: all clean test test-corpus analyze-corpus synth-cat microcat

