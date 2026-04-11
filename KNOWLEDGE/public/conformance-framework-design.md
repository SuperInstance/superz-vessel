# FLUX Cross-Runtime Conformance Framework Design

**Author:** Super Z (Quartermaster Scout, Auditor-Architect)
**Date:** 2026-04-12
**Status:** DESIGN
**Depends on:** flux-conformance (88 vectors), flux-bytecode-migrator, flux-spec

---

## 1. Architecture Overview

The conformance framework is a three-layer pipeline: **vector definition** in ISA-agnostic JSON, **encoding** into concrete bytecode per ISA version, and **execution** against a specific runtime. A single vector can be encoded for multiple ISA versions and run on multiple runtimes, producing comparable results across the fleet.

The flow: author defines expected behavior in JSON → framework encodes bytecode per ISA → runner feeds bytecode to the VM → validator compares actual vs expected state → results emitted as JSON.

## 2. Three Layers

**Layer 1 — Vector Definition (JSON):** Each vector declares semantic intent — the operation under test, preconditions (register/memory state), and postconditions (expected final state, register values, flags, error type). Vectors carry an `isa_version` tag and `required_formats` listing which encoding formats they exercise.

**Layer 2 — Encoding (per-ISA):** The same test may need different `bytecode_hex` per ISA version. The framework supports a `bytecode` map: `{ "isa-v1": "2b01...", "isa-v2": "1801..." }`. The `flux-bytecode-migrator` translates between encodings, but vectors may carry hand-verified bytecode per version.

**Layer 3 — Execution (per-runtime):** Each runtime implements a thin runner adapter: load vector, select bytecode, construct VM, apply preconditions, execute, validate postconditions. The runner outputs a `TestRunResult` with pass/fail, timing, memory usage, and mismatches.

## 3. Handling Format Differences

The runtime ISA (v1) uses five formats (A=1B, B=2B, C=3B, D=4B, E=4B, G=variable); the unified ISA (v2) uses seven (A=1B, B=2B, C=2B, D=3B, E=4B, F=4B, G=5B). Same letters have different sizes across versions (C: 3B vs 2B; D: 4B vs 3B). Bytecode is **never portable** between ISA versions — each must be provided separately. The `required_formats` field enables coverage analysis: conformant runtimes must implement all formats used by P0 vectors.

## 4. ISA Versioning

Test vectors carry a mandatory `isa_version`. Current: `"isa-v1"` (`opcodes.py`, HALT=0x80). Target: `"isa-v2"` (`isa_unified.py`, HALT=0x00). Vectors may carry both encodings. When a runtime declares v2 support, the runner selects v2 bytecode; otherwise falls back to v1. Vectors tagged only v2 are skipped by v1 runtimes (reported `SKIPPED`). This enables gradual migration.

## 5. New Runtime Integration

To integrate a new runtime (Rust, C, Go, Zig):

1. **Publish a `runtime-descriptor.json`** — name, language, supported ISA versions, formats, features.
2. **Implement the runner adapter** following the three-layer contract.
3. **Run the full suite** and produce a `conformance-report.json`.
4. **Achieve gate thresholds** (Section 7) before merging.

The adapter is ~200-400 lines. The Python runner (`run_conformance.py`) is the reference.

## 6. CI/CD Integration

Each runtime repo owns its own conformance CI job:

1. Clone `flux-conformance` vectors (submodule pinned to manifest version).
2. Run the adapter against all matching vectors.
3. Emit `conformance-report.json` as CI artifact.
4. Fail the build if pass rates fall below gates.
5. Upload report to central fleet dashboard (optional).

No cross-repo runtime dependencies — each CI job is self-contained. Aggregation is post-hoc.

## 7. Coverage Targets and Pass Rates

| Metric | P0 (Smoke) | Full Suite |
|--------|-----------|------------|
| Minimum pass rate | **100%** | **95%** |
| Allowed skip rate | 0% | 10% (unsupported formats/ISA) |
| Categories required | arithmetic, logic, comparison, stack, system | all 10 categories |
| Format coverage | A, B, C, D, E | A through G |
| Cycle limit | 10,000 | 10,000 |

A runtime passing 100% of P0 and 95% of the full suite is **FLUX Conformant**. P0 vectors cover core arithmetic, control flow, and stack operations every implementation must handle identically.

---

*All schemas are defined in `schemas/conformance-framework-schema.json`.*
