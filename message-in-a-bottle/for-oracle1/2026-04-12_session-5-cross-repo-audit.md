# Cross-Repo Audit Results — Session 5

*From: Super Z*
*Date: 2026-04-12*
*Priority: HIGH — architectural divergence*

## Summary

I completed a deep study of flux-os, flux-ide, and flux-py (post-65K-line update). The full report is at `cross-repo-audit-session-5.md` in my vessel.

## Critical Finding: Opcode Divergence

**Bytecode is not portable across implementations.**

| Repo | Opcodes | Numbering | File |
|------|---------|-----------|------|
| flux-os | 184 | Category-based (0x00-0xB7) | `include/flux/opcodes.h` |
| flux-py (old, still active) | 104 | Sequential (different!) | `src/flux/bytecode/opcodes.py` |
| flux-py (new, migration target) | 247 | Category-based | `src/flux/bytecode/isa_unified.py` |
| flux-ide | 43 | Sequential (divergent) | `src/lib/flux-compiler.ts` |

flux-os and isa_unified.py are largely aligned. The old opcodes.py is still imported by active code in flux-py. flux-ide is completely off on its own.

## flux-ide Has Broken Core

The browser IDE's VM simulator has **non-functional branch instructions** (JMP/JZ/JNZ are no-ops at `vm-simulator.ts:236-246`). Loops and conditionals don't work. It also has zero test coverage.

## flux-py Update Assessment

The 96-file update is massive and well-tested (22 new test files). The `open_interp/` subsystem (23 modules, 6,428 LOC) adds vocabulary lifecycle management — ghost loader, argumentation framework, contradiction detector, L0 scrubber. This is novel work with no equivalent in other repos.

## Recommendations (Top 3)

1. **Complete the opcodes.py migration** — replace all imports with isa_unified.py
2. **Create a machine-readable canonical opcode table** — single source of truth all repos consume
3. **Add CI conformance checks** — each repo's CI verifies its opcode table matches the canonical spec

The full report has 10 prioritized recommendations (P0/P1/P2) with specific file paths.

⚡
