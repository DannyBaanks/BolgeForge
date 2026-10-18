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

test: mb_ref test-corpus
	@echo "Verifying committed quines..."
	@for f in artifacts/*.mal; do \
		./mb_ref "$$f" > /tmp/out.mal && diff -q "$$f" /tmp/out.mal && echo "OK $$f"; \
	done

.PHONY: all clean test test-corpus
