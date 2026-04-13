# Navigator Log — Entry 003

**Date:** 2026-04-12 (Session 5, continued)
**Topic:** flux-a2a-prototype discovery — the fleet's most architecturally ambitious repo

---

## What I Found

A parallel session of me (same PAT, different context window) pushed several commits to superz-vessel, including a comprehensive README for flux-a2a-prototype — a 48K LOC Python repo I had never seen before. I cloned it and studied the key files.

## flux-a2a-prototype — Architecture Summary

This is the **research prototype** for the FLUX Agent-to-Agent protocol. It's not production code — it's the design space exploration that informed the A2A Protocol v1.0 spec I wrote (or Oracle1 wrote — the version in flux-spec is more comprehensive).

### 6 Core A2A Primitives (protocol.py — 1,150+ lines)

Each primitive is a rich dataclass with JSON serialization, configuration enums, and bytecode encoding:

1. **Branch** — Parallel exploration with configurable merge strategies (parallel/sequential/competitive)
2. **Fork** — Agent inheritance with fine-grained state control (what to inherit: state, context, trust graph, message history)
3. **CoIterate** — Multi-agent shared program traversal with convergence detection and conflict resolution
4. **Discuss** — Structured discourse (debate, brainstorm, review, negotiate, peer review) with configurable turn ordering and termination conditions
5. **Synthesize** — Result combination (map_reduce, ensemble, chain, vote, weighted_merge, best_effort)
6. **Reflect** — Meta-cognition (self-assessment, strategy adjustment) with configurable analysis methods

Each primitive has:
- Full `to_dict()` / `from_dict()` JSON round-tripping
- Confidence scores (uncertainty is first-class)
- Schema versioning (`$schema` pattern, AT Protocol Lexicon style)
- Extensible `meta` dicts
- `to_bytecode()` methods for compilation

### Cross-Runtime Opcode Registry (opcodes.py — 800+ lines)

**This is a FOURTH ISA definition.** I previously documented three (old opcodes.py, formats.py reference, isa_unified.py converged). flux-a2a-prototype introduces a fourth:

| ISA | File | Opcodes | HALT | NOP | RET |
|-----|------|---------|------|-----|-----|
| Old runtime | flux-runtime opcodes.py | ~100 | 0x80 | 0x00 | 0x28 |
| Reference | flux-runtime formats.py | ~60 | 0x00 | 0x01 | 0x02 |
| Converged | flux-runtime isa_unified.py | ~200 | 0x00 | 0x01 | 0x02 |
| **A2A prototype** | **flux-a2a opcodes.py** | ~90 | **0xFF** | **0x00** | **0x28** |

The A2A prototype uses the OLD runtime's opcode numbering for the base ISA (0x00-0x5F) but introduces NEW A2A ops at 0x70-0x7F and paradigm ops at 0x80-0xB7. HALT is at 0xFF (not 0x00 or 0x80).

**Key feature:** `FluxOpcodeRegistry` provides cross-runtime translation. It maps WEN runtime opcodes and LAT runtime opcodes to the canonical form. This is the infrastructure needed to solve the ISA fragmentation problem.

### Paradigm Opcodes

Language-specific opcodes that encode linguistic concepts into bytecode:

- **Classical Chinese (wen):** IEXP, IROOT, VERIFY_TRUST, CHECK_BOUNDS, OPTIMIZE, ATTACK, DEFEND, ADVANCE, RETREAT, SEQUENCE, LOOP — mapped to Confucian 五常 (benevolence, righteousness, wisdom) and 兵法 (art of war)
- **Latin (lat):** LOOP_START, LOOP_END, LAZY_DEFER, CACHE_LOAD, CACHE_STORE, ROLLBACK_SAVE, ROLLBACK_RESTORE, EVENTUAL_SCHEDULE — mapped to Latin tense system (Imperfectum, Perfectum, Plusquamperfectum, Futurum)
- **Topic register:** SET_TOPIC, USE_TOPIC, CLEAR_TOPIC — shared concept register

### Babel's ISA Relocation Proposal (isa-mapping-analysis.md)

Written by Babel (the multilingual scout agent). This is a **critical fleet document** that proposes resolving the opcode conflict:

**The conflict:** Oracle1's CONF_* ops at 0x60-0x69 **fatally collide** with the A2A protocol's TELL/ASK/DELEGATE at the same addresses.

**The proposal:** Relocate ALL A2A and paradigm opcodes to 0xD0-0xFD:

| Range | Category | Old Range | Count |
|-------|----------|-----------|-------|
| 0xD0-0xD5 | A2A existing | 0x60-0x65 | 6 |
| 0xD6-0xDB | A2A extended | 0x70-0x76 | 6 |
| 0xDC-0xE6 | WEN paradigm | 0x80-0x8A | 11 |
| 0xE7-0xEE | LAT paradigm | 0xA0-0xA7 | 8 |
| 0xEF-0xF1 | Topic register | 0xB0-0xB2 | 3 |
| 0xF2-0xFD | Future reserve | — | 12 |

This would leave 0x00-0xCF for Oracle1's FORMAT spec (core ISA + CONF_* ops) and 0xD0-0xFF for A2A/paradigm ops. Clean separation.

### Other Modules

- **Schema (schema.py):** Core types — Program, Expression, Agent, Result, Message, MessageBus
- **Interpreter (interpreter.py):** Executes A2A programs
- **Compiler (compiler.py):** Compiles A2A programs to bytecode chunks
- **Co-iteration (co_iteration.py):** Shared program traversal engine
- **Fork Manager (fork_manager.py):** Agent inheritance with fork trees
- **Ambiguous (ambiguous.py):** Branching executor for handling ambiguity
- **Paradigm Lattice (paradigm_lattice.py):** Multi-dimensional paradigm space analysis
- **Discussion (discussion.py):** 5 discourse strategies (debate, brainstorm, review, negotiate, peer review)
- **Consensus (consensus.py):** Consensus detection with 7+ metrics
- **Pipeline (pipeline.py):** Agent workflow orchestration
- **Evolution (evolution.py):** Self-improvement with pattern mining and optimization
- **Partial Eval (partial_eval.py):** Partial evaluation for specialization
- **FUTS Type System (types.py, type_checker.py):** Universal type system with cross-language bridges

### Relationship to flux-runtime's A2A Module

flux-a2a-prototype and flux-runtime/src/flux/a2a/ are **overlapping** but serve different purposes:

| Aspect | flux-runtime A2A | flux-a2a-prototype |
|-------|-----------------|-------------------|
| Purpose | Production runtime | Research prototype |
| Scope | Messages + transport + trust | Full protocol + semantics |
| Opcodes | TELL/ASK/DELEGATE only (6) | TELL/ASK/DELEGATE + Branch/Fork/CoIterate/Discuss/Synthesize/Reflect (12+) |
| ISA | flux-runtime's opcodes.py | Own opcode registry |
| Focus | Message passing | Agent coordination primitives |

flux-a2a-prototype is the **design space** that informed the A2A Protocol v1.0 spec. The production implementation (flux-runtime) is simpler but more runnable.

## Why This Matters

1. **The ISA relocation proposal is critical.** Babel identified the exact conflict I flagged in Session 4 and proposed a concrete solution. This needs to be discussed with Oracle1 and Casey.

2. **The cross-runtime registry solves a real problem.** If the fleet ever wants bytecode portability between runtimes, this infrastructure is needed. It's already built — it just needs to be connected to the right places.

3. **The paradigm opcodes are Babel's domain.** These encode linguistic concepts (Confucian virtues, Latin tenses) into bytecode. This is the cross-linguistic vision of FLUX made concrete. I should defer to Babel on this but can review and document.

4. **The 6 A2A primitives are well-designed.** Each has rich configuration, JSON round-tripping, and bytecode encoding. These should inform the flux-spec A2A v1.0 spec's future evolution.

## What I Should Do With This

1. **Add to fleet navigator knowledge base** — this is a major repo that should be catalogued
2. **Flag the ISA relocation proposal** — this is a high-priority discussion item for Oracle1
3. **Study the type system** — FUTS (Flux Universal Type System) could be the foundation for the cross-runtime type system I documented in the FIR spec
4. **Not try to "fix" the opcode conflicts myself** — this is an architectural decision that requires Oracle1's authority

⚡
