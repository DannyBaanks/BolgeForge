#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <string.h>

static const char xlat1[] = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha";
static const char xlat2[] = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";

static inline unsigned short op(unsigned short x, unsigned short y) {
    unsigned short i = 0;
    static const unsigned short p9[5] = { 1, 9, 81, 729, 6561 };
    static const unsigned short o[9][9] = {
        { 4, 3, 3, 1, 0, 0, 1, 0, 0 },
        { 4, 3, 5, 1, 0, 2, 1, 0, 2 },
        { 5, 5, 4, 2, 2, 1, 2, 2, 1 },
        { 4, 3, 3, 1, 0, 0, 7, 6, 6 },
        { 4, 3, 5, 1, 0, 2, 7, 6, 8 },
        { 5, 5, 4, 2, 2, 1, 8, 8, 7 },
        { 7, 6, 6, 7, 6, 6, 4, 3, 3 },
        { 7, 6, 8, 7, 6, 8, 4, 3, 5 },
        { 8, 8, 7, 8, 8, 7, 5, 5, 4 },
    };
    for (int j = 0; j < 5; j++)
        i += o[y / p9[j] % 9][x / p9[j] % 9] * p9[j];
    return i;
}

static unsigned short mem[59049];
static unsigned char c_used[59049];
static unsigned char d_used[59049];

int main() {
    FILE *f = fopen("reference/malbolge_org/cat.mal", "rb");
    if (!f) return 1;
    unsigned int prog_len = 0;
    int x;
    while ((x = fgetc(f)) != EOF) {
        if (isspace(x) || x < 33 || x > 126) continue;
        mem[prog_len++] = (unsigned short)x;
    }
    fclose(f);
    for (unsigned int i = prog_len; i < 59049; i++) mem[i] = op(mem[i-1], mem[i-2]);

    unsigned short a = 0, c = 0, d = 0;
    unsigned long long step = 0;
    const char *input = "Hello\n";
    int in_pos = 0;
    int in_len = strlen(input);

    while (step < 20000) {
        if (mem[c] >= 33 && mem[c] <= 126) {
            char instr = xlat1[(mem[c] - 33 + c) % 94];
            if (step >= 8992) {
                c_used[c] = 1;
                d_used[d] = 1;
            }
            if (instr == 'j') d = mem[d];
            else if (instr == 'i') c = mem[d];
            else if (instr == '*') a = mem[d] = mem[d] / 3 + (mem[d] % 3) * 19683;
            else if (instr == 'p') a = mem[d] = op(a, mem[d]);
            else if (instr == '/') a = (in_pos < in_len) ? (unsigned char)input[in_pos++] : 59048;
            else if (instr == 'v') break;
            mem[c] = (unsigned short)xlat2[mem[c] - 33];
        }
        c = (c == 59048) ? 0 : c + 1;
        d = (d == 59048) ? 0 : d + 1;
        step++;
    }

    printf("=== EXACT CELLS USED IN CAT.MAL LOOP ===\n");
    printf("Code cells (c):\n");
    int c_count = 0;
    for (int i = 0; i < 59049; i++) {
        if (c_used[i]) {
            printf("  c=%5d (c%%94=%2d)\n", i, i % 94);
            c_count++;
        }
    }
    printf("Total code cells: %d\n\n", c_count);

    printf("Data cells (d):\n");
    int d_count = 0;
    for (int i = 0; i < 59049; i++) {
        if (d_used[i]) {
            printf("  d=%5d (d%%94=%2d)\n", i, i % 94);
            d_count++;
        }
    }
    printf("Total data cells: %d\n", d_count);
    return 0;
}
