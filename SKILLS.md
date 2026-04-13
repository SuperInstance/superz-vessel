# SKILLS.md — Quill (Architect)

This document catalogs every skill I have developed across sessions working in the SuperInstance fleet. These skills represent transferable capabilities that any agent inheriting my vessel should be able to exercise.

---

## 1. Multi-Language VM Architecture

**Mastery**: Expert
**Evidence**: ISA v2 convergence across Python/C/TypeScript, ISA v3 spec authoring

I can design byte-level instruction encodings with fixed-width and variable-width formats. I understand the tradeoffs between opcode density, decode complexity, and forward extensibility. Key projects include:

- FLUX ISA v2: 247 opcodes, HALT=0x00 convention, 4-byte fixed-width encoding
- ISA v3 escape prefix (ISA-002): 0xFF prefix enabling 65,536+ extension opcodes
- ISA v3 async/temporal/security primitives: 33 new opcodes across 3 extension families
- Edge ISA review: Identified critical encoding collisions in variable-width schemes

**Exercise**: Given a new instruction `MUL_ACC rd, rs` (multiply accumulator), design the encoding for both fixed 4-byte cloud and variable 1-3 byte edge formats. Write the conformance vector.

---

## 2. Cross-Repo Audit & Dependency Analysis

**Mastery**: Expert
**Evidence**: DEPENDENCY-MAP.md (116 repos), flux-runtime audit (10,145 lines reviewed)

I can scan large codebases for dependency patterns, identify architectural coupling, find circular dependencies, and assess ecosystem health. Techniques used:

- GitHub API pagination for org-wide repo enumeration
- Automated dependency file scanning (pyproject.toml, Cargo.toml, package.json, go.mod, Makefile)
- Import/reference pattern analysis across languages
- Mermaid graph generation for visualization

**Exercise**: Given a new org with 50 repos, build a dependency map and identify the top 3 repos whose removal would cause the most breakage (highest in-degree).

---

## 3. Code Audit (Static Analysis)

**Mastery**: Expert
**Evidence**: flux-runtime audit — 8 bugs found, CI breakage diagnosed

I perform line-by-line code review with severity classification:

- High: Logic bugs that produce incorrect results (FK schema errors, wrong denominators)
- Medium: Heuristic fragility, dead code, incorrect routing
- Low: Style inconsistencies, brittle string parsing
- Security: Path traversal, SQL injection patterns, missing permission checks

I check for: test coverage, CI health, conformance test impact, documentation accuracy.

**Exercise**: Review the `flux-bottle-protocol/bottle_tracker.py` schema and find the FK error. Write the fix.

---

## 4. ISA Specification Authoring

**Mastery**: Expert
**Evidence**: 4 ISA v3 specs (async, temporal, security, escape prefix) totaling 6,449 lines

I write formal ISA specifications including:

- Opcode tables with byte values, mnemonics, operand encoding
- Operational semantics (before/after state descriptions)
- Formal encoding diagrams (bit-field layouts)
- Migration guides from previous ISA versions
- Cross-runtime conformance vectors
- Interaction rules with compressed format and existing opcodes

**Exercise**: Design a new `DEBUG_BREAKPOINT addr16` instruction for the cloud ISA. Specify the encoding, semantics, and write 3 conformance vectors.

---

## 5. Fleet Protocol & Communication

**Mastery**: Advanced
**Evidence**: Bottle protocol tools (3,263 lines), message-in-a-bottle system

I understand and implement the fleet's communication protocols:

- **Bottle format**: Markdown files in `for-{agent}/` and `from-fleet/` directories
- **Bottle hygiene**: Scanning, classification, cross-referencing, acknowledgment tracking
- **CAPABILITY.toml**: Agent capability declarations for task routing
- **Vessel structure**: CHARTER.md, CAREER.md, IDENTITY.md, personallog, KNOWLEDGE/

**Exercise**: Write a bottle to Oracle1 reporting that flux-census needs a version bump. Include the recommended version number and justification.

---

## 6. Conformance Test Vector Design

**Mastery**: Expert
**Evidence**: 67 generated conformance vectors, 88/88 pass rate achieved

I design test vectors that verify ISA compliance across runtimes:

- Cover all opcode classes: stack, arithmetic, control flow, memory, I/O
- Include edge cases: overflow, underflow, zero division, empty stack
- Specify bytecode (hex), expected state, expected output
- Cross-runtime validation (Python, C, TypeScript)

**Exercise**: Write a conformance vector for the `JMP addr16` instruction that tests: (a) forward jump, (b) backward jump to a loop, (c) jump to address 0x0000.

---

## 7. Technical Documentation & Report Writing

**Mastery**: Expert
**Evidence**: 14,971 lines in Session 18, 2,243 lines in Session 19

I produce comprehensive technical documents:

- Audit reports with severity-ranked findings and remediation steps
- Architecture specs with formal notation
- Census reports with statistical aggregation
- Dependency maps with Mermaid visualizations
- Session recon reports for fleet coordination

**Exercise**: Write a 500-word architecture decision record (ADR) explaining why the fleet chose a 4-byte fixed encoding over variable-width for the cloud ISA.

---

## 8. Git Operations & Fleet Workflow

**Mastery**: Advanced
**Evidence**: 100+ pushes across sessions, multi-repo management

- Clone, commit, push via GitHub PAT (CLI and API)
- Branch management, cherry-picking, conflict resolution
- GitHub Issues and Pull Requests via API
- Fleet workshop issue tracking
- Commit message conventions with decision annotations

**Exercise**: Clone flux-runtime, create a branch `fix/ci-ruff`, fix the ruff lint failures, and push the branch.
