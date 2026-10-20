#!/usr/bin/env python3
"""Reproduce the audit against an immutable checkout; preserve every run's I/O.

Usage: python3 audit_e2e.py CHECKOUT STRICT_ORACLE OUTPUT_NEW_DIRECTORY
The checkout must have mb_ref built. STRICT_ORACLE is compiled from the separately
preserved Olmstead mirror. This audits behavior; it does not change production.
"""
import array
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

ROOT, STRICT, OUT = map(Path, sys.argv[1:4])
OUT.mkdir(parents=True, exist_ok=False)
LOCAL = ROOT / "mb_ref"
ROWS = []


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(label, argv, payload=b"", expected=None, timeout=6, cwd=ROOT):
    start = time.monotonic()
    try:
        p = subprocess.run(list(map(str, argv)), input=payload,
                           capture_output=True, timeout=timeout, cwd=cwd)
        stdout, stderr, rc, status = p.stdout, p.stderr, p.returncode, "EXIT"
    except subprocess.TimeoutExpired as e:
        stdout, stderr, rc, status = e.stdout or b"", e.stderr or b"", None, "TIMEOUT"
    stem = f"{len(ROWS):04d}_{label}"
    for suffix, data in [("stdin", payload), ("stdout", stdout), ("stderr", stderr)]:
        (OUT / f"{stem}.{suffix}").write_bytes(data)
    row = dict(label=label, argv=list(map(str, argv)), cwd=str(cwd),
               status=status, returncode=rc, seconds=time.monotonic()-start,
               input_bytes=len(payload), output_bytes=len(stdout),
               output_sha256=digest(stdout), raw_prefix=stem)
    if expected is not None:
        row["expected_sha256"] = digest(expected)
        row["exact"] = stdout == expected
        row["meets_expectation"] = rc == 0 and stdout == expected
    ROWS.append(row)
    return row, stdout


spec = b"".join(("FizzBuzz" if i % 15 == 0 else "Fizz" if i % 3 == 0
                 else "Buzz" if i % 5 == 0 else str(i)).encode()+b"\n"
                for i in range(1, 101))
# Every delivered milestone on a separately compiled strict interpreter.
for path in sorted((ROOT / "artifacts").glob("candidate_m*.mal")):
    run("strict_"+path.stem, [STRICT, path], expected=path.read_bytes())
for name, payload in [("microcat", b"ABC"), ("truth_machine", b"0"),
                      ("fizzbuzz", b"")]:
    run("strict_"+name, [STRICT, ROOT/"artifacts"/(name+".mal")], payload,
        spec if name == "fizzbuzz" else b"0" if name == "truth_machine" else payload)
for folder in ["reference/malbolge_org", "artifacts"]:
    for name, payload, expected in [
        ("cat" if folder.startswith("reference") else "cat_compressed", b"", b""),
        ("cat" if folder.startswith("reference") else "cat_compressed", b"ABCD", b"ABCD"),
        ("cat" if folder.startswith("reference") else "cat_compressed", bytes(range(256)), bytes(range(256))),
        ("digital_root" if folder.startswith("reference") else "digital_root_compressed", b"12345\n", b"6\n"),
        ("adder" if folder.startswith("reference") else "adder_compressed", b"12\n34\n", b"46\n"),
    ]:
        run("strict_"+folder.replace("/", "_")+"_"+name,
            [STRICT, ROOT/folder/(name+".mal")], payload, expected)
    run("strict_bottles_"+folder.replace("/", "_"),
        [STRICT, ROOT/folder/("99_bottles.mal" if folder.startswith("reference") else "99_bottles_compressed.mal")])
# Differential arithmetic, varied lengths and carries, with deterministic inputs.
rng = random.Random(20261020)
for kind in ["adder", "digital_root"]:
    cases = [(0, 0), (999, 1), (10**40-1, 1)] if kind == "adder" else [0, 1, 9, 10, 10**40-1]
    cases += [(rng.randrange(10**30), rng.randrange(10**30)) for _ in range(20)] if kind == "adder" else [rng.randrange(10**40) for _ in range(20)]
    for i, case in enumerate(cases):
        payload = (f"{case[0]}\n{case[1]}\n" if kind == "adder" else f"{case}\n").encode()
        expected = (str(sum(case)) if kind == "adder" else str(0 if case == 0 else 1+(case-1)%9)).encode()+b"\n"
        for folder, suffix in [("reference/malbolge_org", ""), ("artifacts", "_compressed")]:
            run(f"arithmetic_{kind}_{i}_{suffix or 'reference'}",
                [STRICT, ROOT/folder/(kind+suffix+".mal")], payload, expected)
_, original_bottles = run("bottles_reference_full", [STRICT, ROOT/"reference/malbolge_org/99_bottles.mal"])
run("bottles_compressed_full", [STRICT, ROOT/"artifacts/99_bottles_compressed.mal"], expected=original_bottles)
for i, payload in enumerate([b"", b"A", b"ABC", b"ABCD", b"ABCDE", b"A"*16, bytes(range(256))]):
    run(f"local_microcat_{i}", [LOCAL, ROOT/"artifacts/microcat.mal", "2000000"], payload, payload)
for i, payload in enumerate([b"", b"arbitrary input\x00\xff", bytes(range(256))]):
    run(f"local_fizzbuzz_{i}", [LOCAL, ROOT/"artifacts/fizzbuzz.mal", "2000000"], payload, spec)
# Missing artifact control: the existing compressed suite can succeed with none.
fixture = OUT/"missing_fixture"
(fixture/"tools").mkdir(parents=True)
shutil.copyfile(ROOT/"tools/test_compressed.py", fixture/"tools/test_compressed.py")
run("missing_all_compressed", [sys.executable, fixture/"tools/test_compressed.py"], cwd=fixture)
# Replay the exact Makefile quine recipe with a broken first candidate and good last.
fixture2 = OUT/"quine_recipe_fixture"
(fixture2/"artifacts").mkdir(parents=True)
(fixture2/"artifacts/candidate_m000_bad.mal").write_bytes(b"QP")
shutil.copyfile(ROOT/"artifacts/candidate_m308_58709b.mal", fixture2/"artifacts/candidate_m308_58709b.mal")
(fixture2/"mb_ref").symlink_to(LOCAL)
recipe = 'for f in artifacts/candidate_m*.mal; do ./mb_ref "$f" > out.mal && diff -q "$f" out.mal && echo "OK $f"; done'
run("broken_first_quine_recipe", ["/bin/sh", "-c", recipe], cwd=fixture2)
# Step exhaustion is indistinguishable from HALT in the local oracle.
run("local_zero_fuel", [LOCAL, ROOT/"artifacts/fizzbuzz.mal", "0"], expected=spec)

# An independent trit-by-trit machine model. Permissive loading is explicit here:
# it characterizes the local dialect, not Classic admission of these programs.
XL1 = '+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA"lI.v%{gJh4G\\-=O@5`_3i<?Z\';FNQuY]szf$!BS/|t:Pn6^Ha'
XL2 = '5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK\'X~xDl}REokN:#?G"i@'


def crazy(x, y):
    result, place = 0, 1
    for _ in range(10):
        result += ((1, 0, 0), (1, 0, 2), (2, 2, 1))[y%3][x%3]*place
        x, y, place = x//3, y//3, place*3
    return result


def model(name, payload, detect_cycle=False):
    mem = array.array("H", list(b"".join((ROOT/"artifacts"/(name+".mal")).read_bytes().split())))
    for i in range(len(mem), 59049):
        mem.append(crazy(mem[i-1], mem[i-2]))
    a = c = d = pos = 0
    output = bytearray()
    seen, reads, instructions = {}, 0, []
    for step in range(10000):
        if detect_cycle:
            state = (a, c, d, pos, mem.tobytes())
            if state in seen:
                prev_step, prev_out = seen[state]
                return dict(status="FULL_STATE_CYCLE", step=step, previous_step=prev_step,
                            period=step-prev_step, emitted_per_period=bytes(output[prev_out:]).hex(),
                            output_hex=output.hex(), input_reads=reads,
                            repeated_state_sha256=digest(mem.tobytes()))
            seen[state] = (step, len(output))
        raw = mem[c]
        if not 33 <= raw <= 126:
            return dict(status="NONPRINTABLE_PC", step=step, c=c, raw=raw)
        ins = XL1[(raw-33+c)%94]
        if len(instructions) < 30:
            instructions.append(dict(step=step, a=a, c=c, d=d, instruction=ins))
        if ins == "v":
            return dict(status="HALT", step=step, output_hex=output.hex(), input_reads=reads, trace=instructions)
        if ins == "j": d = mem[d]
        elif ins == "i": c = mem[d]
        elif ins == "*": a = mem[d] = mem[d]//3+(mem[d]%3)*19683
        elif ins == "p": a = mem[d] = crazy(a, mem[d])
        elif ins == "<": output.append(a%256)
        elif ins == "/":
            a = payload[pos] if pos < len(payload) else 59048
            pos += pos < len(payload)
            reads += 1
        mem[c] = ord(XL2[mem[c]-33])
        c, d = (c+1)%59049, (d+1)%59049
    return dict(status="MAX_STEPS", output_hex=output.hex(), input_reads=reads)


MODELS = {"truth_0": model("truth_machine", b"0"),
          "truth_1": model("truth_machine", b"1", True),
          "fizzbuzz": model("fizzbuzz", b"arbitrary"),
          "microcat_ABCD": model("microcat", b"ABCD")}
(OUT/"models.json").write_text(json.dumps(MODELS, indent=2)+"\n")
(OUT/"runs.json").write_text(json.dumps(ROWS, indent=2)+"\n")
print(json.dumps({"runs":len(ROWS), "expectation_failures":[r["label"] for r in ROWS if r.get("meets_expectation") is False],
                  "model_status":{k:v["status"] for k,v in MODELS.items()}}, indent=2))
