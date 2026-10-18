/* trace_loop.c - M3 phase tracer for Classic Malbolge. Derived 1:1 from oracle/mb_ref.c
 * (same load, same padding, same instruction semantics, same step accounting),
 * plus instrumentation: phase-triggered executed/write maps and a step window.
 *
 * Usage: trace_loop <prog.mal> [max_steps] [-f from_c] [-p from_print] [-w window]
 *                    [-o outfile] [-t tracefile] [-W cell[,cell|lo-hi...]]
 * Defaults: max_steps=2^40, window=400, outfile=stdout, tracefile=none.
 * -W: watch cells; log first occurrences of execution at c in set and of data
 *     reads (j,i,p,*) at d in set; report per-cell totals at the end.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

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
static unsigned int cntA[59049], cntB[59049], wA[59049], wB[59049];
static unsigned int rA[59049], rB[59049];
static unsigned char watch[59049];
static unsigned long long wx[59049], wr[59049], ww[59049];   /* watch: exec / read / write counts */
static unsigned char wlog[59049], wlogr[59049], wlogw[59049];

#define WLOG_LIMIT 5
static void wlog_exec(unsigned short c, unsigned short d, unsigned short a, char instr, unsigned long long step) {
    wx[c]++;
    if (wlog[c] < WLOG_LIMIT) {
        wlog[c]++;
        printf("WATCH exec cell=%u step=%llu c=%u d=%u a=%u op=%c\n", c, step, c, d, a, instr);
    }
}
static void wlog_read(unsigned short cell, unsigned short d, unsigned short a, char instr, unsigned long long step) {
    wr[cell]++;
    if (wlogr[cell] < WLOG_LIMIT) {
        wlogr[cell]++;
        printf("WATCH read cell=%u step=%llu cpt d=%u a=%u op=%c\n", cell, step, d, a, instr);
    }
}

static void print_ranges(unsigned int *cnt, const char *label) {
    unsigned long long total = 0;
    int nr = 0, shown = 0;
    for (int i = 0; i < 59049; i++) if (cnt[i]) { nr++; total += cnt[i]; }
    printf("%s: %d range(s), %llu events\n", label, nr, total);
    for (int i = 0; i < 59049 && shown < 40; ) {
        if (!cnt[i]) { i++; continue; }
        int j = i;
        unsigned long long tot = 0;
        while (j < 59049 && cnt[j]) { tot += cnt[j]; j++; }
        printf("  [%d..%d] cells=%d events=%llu\n", i, j - 1, j - i, tot);
        shown++; i = j;
    }
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "Usage: %s <prog.mal> [max_steps] [-f from_c] [-p from_print] [-w window] [-o outfile] [-t tracefile]\n", argv[0]); return 1; }
    unsigned long long max_steps = 1ULL << 40;
    long long from_c = -1, from_print = -1;
    int window = 400;
    const char *outpath = NULL, *tracepath = NULL, *watchspec = NULL, *tablepath = NULL;
    int ai = 2;
    if (ai < argc && argv[ai][0] != '-') max_steps = strtoull(argv[ai++], NULL, 10);
    for (; ai < argc; ai++) {
        if (!strcmp(argv[ai], "-f") && ai + 1 < argc) from_c = atoll(argv[++ai]);
        else if (!strcmp(argv[ai], "-p") && ai + 1 < argc) from_print = atoll(argv[++ai]);
        else if (!strcmp(argv[ai], "-w") && ai + 1 < argc) window = atoi(argv[++ai]);
        else if (!strcmp(argv[ai], "-o") && ai + 1 < argc) outpath = argv[++ai];
        else if (!strcmp(argv[ai], "-t") && ai + 1 < argc) tracepath = argv[++ai];
        else if (!strcmp(argv[ai], "-W") && ai + 1 < argc) watchspec = argv[++ai];
        else if (!strcmp(argv[ai], "-T") && ai + 1 < argc) tablepath = argv[++ai];
        else { fprintf(stderr, "unknown arg %s\n", argv[ai]); return 1; }
    }
    if (watchspec) {
        char buf[65536]; strncpy(buf, watchspec, sizeof buf - 1); buf[sizeof buf - 1] = 0;
        char *tok = strtok(buf, ",");
        while (tok) {
            long lo = -1, hi = -1;
            if (sscanf(tok, "%ld-%ld", &lo, &hi) != 2) { hi = lo = atol(tok); }
            if (lo < 0 || hi >= 59049 || hi < lo) { fprintf(stderr, "bad watch %s\n", tok); return 1; }
            for (long z = lo; z <= hi; z++) watch[z] = 1;
            tok = strtok(NULL, ",");
        }
    }

    FILE *f = fopen(argv[1], "rb");
    if (!f) { fprintf(stderr, "Cannot open %s\n", argv[1]); return 1; }
    unsigned int i = 0;
    int x;
    unsigned long long src_clean = 0;
    while ((x = fgetc(f)) != EOF) {
        if (isspace(x)) continue;
        if (x < 33 || x > 126) { fprintf(stderr, "Invalid character 0x%02x\n", x); fclose(f); return 1; }
        if (i == 59049) { fprintf(stderr, "Input program too long\n"); fclose(f); return 1; }
        mem[i++] = (unsigned short)x;
    }
    fclose(f);
    src_clean = i;
    while (i < 59049) { mem[i] = op(mem[i - 1], mem[i - 2]); i++; }

    FILE *outf = stdout;
    if (outpath) { outf = fopen(outpath, "wb"); if (!outf) { fprintf(stderr, "Cannot write %s\n", outpath); return 1; } }
    FILE *trf = NULL;
    if (tracepath) { trf = fopen(tracepath, "w"); if (!trf) { fprintf(stderr, "Cannot write %s\n", tracepath); return 1; } }

    unsigned short a = 0, c = 0, d = 0;
    unsigned long long step = 0, prints = 0, out_bytes = 0, anomalies = 0;
    unsigned long long inA = 0, inB = 0;
    int loop_active = 0, halt = 0;
    unsigned long long window_end = 0;
    unsigned long long trig_step = 0; unsigned short trig_c = 0, trig_d = 0, trig_a = 0;

    while (step < max_steps) {
        unsigned short v = mem[c];
        if (v < 33 || v > 126) {
            c = (c == 59048) ? 0 : c + 1;
            d = (d == 59048) ? 0 : d + 1;
            step++;
            continue;
        }
        if (!loop_active && ((from_c >= 0 && c >= (unsigned)from_c) || (from_print >= 0 && (long long)prints >= from_print))) {
            loop_active = 1;
            trig_step = step; trig_c = c; trig_d = d; trig_a = a;
            window_end = step + (window > 0 ? (unsigned long long)window : 0);
            fprintf(stderr, "[trigger] step=%llu c=%u d=%u a=%u prints=%llu\n", step, c, d, a, prints);
        }
        if (loop_active) cntB[c]++; else cntA[c]++;

        char instr = xlat1[(v - 33 + c) % 94];
        if (watch[c]) wlog_exec(c, d, a, instr, step);
        int inwin = (loop_active && trf && step < window_end);
        if (inwin) fprintf(trf, "%llu\tc=%u\td=%u\t%c\ta=%u", step, c, d, instr, a);
        if (instr == 'j') { if (loop_active) rB[d]++; else rA[d]++; if (watch[d]) wlog_read(d, d, a, instr, step); d = mem[d]; }
        else if (instr == 'i') { if (loop_active) rB[d]++; else rA[d]++; if (watch[d]) wlog_read(d, d, a, instr, step); c = mem[d]; }
        else if (instr == '*') {
            unsigned short old = mem[d];
            if (loop_active) rB[d]++; else rA[d]++;
            if (watch[d]) wlog_read(d, d, a, instr, step);
            mem[d] = mem[d] / 3 + (mem[d] % 3) * 19683;
            a = mem[d];
            if (loop_active) wB[d]++; else wA[d]++;
            if (watch[d]) {
                ww[d]++;
                if (wlogw[d] < WLOG_LIMIT) {
                    wlogw[d]++;
                    printf("WATCH write d=%u step=%llu old=%u new=%u op=* c=%u\n", d, step, old, mem[d], c);
                }
            }
            if (inwin) fprintf(trf, "\t* d=%u:%u->%u", d, old, mem[d]);
        }
        else if (instr == 'p') {
            unsigned short old = mem[d];
            if (loop_active) rB[d]++; else rA[d]++;
            if (watch[d]) wlog_read(d, d, a, instr, step);
            mem[d] = op(a, mem[d]);
            a = mem[d];
            if (loop_active) wB[d]++; else wA[d]++;
            if (watch[d]) {
                ww[d]++;
                if (wlogw[d] < WLOG_LIMIT) {
                    wlogw[d]++;
                    printf("WATCH write d=%u step=%llu old=%u new=%u op=p c=%u\n", d, step, old, mem[d], c);
                }
            }
            if (inwin) fprintf(trf, "\tp d=%u:%u->%u", d, old, mem[d]);
        }
        else if (instr == '<') {
            fputc((int)(a & 255), outf);
            prints++; out_bytes++;
            if (inwin) fprintf(trf, "\tOUT:%u", (unsigned)(a & 255));
        }
        else if (instr == '/') {
            if (loop_active) inB++; else inA++;
            int in_ch = getchar();
            a = (in_ch == EOF) ? 59048 : (unsigned short)in_ch;
            if (inwin) fprintf(trf, "\tIN:%u", a);
        }
        else if (instr == 'v') {
            if (inwin) fprintf(trf, "\tHALT");
            step++;
            halt = 1;
            break;
        }
        if (33 <= mem[c] && mem[c] <= 126)
            mem[c] = (unsigned short)xlat2[mem[c] - 33];
        else
            anomalies++;
        if (inwin) fputc('\n', trf);
        c = (c == 59048) ? 0 : c + 1;
        d = (d == 59048) ? 0 : d + 1;
        step++;
    }

    if (outf != stdout) fclose(outf);
    if (trf) fclose(trf);

    printf("file=%s\n", argv[1]);
    printf("clean_cells=%llu loaded=%u\n", src_clean, i);
    printf("steps=%llu halt=%s prints=%llu out_bytes=%llu anomalies=%llu\n",
           step, halt ? "v" : "max_steps", prints, out_bytes, anomalies);
    if (loop_active)
        printf("trigger: step=%llu c=%u d=%u a=%u (prints=%llu)\n", trig_step, trig_c, trig_d, trig_a, prints);
    printf("stdin reads: preamble=%llu loop=%llu\n", inA, inB);

    if (outpath) {
        FILE *fo = fopen(outpath, "rb");
        FILE *fs = fopen(argv[1], "rb");
        if (fo && fs) {
            int ok = 1; unsigned long long pos = 0; int b1, b2;
            while (1) {
                b1 = fgetc(fo); b2 = fgetc(fs);
                if (b1 == EOF && b2 == EOF) break;
                if (b1 != b2) { ok = 0; printf("SANITY out==src: 0 (first diff at %llu: out=%d src=%d)\n", pos, b1, b2); break; }
                pos++;
            }
            if (ok) printf("SANITY out==src: 1 (byte-for-byte, %llu bytes)\n", pos);
            fclose(fo); fclose(fs);
        }
    }
    print_ranges(cntA, "executed c, preamble phase");
    print_ranges(cntB, "executed c, loop phase");
    print_ranges(wA, "written d, preamble phase");
    print_ranges(wB, "written d, loop phase");
    if (watchspec) {
        int any = 0;
        printf("WATCH totals (exec/read):\n");
        for (int z = 0; z < 59049; z++)
            if (watch[z] && (wx[z] || wr[z] || ww[z])) {
                printf("  cell %d: exec=%llu read=%llu write=%llu\n", z, wx[z], wr[z], ww[z]);
                any = 1;
            }
        if (!any) printf("  (no watched events)\n");
    }
    if (tablepath) {
        FILE *tf = fopen(tablepath, "w");
        if (!tf) { fprintf(stderr, "Cannot write %s\n", tablepath); return 1; }
        fprintf(tf, "cell execA readA writeA execB readB writeB\n");
        for (int z = 0; z < 59049; z++)
            fprintf(tf, "%d %u %u %u %u %u %u\n", z, cntA[z], rA[z], wA[z], cntB[z], rB[z], wB[z]);
        fclose(tf);
    }
    return 0;
}
