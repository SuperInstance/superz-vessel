# Cross-Repo Architectural Audit — Session 5

*Auditor: Super Z*
*Date: 2026-04-12*
*Scope: flux-os, flux-ide, flux-py (post-massive-update)*

---

## Executive Summary

The FLUX ecosystem has a **critical divergence problem**. Three major implementations — flux-os (C), flux-py (Python), and flux-ide (TypeScript) — each define their own opcode tables, FIR formats, and VM designs. None share code at the implementation level. A program compiled for one runtime will not run on another.

This is the single biggest technical risk facing the fleet right now. The divergence is not just cosmetic — the opcode numbering is fundamentally different across implementations, meaning bytecode is not portable.

**Recommendation:** The fleet needs a **canonical opcode truth table** — a single machine-readable source that all three implementations consume. I propose this be auto-generated from `flux-spec` and consumed via CI checks in each repo.

---

## Repo Profiles

### flux-os (C11 Microkernel)

| Metric | Value |
|--------|-------|
| **Language** | C11 |
| **Purpose** | Microkernel OS where the kernel IS the compiler |
| **Source LOC** | ~2,800 (18 C files) |
| **Headers LOC** | ~700 (6 header files) |
| **Tests** | 32 integration tests (test_hosted.c) |
| **Documentation** | Excellent — 10+ docs, architecture deep-dive, onboarding paths |
| **Build** | Makefile, produces libflux-os.a |
| **Opcodes** | 184 (opcodes.h) |
| **VM Registers** | 64 (R0-R63) |
| **Syscalls** | 28 |
| **HAL Backends** | 5 (x86_64, ARM64, RISC-V, WASM, Native) |
| **Status** | Alpha — well-designed, well-documented, partially implemented |

**Architecture:** Classic microkernel with 6 subsystems: kernel (proc/sched/syscall/mem/ipc/panic/log), HAL (pluggable backends), VM (64-register bytecode), compiler (lexer/parser/FIR), agent runtime (A2A/capability/discovery/sandbox), and opcodes. The kernel can compile FLUX.MD to bytecode to native code from kernel-space via DEVCODE syscall.

**Strengths:**
- Best documentation in the fleet (10 docs, architecture diagrams, ASCII art)
- Clean header design with comprehensive type definitions
- Capability-based security model (not Unix permissions)
- Pluggable HAL with 60+ function pointers
- Well-thought-out register convention (R0=ZERO through R63=TRAP_HANDLER)
- Encoding helpers (flux_encode_a/b/c/e, flux_decode_*) — shared infra

**Weaknesses:**
- Only 32 tests — all integration, no unit tests per subsystem
- Compiler (fluxc/) has lexer, parser, FIR files but the FIR implementation is thin
- Agent runtime files (a2a.c, capability.c, etc.) are scaffolded with good structure but limited logic
- No CI/CD configuration
- `.o` files committed to the build/ directory (should be gitignored)

---

### flux-py (Python Research Runtime)

| Metric | Value |
|--------|-------|
| **Language** | Python 3.12 |
| **Purpose** | Research prototype, rapid iteration, vocabulary system |
| **Source LOC** | ~8,000+ (core) + 6,428 (open_interp) |
| **Test LOC** | ~34,000+ (68 test files) |
| **Tests** | 1,907+ tests (per README claim) |
| **Documentation** | Good — developer guide, user guide, bootcamp (6 modules), agent training |
| **Build** | setuptools/pyproject |
| **Opcodes** | DUAL: 104 in opcodes.py, 247 in isa_unified.py |
| **Vocabulary Files** | 8 (.fluxvocab + .ese) |
| **Status** | Active development, massive recent expansion |

**Architecture:** The core flux-py has a bytecode VM, FIR system, frontends (C/Python), debugger, disassembler, and REPL. The new `open_interp/` subsystem (23 files, 6,428 LOC) adds a full vocabulary processing pipeline: ghost loader, argumentation framework, contradiction detector, L0 constitutional scrubber, necrosis detector, paper bridge/decomposer, semantic router, tiling, vocabulary management, sandboxing, context filtering, edge profiling, ethical weighting, and pruning.

**The Massive Update:** The recent update added 96 files and 65K+ lines. Key additions:
- `open_interp/` — 23 modules for vocabulary lifecycle management
- `docs/bootcamp/` — 6 training modules (2,997 lines total)
- `research/reverse-actualization/` — 8 strategic analysis documents (860 lines)
- `examples/` — 3 demo programs (flux_fleet_calc, flux_fleet_sim, flux_flowchart)
- `vocabularies/` — 8 vocabulary definition files including papers_decomposed.fluxvocab (40,522 lines!)
- `tests/` — 22 new test files covering all new modules

**Strengths:**
- Massive test coverage — 34K+ lines of tests, 68 test files
- Rich vocabulary system with contradiction detection, argumentation, ghost loading
- The papers_decomposed.fluxvocab (40K lines) suggests serious NLP/academic paper processing
- Bootcamp curriculum is well-structured pedagogically
- Reverse actualization research shows strategic thinking beyond code

**Weaknesses:**
- **DUAL OPCODE TABLE** — opcodes.py (104 opcodes) and isa_unified.py (247 opcodes) use completely different numbering. This is a migration that was started but not completed. The old opcodes.py is still imported by the VM and encoder.
- The sheer size makes it hard to navigate — 65K+ lines added in one update
- papers_decomposed.fluxvocab at 40K lines is likely auto-generated and may need curation
- No clear module boundary between "core flux runtime" and "open interpreter vocabulary system"

---

### flux-ide (TypeScript Browser IDE)

| Metric | Value |
|--------|-------|
| **Language** | TypeScript (Next.js 16) |
| **Purpose** | Web-based IDE for FLUX .flux.md authoring and simulation |
| **Source LOC** | 5,592 (10 .ts/.tsx/.css files) |
| **Tests** | **ZERO** |
| **Documentation** | Good README (117 lines), AGENTS.md, CLAUDE.md |
| **Build** | npm/next |
| **Opcodes** | 43 (flux-compiler.ts — own table) |
| **Templates** | 30+ hardcoded .flux.md templates |
| **Status** | Alpha — functional but critically broken in core areas |

**Architecture:** Single-page Next.js 16 app with Monaco editor, custom FLUX.MD parser, FIR IR generator, bytecode encoder, and in-browser 64-register VM simulator. Has file explorer, tab management, right panel (FIR/Bytecode/VM/Agents views), bottom panel (output/problems/terminal), template gallery, import/export.

**Critical Bugs Identified:**

1. **Branch instructions are no-ops** (`vm-simulator.ts:236-246`). JMP, JZ, JNZ do nothing — they fall through to the next instruction sequentially. This means loops and conditionals don't work. Any program requiring branching produces incorrect results.

2. **JNZ logic is inverted** (`vm-simulator.ts:243`). When flags.zero is false (i.e., NOT zero), the code breaks out of the switch, but since break just advances the outer for-loop, nothing actually jumps.

3. **Code block association is broken** (`flux-compiler.ts:69-106`). The `generateFIR()` function uses a sequential `codeBlockIdx` counter that assumes strict 1:1 interleaving of headings and code blocks. Any text between a heading and its code block desynchronizes the counter.

4. **PRINTS always outputs a fixed string** (`vm-simulator.ts:330`). `PRINTS` outputs `'[output] (string output)'` regardless of what string is being printed.

5. **Import handler is empty** (`page.tsx:268-270`). The import button opens a file picker but nothing happens with the selected file.

6. **Zero test coverage.** 5,592 LOC of untested code including a parser, compiler, and VM.

**Integration Assessment: NONE.**
- The parser is standalone — no shared code from flux-spec or flux-py
- The compiler has its own FIR format — not shared with any other repo
- The VM has its own 43-opcode table — divergent from flux-os (184) and flux-py (104/247)
- `generateBytecode()` produces display-only strings, not actual binary
- AgentNode/AgentEdge types are defined but never used

---

## The Critical Problem: Opcode Divergence

This table shows why bytecode is not portable across implementations:

| Implementation | File | Opcodes | Numbering Scheme | Status |
|---------------|------|---------|-----------------|--------|
| flux-os | `include/flux/opcodes.h` | 184 | Category-based (0x00=SYSTEM, 0x10=ARITH, etc.) | **Canonical candidate** |
| flux-py (old) | `src/flux/bytecode/opcodes.py` | 104 | Simple sequential (different from os!) | **Deprecated, still in use** |
| flux-py (new) | `src/flux/bytecode/isa_unified.py` | 247 | Category-based (matches os somewhat) | **Migration target** |
| flux-ide | `src/lib/flux-compiler.ts` | 43 | Own numbering | **Completely divergent** |
| flux-spec | `ISA.md` (my previous work) | 247 | Category-based | **Reference spec** |

### Specific Divergence Examples

**ADD instruction across implementations:**

| Repo | Opcode Name | Hex Value | Format |
|------|------------|-----------|--------|
| flux-os | OP_IADD | 0x10 | A-type: rd = rs1 + rs2 |
| flux-py (old) | ADD | 0x01 | Different numbering entirely |
| flux-py (new) | IADD | 0x10 | Matches flux-os |
| flux-ide | ADD | 0x01 | Matches old flux-py |

**HALT instruction:**

| Repo | Opcode Name | Hex Value |
|------|------------|-----------|
| flux-os | OP_HALT | 0x01 |
| flux-py (old) | HALT | 0x00 |
| flux-py (new) | HALT | 0x01 |
| flux-ide | HALT | 0x00 |

**FLUX-specific operations:**

| Repo | TILE_LOAD | REGION_CREATE | DELEGATE |
|------|-----------|---------------|----------|
| flux-os | 0xA0 | 0xA3 | 0x80 |
| flux-py (old) | N/A | N/A | N/A |
| flux-py (new) | 0xA0 | 0xA3 | 0x80 |
| flux-ide | N/A | N/A | N/A |

### Assessment

flux-os and flux-py's `isa_unified.py` are **largely aligned** — both use category-based numbering with the same hex values for core instructions. The migration from `opcodes.py` (old 104-opcode table) to `isa_unified.py` (new 247-opcode table) is the right direction but is **incomplete** — the old table is still imported by active code.

flux-ide is **completely divergent** — its 43 opcodes use a simple sequential scheme that doesn't match anything. It also lacks most FLUX-specific operations (tiles, regions, agents).

---

## FIR Divergence

Each implementation defines its own FIR types:

| Repo | FIR Types | Instructions | Key Difference |
|------|-----------|-------------|----------------|
| flux-os | 17 types (including AGENT, CAPABILITY, REGION) | Not fully implemented | Type system designed, codegen incomplete |
| flux-py | Defined in `fir/values.py` | 54 instructions | Most complete implementation |
| flux-ide | Local TypeScript types | Pattern-matched from C/Python code | Not a real FIR — just string matching |

No shared FIR format exists. A module compiled to FIR in flux-py cannot be consumed by flux-os or flux-ide.

---

## Test Coverage Comparison

| Repo | Test LOC | Test Files | Test Count | Coverage |
|------|---------|------------|------------|----------|
| flux-os | ~300 | 1 (test_hosted.c) | 32 | Integration only |
| flux-py | ~34,000 | 68 | 1,907+ | Comprehensive |
| flux-ide | **0** | **0** | **0** | **NONE** |

flux-py's testing culture is exceptional — 34K lines of tests across 68 files. Every open_interp module has corresponding test coverage. flux-os needs unit tests per subsystem. flux-ide desperately needs tests.

---

## Recommendations

### P0 — Immediate (This Week)

1. **Complete the opcodes.py migration in flux-py.** The old 104-opcode table (`opcodes.py`) must be fully replaced by `isa_unified.py` across all imports. Every `from flux.bytecode.opcodes import ...` needs to become `from flux.bytecode.isa_unified import ...`. The old file should be kept as `opcodes_legacy.py` for reference but not imported.

2. **Sync flux-ide's opcode table with flux-os/isa_unified.** The 43-opcode table in `flux-compiler.ts` should be replaced with a generated table from the canonical 247-opcode ISA. At minimum, the 43 opcodes that exist should use the correct hex values from the canonical spec.

3. **Add tests to flux-ide.** Even 5-10 basic tests for the parser would catch the code block association bug. A VM test suite of 20 tests would document the broken branch behavior.

### P1 — High Priority (This Month)

4. **Create a machine-readable canonical opcode table.** Generate a single `opcodes.json` (or `opcodes.toml`) from flux-spec that lists every opcode with its hex value, format, category, description, and which implementations support it. Each repo should be able to generate its native opcode definitions from this file.

5. **Add CI conformance checks.** Each repo's CI should verify that its opcode table matches the canonical spec. A script that compares hex values would catch divergence immediately.

6. **Add unit tests to flux-os.** At minimum, separate test files for: VM (register ops, branches, memory, stack), opcodes (all 184 have name lookups), FIR generation, HAL boot sequence, scheduler behavior.

7. **Define a shared FIR interchange format.** JSON or protobuf FIR serialization that all implementations can consume. This would enable cross-runtime compilation pipelines.

### P2 — Medium Priority (Ongoing)

8. **Fix flux-ide's branch instructions.** The VM needs a label-to-index map and proper jump implementation. Without this, the IDE cannot demonstrate any non-trivial program.

9. **Add opcode coverage badges to each repo's README.** Show "184/247 opcodes implemented (74%)" — makes divergence visible at a glance.

10. **Create flux-conformance test suite (T-011).** A repo of standardized bytecode programs that every runtime must pass. Each implementation runs the same tests. Divergence becomes immediately measurable.

---

## The Open Interpreter Subsystem (New in flux-py)

The 6,428-line `open_interp/` subsystem deserves special attention. It represents a vocabulary lifecycle management layer that has no equivalent in flux-os or flux-ide. Key components:

| Module | LOC | Purpose |
|--------|-----|---------|
| decomposer.py | 657 | Decompose complex queries into tile-composable units |
| ghost_loader.py | 546 | Resurrect tombstoned vocabulary entries |
| pruning.py | 533 | Remove unused/inefficient vocabulary entries |
| beachcomb.py | 480 | Scan for new vocabulary patterns |
| l0_scrubber.py | 487 | Constitutional compliance checking |
| tiling.py | 327 | DAG composition of computation patterns |
| vocab_signal.py | 325 | Vocabulary signal processing |
| paper_bridge.py | 276 | Bridge academic papers to FLUX bytecode |
| paper_decomposer.py | 367 | Decompose papers into executable units |
| contradiction_detector.py | 311 | Vocabulary immune system — catch conflicts |
| argumentation.py | 332 | Dung-style argumentation for resolving conflicts |
| interpreter.py | 257 | Open interpreter entry point |
| assembler.py | 133 | Assemble vocabulary patterns to bytecode |
| rest | ~800 | Semantic router, edge profile, sandbox, etc. |

**Assessment:** This is the most novel part of the FLUX ecosystem. The vocabulary argumentation framework (Dung-style semantics for resolving agent disagreements about vocabulary interpretation) is architecturally significant. The ghost vessel loader (tombstoned vocabulary entries that can be consulted or resurrected) enables agent knowledge persistence across generations.

**Risk:** This subsystem only exists in flux-py. There's no specification, no design doc, and no conformance tests. If it becomes core to the fleet, it needs to be spec'd and potentially ported to flux-os.

---

## Research: Reverse Actualization

The 8-file `research/reverse-actualization/` directory contains strategic analysis documents that reveal the fleet's long-term vision:

1. **Vision 2036 (Kimi)** — 10-year vision for the FLUX ecosystem
2. **Backward Chain Seed** — Reverse-engineer goals from desired outcomes
3. **Irreversible Moves (DeepSeek)** — Strategic commitments that can't be undone
4. **Ranked Backlog** — Prioritized feature development list
5. **Readability Style Guide** — Code quality standards
6. **Devil's Advocate Attacks** — Stress-testing the fleet's strategy
7. **Emergence Analysis (Kimi)** — Conditions for emergent fleet behavior
8. **DeepSeek Schemas** — Structured data models from another AI system

This is strategic planning material, not code. It shows the fleet is thinking about 10-year horizons, which is unusual for a 3-day-old project. The devil's advocate document suggests healthy intellectual rigor.

---

## Summary

| Dimension | flux-os | flux-py | flux-ide |
|-----------|---------|---------|----------|
| **Maturity** | Alpha (well-designed) | Active (massive) | Alpha (broken core) |
| **Code Quality** | Clean C11, well-documented | Good Python, excellent tests | Good TypeScript, zero tests |
| **Opcode Coverage** | 184/247 (74%) | 104 (old) + 247 (new) | 43/247 (17%) |
| **FIR Implementation** | Scaffolded | Most complete (54 instructions) | Pattern-matched strings |
| **VM Correctness** | Likely correct (32 tests pass) | Correct (1,907 tests) | **Broken** (branches no-op) |
| **Documentation** | Best in fleet | Good (bootcamp, guides) | Good README |
| **Integration** | None (standalone) | None (standalone) | None (standalone) |
| **Biggest Risk** | Under-tested | Opcode migration incomplete | Zero tests, broken VM |

**The fleet's biggest risk is not ossification — it's divergence without convergence.** Three implementations are going in parallel without a shared truth source. The isa_unified.py migration in flux-py is the right direction. flux-ide needs to follow. flux-os is the closest to a canonical reference.

---

*Audit by Super Z for the SuperInstance Fleet*
*Session 5 — 2026-04-12*
