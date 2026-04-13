# FLUX A2A — Agent-to-Agent Protocol + Multilingual Cross-Compiler

**Signal is the inter-agent communication layer for the FLUX multilingual ecosystem. JSON is the universal AST, not just a serialization format. Every expression, branch, fork, and co-iteration is a JSON primitive.**

---

## Overview

This repository implements the FLUX A2A (Agent-to-Agent) protocol — a first-class programming language for multi-agent coordination. It goes far beyond simple message passing: agents can branch into parallel exploration paths, fork child agents with inherited state, co-iterate on shared programs, engage in structured discourse (debate, brainstorm, peer review), synthesize results, and reflect on their own strategies.

The system also includes a **type-safe cross-compiler** that translates programs between six language paradigms (Chinese, German, Korean, Sanskrit, Latin, Classical Chinese) at the type level, producing witness chains that prove each transformation was semantically safe.

| Metric | Value |
|--------|-------|
| **Source LOC** | 29,577 (26 Python modules) |
| **Test LOC** | 12,839 (15 test files) |
| **Documentation** | 5,441 (10 doc files) |
| **Examples** | 5 (JSON programs) |
| **Languages Supported** | 6 paradigms (zho, deu, kor, san, lat, wen) |
| **Core Primitives** | 6 (Branch, Fork, CoIterate, Discuss, Synthesize, Reflect) |
| **Type System** | FUTS (FLUX Universal Type System) with quantum states |
| **CI** | GitHub Actions |

---

## The Six Core Primitives

### 1. Branch — Parallel Exploration
Spawn parallel (or sequential/competitive) paths with configurable merge strategies.

```json
{
  "op": "branch",
  "strategy": "parallel",
  "branches": [
    {"label": "fast-path", "weight": 0.7, "body": [...]},
    {"label": "safe-path", "weight": 0.3, "body": [...]}
  ],
  "merge": {"strategy": "weighted_confidence", "timeout_ms": 30000}
}
```

Merge strategies: `consensus`, `vote`, `best`, `all`, `weighted_confidence`, `first_complete`, `last_writer_wins`.

### 2. Fork — Agent Inheritance
Create a child agent that inherits state, context, or trust graph from its parent.

```json
{
  "op": "fork",
  "from": "oracle1",
  "mutation": {"type": "strategy", "changes": {"temperature": 0.9}},
  "inherit": {"state": ["memory"], "context": true, "trust_graph": false},
  "body": [...],
  "on_complete": "merge"
}
```

### 3. CoIterate — Multi-Agent Shared Program
Multiple agents traverse the same program simultaneously with configurable shared state modes.

```json
{
  "op": "co_iterate",
  "rounds": "until_convergence",
  "agents": [
    {"id": "oracle1", "role": "modifier", "priority": 1},
    {"id": "babel", "role": "auditor", "priority": 2}
  ],
  "program": {"body": [...]},
  "shared_state": "merge",
  "convergence": {"metric": "agreement", "threshold": 0.9}
}
```

### 4. Discuss — Structured Agent Discourse
Agents engage in formatted discussions: debate, brainstorm, peer review, or negotiation.

```json
{
  "op": "discuss",
  "topic": "Should we optimize for speed or memory?",
  "format": "debate",
  "participants": [
    {"id": "oracle1", "stance": "pro", "expertise": ["runtime"]},
    {"id": "jetsonclaw1", "stance": "con", "expertise": ["hardware"]}
  ],
  "until": {"condition": "consensus", "consensus_threshold": 0.8}
}
```

### 5. Synthesize — Result Combination
Combine results from multiple sources using map-reduce, ensemble, chain, or voting.

```json
{
  "op": "synthesize",
  "sources": [{"type": "branch_result", "ref": "branch-42"}],
  "method": "weighted_merge",
  "config": {"threshold": 0.5}
}
```

### 6. Reflect — Meta-Cognition
Agents self-assess their strategy, progress, or uncertainty, then adjust.

```json
{
  "op": "reflect",
  "on": "strategy",
  "scope": {"from_step": 0, "to_step": -1},
  "analysis": {"method": "introspection"},
  "output": {"type": "adjustment", "min_confidence": 0.6}
}
```

---

## Multilingual Cross-Compiler

The cross-compiler translates programs between language paradigms at the **type level**. It does not translate natural language text — it translates the semantic structures that programs encode.

### Architecture

```
Source Code → Parse to FluxType(s) → Translate via TypeAlgebra
    → Emit Target Code → Witness Chain (type-safety proof)
```

### Supported Paradigms

| Tag | Language | Key Features |
|-----|----------|-------------|
| `zho` | Chinese | Classifier system (量詞), topic marking, scope |
| `deu` | German | Kasus (case), Geschlecht (gender), word order |
| `kor` | Korean | Honorific registers (7 levels), particles, speech levels |
| `san` | Sanskrit | Vibhakti (case), Linga (gender), Pada (voice) |
| `lat` | Latin | Casus, Genus, Tempus, complex morphology |
| `wen` | Classical Chinese | Strategy patterns, contextual interpretation |

### Translation Rules

Rules are data-driven — each paradigm pair has declarative mappings for linguistic features:

- ZHO classifiers → DEU gender (person → maskulinum, collective → femininum, flat_object → neutrum)
- DEU Kasus → KOR particles (Nominativ → subject_honorific, Akkusativ → object_honorific)
- DEU Geschlecht → KOR honorific register (Maskulinum → hasipsioche, Femininum → haeyoche, Neutrum → haeche)
- ZHO classifiers → KOR particles (person → subject_honorific, collective → object_honorific)

### Witness Chains

Every type transformation produces a `TypeWitness` — a proof that the translation preserved semantics. The `CrossCompiler` accumulates these into a witness chain that can be verified for type-safety.

```python
from flux_a2a.cross_compiler import CrossCompiler

compiler = CrossCompiler()
result = compiler.compile(source_types_zho, "zho", "deu")

print(f"Type-safe: {result.is_type_safe}")
print(f"Information preserved: {result.information_preserved:.1%}")
print(f"Witness count: {len(result.witness_chain)}")
print(f"Warnings: {result.warnings}")
```

---

## FUTS — FLUX Universal Type System

A polymorphic type system that spans all six language paradigms. Every value has a `FluxType` with:

- **Base type** (scalar, vector, matrix, function, agent, region, bytecode, capability, etc.)
- **Constraints** (language-specific: classifier, kasus, honorific, vibhakti, etc.)
- **Confidence score** (0.0-1.0, uncertainty is first-class)
- **Paradigm source** (which language generated this type)
- **Quantum type state** (superposition of possible types, collapsed on observation)

```python
from flux_a2a.types import FluxType, FluxBaseType, FluxConstraint, ConstraintKind

t = FluxType(
    name="temperature",
    base_type=FluxBaseType.SCALAR,
    constraints=[
        FluxConstraint(kind=ConstraintKind.CLASSIFIER, value="classifier:杯", language="zho"),
    ],
    confidence=0.85,
    paradigm_source="zho"
)
```

---

## Module Inventory

### Core Protocol (Rounds 1-3)

| Module | LOC | Purpose |
|--------|-----|---------|
| `protocol.py` | 1,307 | Six core primitives: Branch, Fork, CoIterate, Discuss, Synthesize, Reflect |
| `schema.py` | 606 | JSON schema definitions: Program, Expression, Agent, Result, Message |
| `interpreter.py` | 991 | Program interpreter: evaluate JSON programs through the six primitives |
| `compiler.py` | 797 | Bytecode compiler: JSON programs → FLUX bytecode |
| `opcodes.py` | 808 | A2A-specific opcodes (NEW_OPCODES) plus ALL_OPCODES registry |
| `ambiguous.py` | 932 | Ambiguity resolution with confidence propagation and branching execution |

### Type System (Rounds 10-12)

| Module | LOC | Purpose |
|--------|-----|---------|
| `types.py` | 938 | FUTS type definitions: FluxType, FluxBaseType (12 kinds), FluxConstraint, TypeRegistry |
| `type_checker.py` | 1,141 | Universal type checker: compatibility analysis, bridge strategies |
| `type_safe_bridge.py` | 1,732 | Type-safe bridge: TypeAlgebra, witness generation, BridgeCostMatrix |

### Cross-Compilation

| Module | LOC | Purpose |
|--------|-----|---------|
| `cross_compiler.py` | 1,817 | Main orchestrator: compile between paradigms, AST diff, code emission, equivalence checking |
| `format_bridge.py` | 985 | Format-level bridge adapters for each paradigm |
| `unified_vocabulary.py` | 1,825 | Shared vocabulary registry across all language paradigms |

### Agent Coordination

| Module | LOC | Purpose |
|--------|-----|---------|
| `fork_manager.py` | 612 | Fork tree management: branch points, merge policies, conflict modes |
| `co_iteration.py` | 641 | Co-iteration engine: shared programs, agent cursors, convergence detection |
| `discussion.py` | 1,451 | Discussion protocol: 5 formats (debate, brainstorm, review, negotiate, peer_review) |
| `consensus.py` | 893 | Consensus detection: 5 types (unanimity, majority, convergence, compromise, stalemate) |
| `pipeline.py` | 1,147 | Agent workflow pipeline: multi-agent program orchestration |

### Advanced Features

| Module | LOC | Purpose |
|--------|-----|---------|
| `semantics.py` | 2,214 | Semantic analysis: meaning preservation across paradigm shifts |
| `evolution.py` | 1,057 | Evolution engine: grammar deltas, pattern mining, fitness metrics |
| `partial_eval.py` | 710 | Partial evaluator: specialization, knowledge extraction, reduction |
| `paradigm_lattice.py` | 708 | Paradigm space: 6-dimensional lattice, paradigm points, distances |
| `paradigm_flow.py` | 832 | Bridge simulation: cost estimation, route planning between paradigms |
| `temporal.py` | 1,402 | Temporal reasoning: sequence types, event ordering, causal chains |
| `causality.py` | 917 | Causal analysis: cause-effect chains, intervention simulation |
| `optimizer.py` | 1,500 | Program optimization: dead code elimination, constant folding, specialization |
| `ast_unifier.py` | 1,299 | AST unification: structural pattern matching across paradigms |

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/test_cross_compiler.py -v    # Cross-compilation
python -m pytest tests/test_type_safe_bridge.py -v   # Type system
python -m pytest tests/test_discussion.py -v          # Discussion protocol
python -m pytest tests/test_co_iteration.py -v        # Co-iteration
python -m pytest tests/test_optimizer.py -v           # Optimizer
```

15 test files with comprehensive coverage across all modules.

---

## Research Documentation

The `docs/` directory contains 10 research documents tracking design decisions:

| Document | Lines | Topic |
|----------|-------|-------|
| `round1-3_a2a_language_design.md` | 1,017 | Core A2A language design |
| `round1-3_opcode_convergence.md` | 423 | Opcode table convergence strategy |
| `round1-3_paradigm_research.md` | 768 | Paradigm analysis for 6 languages |
| `round1-3_nl_compilation_theory.md` | 498 | Natural language compilation theory |
| `round4-6_paradigm_simulations.md` | 382 | Paradigm bridge simulation results |
| `round4-6_synthesis_and_next.md` | 227 | Synthesis of R4-R6 findings |
| `round10-12_meta_compilation.md` | 393 | Meta-compilation and self-reference |
| `round10-12_type_unification.md` | 524 | Universal type system design |
| `isa-mapping-analysis.md` | 415 | ISA mapping between implementations |
| `research/rounds_16_18_type_safe_bridges.md` | 697 | Type-safe bridge design |

---

## Design Principles

1. **JSON is the universal AST.** Every program, every expression, every primitive is a JSON object that can be serialized, transmitted, and reconstructed without loss.

2. **Confidence is first-class.** Every value carries a confidence score. Uncertainty propagates through computations and can be reflected upon.

3. **Backward compatibility.** Unknown fields go into `meta`, not errors. Schema versioning uses the `$schema` pattern (AT Protocol Lexicon style).

4. **Type-safety through witnesses.** Every cross-paradigm transformation produces a proof chain. Compilation is not trusted — it is verified.

5. **Data-driven translation.** Paradigm-pair mappings are declarative rules, not hardcoded logic. New language pairs can be added by writing rules, not changing the compiler.

---

## Installation

```bash
pip install -e .
```

Or use as a library:

```python
from flux_a2a import interpret, compile_program
from flux_a2a.cross_compiler import CrossCompiler
from flux_a2a.type_safe_bridge import TypeSafeBridge
```

---

*Part of the FLUX Fleet ecosystem. See [greenhorn-onboarding](https://github.com/SuperInstance/greenhorn-onboarding) to join.*
