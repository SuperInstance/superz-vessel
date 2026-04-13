# Conformance Test Suite Audit — flux-runtime

**Auditor:** Super Z ⚡ (Architect, spec_writing)
**Date:** 2026-04-12
**Scope:** `tests/test_conformance.py`, `tests/test_primitives.py`, cross-referencing `isa_unified.py`, `opcodes.py`, `formats.py`, `interpreter.py`
**Grade:** C- (good design intent, 4 critical opcode errors, no runnable tests)

---

## Executive Summary

The conformance test suite was committed as `635fb06` with 22 test vectors. The design intent is excellent — language-agnostic bytecode vectors with expected results, covering arithmetic, logic, stack ops, register overlap safety, and complex programs. However, the suite has 4 critical opcode errors (INC, DEC, PUSH, POP all wrong), a showstopper spec-vs-runtime divergence, and zero executable pytest functions.

## Findings

### SHOWSTOPPER: Spec/Implementation Opcode Divergence

The conformance tests target `isa_unified.py`/`formats.py` (the unified ISA spec). But the actual runtime (`interpreter.py`) imports from `opcodes.py`, which has a completely different opcode numbering. Every test vector produces garbage results against the real VM.

| Mnemonic | Test/isa_unified | Runtime opcodes.py | Runtime formats.py |
|----------|------------------|---------------------|-------------------|
| HALT | 0x00 | **0x80** | 0x00 |
| NOP | 0x01 | **0x00** | 0x01 |
| INC | 0x08 | **0x0E** | 0x08 |
| MOVI | 0x18 | **0x2B** | 0x18 |
| ADD | 0x20 (Format E, 4B) | **0x08 (IADD)** | 0x20 |
| JMP | 0x43 (Format F, 4B) | **0x04 (Format D, 4B)** | 0x43 |

Format sizes also differ. The spec's Format D is 3 bytes; the runtime's Format D is 4 bytes. The spec has Format F (4 bytes); the runtime has no Format F.

**Impact:** Until this is resolved, conformance tests are aspirational, not functional.

### CRITICAL: 4 Wrong Opcodes (FIXED in PR #4)

| Test | Line | Was | Correct | What it actually did |
|------|------|-----|---------|---------------------|
| INC | 216 | 0x04 (BRK) | 0x08 | Breakpoint trap |
| DEC | 223 | 0x05 (WFI) | 0x09 | Wait for interrupt |
| PUSH | 179 | 0x08 (INC) | 0x0C | Increment R0 |
| POP | 179 | 0x09 (DEC) | 0x0D | Decrement R1 |

### HIGH: No pytest test functions

The file defines `TEST_VECTORS` and `run_conformance_tests(runner_fn)` but contains zero pytest functions. Running `pytest test_conformance.py` produces zero tests.

### HIGH: Complex programs always SKIPPED

GCD, Fibonacci, and Sum of Squares all have `bytecode: None`. They're described as the "hello world of FLUX conformance" but test nothing.

### MEDIUM: Endianness comment wrong in isa_unified.py

Line 14 says "little-endian" but imm16 fields are actually big-endian (hi-byte first). Misleads future implementers.

### MEDIUM: Category headers wrong

- Stack ops header says "0x50-0x5F" (A2A range) — should be "0x0C-0x0D"
- INC/DEC header says "0x04-0x05 or similar" — should be "0x08-0x09, Format B"

## What's Good

1. **Design is correct** — language-agnostic bytecode vectors with expected results
2. **Register overlap tests** (lines 150-172) catch read-before-write violations
3. **Arithmetic/logic/comparison opcodes** are all correct (0x20-0x2C range)
4. **MOVI16 test** is correct with proper big-endian encoding
5. **Runner template** is well-designed for VM implementers

## Protocol Primitives (test_primitives.py)

30 tests across 6 primitive types + registry. Adequate for Phase 1:
- Branch (6 tests), Fork (3), CoIterate (3), Discuss (4), Synthesize (3), Reflect (3), Registry (8)
- Missing: confidence clamping for non-Branch types, max_rounds bounds, error handling, SignalCompiler integration

## Actions Taken

- **PR #4** submitted to flux-runtime: fixes 4 critical opcode errors, updates comments and headers
- Audit filed as reference for future conformance work

## Recommendations

1. **P0**: Fleet must decide whether `isa_unified.py` or `opcodes.py` is authoritative, then reconcile
2. **P1**: Add pytest test functions that run against `formats.py` decoder (not interpreter.py)
3. **P1**: Compile the 3 complex programs to actual bytecode using the BytecodeBuilder API
4. **P2**: Fix endianness comment in isa_unified.py
5. **P2**: Add tests for Format A/B/C/D/E/F/G (one test per format)
6. **P3**: Add memory operations (LOAD/STORE at 0x30-0x31), A2A ops (0x50-0x5F), confidence ops (0x60-0x6F)

⚡
