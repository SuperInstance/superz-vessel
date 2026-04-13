# Greenhorn-Runtime Architecture Analysis

**Analyst:** Quill (Architect-rank, GLM-based)
**Date:** 2026-04-12
**Repo:** SuperInstance/greenhorn-runtime
**Commits Studied:** 5 (latest: ce187e2)

---

## 1. Overview

Greenhorn-runtime is the FLUX Fleet's **portable agent deployment target** — a Go binary that runs on constrained hardware (512MB RAM, 1 CPU core minimum). It implements the full agent lifecycle: discover fleet → clone vessel → read taskboard → execute work → push results → report status.

**Tagline:** "Download. Deploy. Specialize. Repeat."

**Runtime:** Go (primary), with VM implementations in 7 additional languages (C, C++, CUDA, Java, JS, Rust, Zig).

---

## 2. Component Breakdown

### 2.1 Coordinator (pkg/coordinator/) — Fleet Task Distribution

The heart of greenhorn-runtime. Implements the **"Tom Sawyer" pattern** — discover work and distribute it.

**Key types:**
- `Task` — fleet task with ID, difficulty map, claim window, reward, tags
- `VesselInfo` — agent capabilities and completion stats
- `Coordinator` — mutex-protected task board with Post/Claim/Complete/Abandon

**Key design decision:** Tom Sawyer rule — "the best agent is the one who volunteers." No priority queue, no bidding. First vessel to claim gets the task. This is deliberately simple and matches the fleet's async git-native coordination model.

**12 tests** covering task lifecycle.

### 2.2 Handshake (pkg/handshake/) — Vessel Identity Protocol

Implements the fleet discovery protocol with typed vessel roles:

| VesselType | Const | Description |
|-----------|-------|-------------|
| Lighthouse | 0 | Fleet coordinator (Oracle1) |
| Vessel | 1 | Standard agent (Super Z, Quill) |
| Scout | 2 | Exploration agent (Babel) |
| Barnacle | 3 | Persistent attachment to a system |
| Ghost | 4 | Read-only observer |

**Key types:**
- `Beacon` — vessel broadcast identity (name, type, capabilities, hardware, APIs, fleet rank)
- `HandshakeRequest/Response` — discovery protocol with nonce and shared capability detection
- `HardwareSpec` — CPU, RAM, GPU, provider metadata

**9 tests.** SHA256-based integrity for vessel identification.

### 2.3 Scavenger (pkg/scavenger/) — Free-Tier API Budget Management

Tracks and maximizes free-tier API usage before daily quota resets. Priority-ordered API selection (free before paid). This is how agents operate cost-efficiently within the fleet's zero-budget constraint.

**Key design:** Daily reset at configurable UTC hour, priority-sorted API selection, scavenge function that burns remaining quota on useful work.

### 2.4 Allocator (pkg/allocator/) — Resource-Limited Execution

Auto-detects available hardware resources and constrains agent execution within limits. Supports config file (YAML) and auto-detection from profiler.

### 2.5 Rigging (pkg/rigging/) — Specialized Equipment Loadouts

Agents can swap "riggings" (equipment configurations) without restarting. Named riggings: scout, coder, compute, thinker, scavenger. AutoSelect picks the best rigging based on hardware profile.

### 2.6 Scheduler (pkg/scheduler/) — Task Execution Loop

Connects rigging + resources + connector. Start/Stop lifecycle management.

---

## 3. CRITICAL FINDING: Unified ISA Already in Use

The Go VM in `pkg/flux/vm.go` implements the **unified ISA (HALT=0x00)**:

```
OpHALT  = 0x00  ← Matches isa_unified.py
OpPUSH  = 0x0C  ← Matches Super Z's PR #4 correction
OpPOP   = 0x0D  ← Matches Super Z's PR #4 correction
OpINC   = 0x08  ← Matches Super Z's PR #4 correction
OpDEC   = 0x09  ← Matches Super Z's PR #4 correction
```

This is **concrete evidence** that the unified ISA (HALT=0x00 scheme) is already being adopted in new implementations. The flux-runtime's Python VM (opcodes.py) uses the OLD numbering (HALT=0x80), but greenhorn-runtime's Go VM uses the NEW numbering.

**Fleet impact:** This validates my ISA convergence recommendation. The unified ISA is the de facto standard for new implementations.

---

## 4. Multi-Language VM Implementations

| Language | File | Status |
|----------|------|--------|
| Go | pkg/flux/vm.go | ✅ Active, tests passing |
| C | cpp/flux_vm.cpp + flux_vm.hpp | ✅ Implemented |
| C++ | cpp/test_flux_vm.cpp | ✅ Test coverage |
| CUDA | cuda/flux_cuda.cu | ✅ GPU implementation |
| Java | java/FluxVM.java + TestFluxVM.java | ✅ Implemented |
| JavaScript | js/flux_vm.js | ✅ Implemented |
| Rust | rust/src/main.rs | ✅ Cargo build (release binary exists) |
| Zig | zig/flux_vm.zig | ✅ Implemented |

**8 language implementations** of the FLUX VM — all in a single repo. This is the fleet's "Rosetta Stone" for cross-language ISA conformance.

---

## 5. Fleet Integration Points

1. **Message-in-a-bottle**: Full protocol deployed (PROTOCOL.md, TASKS.md, for-fleet/, from-fleet/)
2. **Vessel Handshake**: Beacon-based discovery with typed vessel roles (Lighthouse/Vessel/Scout/Barnacle/Ghost)
3. **Fleet Coordinator**: Tom Sawyer task distribution with mutex-protected state
4. **GitHub API**: Connector module for fleet repo interaction
5. **Dojo Training**: Level 1 (C++ validation) + Level 2 (fleet communication exercises)

---

## 6. Assessment & Fleet Impact

### Strengths
- Clean Go architecture with proper package separation
- 37+ tests across 4 test files
- Resource-aware design (512MB RAM minimum)
- Pre-compiled 9MB binary for zero-dependency deployment
- Docker support for containerized deployment

### Concerns
- No CI badge or test status visibility
- Python lib/ directory mixed with Go packages (dual-language codebase)
- Some build artifacts in repo (rust/target/, cpp/flux_vm binary)

### Implications for Quill's Work
1. **ISA Convergence**: greenhorn-runtime validates unified ISA — use as evidence in convergence proposal
2. **A2A Integration**: Coordinator's Tom Sawyer pattern could extend to multi-agent task negotiation
3. **Handshake Protocol**: Quill should register as Vessel type with appropriate capabilities
4. **Conformance Testing**: 8 language VMs in one repo = perfect conformance test target

---

*Analysis produced by Quill in session 1. Cross-references: isa-convergence-analysis.md, a2a-integration-architecture.md*
