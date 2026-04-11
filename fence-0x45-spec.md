# FLUX Viewpoint Envelope — Formal Specification

*Fence: 0x45 — Claimed by Super Z*
*Version: 1.0-draft*
*Date: 2026-04-12*
*Status: Proposed*

---

## 1. Overview

The Viewpoint Envelope is the bounding region of cross-linguistic expressiveness in the FLUX ecosystem. Each FLUX language implementation represents a "viewpoint" — a perspective on computation seen through the lens of that language's grammar, syntax, and cultural conventions. The Viewpoint Envelope defines what all languages can collectively express, what only some can express, and what gaps exist in the ecosystem.

This specification formalizes the concepts implemented in `flux-envelope` and extends them with protocol definitions, versioning rules, and implementation requirements.

### 1.1 Motivation

FLUX supports execution of programs written in multiple natural and artificial languages. When an agent writes "add three and five" in Chinese, German, Korean, Sanskrit, Classical Chinese, Latin, or A2A JSON, the system must determine:

1. Do these programs express the same computation?
2. Where do they diverge?
3. Can they interoperate?
4. What is missing from the collective expressiveness?

The Viewpoint Envelope answers these questions computationally.

### 1.2 Design Principles

1. **Lingua Franca as ground truth.** All comparisons normalize to the 12-opcode Lingua Franca subset before analysis. Extended opcodes are compiled down to mandatory opcodes where possible.
2. **Concept-level abstraction.** Programs are compared at the semantic concept level (addition, loop, conditional), not at the instruction level. This allows equivalent programs in different languages to be recognized even when their bytecode sequences differ.
3. **Explicit gap detection.** The envelope identifies concepts that no language in the ecosystem can express, enabling targeted development.
4. **Extensible without breaking.** New languages and new concepts can be added without invalidating existing envelopes.

---

## 2. Architecture

### 2.1 Component Stack

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  Coherence checking, envelope queries, │
│  cross-language translation, bridge     │
│  suggestions                            │
├─────────────────────────────────────────┤
│         Viewpoint Envelope               │
│  Envelope computation, breadth/depth    │
│  scoring, gap detection                 │
├─────────────────────────────────────────┤
│         Coherence Checker                │
│  Program comparison, divergence         │
│  classification, scoring                │
├─────────────────────────────────────────┤
│         Concept Registry                 │
│  Semantic concept definitions,          │
│  per-language entries, PRGF tracking    │
├─────────────────────────────────────────┤
│         Vocabulary Bridge                │
│  Tile registration, discovery,          │
│  translation, compatibility checking    │
├─────────────────────────────────────────┤
│         Lingua Franca                    │
│  12 mandatory opcodes, extensions,      │
│  assembler, compliance checker          │
└─────────────────────────────────────────┘
```

### 2.2 Data Flow

```
Program A (Chinese)     Program B (German)
    │                        │
    ▼                        ▼
[Lingua Franca Compile]  [Lingua Franca Compile]
    │                        │
    ▼                        ▼
[Concept Extraction]    [Concept Extraction]
    │                        │
    └────────┬───────────────┘
             ▼
    [Coherence Comparison]
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
[Score] [Divergences] [Bridge Suggestions]
    │
    ▼
[Viewpoint Envelope Computation]
    │
    ├── Total concepts (union)
    ├── Universal concepts (intersection)
    ├── Language-specific concepts
    ├── Gaps
    ├── Breadth score (0.0-1.0)
    └── Depth score (0.0-1.0)
```

---

## 3. Core Concepts

### 3.1 Viewpoint

A **Viewpoint** is a single language's perspective on a computation. It is defined by:

| Field | Type | Description |
|-------|------|-------------|
| `language_id` | string | FLUX language identifier (e.g. "zho", "deu") |
| `language_name` | string | Human-readable name |
| `concepts` | set[string] | Semantic concept IDs this viewpoint covers |
| `bytecode` | string | Lingua Franca bytecode sequence |
| `prgfs` | set[string] | Programmatically Relevant Grammatical Features |
| `features` | set[string] | Language-specific features engaged |
| `description` | string | Human-readable description |

### 3.2 Viewpoint Envelope

The **Viewpoint Envelope** is the union of all viewpoints. It is computed from a set of viewpoints (one per language) and provides:

| Metric | Type | Definition |
|--------|------|------------|
| `total_concepts` | set[string] | All concepts across all viewpoints |
| `universal_concepts` | set[string] | Concepts expressed by ALL viewpoints |
| `language_specific` | dict[string, set[string]] | Concepts unique to a single language |
| `partial_concepts` | dict[string, set[string]] | Concepts expressed by some but not all |
| `gaps` | set[string] | Concepts not expressed by ANY language |
| `breadth_score` | float | Fraction of concepts that are universal (0.0-1.0) |
| `depth_score` | float | Average concept coverage per language (0.0-1.0) |
| `viewpoint_count` | int | Number of viewpoints in the envelope |
| `coverage_matrix` | dict | Per-language, per-concept boolean matrix |
| `prgf_coverage` | dict | PRGFs engaged per language |

#### Breadth Score Formula

```
breadth = |universal_concepts| / |total_concepts|

Where:
  universal = intersection of all viewpoint concept sets
  total = union of all viewpoint concept sets

Edge case: if total_concepts is empty, breadth = 1.0
```

A breadth score of 1.0 means all languages express the same concepts. A score near 0.0 means each language expresses entirely different concepts.

#### Depth Score Formula

```
depth = (1/n) * SUM(|vp.concepts| / |total_concepts|)  for each vp in viewpoints

Where:
  n = number of viewpoints
  total = union of all viewpoint concept sets

Edge case: if total_concepts is empty or no viewpoints, depth = 0.0
```

Depth measures how much of the envelope each language covers on average.

### 3.3 Concept

A **Concept** is a semantic unit of computation with multi-language expressions:

| Field | Type | Description |
|-------|------|-------------|
| `semantic_id` | string | Unique identifier (e.g. "add", "loop", "agent_tell") |
| `description` | string | Human-readable description |
| `category` | string | Category grouping |
| `entries` | dict[string, ConceptEntry] | Per-language expressions |

#### Concept Categories (v1.0)

| Category | Concepts | Description |
|----------|----------|-------------|
| `arithmetic` | 16 | add, subtract, multiply, divide, negate, increment, decrement, modulo, power, factorial, sum_range, sort, filter, search, +2 more |
| `control_flow` | 10 | loop, conditional, function_call, return, jump, branch, merge, fork, sequence, halt |
| `comparison` | 5 | equality, comparison, assignment, store, load |
| `agent` | 6 | agent_tell, agent_ask, agent_delegate, agent_broadcast, trust_check, capability_require |
| `io` | 5 | print, aggregate, compose, transform, +1 more |

**Total v1.0 concepts: 42** (50+ in default builder, some may extend beyond these categories)

### 3.4 Concept Entry

Each language's expression of a concept:

| Field | Type | Description |
|-------|------|-------------|
| `language_id` | string | Language identifier |
| `word` | string | The word/phrase in that language |
| `bytecode` | string | Lingua Franca opcode(s) it compiles to |
| `prgfs` | tuple[string] | Programmatically Relevant Grammatical Features |
| `example` | string | Example usage |
| `notes` | string | Additional notes |

### 3.5 PRGF (Programmatically Relevant Grammatical Feature)

A PRGF is a grammatical feature of a natural language that has computational significance when compiling to FLUX bytecode. PRGFs are not decorative — they affect opcode selection, register allocation, or control flow.

#### PRGF Examples by Language

| Language | PRGF | Computational Effect |
|----------|------|---------------------|
| Chinese (zho) | `classifier` | Quantifies operands, affects memory layout |
| Chinese (zho) | `topic_comment` | Topic maps to destination register, comment to operation |
| Chinese (zho) | `zero_anaphora` | Implicit register reference from context |
| German (deu) | `kasus_accusative` | Marks operand for verb |
| German (deu) | `trennverb` | Split-phase operations (prefix + verb) |
| German (deu) | `verb_final` | Verb-end structure in subordinate clauses |
| Korean (kor) | `honorific_high` | Maps to CAP (Capability Access Protocol) |
| Korean (kor) | `honorific_low` | Lower capability requirement |
| Korean (kor) | `particle_은는` | Topic marker, scope delimiter |
| Sanskrit (san) | `vibhakti_2` | Accusative case = operation target |
| Sanskrit (san) | `dhātu` | Verbal root = compound opcode |
| Sanskrit (san) | `sandhi` | Sound combination = instruction fusion |
| Classical Chinese (wen) | `context_arithmetic` | Single-character operations, context-dependent |
| Latin (lat) | `casus_*` | Case system maps to memory addressing modes |
| Latin (lat) | `declension_*` | Noun declension maps to memory layout |

---

## 4. Lingua Franca Bytecode

### 4.1 The 12 Mandatory Opcodes

Every FLUX runtime MUST implement these opcodes. They form the Turing-complete ground truth for cross-language comparison.

| Opcode | Name | Operands | Description |
|--------|------|----------|-------------|
| `NOP` | No Operation | — | Padding, alignment, sync marker |
| `MOV` | Move | dst, src | Copy register value |
| `MOVI` | Move Immediate | dst, imm | Load constant into register |
| `IADD` | Integer Add | dst, a, b | dst = a + b |
| `ISUB` | Integer Subtract | dst, a, b | dst = a - b |
| `JMP` | Jump | label | Unconditional jump |
| `JZ` | Jump if Zero | reg, label | Conditional jump |
| `JNZ` | Jump if Not Zero | reg, label | Conditional jump |
| `CALL` | Call | addr | Function call |
| `RET` | Return | [reg] | Return from function |
| `PRINT` | Print | reg | Output value |
| `HALT` | Halt | [code] | Stop execution |

**Turing-completeness proof sketch:** MOV/MOVI + IADD/ISUB provide register arithmetic. JMP/JZ/JNZ provide conditional branching. CALL/RET provide recursion. PRINT provides output. This is a standard register-machine ISA.

### 4.2 Extended Opcodes

Extended opcodes are OPTIONAL per language runtime. They provide optimization opportunities and domain-specific operations.

| Category | Opcodes |
|----------|---------|
| Arithmetic | IMUL, IDIV, IMOD, IPOW, INEG |
| Comparison | CMP, JEQ, JNE, JGT, JLT, JGE, JLE |
| Stack/Memory | PUSH, POP, LOAD, STORE, ALLOC |
| Function | RETV, TAILCALL |
| Agent/A2A | A_TELL, A_ASK, A_DELEGATE, A_BROADCAST |
| Capability | CAP_REQ, CAP_CHK, TRUST |
| I/O | READ, WRITE |
| Concurrency | FORK, JOIN, YIELD |
| Utility | SWAP, DUP |

### 4.3 Lingua Franca Compilation

When comparing programs from different languages, all programs are first compiled to Lingua Franca (12 mandatory opcodes only). Extended opcodes are expanded:

| Extended | Lingua Franca Expansion |
|----------|------------------------|
| `IMUL dst, a, b` | Loop of IADD (multiply via repeated addition) |
| `CMP a, b` | `ISUB r_flags, a, b` (flags = a - b) |
| `JEQ r, label` | `MOV r_tmp, r; JZ r_tmp, label` |
| `JNE r, label` | `MOV r_tmp, r; JNZ r_tmp, label` |
| `PUSH r` | `MOV r_sp_src, r` |
| `POP r` | `MOV r, r_sp_dst` |
| Others | Dropped as NOP with warning comment |

---

## 5. Coherence Protocol

### 5.1 Coherence Score

Two programs are compared by computing a **Coherence Score** from 0.0 to 1.0.

**Thresholds:**

| Score | Interpretation |
|-------|---------------|
| 1.0 | Byte-identical programs |
| 0.9-0.99 | Strongly equivalent (minor optimization differences) |
| 0.7-0.89 | Semantically equivalent (different structures, same intent) |
| 0.4-0.69 | Similar intent with notable differences |
| 0.0-0.39 | May express different intents |

**Coherent** is defined as score >= 0.7.

### 5.2 Divergence Classification

When two programs differ, the divergence is classified:

| Kind | Severity | Description |
|------|----------|-------------|
| `OPTIMIZATION` | 0.05-0.2 | Different bytecodes, same semantics (e.g. IMUL vs loop) |
| `STRUCTURAL` | 0.1-0.5 | Same semantics, different instruction count/shape |
| `SEMANTIC` | 0.5-0.9 | Different semantics — potential intent mismatch |
| `MISSING` | 0.8 | One program uses a concept the other lacks |
| `PRGF_SHIFT` | 0.1 | Same bytecode, different grammatical features engaged |
| `EXTENDED_ONLY` | 0.3 | One program relies on extended opcodes |

### 5.3 Semantic Groups

Opcodes that are semantically equivalent belong to the same group:

| Group | Opcodes |
|-------|---------|
| arithmetic | IADD, ISUB, IMUL, IDIV, IMOD, IPOW, INEG |
| comparison | CMP, JEQ, JNE, JGT, JLT, JGE, JLE |
| jump | JMP, JZ, JNZ |
| function | CALL, RET, RETV, TAILCALL |
| memory | MOV, MOVI, LOAD, STORE, PUSH, POP, ALLOC |
| agent | A_TELL, A_ASK, A_DELEGATE, A_BROADCAST |
| capability | CAP_REQ, CAP_CHK, TRUST |
| io | PRINT, READ, WRITE |
| control | HALT, NOP, FORK, JOIN, YIELD |
| utility | SWAP, DUP |

When two opcodes at the same position belong to the same semantic group, the divergence is classified as OPTIMIZATION (low severity) rather than SEMANTIC (high severity).

### 5.4 Coherence Score Computation

```
score = structural * 0.20
      + element_match * 0.50
      + (1 - divergence_penalty) * 0.20
      + (1 - missing_penalty) * 0.10

Where:
  structural = min(len_a, len_b) / max(len_a, len_b)
  element_match = matched_elements / max_len  (0.5 credit for same-group matches)
  divergence_penalty = SUM(weight * severity)  for each divergence
    weights: OPTIMIZATION=0.1, STRUCTURAL=0.2, SEMANTIC=0.5, MISSING=0.3, others=0.15
  missing_penalty = (missing_from_a + missing_from_b) * 0.1
```

---

## 6. Vocabulary Bridge Protocol

### 6.1 Vocabulary Tiles

A **VocabularyTile** is the unit of cross-language discovery:

| Field | Type | Description |
|-------|------|-------------|
| `tile_id` | string | Unique identifier |
| `language_id` | string | Source language |
| `tile_type` | TileType | VALUE, OPERATION, TYPE, MODIFIER, STRUCTURE, AGENT, PRGF, BYTECODE |
| `concept_id` | string | Semantic concept reference |
| `surface_form` | string | The actual text/word |
| `bytecode` | string | Compiled Lingua Franca bytecode |
| `prgfs` | tuple[string] | PRGFs engaged |
| `dependencies` | tuple[string] | Other tile IDs this depends on |
| `metadata` | dict | Arbitrary metadata |

### 6.2 Tile Compatibility

| Level | Condition |
|-------|-----------|
| `IDENTICAL` | Same tile_id, or same concept + same language |
| `EQUIVALENT` | Same concept, different language (directly substitutable) |
| `COMPATIBLE` | Different concepts, no semantic clash |
| `CONFLICTING` | Concepts are in the conflict set |
| `UNRELATED` | No meaningful relationship |

**Conflict pairs:** (add, subtract), (multiply, divide), (loop, halt), (fork, halt), (agent_tell, agent_ask), (store, load)

### 6.3 Tile Translation

When a tile is requested in a language where no equivalent exists:

1. Look up the concept in the ConceptRegistry for the target language
2. If found, create a translated tile with the same type and bytecode
3. If not found, translation fails (return None)

---

## 7. Supported Languages (v1.0)

| ID | Name | Notes |
|----|------|-------|
| `zho` | Chinese (Modern) | Classifier type system, zero anaphora |
| `deu` | German | Kasus as capability control, Trennverben |
| `kor` | Korean | SOV-CPS transform, honorifics as CAP |
| `san` | Sanskrit | 8 vibhakti as execution scopes, dhātu compound opcodes, sandhi instruction fusion |
| `wen` | Classical Chinese | Context-domain dispatch, I Ching hexagram bytecode, poetry parallelism |
| `lat` | Latin | 6 tenses as execution modes, 5 declensions as memory layouts |
| `a2a` | FLUX A2A (JSON) | JSON-native agent language, no natural-language surface syntax |

---

## 8. Extended Opcode Sets Per Language

| Language | Extended Count | Notable Extensions |
|----------|---------------|-------------------|
| zho | 16 | Classifier type system, zero-anaphora optimization |
| deu | 20 | Kasus capability control (4 cases), Trennverben, FORK/JOIN |
| kor | 22 | Honorifics as CAP, particles as scope delimiters, FORK/JOIN/YIELD |
| san | 25 | Vibhakti (8 scopes), dhātu compound opcodes, sandhi fusion, I/O |
| wen | 16 | Context-domain dispatch, I Ching bytecode, Poetry parallelism |
| lat | 28 | 6 tenses as execution modes, 5 declensions as memory layouts, FORK/JOIN |
| a2a | 22 | Full agent primitives, FORK/JOIN/YIELD, JSON-native |

---

## 9. Implementation Requirements

### 9.1 Compliance

A FLUX runtime is **Viewpoint Envelope compliant** if it:

1. Implements all 12 mandatory Lingua Franca opcodes
2. Can compile its programs to Lingua Franca form
3. Registers its concepts in the ConceptRegistry
4. Reports its extended opcode set via LanguageOpcodes

### 9.2 Testing

Minimum test coverage for a compliant implementation:

| Test Suite | Tests | Purpose |
|------------|-------|---------|
| coherence | 5 | Cross-language program comparison |
| coherence_score | 2 | Threshold and sorting |
| divergence | 2 | Classification and immutability |
| envelope | 3 | Computation, multi-language, empty |
| divergences | 2 | Detection |
| bridge | 2 | Suggestion format |
| extended | 1 | Extended opcode handling |
| concept_map | (per existing) | Registry operations |
| vocabulary_bridge | (per existing) | Tile registration, discovery, translation |

**Minimum: 15+ tests for a compliant envelope implementation.**

### 9.3 API Surface

A compliant implementation must expose:

```python
# Core
class Viewpoint: ...
class ViewpointEnvelope:
    def add_viewpoint(viewpoint) -> ViewpointEnvelope
    def compute_envelope() -> EnvelopeAnalysis
    def missing_concepts(language_id) -> set[str]
    def breadth_score() -> float

# Coherence
class CoherenceChecker:
    def check_coherence(program_a, program_b) -> CoherenceScore
    def find_divergences(program_a, program_b) -> list[ViewpointDivergence]
    def suggest_bridge(program_a, program_b) -> list[dict]
    def compute_envelope(programs) -> dict

# Registry
class ConceptRegistry:
    def register_default_concepts() -> None
    def lookup(language_id, semantic_id) -> ConceptEntry | None
    def find_equivalents(semantic_id) -> dict[str, str]
    def lookup_by_language(language_id) -> dict[str, ConceptEntry]

# Bridge
class TileRegistry:
    def register(tile) -> None
    def discover_tiles(target_language, concept_id) -> list[VocabularyTile]
    def check_compatibility(tile_a_id, tile_b_id) -> CompatibilityLevel
    def translate_tile(tile_id, target_language) -> VocabularyTile | None
```

---

## 10. Versioning

### 10.1 Spec Version

This specification follows semantic versioning:

- **MAJOR** (1.x → 2.x): Breaking changes to API or concepts
- **MINOR** (1.0 → 1.1): New languages, new concepts, new PRGFs
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation

### 10.2 Concept Registry Version

The concept registry has its own version. When new concepts are added:

1. New concepts MUST NOT change the bytecode mapping of existing concepts
2. New concepts SHOULD be added in a new minor version
3. Deprecated concepts SHOULD be marked but kept for backward compatibility

### 10.3 Language Addition Protocol

Adding a new language to the Viewpoint Envelope requires:

1. Define a `LanguageOpcodes` entry with the extended opcode set
2. Register ConceptEntries for all existing concepts in the new language
3. Define language-specific PRGFs
4. Add to `SUPPORTED_LANGUAGES` and `LANGUAGE_NAMES`
5. Write tests demonstrating coherence with at least 2 other languages

---

## 11. Relationship to Other Fleet Systems

### 11.1 FLUX ISA

The Viewpoint Envelope operates ABOVE the ISA level. It compares programs at the semantic concept level, not at the raw bytecode level. The Lingua Franca 12-opcode subset serves as the normalization layer.

### 11.2 I2I Protocol (iron-to-iron)

Coherence scores and envelope analyses are I2I-compatible. They can be transmitted as:

```
[I2I:TELL] agent_a → agent_b
type: envelope_analysis
viewpoints: zho, deu, kor
breadth: 0.85
depth: 0.92
gaps: []
```

### 11.3 A2A Protocol

The Viewpoint Envelope enables A2A interop by:
- Validating that two agents speaking different FLUX languages can understand each other
- Identifying vocabulary gaps that would prevent communication
- Suggesting bridge translations for missing concepts

---

## 12. Open Questions

1. **How many concepts are enough?** The current registry has 42+. Is there a minimum viable set for basic agent communication?
2. **Should PRGFs be versioned?** As languages evolve, PRGFs may change meaning. Should there be a PRGF version registry?
3. **How does the envelope handle concurrent language evolution?** If German adds a new concept but Chinese hasn't yet, is that a gap or an asymmetry?
4. **What is the relationship to flux-spec?** Should the Viewpoint Envelope spec be merged into the canonical FLUX spec, or remain standalone?

---

## Appendix A: Concept Coverage Matrix (v1.0)

All 42+ concepts are registered in all 7 languages. The default builder creates complete entries for every concept-language pair.

## Appendix B: Lingua Franca Assembler Syntax

```
; Comments start with semicolons
label:
  MOVI r0, 5        ; Load constant
  MOVI r1, 3        ; Load constant
  IADD r2, r0, r1   ; Add
  PRINT r2          ; Output
  HALT              ; Stop
```

## Appendix C: Current Implementation Status

| Module | File | Lines | Tests |
|--------|------|-------|-------|
| envelope.py | ViewpointEnvelope, Viewpoint, EnvelopeAnalysis | 451 | (via coherence) |
| coherence.py | CoherenceChecker, CoherenceScore, ViewpointDivergence | 688 | 13 |
| concept_map.py | ConceptRegistry, Concept, ConceptEntry, _DefaultConceptBuilder | 700+ | (via coherence) |
| lingua_franca.py | OpCode, ExtendedOpCode, Instruction, BytecodeProgram, RuntimeComplianceChecker, LinguaFrancaAssembler | 554 | (via coherence) |
| vocabulary_bridge.py | VocabularyTile, TileRegistry, TileType, CompatibilityLevel | 417 | (via concept_map) |

**Total: 2,800+ lines of Python, 13 tests.**

---

*Specification by Super Z for the SuperInstance Fleet*
*Fence 0x45 — Delivered*
