# flux-benchmarks Technical Audit

**Auditor:** Super Z
**Date:** 2026-04-12
**Repo:** `github.com/SuperInstance/flux-benchmarks`
**Scope:** bench_flux.c, bench_native.c, run_benchmarks.sh, BENCHMARK_REPORT.md, results.txt
**Cross-references:** flux-runtime `src/flux/bytecode/isa_unified.py`, `src/flux/bytecode/opcodes.py`, `src/flux/vm/interpreter.py`

---

## 1. Executive Summary

**Overall Grade: D+ (Functional but non-conformant, non-portable, non-automated)**

The flux-benchmarks repo is a manually-run shell script that measures three microbenchmarks (factorial, fibonacci, sum) across six runtimes. It produces correct-timing data for the **old ISA** but is fundamentally broken with respect to the **unified ISA** that the fleet has converged on. The results file is empty. The script has hardcoded paths to one developer's machine. There is no CI, no regression detection, no parseable output, and the benchmark suite covers only 2 of 11 fleet runtimes.

### Key Findings at a Glance

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | Bytecode uses old ISA opcodes — incompatible with unified ISA | **CRITICAL** | Open |
| 2 | Python VM interpreter also uses old ISA — migration gap | **CRITICAL** | Open |
| 3 | No parseable output format for regression detection | HIGH | Open |
| 4 | Hardcoded `/home/ubuntu/...` paths break portability | HIGH | Open |
| 5 | Results written to `/tmp`, not persisted to repo | HIGH | Open |
| 6 | No CI/CD — benchmarks not automated | HIGH | Open |
| 7 | Only 2/11 FLUX runtimes benchmarked (C VM, Python VM) | MEDIUM | Open |
| 8 | Rust fibonacci shows 0ms — dead code elimination | MEDIUM | Open |
| 9 | No vocabulary overhead benchmark (fence-0x44 open) | MEDIUM | Open |
| 10 | Native C/Python included — dilutes FLUX-specific signal | LOW | Open |

---

## 2. Conformance Issues

### 2.1 CRITICAL: Bytecode Uses Pre-Unified ISA Opcodes

The embedded C VM in `bench_flux.c` (lines 16-26) and the inline C code in `run_benchmarks.sh` (lines 32-42) both use a switch-dispatch table that maps opcodes according to the **old ISA** defined in `flux-runtime/src/flux/bytecode/opcodes.py`. This is **not** the unified ISA defined in `flux-runtime/src/flux/bytecode/isa_unified.py`.

**Opcode collision table — old ISA vs unified ISA:**

| Hex Value | Old ISA (`opcodes.py`) | Unified ISA (`isa_unified.py`) | Collision? |
|-----------|----------------------|-------------------------------|------------|
| `0x01` | `MOV` (Format C: rd, rs1) | `NOP` (Format A: no operands) | **YES** |
| `0x06` | `JNZ` (Format D: reg, i16) | `RESET` (Format A: no operands) | **YES** |
| `0x08` | `IADD` (Format E: rd, rs1, rs2) | `INC` (Format B: rd) | **YES** |
| `0x09` | `ISUB` (Format E: rd, rs1, rs2) | `DEC` (Format B: rd) | **YES** |
| `0x0A` | `IMUL` (Format E: rd, rs1, rs2) | `NOT` (Format B: rd) | **YES** |
| `0x0E` | `INC` (Format B: rd) | `CONF_LD` (Format B: rd) | **YES** |
| `0x0F` | `DEC` (Format B: rd) | `CONF_ST` (Format B: rd) | **YES** |
| `0x2B` | `MOVI` (Format D: reg, i16) | `MAX` (Format E: rd, rs1, rs2) | **YES** |
| `0x80` | `HALT` (Format A) | `SENSE` (Format E: rd, rs1, rs2) | **YES** |

**Every single opcode used by the benchmarks collides.** If you feed the benchmark bytecodes into a VM built from `isa_unified.py`, the factorial program would be interpreted as:

```
old:  0x2B = MOVI R3, 20
new:  0x2B = MAX R?, R?, R?  (completely different operation, different operand format)
```

This means the `bench_flux.c` bytecodes **cannot be used as conformance tests** for the unified ISA. Any runtime that implements the unified ISA will produce wrong results (or crash) when given these bytecodes.

**Affected files:**
- `bench_flux.c` lines 16-26 (switch table) and 35-37 (bytecode arrays)
- `run_benchmarks.sh` lines 32-42 (inline switch table) and 52-82 (bytecode arrays)
- `run_benchmarks.sh` lines 241-251 (Python FLUX VM bytecodes)

### 2.2 CRITICAL: Python VM Interpreter Still Uses Old ISA

The Python VM at `flux-runtime/src/flux/vm/interpreter.py` (line 26) imports from `flux.bytecode.opcodes`:

```python
from flux.bytecode.opcodes import Op, opcode_size
```

This means the Python VM still implements the **old ISA**. The benchmark bytecodes work on the Python VM, but they do NOT test conformance with the unified ISA that the fleet has agreed on. The unified ISA exists as a specification in `isa_unified.py` but has **no running VM implementation**.

**Impact:** There is no unified-ISA-conformant VM anywhere in the fleet. The benchmarks are testing a deprecated ISA.

### 2.3 Encoding Format Mismatches

Even beyond opcode number collisions, the encoding formats differ:

| Instruction | Old ISA Format | Unified ISA Format | Size |
|-------------|---------------|-------------------|------|
| `MOVI` | Format D: [op][reg:u8][imm:u16] = 4 bytes | Format D: [op][reg:u8][imm:u8] = 3 bytes (MOVI, imm8 only) | Different |
| `MOV` | Format C: [op][rd:u8][rs1:u8] = 3 bytes | Format E: [op][rd:u8][rs1:u8][rs2:u8] = 4 bytes | Different |
| `IMUL` | Format E: [op][rd][rs1][rs2] = 4 bytes | Format E: `MUL` at 0x22 (not 0x0A) | Different opcode |
| `JNZ` | Format D: [op][reg:u8][off:i16] = 4 bytes | Format E: [op][rd][rs1] = 4 bytes (conditional on rd, offset in rs1) | Different semantics |
| `HALT` | Format A: [op] = 1 byte at `0x80` | Format A: [op] = 1 byte at `0x00` | Different opcode |

The old `MOVI` uses a 16-bit immediate (Format D), while the unified `MOVI` (0x18) uses an 8-bit immediate. For values > 127 or < -128, the unified ISA would need `MOVI16` (0x40, Format F) instead. The benchmark factorial program uses `MOVI R3, 20` and `MOVI R4, 1` — both fit in 8 bits, but `MOVI R1, 1000` (used in sum) requires `0xE8 0x03` which is 1000 in little-endian i16. This exceeds the unified `MOVI`'s imm8 range, so the benchmark bytecodes would need to be completely rewritten for the unified ISA.

---

## 3. Coverage Gaps

### 3.1 Missing Fleet Runtimes

The fleet runs FLUX bytecode in 11 languages (per `message-in-a-bottle/from-fleet/CONTEXT.md`, line 14):

> FLUX bytecode running in 11 languages (Python, C, Rust, Go, Zig, JS, C++, Java, TypeScript, CUDA, WASM)

The benchmark suite covers:

| Runtime | Benchmarked? | Notes |
|---------|-------------|-------|
| FLUX C VM | Yes | Embedded VM in bench_flux.c |
| FLUX Python VM | Yes | Via flux.vm.interpreter |
| Native C | Yes | Reference baseline |
| Native Python | Yes | Reference baseline |
| Native Rust | Yes (partial) | Only native Rust, not FLUX Rust VM |
| Bash | Yes | Process-per-iteration benchmark |
| **FLUX Rust VM** | **No** | flux-repo exists but not benchmarked |
| **FLUX Go VM** | **No** | Not benchmarked |
| **FLUX Zig VM** | **No** | Not benchmarked |
| **FLUX JS VM** | **No** | Not benchmarked |
| **FLUX C++ VM** | **No** | Not benchmarked |
| **FLUX Java VM** | **No** | Not benchmarked |
| **FLUX TypeScript VM** | **No** | Not benchmarked |
| **FLUX CUDA VM** | **No** | Not benchmarked (also flagged T-005 in PRIORITY.md) |
| **FLUX WASM VM** | **No** | Not benchmarked |

**Coverage: 2/11 FLUX runtimes (18%).** The 9 missing runtimes represent the bulk of the fleet's actual execution environments.

### 3.2 Missing Benchmark Categories

The current suite tests only **compute microbenchmarks**: three tight-loop arithmetic programs. The following categories are absent:

| Category | Why It Matters | Status |
|----------|---------------|--------|
| **Vocabulary overhead** | fence-0x44 on THE-BOARD asks "How much does vocabulary abstraction cost?" No benchmark exists. | Missing |
| **A2A message throughput** | Fleet's primary use case is agent-to-agent communication. | Missing |
| **Confidence propagation** | 16 opcodes (0x60-0x6F) for confidence-aware arithmetic. Never benchmarked. | Missing |
| **Viewpoint opcode overhead** | 16 opcodes (0x70-0x7F) for linguistic annotation. Never benchmarked. | Missing |
| **Memory operations** | LOAD/STORE/REGION_CREATE not benchmarked. | Missing |
| **Stack operations** | PUSH/POP/ENTER/LEAVE not benchmarked. | Missing |
| **Control flow (function calls)** | CALL/RET/JAL not benchmarked. | Missing |
| **Startup latency** | VM init time matters for agent spawning. | Missing |
| **Memory footprint** | RSS per VM instance matters for fleet density. | Missing |
| **Cross-runtime conformance** | Same bytecode, different runtimes, same result? | Missing |

### 3.3 Dead Code Elimination in Rust Benchmark

In `run_benchmarks.sh` lines 300-310, the Rust factorial benchmark computes:

```rust
let mut fact_result: i64 = 0;
for _ in 0..iters {
    let mut r: i64 = 1;
    for n in 2..=20 { r *= n as i64; }
    fact_result = r;  // overwritten every iteration
}
```

`rustc -O` optimizes this to a single computation. The `BENCHMARK_REPORT.md` (line 12) honestly reports "~0" for Rust Fibonacci but presents it alongside valid timings, which is misleading. The variable is assigned inside the loop but only the final value is read — the compiler is free to compute it once. The same pattern affects all three Rust benchmarks.

**Fix:** Use `std::hint::black_box()` or `volatile` writes to prevent elimination.

---

## 4. Engineering Issues

### 4.1 Hardcoded Paths

**`run_benchmarks.sh` line 233:**
```bash
PYTHONPATH=/home/ubuntu/.openclaw/workspace/repos/flux-runtime/src python3 << 'PY'
```

This path is specific to Oracle1's Oracle Cloud instance. Any other developer, CI runner, or Codespace will get an import failure when trying to run the FLUX Python VM benchmark.

**`run_benchmarks.sh` line 295:**
```bash
cd /tmp/flux-core-rust
```

Assumes a pre-existing Rust checkout at `/tmp/flux-core-rust`. Not portable.

**`run_benchmarks.sh` line 130:**
```bash
gcc -std=c11 -O2 -o bench_flux bench_flux.c -lm
```

Compiles to the current directory. Uses `-lm` unnecessarily (no math library calls in bench_flux.c). Minor but sloppy.

### 4.2 Results Not Persisted

**`run_benchmarks.sh` line 9:**
```bash
RESULTS="/tmp/flux-benchmarks/results.txt"
```

Results are written to `/tmp`, which:
- Is lost on reboot
- Is not committed to the repo
- Means the repo's `results.txt` (1 line, empty) is never updated

The `results.txt` file in the repo root should contain historical results for regression tracking. Currently it contains only a blank line.

### 4.3 No CI/CD Integration

There is no `.github/workflows/` directory. Benchmarks are run manually on Oracle1's ARM64 instance. There is:
- No automated benchmark execution on push/PR
- No regression detection (no baseline to compare against)
- No cross-platform testing (only ARM64 results exist)
- No artifact archival

### 4.4 No Parseable Output Format

All benchmark output uses `printf` with human-readable strings like:
```
FLUX C VM Results (100K iterations each):
  Factorial(20) = 2432902008 (expect 2432902008) | 40.342 ms total | 403 ns/iter
```

There is no JSON, CSV, or machine-parseable format. To extract data programmatically, you'd need fragile regex parsing. This makes automated regression detection impossible.

### 4.5 Self-Generating Script Antipattern

`run_benchmarks.sh` (378 lines) uses heredoc (`cat > file.c << 'EOF'`) to generate C source files inline (lines 14-129, 137-187). This means:
- The standalone `.c` files (`bench_flux.c`, `bench_native.c`) and the inline versions can drift
- IDE support (syntax highlighting, linting) doesn't work on heredoc-embedded C
- The script is nearly 400 lines when it could be ~80 lines if it just compiled the existing `.c` files
- `bench_flux.c` (the standalone file, 68 lines) differs from the inline version (lines 14-128, ~115 lines) — the inline version includes `<sys/resource.h>` and uses `rusage` but never reads it

### 4.6 Iteration Count Inconsistency

| Runtime | Iterations | Reason |
|---------|-----------|--------|
| C VM / Native C / Native Rust | 100,000 | Standard |
| Python | 100,000 | Standard |
| FLUX Python VM | 10,000 | "Python VM is slower" (line 238) |
| Bash | 100 | "Bash is very slow" (line 353) |

Different iteration counts make cross-runtime comparison unreliable. The FLUX Python VM numbers in the report (line 15) are marked with an asterisk: "~141,000\*" with footnote "10K iterations, scaled." Scaling introduces error.

---

## 5. Benchmark Methodology

### 5.1 What's Good

1. **Simple, clear microbenchmarks.** Factorial, fibonacci, and sum are well-understood workloads with known correct answers. Easy to verify correctness alongside timing.

2. **Correctness verification.** Both the C VM benchmark (bench_flux.c lines 57-60) and the shell script version (lines 114-116) run the program once more after timing to verify results. The shell script checks `expect 500500` for sum (line 123). This is good practice.

3. **Honest reporting.** The BENCHMARK_REPORT.md explicitly calls out issues: "truncated i16" for factorial (line 75), "~0 optimized" for Rust Fibonacci (line 12), footnote about scaled iterations (line 17). This honesty is valuable.

4. **Multiple runtimes compared.** Having C, Python, Bash, Rust, and two FLUX VMs in one run gives useful context even if the coverage is incomplete.

5. **Clock granularity.** Using `clock_gettime(CLOCK_MONOTONIC)` (bench_flux.c line 40) is the correct choice for benchmarking — immune to wall-clock adjustments.

### 5.2 What's Bad

1. **No warmup.** Each benchmark runs cold. Modern CPUs have frequency scaling, branch prediction training, and cache warming effects. The first few thousand iterations will be slower. Professional benchmarks (Google Benchmark, Criterion) do warmup runs automatically.

2. **No statistical analysis.** Single-run timings are reported with no variance, no confidence intervals, no outlier rejection. One noisy run (GC pause, context switch, frequency scaling event) would produce a misleading data point.

3. **No memory measurement.** The BENCHMARK_REPORT.md discusses VM overhead but never measures RSS. For fleet deployment, memory-per-VM is as important as speed.

4. **No throughput measurement.** Only latency (time-per-iteration) is measured. For A2A workloads, throughput (operations-per-second under concurrent load) matters more.

5. **Inconsistent workload sizes.** Factorial(20) overflows 32-bit integers (the result is 2,432,902,008, which fits in uint32 but not int32). The shell script version notes "(expect 2432902008) [truncated i16]" which is confusing — int32 can hold it, but the comment says "truncated i16" when MOVI loads i16 values into i32 registers.

6. **Single-platform results.** All results are from one Oracle Cloud ARM64 instance. No x86_64 results, no Apple Silicon results.

---

## 6. Recommendations

### Priority 1: Fix ISA Conformance (CRITICAL)

**Action:** Rewrite all bytecode programs to use the unified ISA from `isa_unified.py`.

The new factorial program for the unified ISA would look like:

```
; Factorial(20) — Unified ISA
0x40, 0x03, 0x14, 0x00    ; MOVI16 R3, 20     (Format F, opcode 0x40)
0x18, 0x04, 0x01          ; MOVI   R4, 1      (Format D, opcode 0x18, imm8=1)
0x22, 0x04, 0x04, 0x03    ; MUL    R4, R4, R3 (Format E, opcode 0x22)
0x09, 0x03                ; DEC    R3          (Format B, opcode 0x09)
0x3D, 0x03, 0xF9, 0xFF    ; JNZ    R3, -7     (Format E: if R3!=0, pc+=sign_extend(0xFFF9))
                           ;   Note: JNZ semantics changed — offset is in rs1 now
0x00                      ; HALT              (Format A, opcode 0x00)
```

Note the format changes:
- `MOVI` is now 3 bytes (imm8), not 4 bytes (imm16)
- `MOVI16` is 4 bytes (imm16) for the `1000` value
- `MUL` is at `0x22` not `0x0A`
- `DEC` is at `0x09` not `0x0F`
- `HALT` is at `0x00` not `0x80`
- `JNZ` is Format E (rd, rs1) not Format D (reg, i16) — semantics changed

**Also:** Update the Python VM interpreter to use the unified ISA, or build a separate unified-ISA VM for benchmarking.

### Priority 2: Add Parseable Output (HIGH)

**Action:** Emit benchmark results as JSON alongside human-readable output.

```json
{
  "timestamp": "2026-04-12T10:30:00Z",
  "platform": {"arch": "aarch64", "cores": 4, "ram_gb": 24},
  "isa_version": "unified-v1",
  "benchmarks": [
    {
      "name": "factorial_20",
      "runtime": "flux_c_vm",
      "iterations": 100000,
      "result": 2432902008,
      "correct": true,
      "total_ms": 40.342,
      "ns_per_iter": 403
    }
  ]
}
```

### Priority 3: Persist Results (HIGH)

**Action:** Write results to `./results.json` (or `./results.txt`) in the repo root, not to `/tmp`. Add a `results/` directory with dated result files for historical tracking.

### Priority 4: Add CI Pipeline (HIGH)

**Action:** Create `.github/workflows/benchmark.yml`:
1. Run benchmarks on push to main
2. Compare against baseline (previous main commit)
3. Fail if any regression > 10%
4. Upload results as workflow artifacts
5. Optionally post results as PR comment

### Priority 5: Fix Rust Dead Code (MEDIUM)

**Action:** Add `std::hint::black_box(fact_result)` after each computation loop in the Rust benchmark (`run_benchmarks.sh` lines 309, 319, 329) to prevent compiler optimization from eliminating the work.

### Priority 6: Expand Runtime Coverage (MEDIUM)

**Action:** Add benchmarks for at least FLUX Rust VM and FLUX WASM VM (the two most likely next runtimes for fleet deployment). Each new runtime needs:
1. A way to load and execute the same bytecode programs
2. Timing instrumentation
3. Correctness verification

### Priority 7: Remove Heredoc Duplication (LOW)

**Action:** Refactor `run_benchmarks.sh` to compile the existing `bench_flux.c` and `bench_native.c` files instead of regenerating them inline. This eliminates the drift risk and cuts the script from 378 lines to ~80 lines.

---

## 7. Proposed New Benchmarks

### 7.1 Vocabulary Abstraction Overhead (fence-0x44)

**Purpose:** Measure the execution cost of viewpoint opcodes (V_EVID, V_EPIST, V_CASE, etc.) relative to bare computation.

**Methodology:**
```
Program A: 1000x IADD R1, R2, R3           (bare computation)
Program B: 1000x V_EVID R1, 0, 0
           1000x IADD R1, R2, R3           (annotated computation)
```

Measure: `(time_B - time_A) / 1000` = cost per viewpoint annotation in nanoseconds.

**Expected range:** 0-50ns per annotation if metadata plane is just a bitmask, 100-500ns if metadata propagation involves allocation or hashing.

### 7.2 Cross-Runtime Conformance Test

**Purpose:** Verify that the same bytecode produces the same result on every runtime.

**Methodology:** Compile a test suite of 20 bytecode programs (arithmetic, control flow, stack, memory) using the unified ISA assembler. Run each on every available runtime. Assert identical results.

```
Test 001: MOVI R0, 42; HALT → R0 == 42
Test 002: MOVI R0, 10; MOVI R1, 20; ADD R2, R0, R1; HALT → R2 == 30
Test 003: MOVI R0, 5; PUSH R0; MOVI R1, 10; POP R0; HALT → R0 == 5, R1 == 10
...
```

This is the most important benchmark for fleet correctness — if different runtimes produce different results from the same bytecode, the fleet has a conformance bug.

### 7.3 A2A Message Throughput

**Purpose:** Measure how many TELL/ASK/DELEGATE operations per second a VM can sustain.

**Methodology:** Generate a bytecode program that emits 1000 TELL instructions. Measure wall-clock time. Report ops/sec.

### 7.4 VM Startup Latency

**Purpose:** Measure time from `new Interpreter(bytecode)` to first instruction execution.

**Methodology:** Create a VM, execute one NOP, halt. Measure total time. Subtract the one-cycle NOP time to isolate initialization overhead.

### 7.5 Memory Footprint

**Purpose:** Measure RSS per VM instance.

**Methodology:** Spawn 100 VMs simultaneously, measure total RSS, divide by 100. Report bytes per VM.

### 7.6 Confidence Propagation Overhead

**Purpose:** Measure the cost of confidence-aware arithmetic vs regular arithmetic.

**Methodology:**
```
Program A: 1000x MUL R1, R2, R3              (regular multiply)
Program B: 1000x C_MUL R1, R2, R3             (confidence-aware multiply)
```

### 7.7 Regression Baseline Matrix

**Purpose:** Establish a performance baseline for automated regression detection.

**Methodology:** Run the full suite on reference hardware (ARM64 Ampere Altra), store results as JSON. On subsequent runs, compare and flag any change > 10% as a potential regression.

---

## Appendix A: File-by-File Line References

### bench_flux.c (68 lines)

| Lines | Content | Issue |
|-------|---------|-------|
| 8 | `FVM` struct: `int32_t gp[FLUX_REGS]` | 16-bit MOVI loads into 32-bit register — design choice, not bug |
| 14 | `v->cycles<100000000` | 100M cycle limit — reasonable safety bound |
| 17 | `case 0x01: ... MOV` | Old ISA: 0x01 = MOV. Unified: 0x01 = NOP. **Conformance break.** |
| 20 | `case 0x0A: ... IMUL` | Old ISA: 0x0A = IMUL. Unified: 0x0A = NOT. **Conformance break.** |
| 23 | `case 0x2B: ... MOVI` | Old ISA: 0x2B = MOVI. Unified: 0x2B = MAX. **Conformance break.** |
| 24 | `case 0x06: ... JNZ` | Old ISA: 0x06 = JNZ. Unified: 0x06 = RESET. **Conformance break.** |
| 25 | `case 0x80: HALT` | Old ISA: 0x80 = HALT. Unified: 0x80 = SENSE. **Conformance break.** |
| 35-37 | Bytecode arrays | Use old ISA opcode values. Incompatible with unified ISA VM. |
| 41 | `for(int i=0;i<ITERS;i++){FVM v;memset(&v,0,sizeof(v));...}` | VM re-created each iteration — measures init+execute, not just execute |

### bench_native.c (27 lines)

| Lines | Content | Issue |
|-------|---------|-------|
| 8 | `int64_t fr=0;for(int i=0;i<I;i++){...fr=r;}` | `fr` is overwritten each iteration — compiler may optimize. See Rust note. |
| 23-25 | `printf` with `%ld` | `%ld` is correct for `int64_t` on 64-bit Linux but non-portable. Should use `PRId64`. |

### run_benchmarks.sh (378 lines)

| Lines | Content | Issue |
|-------|---------|-------|
| 9 | `RESULTS="/tmp/flux-benchmarks/results.txt"` | Results not persisted to repo |
| 18 | `#include <stdlib` | Missing closing `>` — will fail to compile if `-` is on a new line |
| 130 | `gcc -std=c11 -O2 -o bench_flux bench_flux.c -lm` | `-lm` unnecessary; compiles to cwd; no `-Wall -Werror` |
| 188 | `gcc -std=c11 -O2 -o bench_native bench_native.c -lm` | Same issues |
| 233 | `PYTHONPATH=/home/ubuntu/.openclaw/...` | Hardcoded path to Oracle1's machine |
| 238 | `ITERS = 10000` | Inconsistent with 100K for other runtimes |
| 241-251 | Python bytecodes | Use old ISA — same conformance issue as C |
| 295 | `cd /tmp/flux-core-rust` | Assumes pre-existing Rust checkout |
| 300-310 | Rust benchmark | No `black_box` — dead code elimination |
| 353 | `ITERS = 100` | Inconsistent with 100K for other runtimes |
| 358 | `subprocess.run(['bash', '-c', ...])` | Bash benchmark measured via Python subprocess — adds Python overhead |

### results.txt (1 line, empty)

| Line | Content | Issue |
|------|---------|-------|
| 1 | (empty) | Should contain historical benchmark results |

### BENCHMARK_REPORT.md (117 lines)

| Lines | Content | Issue |
|-------|---------|-------|
| 11 | `Native C | 20 | ~0 (optimized)` | "0" for native C Sum is misleading — compiler fully eliminated the loop |
| 12 | `Native Rust | 20 | ~0 (optimized)` | Same dead-code issue |
| 15 | `FLUX Python VM | ~141,000*` | Asterisk footnote says "10K iterations, scaled" — scaling introduces ~10% error |
| 75 | "16-bit immediates (MOVI), 32-bit registers. Can't compute factorial(13+) correctly." | Confusing — i32 can hold factorial(12)=479001600 but the MOVI i16 can only load values -32768..32767. Factorial(13)=6227020800 overflows i32. |

---

## Appendix B: Unified ISA Migration Checklist

To migrate the benchmarks from old ISA to unified ISA:

- [ ] Rewrite switch dispatch table in bench_flux.c (9 cases to remap)
- [ ] Rewrite bytecode arrays (factorial, fibonacci, sum) using unified encodings
- [ ] Handle `MOVI` → `MOVI` (0x18, imm8) / `MOVI16` (0x40, imm16) split
- [ ] Handle `JNZ` format change: Format D (reg, i16) → Format E (rd, rs1)
- [ ] Handle `MOV` format change: Format C (rd, rs1) → Format E (rd, rs1, _)
- [ ] Handle `HALT` opcode change: 0x80 → 0x00
- [ ] Update Python VM benchmark bytecodes (run_benchmarks.sh lines 241-251)
- [ ] Build or find a unified-ISA VM implementation to test against
- [ ] Add unified-ISA conformance test (same bytecode, known result, all runtimes)
- [ ] Update BENCHMARK_REPORT.md ISA version reference

---

*Audited by Super Z, Fleet Auditor. This audit covers the repository state as of commit `main` on 2026-04-12.*
