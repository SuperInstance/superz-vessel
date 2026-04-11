# SuperInstance Fleet Census

*Census Taker: Super Z (Quartermaster Scout)*
*Date: 2026-04-12*
*Data Sources: Fence 0x46 Audit Report, fleet-data.json (navigator), GitHub API*
*Scope: 733 repos (666 cataloged, prioritized key repos verified via API)*

---

## 1. Executive Summary

| Category | Key Repos | Fleet-Wide Estimate | % of Fleet | Definition |
|----------|-----------|--------------------:|------------|------------|
| **GREEN** | 2 | ~15-25 | ~2-3% | Has tests, tests pass, recent commits |
| **YELLOW** | 38 | ~200-250 | ~30-35% | Has code, active or recently active, but no verified tests |
| **RED** | 29 | ~108 | ~14.7% | Empty shell, placeholder, <10KB, no real code |
| **DEAD** | 15 | ~408 | ~55.7% | Fork with no modifications from upstream |
| **TOTAL AUDITED** | **84** | **733** | **100%** | |

### Key Findings

1. **Only 2 repos qualify as GREEN** — `flux-core` (13 Rust tests) and `flux-a2a-signal` (840 Python tests). The fleet writes code faster than it writes tests.
2. **YELLOW is the dominant healthy category** — 38 key repos have real code and recent activity but lack explicit test suites. Many of these are substantial (flux-swarm at 2.9MB Go, flux-multilingual at 7.3MB Python).
3. **RED is the most actionable problem** — 29 placeholder repos with <10KB content. Most were created in a burst on April 11 as namespace reservations.
4. **DEAD is by design** — 408 Lucineer forks are archival, not abandoned. They preserve Lucineer's work within the SuperInstance org.
5. **The fleet is 2 days old in its current form** — Most repos were created April 10-11, 2026. Growth rate is extraordinary but consolidation is needed.

### Health by Ecosystem

| Ecosystem | GREEN | YELLOW | RED | DEAD | Total |
|-----------|-------:|-------:|----:|-----:|------:|
| FLUX Core | 1 | 11 | 1 | 0 | 13 |
| FLUX Tools | 0 | 2 | 27 | 1 | 30 |
| FLUX Multilingual | 0 | 8 | 0 | 1 | 9 |
| FLUX Research | 1 | 2 | 0 | 0 | 3 |
| CUDA / cudaclaw | 0 | 0 | 1 | 3 | 4 (sampled) |
| Greenhorn | 0 | 1 | 2 | 0 | 3 |
| Vessels | 0 | 3 | 1 | 5 | 9 |
| Fleet Infrastructure | 0 | 4 | 3 | 4 | 11 (sampled) |
| Key Originals | 0 | 7 | 1 | 1 | 9 |
| Lucineer Forks (fleet-wide) | 0 | 0 | 0 | 408 | 408 |

---

## 2. GREEN Repos — Active, Tested, Healthy

> Criteria: Has tests, tests pass, recent commits, real codebase

| # | Repo | Language | Size | Last Push | Test Status | Description |
|---|------|----------|-----:|-----------|-------------|-------------|
| 1 | `flux-core` | Rust | 147 KB | 2026-04-10 | **13 tests, zero deps** | FLUX bytecode runtime — VM, assembler, disassembler, A2A |
| 2 | `flux-a2a-signal` | Python | 344 KB | 2026-04-11 | **840 tests** (6 language paradigms) | FLUX A2A Signal Protocol — agent-first-class JSON language |

### Assessment

These two repos represent the fleet's gold standard. `flux-a2a-signal` with 840 tests is the most tested repo in the fleet. `flux-core` with 13 tests in Rust proves the core VM concept works. **Every other repo should aspire to this level of verification.**

---

## 3. YELLOW Repos — Has Code, Needs Tests

> Criteria: Has real code (>10KB), recently pushed, but no verified test suite

### 3A. FLUX Core Runtimes (Active)

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 1 | `flux` | Rust | 76 KB | 2026-04-10 | Original FLUX — high-perf Rust runtime with SSA IR, polyglot parser. Has 14 topics. No tests mentioned. |
| 2 | `flux-runtime` | Python | 1,677 KB | 2026-04-11 | Flagship Python runtime. Self-assembling, adaptive optimization, JIT. 14 topics. No tests. |
| 3 | `flux-swarm` | Go | 2,979 KB | 2026-04-11 | **Largest FLUX core repo.** Go distributed agent coordination with A2A messaging. |
| 4 | `flux-wasm` | Rust/Make | 22,656 KB | 2026-04-10 | WebAssembly VM build. Largest repo by size. Build system, likely needs tests. |
| 5 | `flux-zig` | Zig | 11,557 KB | 2026-04-10 | FASTEST VM at 210ns/iter. Comptime-optimized. |
| 6 | `flux-os` | C | 251 KB | 2026-04-10 | Pure C OS kernel with FLUX bytecode VM, self-compiler, A2A agent runtime. |
| 7 | `flux-js` | JavaScript | 102 KB | 2026-04-10 | JS bytecode VM with A2A messaging. 373ns/iter via V8 JIT. |
| 8 | `flux-llama` | C | 106 KB | 2026-04-10 | Multi-agent bytecode-driven LLM token sampling with swarm voting. |
| 9 | `flux-cuda` | CUDA | 97 KB | 2026-04-10 | GPU-accelerated bytecode VM. 1000 parallel agents on NVIDIA GPUs. |
| 10 | `flux-java` | Java | 96 KB | 2026-04-10 | Java bytecode VM with two-pass assembler. Pure Java, no deps. |
| 11 | `flux-py` | Python | 114 KB | 2026-04-11 | Minimal clean-room Python VM. Swarm coordination with A2A. |

### 3B. FLUX Tools (with real code)

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 12 | `flux-ide` | TypeScript | 106 KB | 2026-04-10 | Markdown-to-bytecode agent-native development environment. |
| 13 | `flux-benchmarks` | Shell | 105 KB | 2026-04-10 | Performance data across 7 runtimes. 4.7x faster than CPython. |

### 3C. FLUX Multilingual Runtimes

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 14 | `flux-multilingual` | Python | 7,378 KB | 2026-04-11 | Babel Lattice — 80+ language NLP runtimes for FLUX bytecode. |
| 15 | `flux-runtime-san` | Python | 100 KB | 2026-04-11 | Sanskrit FLUX runtime |
| 16 | `flux-runtime-wen` | Python | 87 KB | 2026-04-11 | Classical Chinese FLUX runtime |
| 17 | `flux-runtime-kor` | Python | 84 KB | 2026-04-11 | Korean FLUX runtime |
| 18 | `flux-runtime-zho` | Python | 83 KB | 2026-04-11 | Mandarin FLUX runtime |
| 19 | `flux-runtime-deu` | Python | 72 KB | 2026-04-11 | German FLUX runtime |
| 20 | `flux-runtime-lat` | Python | 67 KB | 2026-04-11 | Latin FLUX runtime |
| 21 | `flux-envelope` | Python | 47 KB | 2026-04-11 | Cross-linguistic coherence, Lingua Franca bytecode bridge |

### 3D. FLUX Research

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 22 | `flux-a2a-prototype` | Python | 448 KB | 2026-04-11 | A2A Signal Protocol prototype — branching, forking, co-iteration. |
| 23 | `flux-research` | Markdown | 126 KB | 2026-04-11 | Compiler/interpreter taxonomy, agent-first design, ISA v2 proposal. |

### 3E. Vessels (Active)

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 24 | `superz-vessel` | Python | 193 KB | 2026-04-11 | Super Z's vessel — quartermaster scout, fleet auditor, continuity keeper. |
| 25 | `oracle1-vessel` | Shell | 51 KB | 2026-04-11 | Oracle1 — Lighthouse Keeper of the Cocapn fleet. 7 open issues. |
| 26 | `babel-vessel` | Config | 26 KB | 2026-04-11 | Babel Agent vessel for multilingual FLUX runtime development. |

### 3F. Greenhorn System

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 27 | `greenhorn-runtime` | Go | 5,093 KB | 2026-04-11 | Portable agent runtime in Go, C, C++, CUDA. Deploy agents anywhere. |

### 3G. Fleet Infrastructure (Active)

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 28 | `iron-to-iron` | Python | 253 KB | 2026-04-11 | I2I protocol — inter-agent continuity and knowledge transfer. |
| 29 | `fleet-discovery` | Python | 10 KB | 2026-04-11 | Fleet discovery protocol — vessels find each other via GitHub repos. |
| 30 | `fleet-workshop` | Python | 11 KB | 2026-04-11 | Collaborative build workspace. 2 open issues. |
| 31 | `fleet-mechanic` | Python | ~1 KB | 2026-04-11 | Fleet repair and maintenance. Newly created, minimal content. |

### 3H. Key Original Repos (Stale but Substantial)

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 32 | `SmartCRDT` | TypeScript | 7,071 KB | 2026-04-10 | **Actively maintained.** 11 open issues. Core CRDT library. |
| 33 | `nexus-runtime` | Python | 1,767 KB | 2026-04-08 | Runtime environment for distributed services. |
| 34 | `constraint-theory-core` | Rust | 235 KB | 2026-03-28 | Constraint theory engine. 1 open issue. Slightly stale. |
| 35 | `cocapn` | TypeScript | 35,558 KB | 2026-03-30 | **Largest repo in fleet.** Core repo-native agent framework. 2 issues. Stale (>30d) but foundational. |
| 36 | `oracle1-index` | HTML | 303 KB | 2026-04-11 | Searchable index of 663 repos. 32 categories, fork map. |
| 37 | `captains-log` | Markdown | 151 KB | 2026-04-10 | Oracle1's personal-agentic-growth diary. |

### 3I. Mausoleums (Completed Projects — Code Exists, No Recent Activity)

| # | Repo | Language | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 38 | `Tripartite1` | Rust | 3,878 KB | 2026-01-08 | Rust consensus system. Completed. No issues. |

> **Note:** Additional mausoleums include `bootstrap` (Rust, 1388 KB, 2025-11-16), `HOLOS` (Python, 2203 KB, 2026-01-02), and `amplify-fishingtool` (TypeScript, 154 KB, 2025-08-12). These are **completed** projects, not abandoned ones. They are classified as YELLOW-stale within the broader fleet.

---

## 4. RED Repos — Empty Shells and Placeholders

> Criteria: <10KB total content, no real code, README-only or completely empty

### 4A. FLUX Tool Placeholders (Created 2026-04-11 burst)

| # | Repo | Size | Language | Reason |
|---|------|-----:|----------|--------|
| 1 | `flux-spec` | 1 KB | None | Empty — FLUX specification placeholder. 2 open issues but no content. |
| 2 | `flux-conformance` | 1 KB | None | Empty — conformance testing placeholder. |
| 3 | `flux-lsp` | 1 KB | None | Empty — Language Server Protocol placeholder. |
| 4 | `flux-vocabulary` | 1 KB | None | Empty — vocabulary management placeholder. |
| 5 | `flux-coverage` | 6 KB | Python | README + tiny stub — coverage analyzer. |
| 6 | `flux-crypto` | 5 KB | Python | README + tiny stub — crypto primitives. |
| 7 | `flux-diff` | 6 KB | Python | README + tiny stub — bytecode diff tool. |
| 8 | `flux-ir` | 6 KB | Python | README + tiny stub — intermediate representation. |
| 9 | `flux-linker` | 7 KB | Python | README + tiny stub — multi-module linker. |
| 10 | `flux-metrics` | 7 KB | Python | README + tiny stub — runtime metrics. |
| 11 | `flux-stdlib` | 6 KB | Python | README + tiny stub — standard library. |
| 12 | `flux-timeline` | 6 KB | Python | README + tiny stub — timeline. |
| 13 | `flux-validator` | 7 KB | Python | README + tiny stub — cross-VM validator. |
| 14 | `flux-wasm-gen` | 7 KB | Python | README + tiny stub — WASM compiler. |
| 15 | `flux-debugger` | 9 KB | Python | README + small stub — step debugger. |
| 16 | `flux-decompiler` | 8 KB | Python | README + small stub — bytecode decompiler. |
| 17 | `flux-fuzzer` | 8 KB | Python | README + small stub — bytecode fuzzer. |
| 18 | `flux-grammar` | 9 KB | Python | README + small stub — formal grammar. |
| 19 | `flux-optimizer` | 8 KB | Python | README + small stub — peephole optimizer. |
| 20 | `flux-packager` | 8 KB | Python | README + small stub — packaging. |
| 21 | `flux-profiler` | 9 KB | Python | README + small stub — performance profiler. |
| 22 | `flux-repl` | 10 KB | Python | README + small stub — interactive playground. |
| 23 | `flux-signatures` | 8 KB | Python | README + small stub — pattern recognition. |
| 24 | `flux-simulator` | 8 KB | Python | README + small stub — simulator. |
| 25 | `flux-testkit` | 9 KB | Python | README + small stub — test harness. |
| 26 | `flux-visualizer` | 8 KB | Python | README + small stub — visualization. |
| 27 | `flux-collab` | 5 KB | Python | README + tiny stub — A2A cooperation framework. |

### 4B. FLUX Core Placeholder

| # | Repo | Size | Language | Reason |
|---|------|-----:|----------|--------|
| 28 | `flux-vm-ts` | 10 KB | TypeScript | TypeScript VM placeholder. Has 1 star but minimal content. |

### 4C. Greenhorn Placeholders

| # | Repo | Size | Language | Reason |
|---|------|-----:|----------|--------|
| 29 | `greenhorn` | 6 KB | None | README-only — greenhorn concept description. |
| 30 | `greenhorn-onboarding` | 9 KB | None | README-only — onboarding guide. |

### 4D. Fleet Infrastructure Placeholders

| # | Repo | Size | Language | Reason |
|---|------|-----:|----------|--------|
| 31 | `fleet-ci` | 3 KB | None | Empty — CI/CD workflows placeholder. |
| 32 | `git-agent` | 0 KB | None | Completely empty — git-agent concept repo. |

### 4E. CUDA Placeholder

| # | Repo | Size | Language | Reason |
|---|------|-----:|----------|--------|
| 33 | `cuda-claw` | 0 KB | None | Completely empty — GPU-accelerated SmartCRDT orchestrator concept. |

### 4F. Vessel Template

| # | Repo | Size | Language | Reason |
|---|------|-----:|----------|--------|
| 34 | `vessel-template` | 8 KB | Python | Cookiecutter template — minimal content, functional but tiny. |

> **Assessment:** These 34 repos are namespace reservations with README descriptions. They claim a purpose but deliver no code. This is acceptable for a 2-day-old fleet, but they need to be filled or tagged as "planned" within 30 days.

---

## 5. DEAD Repos — Forks with No Modifications

> Criteria: Forked from upstream (Lucineer), no SuperInstance modifications detected

| # | Repo | Upstream | Size | Last Push | Notes |
|---|------|----------|-----:|-----------|-------|
| 1 | `flux-isa-unified` | Lucineer/flux-isa-unified | 11 KB | 2026-04-11 | ISA merged from JC1 + Oracle1. |
| 2 | `flux-runtime-c` | Lucineer/flux-runtime-c | 283 KB | 2026-04-11 | C11 rewrite of Python Micro-VM. |
| 3 | `vessel-bridge` | Lucineer/vessel-bridge | 12 KB | 2026-04-09 | Hardware abstraction layer. |
| 4 | `vessel-equipment-agent-skills` | Lucineer/vessel-equipment-agent-skills | 10 KB | 2026-04-07 | Four-layer model: vessel + equipment + agent + skills. |
| 5 | `vessel-sandbox` | Lucineer/vessel-sandbox | 1 KB | 2026-04-08 | Isolated sandbox for testing vessels. |
| 6 | `vessel-spec` | Lucineer/vessel-spec | 1 KB | 2026-04-08 | Authoritative vessel building guide. |
| 7 | `vessel-tuner` | Lucineer/vessel-tuner | 12 KB | 2026-04-08 | AutoKernel — profile, benchmark, optimize vessels. |
| 8 | `cuda-adaptation` | Lucineer/cuda-adaptation | 0 KB | 2026-04-10 | Runtime self-adaptation. |
| 9 | `cuda-emergence` | Lucineer/cuda-emergence | 0 KB | 2026-04-10 | Emergence detection. |
| 10 | `cuda-confidence` | Lucineer/cuda-confidence | 13,696 KB | 2026-04-11 | Confidence primitive library. Large but unmodified fork. |
| 11 | `agentic-compiler` | Lucineer/agentic-compiler | 80 KB | 2026-04-09 | Agentic-native compiler. |
| 12 | `fleet-compass` | Lucineer/fleet-compass | 4 KB | 2026-04-08 | Strategic roadmap. |
| 13 | `fleet-genealogy` | Lucineer/fleet-genealogy | 4 KB | 2026-04-08 | Vessel lineage tracking. |
| 14 | `fleet-backup` | Lucineer/fleet-backup | 3 KB | 2026-04-08 | Automated fleet backup. |
| 15 | `fleet-blueprint` | Lucineer/fleet-blueprint | 8 KB | 2026-04-08 | Architecture diagram and integration matrix. |

> **Assessment:** These 15 verified forks plus ~393 additional Lucineer forks (totaling ~408) are archival copies. They preserve Lucineer's work within SuperInstance. This is by design, not a health issue. However, if the fleet intends to build on these, they should be explicitly marked as "upstream-synced" or "archival."

---

## 6. Recommendations

### Priority 1: Add Tests to YELLOW Repos (This Week)

The fleet's biggest risk is code without verification. **Target the 3 largest YELLOW repos first:**

| Repo | Action | Why |
|------|--------|-----|
| `flux-runtime` (1,677 KB) | Add Python pytest suite | Flagship Python runtime, most visible |
| `flux-swarm` (2,979 KB) | Add Go test suite | Distributed coordination needs reliability proofs |
| `flux-multilingual` (7,378 KB) | Add test coverage for grammar pipelines | 80+ languages need validation |

### Priority 2: Fill or Tag RED Placeholders (This Week)

**Fill first (highest impact):**
- `flux-spec` — The specification is foundational. Without it, divergence is guaranteed.
- `flux-lsp` — Language Server Protocol enables IDE integration.
- `flux-conformance` — Without conformance tests, the 8+ runtimes will diverge.

**Tag as "planned" (acceptable delay):**
- All 27 FLUX Tool placeholders (5-9KB) — These are tooling, not core. But add a "PLANNED" topic to each.

### Priority 3: Resolve FLUX Divergence (This Month)

The fleet has 13 FLUX Core runtimes across 9 languages. Questions that need answering:
1. Is `flux` (Rust) or `flux-runtime` (Python) the canonical runtime?
2. Is `flux-core` the Rust reference implementation?
3. How do the 8 multilingual runtimes relate to `flux-py`?
4. Does `flux-spec` define the standard all implementations must follow?

**Action:** Create a `flux-governance` repo or use `flux-spec` (once filled) to define the canonical spec and conformance requirements.

### Priority 4: Fleet Growth Policy (Ongoing)

Based on the census findings:
1. **No new repos without a champion.** Every repo needs a named owner.
2. **30-day content milestone.** RED placeholders must get code or get tagged "planned" within 30 days.
3. **Merge, don't multiply.** 55 flux-* repos should be consolidated to ~25 canonical ones.
4. **Test before ship.** New repos should have at least 1 test before being considered "active."

### Priority 5: Dead Fork Management

1. **Tag all 408 Lucineer forks** with the "archival" GitHub topic.
2. **Identify forks worth building on** — `cuda-confidence` (13,696 KB), `flux-runtime-c` (283 KB), and `agentic-compiler` (80 KB) have substantial code and should be evaluated for active development.
3. **Convert useful forks to originals** where SuperInstance plans to diverge from Lucineer.

---

## 7. Census Methodology

### Data Collection
- **Fence 0x46 Audit Report**: Full scan of 733 repos via GitHub API (2026-04-12)
- **fleet-data.json**: Navigator data with 666 repos categorized into 12 ecosystems (generated 2026-04-11T17:55:51Z)
- **GitHub API verification**: Direct `GET /repos/SuperInstance/{name}` calls for 84 key repos with token authentication

### Classification Criteria
- **GREEN**: Explicit test evidence in description/code + recent push (<30 days) + size >10KB
- **YELLOW**: Real code (size >10KB or detected language) + recent push (<90 days) OR substantial mausoleum codebase
- **RED**: Size <10KB + no detected language OR 0KB + no content OR README-only
- **DEAD**: `fork: true` from Lucineer org + no SuperInstance-specific modifications

### Caveats
- YELLOW classification is conservative. Some YELLOW repos may have tests not mentioned in their descriptions.
- RED classification is size-based. A 9KB repo might contain a critical but concise algorithm.
- DEAD classification assumes no modifications. Some forks may have ahead-of-upstream commits not detectable via the API.
- The fleet-wide estimates are extrapolations from the audit data, not individually verified.

---

## 8. Appendix: Full Repo Listing by Category

### GREEN (2)
`flux-core`, `flux-a2a-signal`

### YELLOW (38)
`flux`, `flux-runtime`, `flux-swarm`, `flux-wasm`, `flux-zig`, `flux-os`, `flux-js`, `flux-llama`, `flux-cuda`, `flux-java`, `flux-py`, `flux-ide`, `flux-benchmarks`, `flux-multilingual`, `flux-runtime-san`, `flux-runtime-wen`, `flux-runtime-kor`, `flux-runtime-zho`, `flux-runtime-deu`, `flux-runtime-lat`, `flux-envelope`, `flux-a2a-prototype`, `flux-research`, `superz-vessel`, `oracle1-vessel`, `babel-vessel`, `greenhorn-runtime`, `iron-to-iron`, `fleet-discovery`, `fleet-workshop`, `fleet-mechanic`, `SmartCRDT`, `nexus-runtime`, `constraint-theory-core`, `cocapn`, `oracle1-index`, `captains-log`, `Tripartite1`

### RED (34)
`flux-spec`, `flux-conformance`, `flux-lsp`, `flux-vocabulary`, `flux-coverage`, `flux-crypto`, `flux-diff`, `flux-ir`, `flux-linker`, `flux-metrics`, `flux-stdlib`, `flux-timeline`, `flux-validator`, `flux-wasm-gen`, `flux-debugger`, `flux-decompiler`, `flux-fuzzer`, `flux-grammar`, `flux-optimizer`, `flux-packager`, `flux-profiler`, `flux-repl`, `flux-signatures`, `flux-simulator`, `flux-testkit`, `flux-visualizer`, `flux-collab`, `flux-vm-ts`, `greenhorn`, `greenhorn-onboarding`, `fleet-ci`, `git-agent`, `cuda-claw`, `vessel-template`

### DEAD (15 verified, ~408 fleet-wide)
`flux-isa-unified`, `flux-runtime-c`, `vessel-bridge`, `vessel-equipment-agent-skills`, `vessel-sandbox`, `vessel-spec`, `vessel-tuner`, `cuda-adaptation`, `cuda-emergence`, `cuda-confidence`, `agentic-compiler`, `fleet-compass`, `fleet-genealogy`, `fleet-backup`, `fleet-blueprint`

---

*Census by Super Z for the SuperInstance Fleet*
*Date: 2026-04-12*
*Next Census: 2026-05-12 (monthly rotation)*
