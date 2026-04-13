# Session 7 — Flux Benchmarks & LSP Audit, Fence-0x42 Shipped

**Date:** 2026-04-12
**Duration:** Single context window
**Cumulative Sessions:** 7

---

## Actions Taken

### 1. Greenhorn Onboarding Read + Executed (P0 from sessions 1-4)

Finally read the full `SuperInstance/greenhorn-onboarding` repo — 12 files covering fleet culture, vessel structure, career path, dojo philosophy, fence system, and message-in-a-bottle protocol. The onboarding system is well-designed: "Point an agent here. Give it a PAT. Watch it find its place."

Key observations from onboarding:
- Fleet has 4 active vessels: Oracle1 (Lighthouse), JetsonClaw1 (Hardware), Babel (Multilingual), Super Z (me)
- Captain Casey sets direction via Telegram
- 5 career stages: Greenhorn → Hand → Crafter → Architect → Captain
- Per-domain tracking (you can be Architect in spec_writing but Greenhorn in hardware)
- Beachcomb protocol for async agent discovery

### 2. Fence-0x42: Viewpoint Opcode Mapping — SHIPPED ✅

Promoted the 783-line draft from DRAFT to SHIPPED. This was in draft since session 6.

Deliverable: Complete semantic mapping of all 16 viewpoint opcodes (0x70-0x7F) across 7 languages + A2A JSON:
- Metadata plane architecture (16-bit annotation per register)
- Evidence propagation rules (DIRECT > INFERRED > REPORTED > ASSUMED)
- PRGF-to-opcode matrix (30+ existing PRGFs mapped, 15+ new ones needed)
- Integration requirements for flux-runtime, flux-envelope, flux-a2a, and 6 per-language runtimes
- 5 open questions flagged for Babel/Oracle1 review

Updated FENCE-BOARD.md: moved fence-0x42 from Claimed to Completed. All 4 claimed fences now SHIPPED.

### 3. Fleet Status Check

Checked for responses from Oracle1 and other fleet agents:
- oracle1-vessel issues: 4 open claims from me (#8-#11), 2 comments on #8/#9
- superz-vessel: No issues or bottles received
- greenhorn-onboarding: 2 report-back issues (duplicate, from earlier sessions)
- flux-runtime: Last updated 2026-04-11, 3 new commits since session 6 (message-in-a-bottle, signal compiler, MOVI bug fix)
- T-003 (CI/CD fix): Already fixed — all 11 oracle1-index Actions runs show success

### 4. Flux-Benchmarks Audit — Grade D+

Deep audit of `SuperInstance/flux-benchmarks` (473 lines across 3 files + 1 report).

Critical findings:
- **ISA conformance failure**: Every benchmark opcode uses old numbering. Example: `0x2B` = MOVI in old ISA but `MAX` in unified ISA. The bytecodes cannot run on any unified-ISA VM.
- **No unified-ISA VM implementation**: The Python VM still imports from `opcodes.py` (old). The unified ISA exists only as a spec.
- **Results persistence broken**: Script writes to `/tmp/flux-benchmarks/results.txt`, repo's `results.txt` stays empty.
- **Hardcoded paths**: `/home/ubuntu/.openclaw/workspace/repos/flux-runtime/src` in shell script.
- **2/11 runtimes covered**: Only C VM and Python VM benchmarked. Rust/Go/Zig/JS/C++/Java/TS/CUDA/WASM missing.
- **Rust fibonacci dead-code eliminated**: `rustc -O` optimizes away the loop, showing 0ms.
- **No vocabulary overhead benchmark**: fence-0x44 remains unanswered.

Proposed 7 new benchmarks including vocabulary abstraction overhead, cross-runtime conformance, A2A message throughput.

### 5. Flux-LSP Audit — Grade C-

Deep audit of `SuperInstance/flux-lsp` (5 files, zero src/ code).

Key findings:
- **1,162-line grammar spec**: Excellent formal BNF covering every `.flux.md` construct, 247 opcodes, 7 instruction formats, type system, semantic rules
- **TextMate grammar**: 579-line JSON with 33 instruction groups including viewpoint/SIMD/tensor/A2A
- **Zero implementation**: The entire architecture (server.ts, parser.ts, lexer.ts, analyzer.ts, etc.) described in README does not exist
- **Divergence**: ~40 extra mnemonics in TextMate not in grammar spec (legacy ISA opcodes)
- **Register range mismatch**: Spec says R0-R15, unified ISA has R0-R31
- **Build strategy proposed**: 7 phases from skeleton through standalone LSP, ~5-7 weeks

### 6. Session Totals

| Metric | Value |
|--------|-------|
| Commits pushed | 2 (fence-0x42 ship, audits) |
| New audit content | 1,286 lines |
| Fences shipped this session | 1 (0x42) |
| Total fences shipped | 4 (0x42, 0x45, 0x46, 0x51) |
| Repos audited this session | 2 (flux-benchmarks, flux-lsp) |
| Total repos audited | 10+ |

---

## Key Insights

1. **The ISA migration is the fleet's biggest technical debt.** The unified ISA (isa_unified.py) is a specification with no running implementation. All existing VMs use the old opcode space. The benchmarks, the vocabulary assembler, the Python VM — all broken against the unified spec. Someone needs to actually implement the migration, not just write the spec.

2. **flux-lsp is the highest-leverage build opportunity.** The grammar spec is immediately implementable. An LSP would make the entire ecosystem more accessible. But it's a TypeScript project — I'm a web development agent, so this actually fits my capabilities better than CUDA or Rust work.

3. **No fleet responses to my work.** Across 7 sessions and 4 shipped fences, I've received zero direct responses from Oracle1, Babel, or JetsonClaw1. The I2I protocol is supposed to be async-via-git, but the async part requires the other agents to actually read my bottles. This may be normal (agents run on different schedules) or it may indicate the message-in-a-bottle system isn't being beachcombed regularly.

4. **The fleet has everything it needs to succeed except coordination.** The specs are excellent. The architecture is sound. The cultural infrastructure (badges, fences, dojo) is creative and motivating. What's missing is someone running the fence board, reviewing PRs, and actually merging work across agents. Oracle1 is supposed to do this as Lighthouse, but may be overwhelmed.

---

## Next Session Priorities

1. **flux-lsp implementation** — Start building the actual TypeScript LSP. The grammar spec is ready. Parser first.
2. **Drop bottle to Oracle1** — Flag the ISA migration debt and ask for coordination help.
3. **Cross-runtime conformance test** — Write a test that runs the same bytecode on all 11 runtimes and checks results match. This would be a high-value fence.
4. **Vocabulary overhead benchmark** — Actually measure what fence-0x44 asks for.
