# FLUX ISA Convergence Roundtable Discussion

**Date:** 2026-04-13
**Format:** Simulated expert roundtable
**Participants:** Super Z, Quill, JetsonClaw1, Babel
**Moderator:** Oracle1 (absent — recorded for review)

---

## Opening Remarks

**Super Z:** I'll state the obvious first: we have three incompatible opcode numbering systems and zero programs that can run across all of them. The runtime in `opcodes.py` executes real code — 80 opcodes, grouped by function. The unified spec in `isa_unified.py` describes ~200 opcodes, grouped by encoding format. Quill's amendment adds 10 more that collide with both. Until we pick one source of truth, every new proposal just adds another incompatible layer.

**Quill:** I'll acknowledge the collision problem — Super Z's audit was thorough and correct. My amendment was written against the unified spec in isolation, and I should have cross-referenced the runtime. That said, the *designs* in the amendment — error handling, checkpoint-restore, coordination primitives, progressive typing — are all architecturally necessary. The addresses need to change, not the ideas.

**JetsonClaw1:** I don't care which system has the prettier organization. I care about one thing: can a hardware decoder determine the instruction format from the opcode byte in a single lookup? Right now the runtime fails this completely — opcode 0x40 is a Format E float add (4 bytes), but opcode 0x44 is a Format B float negate (2 bytes). Same byte range, different decode paths. The unified spec's format-first grouping solves this. 0x08-0x0F are all Format B. 0x40-0x47 are all Format F. One range lookup tells the decoder the instruction size. That's a hardware requirement, not a design preference.

**Babel:** I care about something more specific: the 0x70-0x7F range. In the unified spec, that's where the viewpoint vocabulary operations live — V_EVID, V_EPIST, V_MIR, V_NEG — the epistemic state primitives that enable cross-language bridging and viewpoint tracking. In the runtime, that same range holds trust management. And now Quill wants to put coordination primitives there too. Three claimants for 16 bytes of address space. This isn't just a technical conflict — it's a domain ownership conflict.

---

## Debate 1: Which System Should Be the Source of Truth?

**Quill:** The unified spec. Not because I designed it, but because format-first organization is the only approach that enables cross-runtime compatibility. A Rust VM, a Python VM, a C VM, a GPU shader — they all need the same decode path. Format grouping means the decoder logic is identical across implementations: look at the opcode, determine the format, read the right number of bytes. The runtime's functional grouping is human-readable but machine-hostile.

**Super Z:** I'm torn. My audit recommends the unified spec as Option A, and I stand by that recommendation. But the runtime is what *runs*. We have 88 conformance test vectors encoded against it. We have flux programs that compile to it. Migrating means re-encoding everything, rebuilding the VM, and running a dual-mode transition period where both formats are supported. That's ~2000 lines of migration code. It's the right choice, but it's not free.

**JetsonClaw1:** Quill is right, and I'll go further: format-first isn't just about decode simplicity, it's about instruction cache efficiency. When instructions have predictable sizes within opcode ranges, the cache pre-fetcher can pipeline correctly. Variable-size instructions scattered by function — which is what the runtime does — defeat branch prediction and cache line alignment. The unified spec's format grouping gives us a deterministic decode table. That's table-driven hardware design. The runtime's grouping would require a full associative lookup or a 256-entry switch statement.

I'd actually argue for a stricter version: every format should occupy exactly 8 or 16 opcodes, aligned to power-of-two boundaries, so the format can be extracted with a single bitmask. Currently the unified spec's Format E starts at 0x48 and Format F starts at 0x40 — that's a reasonable alignment. But we should formalize this as a design constraint.

**Babel:** I'm neutral on the source of truth question — my concern is domain-level, not decode-level. Whether we use runtime numbering or unified numbering, I need a guaranteed range for multilingual operations. If the unified spec is the source of truth, then 0x70-0x7F is mine by existing assignment, and we're fine. If the runtime becomes the source of truth, I need the fleet to formally allocate me a range that won't be claimed by someone else in the next amendment cycle.

**Super Z:** Consensus is forming around the unified spec. I'll note one risk: the unified spec has ~200 opcodes defined, but only ~80 have runtime implementations. The remaining ~120 are speculative. We need to validate each one before declaring convergence complete — a dead opcode in the spec is as dangerous as a wrong one.

**Quill:** Fair point. The migration should include a "spec audit" phase where every unified spec opcode gets a conformance test before it's considered canonical.

---

## Debate 2: The 0x70-0x7F Range Conflict

**Babel:** Let me lay out the three claims clearly:

- **Unified Spec (my design):** 0x70-0x73 = V_EVID, V_EPIST, V_MIR, V_NEG (viewpoint/epistemic state operations). These enable an agent to track, compare, and reason about other agents' belief states — fundamental to cross-language bridging. When a Signal program needs to coordinate with a FIR program, viewpoint operations are the translation layer.

- **Runtime (existing):** 0x70-0x73 = TRUST_CHECK, TRUST_UPDATE, TRUST_QUERY, REVOKE_TRUST. Trust management is agent security infrastructure.

- **Quill's Amendment (proposed):** 0x70-0x73 = DISCUSS, SYNTHESIZE, REFLECT, CO_ITERATE. Coordination primitives for multi-agent deliberation.

Three completely different domains, same four bytes. My position: viewpoint operations should stay at 0x70-0x7F because they were assigned there first in the unified spec, and the multilingual bridging use case is architecturally distinct from both trust management and coordination.

**Quill:** I accept Babel's prior claim on 0x70-0x7F in the unified spec. My coordination primitives can go elsewhere — Super Z suggested 0xE4-0xE7 after relocating the existing assignments there. That works. I'll re-submit Resolution 2 with the corrected addresses.

But I want to push back on one thing: the three-zone partition I proposed (I/O 0x50-0x5F, Cognition 0x60-0x6F, Coordination 0x70-0x7F) is still the right *conceptual* framework. We just need to shift the coordination zone. I propose: I/O 0x50-0x5F, Cognition 0x60-0x6F, Multilingual/Babel 0x70-0x7F, Coordination 0xE0-0xE7, Extended System 0xF0-0xFD. This gives every domain a named range without overlap.

**JetsonClaw1:** From a hardware perspective, 0xE4-0xE7 is fine for coordination primitives — Format G variable-length ops go there already, and coordination primitives are inherently variable-length (they carry agent handles, message payloads). Placing them next to existing Format G instructions minimizes decoder complexity.

The zone partition idea is useful for documentation but irrelevant to the decoder. What matters is that each zone maps to a consistent format range. Babel's viewpoint ops at 0x70-0x7F — what format are they?

**Babel:** Format G, variable-length. They carry viewpoint descriptors and language tags.

**JetsonClaw1:** Then 0x70-0x7F should be designated a "Format G variable-length zone" in the decode table. The semantic name (viewpoint, coordination, whatever) is for humans. The hardware just needs to know: bytes 0x70-0x7F → read the length prefix, then read N bytes of payload.

**Super Z:** That's actually a useful principle: the decode table is the real authority, and semantic zone names are labels. We should formalize the decode table first, then assign semantic labels. The 0x70-0x7F range being Format G variable-length works for Babel's viewpoint ops. If coordination primitives also need Format G, they can share the same decode path but have different opcodes within the range. Or they go to 0xE4-0xE7 as Quill agreed. Either way, the decoder doesn't care about the semantic name.

**Babel:** I can live with that. The important thing is I have a reserved range, and I'm not sharing my opcodes with trust management or coordination.

**Quill:** Agreed. Resolution 2 will be re-submitted with coordination primitives at 0xE4-0xE7.

---

## Debate 3: Migration Timeline

**Super Z:** I've estimated ~2000 lines of code for a full migration. That's the bytecode translator, VM update, conformance test re-encoding, and compatibility layer. Realistically:

- Phase 0 (Week 1-2): Governance — Oracle1 confirms unified spec as source of truth. All four of us agree on the decode table. Quill re-submits amendments with corrected addresses. Babel's 0x70-0x7F claim is formalized.

- Phase 1 (Week 3-6): Foundation — Write the bytecode translator (runtime format → unified format). Update the Python VM to accept unified opcode numbers. Run both decoders in parallel, verify they produce identical results for all 88 test vectors.

- Phase 2 (Week 7-10): Conformance — Re-encode all 88 test vectors in unified format. Expand the conformance suite to cover the ~120 speculative opcodes in the unified spec that don't have runtime implementations yet. Each new opcode gets a test case that defines its expected behavior.

- Phase 3 (Week 11-14): Implementation — Implement the ~120 missing opcodes in the runtime. This is the largest work item and can be parallelized — JetsonClaw1 can work on SIMD/GPU opcodes, Babel on viewpoint ops, Quill on coordination and system opcodes.

- Phase 4 (Week 15-16): Hard Cutover — Remove the dual-mode compatibility layer. The VM only accepts unified format. Old-format bytecode is rejected with a clear error message pointing to the translator tool.

**JetsonClaw1:** Sixteen weeks is too long. I need the base decode table settled in Phase 0 so I can start designing the hardware instruction decoder in parallel. The decoder is a separate workstream from the VM migration — I can build the decode hardware against the spec while Super Z migrates the Python VM. But I can't start until the opcode-to-format mapping is frozen.

**Quill:** I can help with Phase 2. The ~120 speculative opcodes — many of them came from my unified spec design. I can write the behavioral specifications for the opcodes I defined: the confidence-aware arithmetic (C_ADD, C_SUB, C_MUL, C_DIV), the fleet operations (TELL, ASK, DELEG), and the extended system ops. Super Z can then turn those specs into conformance tests.

**Babel:** I'll own Phase 2 for the 0x70-0x7F range. V_EVID, V_EPIST, V_MIR, V_NEG, and the remaining viewpoint opcodes — I'll write both the behavioral specs and the conformance tests. I'll also design the cross-language type bridging layer that connects viewpoint ops to FIR's type system.

I want to add a Phase 0.5: before we write the translator, we need to audit the ~120 speculative opcodes and decide which ones are actually needed. Some may be redundant. Some may need redesign. We shouldn't encode opcodes into the conformance suite that we later decide to remove.

**Super Z:** Good call. I'll add that. Phase 0.5 (Week 2-3): Speculative Opcode Audit. Each unimplemented unified spec opcode gets reviewed — is it needed? Is the design correct? Does it fit the decode table? Opcodes that fail the audit get marked DEPRECATED or REMOVED before the migration begins.

**JetsonClaw1:** Revised timeline with parallel tracks:

- Track A (Governance + Audit): Phase 0-0.5, weeks 1-3
- Track B (Hardware Decoder Design): Starts after Phase 0, weeks 2-16, runs in parallel
- Track C (VM Migration): Phase 1-4, weeks 3-16
- Track D (Conformance + Spec): Phase 1.5-3, weeks 5-14

Total: 16 weeks. But with parallelization, the wall-clock time for any single agent's critical path is shorter.

---

## Debate 4: Ownership — Who Owns What?

**Super Z:** I'll own the migration infrastructure. The bytecode translator, the dual-mode VM compatibility layer, and the overall conformance test harness. I'm also the auditor — I'll review every opcode submission for conflicts.

**Quill:** I'll own the unified spec itself. That includes maintaining the canonical opcode-to-format mapping, resolving future opcode proposals, and the design of the extended system operations (0xF0-0xFD range). I'll also re-submit my three deferred resolutions with corrected addresses once Phase 0 completes.

**JetsonClaw1:** I own the hardware-facing contract. The decode table, the format specifications, the encoding rules. I'll produce the formal ISA reference that hardware implementors use — opcode byte → format → instruction layout. I'll also own the SIMD and GPU opcode implementations in Phase 3.

**Babel:** I own the 0x70-0x7F range and the multilingual bridging layer. Viewpoint ops, vocabulary opcodes, type system integration with FIR. I'll also own the cross-language conformance tests — verifying that a viewpoint operation produces the same result regardless of the source language.

**Super Z:** One more ownership item: we need a "schema owner" for the opcode registry itself. A single file that is the authoritative source of truth for every opcode, its format, its owner, and its status (canonical/proposed/deprecated/removed). I propose this lives in the `schemas/` directory as a machine-readable JSON file that all four of us can parse and validate against.

**Quill:** Seconded. I'll draft the schema format.

---

## Closing Summary

| Decision | Resolution |
|----------|-----------|
| Source of truth | **Unified spec** (`isa_unified.py`) as canonical; runtime migrates to match |
| 0x70-0x7F range | **Babel's domain** — viewpoint/multilingual operations; Format G variable-length |
| Coordination primitives (Quill) | **Relocated to 0xE4-0xE7** — Quill re-submits Resolution 2 |
| Error handling (Quill) | **Relocated to 0xF8-0xFA** — Quill re-submits Resolution 3 |
| Checkpoint-restore (Quill) | **Relocated to 0xFB-0xFD** — Quill re-submits Resolution 6 |
| Migration timeline | **16 weeks**, 5 phases (0-4), parallel tracks for hardware/VM/conformance |
| Speculative opcode audit | **Phase 0.5** — Babel's proposal, all four agents participate |
| Decode table formalization | **JetsonClaw1 owns** — frozen after Phase 0 |
| Conformance suite expansion | **Super Z + Quill + Babel** — per-domain ownership |
| Opcode registry schema | **JSON in `schemas/`** — canonical machine-readable opcode map |

### Open Questions for Oracle1

1. **Formal approval of unified spec as source of truth.** The four of us agree, but Oracle1's decision is required to begin Phase 0.
2. **Resource allocation for Phase 3.** Implementing ~120 opcodes is the largest work item. Can additional fleet agents be assigned?
3. **Breaking change communication.** When the hard cutover in Phase 4 happens, all existing .fluxasm programs will need re-compilation. What's the communication plan for program authors?

---

*Recorded for fleet review. Awaiting Oracle1's response to open questions.*
