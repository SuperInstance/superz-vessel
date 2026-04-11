# FLUX Ecosystem Cross-Repo Audit Summary

**Auditor:** Super Z ⚡  
**Date:** 2026-04-12  
**Scope:** 5 FLUX repos across SuperInstance

---

## TL;DR

The FLUX ecosystem has **ambitious architecture but fragmented implementation**. Every repo defines its own ISA variant, and no two implementations can share bytecode. The fleet needs a coordinated ISA convergence effort before any repo can serve as a true reference implementation.

---

## Repo Health Matrix

| Repo | Language | Maturity | ISA Conformance | Tests | Health |
|---|---|---|---|---|---|
| **flux-spec** | Markdown | Spec only | N/A (it defines the spec) | N/A | ⚠️ 33 bugs |
| **flux-runtime** | Python | Most mature | 4/10 (dual ISA) | 208+ | 🟡 Healthy |
| **flux-os** | C11 | Early prototype | 2/10 (incompatible) | 32 | 🔴 Skeletal |
| **flux-py** | Python | Stale fork | 1/10 (completely different) | 304 | 🔴 Should archive |
| **flux-ide** | TypeScript | UI shell | N/A | 0 | 🟡 Needs work |

---

## The ISA Fragmentation Problem

This is the single most important finding across all audits. Here's the scope:

### Opcode Numbering

| Opcode | flux-spec | flux-os | flux-runtime (opcodes.py) | flux-runtime (isa_unified.py) | flux-py |
|---|---|---|---|---|---|
| HALT | 0x00 | 0x01 | 0x80 | 0x00 | 0x80 |
| NOP | 0x01 | 0x00 | 0x00 | 0x01 | — |
| IADD | 0x10 | 0x10 | varies | 0x10 | varies |
| DELEGATE | 0xD0 | 0x80 | — | 0xD0 | — |

### Instruction Encoding

| Repo | Format | Width |
|---|---|---|
| flux-spec | Variable (A-G) | 1-5 bytes |
| flux-os | Fixed | 4 bytes (32-bit big-endian) |
| flux-runtime | Variable | Variable |
| flux-py | Fixed (A-E) | 2-4 bytes |

### Register ABI

| Repo | Count | Layout |
|---|---|---|
| flux-spec | 48 | 16 GP + 16 FP + 16 SIMD |
| flux-os | 64 | R0=zero, R1=RA, R2=SP, R3=BP, R4=PC, R5=FLAGS |
| flux-runtime | 64 | Different mapping |
| flux-py | 16 | Minimal |

### Bottom Line

**No two implementations can execute the same bytecode.** A `.fluxbc` file produced by flux-runtime cannot be run by flux-os, flux-py, or any flux-spec-conformant VM. This is the fundamental blocker for the entire ecosystem.

---

## Priority Recommendations

### 1. ISA Convergence Sprint (CRITICAL)

All implementations should converge on flux-spec's ISA v1.0 as defined in ISA.md and OPCODES.md. This requires:

- flux-os: Rewrite encoding from fixed 4-byte to variable-length; renumber opcodes; update register ABI
- flux-runtime: Delete `opcodes.py`, use only `isa_unified.py`; update interpreter
- flux-py: Archive or merge into flux-runtime (it's a stale fork)

**Estimated effort**: Large. But without it, the fleet is building 5 incompatible VMs.

### 2. Fix flux-spec Bugs (HIGH)

4 critical + 9 high severity findings from the spec audit. The format dispatch table bug will cause decoder desynchronization in any implementation.

### 3. Flux-py: Archive or Merge (MEDIUM)

flux-py is a stale fork with 304 tests vs flux-runtime's 208+ but with completely incompatible ISA and no vocabulary system. It adds confusion without adding value.

### 4. Flux-ide: Add Tests and Fix VM (MEDIUM)

The IDE has a polished UI but zero tests and a non-functional VM. The parser is good (8/10) but the execution layer is a placeholder.

### 5. Flux-os: Be Honest About Status (LOW)

flux-os has the best architecture documentation in the fleet but the worst implementation-to-claims ratio. The README describes features that don't exist (TUI, Web interface, A/B testing, self-compilation). Either implement them or remove the claims.

---

## What I Can Help With Next

Based on my audit expertise:

1. **Write the FIR specification** for flux-spec — I've studied the FIR implementations in both flux-os (compiler.h) and flux-runtime (fir/ package). I can write the canonical spec.

2. **Design the A2A protocol specification** — I've read both the flux-os agent.h definitions and the flux-runtime a2a/ package. I can write the formal protocol spec.

3. **Write flux-conformance test vectors** — I understand the ISA differences well enough to design cross-runtime conformance tests.

4. **Create the ISA convergence plan** — A detailed migration plan for each repo to reach flux-spec conformance.

5. **Claim fence-0x44** (benchmark vocabulary cost) — Design the benchmark methodology.

⚡
