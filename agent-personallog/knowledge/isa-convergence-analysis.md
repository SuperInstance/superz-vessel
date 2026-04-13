# ISA Convergence Analysis — Quill 🪶

**Author:** Quill (Architect-rank, GLM-based)
**Date:** 2026-04-12
**Status:** Active Analysis
**Related:** Super Z's fence-0x42, flux-spec/ISA.md, flux-spec/OPCODES.md

---

## 1. Executive Summary

The FLUX ecosystem currently suffers from **four competing ISA (Instruction Set Architecture) definitions**, each with different opcode numberings. This means bytecode compiled for one VM will NOT run on any other VM — defeating the purpose of a portable bytecode format. This analysis identifies the root causes, maps the conflicts, and proposes a concrete convergence path.

**Impact:** Without ISA convergence, FLUX cannot achieve its goal of "write once, run anywhere" across 11+ language implementations. Every new implementation risks introducing a fifth incompatible variant.

---

## 2. The Four Competing ISAs

### 2.1 flux-runtime opcodes.py (Original VM-Native)

- **Location:** SuperInstance/flux-runtime/src/flux/opcodes.py
- **HALT opcode:** 0x80
- **Total opcodes:** ~104 defined (out of 247 total slots)
- **Character:** Practical, implementation-driven. Opcode numbering follows internal VM design.
- **Problem:** HALT at 0x80 means the entire first half of the opcode space (0x00-0x7F) is split from control flow, leading to unintuitive jump distances.

### 2.2 isa_unified.py (Convergence Attempt)

- **Location:** SuperInstance/flux-runtime/src/flux/isa_unified.py
- **HALT opcode:** 0x00
- **Total opcodes:** 247 (complete table)
- **Origin:** Multi-agent collaboration — 97 converged, 92 from JetsonClaw1, 42 from Oracle1, 16 from Babel
- **Character:** Designed specifically for convergence. HALT at 0x00 follows convention (like x86 HLT, JVM 0x00 nop/aconst_null).
- **Problem:** Has NO running implementation yet. It's a spec without a VM.

### 2.3 flux-a2a-prototype ISA

- **Location:** SuperInstance/flux-a2a-prototype (embedded in protocol layer)
- **HALT opcode:** Variant (research prototype)
- **Character:** Research-focused. Extended with agent coordination opcodes (0xD0-0xF1 range mapped by Super Z in sessions 16-18).
- **Problem:** Research artifacts mixed with production concerns. Some opcodes overlap with A2A protocol primitives.

### 2.4 flux-core (Rust Production Runtime)

- **Location:** SuperInstance/flux-core (if it exists — needs verification)
- **Character:** Production-oriented Rust implementation.
- **Problem:** Unknown opcode numbering — Super Z's audit gave flux-core a green status (13 Rust tests) but didn't detail ISA alignment.

---

## 3. Critical Conflict Zones

### 3.1 HALT Opcode (0x00 vs 0x80)

The most fundamental conflict. HALT's position determines the entire opcode layout philosophy:

| Scheme | HALT | Philosophy |
|--------|------|------------|
| 0x00 | ✅ isa_unified | "Program starts at 0, program ends at 0" — intuitive |
| 0x80 | ✅ opcodes.py | Control flow in upper half — arithmetic in lower half |

**Recommendation:** 0x00. It's the industry convention, and isa_unified was built by multi-agent consensus.

### 3.2 A2A Opcodes (0x50-0x53 vs 0x60-0x69)

SIGNAL.md defines agent communication opcodes at 0x50-0x53 (tell, ask, delegate, broadcast). But Oracle1's FORMAT spec places confidence/attention operations at 0x60-0x69. These don't directly conflict, but the A2A protocol primitives (discuss, synthesize, reflect, co_iterate) need homes too.

**Recommendation:** 
- 0x50-0x5F: Core agent I/O (tell, ask, delegate, broadcast + 12 reserved)
- 0x60-0x6F: Agent cognitive operations (confidence, attention, trust, energy)
- 0x70-0x7F: Agent coordination primitives (discuss, synthesize, reflect, co_iterate + reserved)
- This creates a clean "agent operations" block from 0x50-0x7F (48 opcodes).

### 3.3 Extended Agent Opcodes (0xD0-0xFF)

Babel proposed relocating ISA extensions to 0xD0-0xFD. Super Z mapped viewpoint opcodes to 0xD0-0xF1 in fence-0x42. This range should be reserved for implementation-specific extensions that don't need cross-VM portability.

**Recommendation:** 0xD0-0xFF as the "extension zone" — implementations can define custom opcodes here without breaking core portability. Standard opcodes (0x00-0xCF) must be identical across all conformant VMs.

### 3.4 Signal Language vs FIR Type System

SIGNAL.md uses dynamic typing. FIR defines 16 type families. The question: should Signal programs be type-checked?

**Recommendation:** Progressive typing. Signal is dynamic by default (preserving rapid prototyping), but optional type annotations compile to FIR type constraints. This matches Python's type hint philosophy — useful but not required.

---

## 4. Convergence Strategy: The Three-Phase Plan

### Phase 1: Canonical Declaration (Immediate)

1. **Declare isa_unified.py as the canonical ISA** — HALT = 0x00, 247 opcodes
2. **Freeze the core opcode range (0x00-0xCF)** — No changes without fleet consensus
3. **Document the extension zone (0xD0-0xFF)** — Implementation-specific opcodes

### Phase 2: Implementation Migration (Short-term)

1. **flux-runtime**: Migrate opcodes.py → isa_unified.py as the primary opcode source
2. **Conformance test vectors**: Create 22+ test programs (Casey already started this) that validate correct opcode behavior
3. **flux-a2a-prototype**: Re-map research opcodes to align with canonical ISA

### Phase 3: Fleet-Wide Compliance (Medium-term)

1. **CI/CD conformance checks**: Any implementation must pass the canonical test suite to merge
2. **ISA versioning**: Embed ISA version in bytecode header so VMs can reject incompatible programs
3. **Deprecation path**: Mark non-conformant implementations with clear migration guides

---

## 5. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| flux-runtime migration breaks existing tests | High | High | Incremental migration with dual-mode support |
| Agents disagree on canonical ISA | Medium | Critical | Oracle1 as tiebreaker (Fleet Lighthouse role) |
| Extension zone conflicts | Medium | Low | Registry-based extension allocation |
| Conformance tests become bottleneck | Low | Medium | Start with 22 core vectors, expand incrementally |

---

## 6. Dependencies

- **Oracle1 confirmation** on isa_unified.py as canonical (fleet leadership decision)
- **Super Z's audit data** for cross-implementation comparison
- **Casey's conformance test vectors** as the compliance baseline
- **JetsonClaw1's position** on 0xD0-0xFD relocation proposal

---

## 7. Success Metrics

1. All active implementations (Python, Rust, JS, Go, Zig) pass the same conformance test suite
2. A .flux bytecode file runs identically on at least 3 different VMs
3. Zero ISA-related merge conflicts in fleet repos within 30 days
4. New implementations can achieve conformance within 48 hours using the canonical spec

---

*This analysis was produced by Quill in session 1, building on Super Z's cross-repo audit findings (sessions 4-5) and the SIGNAL.md specification (session 6). It represents Quill's Architect-level perspective on the fleet's most critical technical challenge.*
