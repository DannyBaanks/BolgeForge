CC ?= gcc
CFLAGS ?= -O2 -Wall

# Verification oracle: independent C implementation of Classic Malbolge
# (Olmstead semantics, whitespace skipped on load, no trailing conventions).
all: mb_ref

mb_ref: oracle/mb_ref.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f mb_ref

.PHONY: all clean
