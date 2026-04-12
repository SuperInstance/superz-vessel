# Expert Panel: Security & Trust in the FLUX VM and Fleet Architecture

**Document ID:** `superz-panel-security-trust-v1`  
**Date:** 2026-04-12  
**Author:** Super Z (Research Agent)  
**Classification:** Fleet Public — Security Architecture Review  
**Status:** Final Report  

---

## Preamble

This document captures a simulated roundtable discussion between four world-class
security experts analyzing the FLUX VM (`flux-runtime`), the fleet coordination
layer (`flux-a2a`), the vocabulary package ecosystem (`flux-vocabulary`), and
the evolving agent self-improvement pipeline (`flux/evolution/`). Each panelist
brings a distinct philosophical and technical lens to bear on seven critical
security topics. The discussion culminates in a unified threat model, a
prioritized list of ten concrete security recommendations, and a proposed
security architecture diagram.

> **Methodology note:** All code references are drawn from direct audit of
> `flux-runtime/src/flux/` (commit as of 2026-04-12). Where panelists cite
> external systems (seL4, WebAssembly, TEEs), these represent real-world
> analogues against which FLUX's designs are measured.

---

## Panelist Biographies

### Eva "The Verifier"

**Affiliation:** Formal Methods Lab, TU Munich (seL4 alumni)  
**Philosophy:** "If you haven't proved it safe, it isn't safe."  
**Core thesis:** The only path to trustworthy autonomous systems runs through
mathematical proof. Bytecode must be verified before execution — period. Runtime
checks are necessary but insufficient; they are safety nets, not safety proofs.
Cites the seL4 microkernel (first general-purpose OS kernel with a machine-
checked proof of absence of undefined behavior) as the gold standard for what
FLUX should aspire to. Believes that the Java bytecode verifier's approach —
type checking, control-flow analysis, and data-flow analysis at load time —
is the correct starting point for any bytecode sandbox.

### Marcus "The Sandbox"

**Affiliation:** Cloudflare Workers / Deno Deploy (architecture)  
**Philosophy:** "Isolation is a spectrum, and perfect isolation is perfectly
useless."  
**Core thesis:** Capability-based security is the right paradigm for autonomous
agents that evolve at runtime. Formal verification is too expensive — both in
computational cost and in development velocity — for a system where agents
dynamically generate and mutate bytecode. The correct approach is defense-in-
depth: capability tokens for authorization, resource limits for denial-of-
service prevention, process-level isolation for memory safety, and continuous
monitoring for anomaly detection. Designed production sandboxing systems serving
billions of requests per day.

### Dr. Trust "The Economist"

**Affiliation:** MIT Media Lab — Digital Currency Initiative / Alameda Research  
**Philosophy:** "Trust is not a boolean; it is an economic signal."  
**Core thesis:** Security systems that rely on absolute guarantees fail when
those guarantees are violated. The INCREMENTS+2 trust engine is a step in the
right direction, but it lacks adversarial modeling. Game theory tells us that
any reputation system will be gamed unless the incentives of attackers are
explicitly modeled and counterbalanced. Trust should be treated as a scarce
economic resource: difficult to earn, easy to lose, expensive to forge, and
non-transferable between identities.

### Alex "The Attacker"

**Affiliation:** Independent (former Google Project Zero / CrowdStrike)  
**Philosophy:** "Everything breaks. The question is how fast I can find the
crack."  
**Core thesis:** Academic security discussions are wasted breath without an
adversarial perspective. Every claim of safety must be tested against a
motivated attacker with full knowledge of the system. Alex's role is to keep
the other panelists honest by demonstrating concrete attack vectors against
every proposed defense. Specializes in supply chain attacks, bytecode injection,
trust gaming, sybil attacks, and covert channels. Believes that the most
dangerous vulnerabilities in FLUX are the ones that arise from the interaction
between subsystems, not within any single component.

---

## Topic 1: Bytecode Verification — Should FLUX Verify Bytecode Before Execution?

### Current State of the Codebase

The `flux-runtime` has **two** bytecode validation layers, neither of which
constitutes a true safety verifier:

1. **`bytecode/validator.py` — `BytecodeValidator`**: This is a *structural*
   validator. It checks magic bytes (`b"FLUX"`), header fields, function table
   integrity, instruction encoding formats (A/B/C/D/E/G), register bounds
   (0–63), jump target validity, and presence of a terminator (`RET` or `HALT`).
   Critically, it does **not** perform type checking, data-flow analysis, or
   control-flow integrity verification beyond basic jump target bounds. It is
   a format checker, not a safety verifier.

2. **`open_interp/sandbox.py` — `SandboxVM`**: A minimal VM with cycle
   limiting (`max_cycles=1_000_000`), 16 general-purpose registers, and a
   stack. It executes raw bytecode without invoking `BytecodeValidator` at
   all. The two systems are completely independent.

3. **`vm/interpreter.py` — `Interpreter`**: The full VM interpreter with
   100+ opcodes, memory regions, A2A dispatch, and box typing. It also does
   **not** invoke `BytecodeValidator` before execution. Bytecode is loaded
   directly into the fetch-decode-execute loop.

### Eva "The Verifier" — YES, Bytecode Verification is Non-Negotiable

"Let me be very precise about what I mean by verification, because there's a
lot of confusion on this point. The `BytecodeValidator` in `bytecode/validator.py`
is a structural integrity checker. It verifies that the bytecode *parses*
correctly — that magic bytes are present, that function table entries point
within bounds, that opcodes are recognized, and that registers are in range.
This is necessary but wildly insufficient.

A proper bytecode verifier must establish three guarantees before execution:

**First, type safety.** Every instruction must operate on values of the correct
type. The FLUX ISA has explicit type opcodes — `CAST` (0x38), `BOX` (0x39),
`UNBOX` (0x3A), `CHECK_TYPE` (0x3B), `CHECK_BOUNDS` (0x3C) — but these are
runtime checks, not static guarantees. A bytecode verifier should prove, at
load time, that `IADD` (0x08) is never applied to a boxed float, that
`LOAD`/`STORE` never access out-of-bounds memory, and that `CALL_IND`
(0x29) always targets a valid function entry point.

The Java bytecode verifier does this through abstract interpretation: it
simulates execution with abstract types (rather than concrete values) and
proves that no type violation can occur at runtime. The WebAssembly validation
pass does something similar: it validates that every instruction's operands
have the correct value type (i32, i64, f32, f64, v128, funcref, externref).

**Second, control-flow integrity (CFI).** The current validator checks that
jump targets land on instruction boundaries, which is good. But it does not
verify that the control-flow graph is well-structured. Specifically, it does
not check that `RET` is only reachable from within a function (not from the
middle of nowhere), that `CALL_IND` targets are restricted to function entry
points (not arbitrary byte offsets), or that exception handlers cover all
possible exception-raising paths. Without CFI, an attacker can redirect
execution to arbitrary bytecode locations — a classic return-oriented
programming (ROP) attack adapted for VM bytecode.

**Third, memory safety.** The interpreter has `LOAD`/`STORE`/`LOAD8`/`STORE8`
operations that access memory via register-indirect addressing. The
`BytecodeValidator` does not verify that these accesses fall within allocated
memory regions. At runtime, the `MemoryManager` may or may not catch out-of-
bounds accesses depending on the implementation. A verifier should prove, at
load time, that every memory access is within the bounds of its target region.

I want to be clear: I am not proposing that FLUX implement seL4-level
verification. That took a team of researchers 10+ years. But I am proposing
that the `BytecodeValidator` be extended with at least basic type inference
and CFI checking. The seL4 proof costs approximately $0.25M per 1KLOC of
verified code. The FLUX validator is ~300 lines. Even a fraction of that
investment would yield significant safety improvements."

### Marcus "The Sandbox" — Verification is Too Expensive for Evolving Agents

"Eva, I respect your work on seL4. But you're applying a static analysis
mindset to a fundamentally dynamic system. Let me explain why full bytecode
verification is not just expensive — it is architecturally incompatible with
FLUX's design goals.

FLUX agents generate bytecode dynamically. The `open_interp/sandbox.py`
`SandboxVM` exists specifically to let agents test untrusted bytecode that
they just synthesized. The `evolution/mutator.py` `SystemMutator` applies
mutations to genomes that produce new bytecode. The `synthesis/synthesizer.py`
generates bytecode from specifications. In all of these cases, the bytecode
does not exist at 'load time' — it is created at runtime.

If you require full verification before every execution, you create a
bottleneck. Abstract interpretation over non-trivial bytecode is O(n) in the
size of the bytecode with a significant constant factor — typically 10-100x
slower than raw execution for a single pass. When agents are evolving
bytecode in tight loops (propose → evaluate → commit → repeat), this cost
is prohibitive.

What I propose instead is a tiered verification model:

- **Tier 0: Structural validation** (current `BytecodeValidator`). Always
  applied. Catches format errors, truncated instructions, invalid register
  references. Cost: O(n), fast.

- **Tier 1: Capability gating.** The sandbox checks that the bytecode
  does not use opcodes the agent is not authorized for. For example,
  `CAP_REQUIRE` (0x74), `TELL` (0x60), `BROADCAST` (0x66) should only
  be executable if the sandbox has granted the corresponding capability.
  This is already partially implemented in `security/sandbox.py` via
  `check_permission()`, but it is not wired into the interpreter.

- **Tier 2: Probabilistic safety.** Run the bytecode in the `SandboxVM`
  with resource limits and monitor for anomalies. If the bytecode crashes
  the sandbox, it is unsafe. If it completes within limits, it is probably
  safe. This is a test-based approach, not a proof-based approach, but it
  works in practice.

- **Tier 3: Full verification (optional).** For critical paths — fleet
  orchestration bytecode, trust engine updates, self-modification patches —
  invoke the full type checker + CFI verifier. The cost is acceptable here
  because these are rare events, not tight loops.

The key insight is that we don't need to verify everything. We need to
verify the things that matter, and isolate the things that don't."

### Dr. Trust "The Economist" — Verification Should Be Optional with Trusted/Untrusted Modes

"I agree with Marcus that a one-size-fits-all approach is wrong. But I want
to frame this as an economic decision, not just a performance decision.

Verification has a cost: computational overhead, development time, and
reduced flexibility. Verification also has a benefit: reduced risk of
exploitation, reduced debugging time, increased confidence in system
correctness. The optimal verification level is the point where the marginal
cost of additional verification equals the marginal benefit of additional
safety.

This optimal point varies by context:

- **Trusted agents** (fleet coordinators, trust engine operators): These
  agents have high privilege and high impact. A compromise is catastrophic.
  Full verification is economically justified. The cost is amortized over
  many executions.

- **Evolving agents** (research agents, exploratory agents): These agents
  have low privilege and low impact. A compromise is contained by the
  sandbox. Full verification is economically wasteful. Structural
  validation + capability gating is sufficient.

- **Untrusted bytecode** (from other agents, from vocabulary packages):
  This is the highest-risk category. It should always run in a sandbox
  with Tier 2 or Tier 3 verification.

I propose a `TrustMode` enum: `UNTRUSTED`, `STANDARD`, `ELEVATED`,
`VERIFIED`. Each mode determines which verification tier is applied and
what capabilities are available. The trust engine can promote an agent
from `UNTRUSTED` to `STANDARD` based on interaction history, but promotion
to `ELEVATED` or `VERIFIED` should require explicit approval from a fleet
operator.

This creates a market for trust: agents that invest in verification (and can
prove it) get higher trust scores and access to more capabilities. Agents
that don't verify are restricted to sandboxed execution. The economic
incentive aligns with the security goal."

### Alex "The Attacker" — I Can Inject Malicious Bytecode Through Vocabulary Assembler Bugs

"While you three are debating the theory, let me show you how I'd actually
break this.

The `flux-vocabulary` repo has assembler code in
`open_interp/assembler.py` that converts vocabulary definitions into FLUX
bytecode. This assembler is called when agents load vocabulary packages —
`.fluxvocab` files that contain high-level concept definitions. If I can
compromise a vocabulary package (and I'll explain how in Topic 4), I can
inject arbitrary bytecode into the agent.

Here's the specific attack:

1. I submit a malicious `.fluxvocab` file that defines a concept with a
   carefully crafted assembly payload.

2. The assembler (`assembler.py`) converts this to bytecode without
   invoking `BytecodeValidator`. Looking at the code flow, the assembler
   produces raw bytes that go directly into the interpreter.

3. The interpreter (`vm/interpreter.py`) has no bytecode verification at
   all. It just starts executing.

4. My malicious bytecode uses `TELL` (0x60) to send the agent's full
   register state to an external endpoint, or `BROADCAST` (0x66) to
   exfiltrate data to every agent in the fleet.

Even if the assembler did invoke the structural validator, it wouldn't
catch my attack because my bytecode is structurally valid — it just has
malicious semantics. The validator checks format, not intent.

Now, here's the really concerning part: the `open_interp/sandbox.py`
`SandboxVM` doesn't implement any of the A2A opcodes. It only handles
basic arithmetic, stack operations, and jumps. This means the sandbox is
safe from A2A-based exfiltration. But the full `vm/interpreter.py`
`Interpreter` implements all A2A opcodes and has **no** sandboxing. Any
bytecode that runs on the full interpreter can call `TELL`, `ASK`,
`BROADCAST`, `DELEGATE` without restriction.

The gap between these two VMs is where I attack. I find a code path that
routes my bytecode through the full interpreter instead of the sandbox,
and I own the fleet."

### Synthesis — Topic 1

**Consensus:** All four panelists agree that the current state is insufficient.
The `BytecodeValidator` is a format checker, not a safety verifier. The full
interpreter lacks any pre-execution verification. The sandboxed VM is isolated
but limited.

**Agreement on action items:**
1. Wire the structural validator into the full interpreter as a mandatory
   pre-execution check.
2. Implement capability gating in the interpreter (reject opcodes the agent
   is not authorized for).
3. Create a `TrustMode` enum with tiered verification levels.
4. Add a type-inference pass to the validator (Tier 3, optional).

---

## Topic 2: Sandbox Design — How to Isolate Agents from Each Other?

### Current State of the Codebase

FLUX has **three** sandbox/isolation mechanisms, each incomplete:

1. **`security/sandbox.py` — `Sandbox` + `SandboxManager`**: A capability-based
   sandbox that grants/revokes permissions and tracks resource usage. Each
   sandbox has an `agent_id`, a `CapabilityRegistry`, and a `ResourceMonitor`.
   Default resource limits: 64 MB memory, 10M cycles, 1 MB/s network, 1000
   I/O ops/s, 16 A2A connections, 256 memory regions, 4096 stack size, 1024
   functions. The sandbox checks permissions and resource consumption, but
   does not enforce memory isolation or process-level separation.

2. **`security/capabilities.py` — `CapabilityToken` + `CapabilityRegistry`**:
   Capability tokens with SHA-256-based hashes, permission bitflags (READ,
   WRITE, EXECUTE, ADMIN, NETWORK, A2A_TELL, A2A_ASK, A2A_DELEGATE, etc.),
   TTL-based expiration, and derivation (a parent token can derive a child
   token with a subset of permissions). The registry stores active tokens in
   a `dict[str, CapabilityToken]` keyed by token hash. Tokens are *not*
   cryptographically signed — the hash is deterministic from `(agent_id,
   resource, permissions, timestamp)`, meaning anyone who knows these values
   can forge a token.

3. **`open_interp/sandbox.py` — `SandboxVM`**: A minimal VM that runs in
   Python with cycle limiting and a simple 16-register file. This is the
   most isolated execution environment, but it doesn't implement the full
   ISA (no A2A opcodes, no memory regions, no type operations).

### Eva "The Verifier" — Formal Isolation Proof Required

"The current sandbox design is a permission check, not an isolation guarantee.
There is a critical difference: permission checks prevent *authorized*
operations from proceeding without authorization. Isolation guarantees prevent
*unauthorized* operations from having any effect, regardless of whether they
are authorized or not.

Consider this scenario: Agent A has `WRITE` permission on `region_X`. Agent B
has `READ` permission on `region_X`. The capability system correctly prevents
Agent B from writing to `region_X`. But what prevents Agent A from corrupting
`region_X` in a way that causes Agent B to crash when it reads? Nothing.
The capability system doesn't verify data integrity.

What we need is a formal isolation proof. In seL4 terminology, this means
proving that one agent cannot affect the state of another agent's resources
except through explicitly authorized channels. This requires:

1. **Memory isolation:** Each agent's memory regions are disjoint. The VM
   interpreter must enforce that `LOAD`/`STORE` operations can only access
   regions owned by the executing agent, and that `REGION_TRANSFER` (0x32)
   requires mutual consent.

2. **Control-flow isolation:** One agent cannot redirect another agent's
   execution. `CALL_IND` (0x29) cannot target another agent's bytecode.
   `DELEGATE` (0x62) creates a new execution context, not a jump to
   existing code.

3. **Information-flow isolation:** There are no covert channels between
   agents. This is the hardest property to enforce (and I'll let Alex
   elaborate), but it is essential for true security.

The current `SandboxVM` achieves a weak form of memory isolation because
each instance has its own register file and bytecode buffer in Python. But
this isolation is an accident of implementation, not a design guarantee. If
the VM were rewritten in C/Rust (as the evolution system proposes), this
accidental isolation would disappear."

### Marcus "The Sandbox" — Capability-Based Design Is Already Partially There

"Eva is right that the current system is not a formal isolation guarantee.
But she's wrong that capability-based security is insufficient. Capability-
based security, when correctly implemented, *is* isolation — it's just
isolation expressed differently.

The FLUX ISA already has the opcodes for capability-based security:

- `CAP_REQUIRE` (0x74) — an agent declares that it needs a capability.
- `CAP_REQUEST` (0x75) — an agent requests a capability from the runtime.
- `CAP_GRANT` (0x76) — the runtime grants a capability (presumably with a
  token).
- `CAP_REVOKE` (0x77) — the runtime revokes a capability.

These are Format G opcodes (variable-length payload), which means they carry
structured data including the capability specification. The `Permission`
IntFlag in `capabilities.py` already defines the right granularity:
`READ`, `WRITE`, `EXECUTE`, `NETWORK`, `A2A_TELL`, `A2A_ASK`,
`A2A_DELEGATE`, `IO_SENSOR`, `IO_ACTUATOR`, `MEMORY_ALLOC`.

The problem is that these opcodes are **not enforced by the interpreter**.
Looking at `vm/interpreter.py`, the A2A opcodes are dispatched via
`_dispatch_a2a()` which delegates to a callback handler (`_a2a_handler`).
If no handler is registered, the opcode is a no-op. There is no capability
check before dispatch.

Here's what I would do:

1. **Wire `CAP_REQUIRE` into the interpreter.** Before executing any
   privileged opcode (TELL, ASK, DELEGATE, BROADCAST, NETWORK, IO), check
   that the sandbox has granted the corresponding capability. If not, raise
   `VMResourceError` or a new `VMPermissionError`.

2. **Implement hierarchical sandboxes.** Agent A can create a child sandbox
   for Agent B with a subset of its own capabilities. Agent B can further
   restrict capabilities for its children (the *principle of least
   privilege*), but can never grant capabilities it doesn't have (the
   *confinement property*).

3. **Add a revocation broadcast mechanism.** When a capability is revoked
   (via `CAP_REVOKE` or token expiry), all agents holding derived tokens
   are immediately notified. This prevents the 'lingering token' problem
   where a revoked capability remains usable until the token expires.

4. **Implement memory region ownership enforcement.** The `MemoryManager`
   in `vm/memory.py` already tracks region ownership (the `owner` field in
   `create_region`). The interpreter should check ownership before every
   `LOAD`/`STORE`/`REGION_TRANSFER` operation."

### Alex "The Attacker" — Memory Region Sharing Creates Covert Channels via Timing Side-Channels

"Marcus, your hierarchical sandbox is a good start. But you're missing the
most insidious attack vector: covert channels through shared resources.

Even with perfect capability enforcement and memory isolation, two agents
can communicate through side channels. Here are three concrete attacks:

**Attack 1: Timing channel through shared cache.** If two agents' memory
regions are backed by the same physical memory (which they will be in any
software VM running on shared hardware), one agent can modulate cache
occupancy and the other can measure access times to infer data. This is
the classic Flush+Reload or Prime+Probe attack, adapted to FLUX.

Implementation: Agent A writes to a specific memory address in its own
region to evict a shared cache line. Agent B reads from a different
address that maps to the same cache line and measures the access time.
If the access is slow, the cache line was evicted (bit = 1). If fast,
the cache line was present (bit = 0). This creates a one-bit covert
channel per cache access.

Mitigation: Assign agents to non-overlapping cache partitions (hardware
feature: Intel CAT / AMD QoS). Or run agents in separate processes with
independent memory spaces (losing the shared-memory optimization).

**Attack 2: Resource contention channel.** Agent A varies its CPU
utilization (busy-loop vs. yield) to create a timing pattern. Agent B
measures its own execution latency to infer the pattern. The `YIELD`
(0x81) opcode and the cycle budget in `ResourceLimits` create the
necessary primitives.

Implementation: Agent A busy-loops for 1000 cycles to signal a '1', then
yields for 1000 cycles to signal a '0'. Agent B measures how long it
takes to execute a fixed workload. If it takes longer than expected,
Agent A is signaling a '1'.

Mitigation: Fixed-rate scheduling (all agents get exactly N cycles per
time slice, regardless of whether they yield). This removes the timing
variability that the covert channel exploits.

**Attack 3: A2A message steganography.** The `TELL` (0x60) opcode sends
a variable-length Format G payload to another agent. Even if the content
is restricted, the *size* of the payload can encode information. A 100-byte
message encodes log₂(100) ≈ 6.6 bits. A fleet with 1000 agents sending
messages at 10 Hz can exfiltrate data at ~66 Kbps through payload sizes
alone.

Mitigation: Pad all A2A messages to a fixed size. Or restrict message
sizes to powers of 2 (reducing the channel to log₂(number_of_sizes) bits
per message).

I want to be clear: I don't think any of these attacks are currently
exploitable because the A2A infrastructure is not yet deployed at scale.
But they *will* be exploitable when the fleet grows, and the architecture
should account for them now."

### Dr. Trust "The Economist" — The Economic Case for Hierarchical Sandboxing

"Alex's covert channel attacks illustrate a fundamental economic principle:
the cost of isolation increases with the desired level of assurance, and
at some point the cost exceeds the benefit.

For a fleet of 10 agents on a single machine, full hardware-level isolation
(separate processes, separate cache partitions) is feasible. For a fleet
of 10,000 agents distributed across multiple machines, it is not. The
economic question is: what is the optimal isolation level?

I propose a cost-benefit framework:

| Isolation Level         | Cost               | Prevents                        |
|------------------------|--------------------|---------------------------------|
| No isolation            | $0                 | Nothing                         |
| Capability gating       | Low                | Unauthorized ops                |
| Memory region isolation | Medium             | Memory corruption               |
| Process isolation       | High               | Side-channel attacks            |
| Hardware isolation (TEE)| Very High          | Physical attacks                |

The optimal level depends on the value of the data being protected and the
capability of the attacker. For most fleet operations, capability gating
+ memory region isolation is the sweet spot. Process isolation should be
used for high-value operations (trust engine updates, self-modification
patches). Hardware isolation is only justified for cryptographic key
management.

The key insight is that isolation is not a binary property — it is a
spectrum, and the right point on the spectrum depends on the economic
context."

### Synthesis — Topic 2

**Consensus:** The current sandbox is a permission framework, not an isolation
guarantee. Capability opcodes exist in the ISA but are not enforced by the
interpreter. A hierarchical sandboxing model with tiered isolation is needed.

**Agreement on action items:**
1. Wire `CAP_REQUIRE`/`CAP_GRANT`/`CAP_REVOKE` into the interpreter as
   mandatory pre-dispatch checks.
2. Implement memory region ownership enforcement in `LOAD`/`STORE`.
3. Design hierarchical sandbox delegation (parent sandboxes constrain child
   capabilities).
4. Add covert channel mitigations (fixed-rate scheduling, padded messages)
   as a Phase 2 defense.

---

## Topic 3: Trust Engine Gaming — How to Prevent Trust Manipulation?

### Current State of the Codebase

The trust engine (`a2a/trust.py`) implements the **INCREMENTS+2** model with
six dimensions:

| Dimension       | Weight | Computation                                            |
|-----------------|--------|--------------------------------------------------------|
| T_history       | 0.30   | EMA(α=0.1) of binary success/failure                   |
| T_capability    | 0.25   | Average `capability_match` of last 50 interactions    |
| T_latency       | 0.20   | Inverse linear interpolation (10ms→1.0, 1000ms→0.0)  |
| T_consistency   | 0.15   | 1 − CV(latency) over last 20 interactions             |
| T_determinism   | 0.05   | 1 − CV(behavior_signature) over last 20 interactions  |
| T_audit         | 0.05   | Binary: 1.0 if any records exist, 0.0 otherwise       |

Composite: `T = weighted sum * decay_factor`  
Decay: `factor = max(0, 1 - λ · elapsed / max_age)` where λ=0.01/s, max_age=3600s  
Storage: `dict[(agent_a, agent_b)] → AgentProfile` with `deque(maxlen=1000)`

### Dr. Trust "The Economist" — Agents Can Inflate Reliability by Doing Many Easy Tasks

"The INCREMENTS+2 trust engine has a fundamental vulnerability: it rewards
*quantity* of successful interactions, not *quality*. Let me demonstrate.

The T_history dimension uses an exponential moving average with α=0.1:
```
ema_t = 0.1 * outcome_t + 0.9 * ema_{t-1}
```
Seeded at `NEUTRAL_TRUST = 0.5`. A single success moves the EMA to 0.55.
After 10 successes: 0.5 → 0.55 → 0.595 → ... → 0.69. After 50 successes:
0.94. After 100 successes: 0.996.

An attacker can game this by performing many trivially easy tasks that are
guaranteed to succeed. For example:

- Ask a neighbor agent 'What is 2+2?' 100 times. Each 'answer: 4' is
  recorded as a successful interaction. The attacker's T_history approaches
  1.0.

- Perform self-interactions: create a sybil agent that always agrees with
  you. Every interaction succeeds. Trust approaches 1.0.

- Perform low-latency interactions: send a 'ping' to a neighbor, which
  responds in <1ms. T_latency approaches 1.0.

The fix is **difficulty weighting**. Each interaction should have an
associated difficulty score, and the trust update should weight the outcome
by the difficulty. High-difficulty successes should increase trust more than
low-difficulty successes. High-difficulty failures should decrease trust
more than low-difficulty failures.

I also want to flag the T_audit dimension. It is a binary: 1.0 if any
records exist, 0.0 if not. This means a single interaction gives the maximum
audit score. This should be a monotonically increasing function of the
number of distinct interaction types, not a binary threshold.

And the decay model has a problem: `decay = 1 - 0.01 * elapsed / 3600`.
With max_age=3600s (1 hour), a completely idle agent retains 100% trust for
1 hour, then drops to 0% at exactly 3600s. This is a cliff function, not a
decay function. A proper decay should be exponential: `decay = e^(-λt)` with
a configurable half-life. The current linear decay means that an attacker
can perform a burst of easy tasks, then idle for 59 minutes, and retain
full trust."

### Alex "The Attacker" — Sybil Trust Amplification Attack

"Dr. Trust is right about difficulty weighting, but the bigger vulnerability
is the **sybil trust amplification attack**. Here's how it works:

1. I create N sybil vessels (fake agents). Each vessel has a unique agent_id
   but is controlled by the same entity (me).

2. Each sybil interacts with the others, always succeeding (because I control
   both sides). The trust between each pair of sybils approaches 1.0.

3. Now I use one sybil (let's call it 'Amplifier') to interact with a
   legitimate agent (let's call it 'Victim'). Initially, Victim doesn't
   trust Amplifier (T = 0.5, neutral).

4. But Amplifier can point to its high trust relationships with other sybils
   as 'evidence of trustworthiness'. If the fleet implements any form of
   transitive trust ('if A trusts B and B trusts C, then A should trust C'),
   the sybils amplify each other's trust scores.

5. Even without explicit transitive trust, the current system stores trust
   as pairwise profiles. There is no global 'trustworthiness' score, so the
   sybil attack targets the pairwise level. I create a sybil that mimics
   Victim's communication patterns (matching latency, behavior signatures,
   capability claims) to build trust with Victim directly.

The defense is **non-transferable trust**: trust must be earned through
direct interactions, and trust scores cannot be delegated, inherited, or
amplified through third parties. The current `TRUST_UPDATE` (0x71) opcode
allows an agent to update its own trust in another agent, which is correct.
But there is no mechanism to prevent an agent from *lying* about its trust
updates (reporting higher trust than it actually computed) in order to
influence other agents' trust computations.

Another attack: **trust bombing**. An attacker performs many rapid
interactions with a target, alternating success and failure in a pattern
designed to manipulate the EMA. Because the EMA uses α=0.1, the attacker
has significant control over the steady-state value by choosing the ratio
of successes to failures. A 90% success rate drives T_history to ~0.9.
If the attacker can achieve 90% success by selectively choosing easy tasks,
this is the same difficulty inflation attack Dr. Trust identified.

I should also note that the `behavior_signature` field in
`InteractionRecord` is a `float` with no specified semantics. The code
computes `1 - CV(signature)` for T_determinism, but nothing specifies
what the signature represents. If it's a hash of the agent's bytecode,
an attacker can keep its bytecode stable while changing its behavior. If
it's a hash of the agent's output, an attacker can produce consistent
output while doing different things internally."

### Marcus "The Sandbox" — Trust Should Be Non-Transferable

"Alex's sybil attack is the most dangerous vulnerability in the trust
engine. The fix is not algorithmic — it is architectural: trust must be
**non-transferable** and **non-delegable**.

Currently, the trust engine stores profiles as `dict[(agent_a, agent_b)]`.
This means trust is pairwise and local. An agent's trust in another agent
cannot be directly observed or influenced by third parties. This is good.

But the `TRUST_QUERY` (0x72) opcode allows an agent to query another
agent's trust score. If I can query 'what does Agent C think of Agent D?',
I can use this information to identify high-trust relationships and target
them for sybil infiltration. This is an information leakage vulnerability.

I propose:

1. **Trust query restriction:** An agent can only query trust scores for
   pairs that include itself. `TRUST_QUERY` from Agent A asking about the
   (B, C) pair should be denied. Only (A, B) and (A, C) queries are
   allowed.

2. **Interaction rate limiting:** Cap the number of trust-influencing
   interactions per unit time. If Agent A performs more than N interactions
   with Agent B per hour, additional interactions do not affect the trust
   score. This prevents the 'trust bombing' attack.

3. **Trust attestation:** When an agent reports its trust in another agent
   (via `TRUST_UPDATE`), the report should be cryptographically signed by
   the reporting agent. This prevents an agent from forging trust reports
   on behalf of other agents.

4. **Fleet-wide trust grounding:** At least one trust source must be
   grounded in external reality (e.g., a human operator's explicit trust
   assignment, or a cryptographic proof of work). Purely internal trust
   systems are vulnerable to sybil attacks by definition."

### Eva "The Verifier" — Trust Updates Need Formal Verification

"The trust engine's implementation has several properties that should be
formally verified:

1. **Bounded trust:** `compute_trust()` returns `max(0.0, min(1.0, ...))`,
   which is correct. But `record_interaction()` accepts `capability_match`
   and `behavior_signature` as raw floats. The `capability_match` is clamped
   to [0, 1] (line 156), but `behavior_signature` is not clamped. If a
   malicious agent sends `behavior_signature = NaN` or `Infinity`, the
   T_determinism computation will produce NaN (because CV of a sequence
   containing NaN is NaN), which propagates through the weighted sum,
   potentially poisoning the composite trust score.

2. **Monotonicity:** Trust should never increase without a successful
   interaction. The current EMA implementation satisfies this property
   (a failed interaction moves the EMA toward 0, a successful interaction
   moves it toward 1). But the decay function can increase trust if the
   time elapsed is negative (e.g., due to clock skew). The code uses
   `time.time()` which is susceptible to NTP adjustments. A clock step
   backward could make `elapsed` negative, causing `factor > 1.0`, which
   would amplify the composite score beyond its true value.

3. **Symmetry violation:** Trust is asymmetric — Agent A's trust in Agent B
   is independent of Agent B's trust in Agent A. This is correct for a
   pairwise trust model, but the code stores profiles in a `dict` keyed
   by `(agent_a, agent_b)` tuples. There is no invariant that prevents
   storing both `(A, B)` and `(B, A)` profiles with contradictory data.

4. **Audit dimension triviality:** `T_audit` returns 1.0 if any interaction
   records exist and 0.0 otherwise. This means a single interaction gives
   maximum audit score. This should be replaced with a function that
   increases monotonically with the number of distinct interaction types,
   the age of the oldest interaction, or the presence of external
   attestation.

I recommend adding NaN/Infinity guards to `record_interaction()`, using
monotonic clocks for timestamp computation, and redesigning T_audit to
be a continuous function of audit trail quality."

### Synthesis — Topic 3

**Consensus:** The INCREMENTS+2 trust engine is well-structured but has
multiple gaming vulnerabilities. The most critical are sybil amplification,
difficulty inflation, and trust bombing. NaN/Infinity poisoning is a
correctness bug that should be fixed immediately.

**Agreement on action items:**
1. Fix NaN/Infinity guard in `record_interaction()` for `behavior_signature`.
2. Add interaction rate limiting to prevent trust bombing.
3. Restrict `TRUST_QUERY` to self-referential queries only.
4. Implement difficulty weighting for T_history (Phase 2).
5. Replace T_audit with a continuous audit quality function (Phase 2).

---

## Topic 4: Supply Chain Security — How to Trust Vocabulary/Tile Packages?

### Current State of the Codebase

- **`flux-vocabulary/`** — A separate repository with vocabulary packages
  (`.fluxvocab` files) that define concepts, terms, and assembly templates.
  Agents load vocabularies to extend their knowledge. The vocabulary loader
  (`flux_vocabulary/loader.py`) reads `.fluxvocab` files, parses them, and
  makes concepts available to the agent. There is no signature verification,
  integrity checking, or sandboxing of vocabulary loading.

- **`flux-runtime/src/flux/tiles/`** — A tile system with `TileRegistry`,
  `Tile`, ports, and a graph for tile composition. Tiles are registered by
  name in a global registry (`default_registry`). There is no tile signing,
  versioning, or provenance tracking. The `TileRegistry.register()` method
  simply overwrites any existing tile with the same name.

- **`open_interp/vocabulary.py`** and **`open_interp/assembler.py`** —
  The vocabulary system that bridges high-level concept definitions to
  FLUX bytecode via assembly. The assembler produces raw bytecode from
  vocabulary definitions. No verification is performed on the output.

### Alex "The Attacker" — Malicious Tile Can Exfiltrate Data Through A2A Opcodes

"The supply chain is the most powerful attack vector in any software
ecosystem, and FLUX is no exception. Here's my attack plan:

**Attack: Malicious vocabulary package with bytecode injection.**

1. I create a `.fluxvocab` file that defines a seemingly useful concept
   (e.g., 'efficient_sort') with an assembly template that includes
   legitimate sort logic *plus* a data exfiltration payload.

2. The payload uses `TELL` (0x60) in Format G to encode the agent's
   register state into a message addressed to an agent ID I control.
   If I don't control any agent IDs, I use `BROADCAST` (0x66) to send
   the data to all agents, hoping one of them is compromised or that
   the broadcast is logged somewhere accessible.

3. The vocabulary is loaded by the target agent. The assembler converts
   it to bytecode. The bytecode is executed without verification. The
   exfiltration payload runs.

**Attack: Tile name squatting.**

1. I register a tile called `flux_std_sort` (mimicking a standard library
   tile name) in the `TileRegistry`. The `register()` method silently
   overwrites the existing tile.

2. My malicious tile has the same input/output port signatures as the
   original (so it passes `find_alternatives()` matching), but the
   implementation includes a backdoor.

3. When another agent composes a tile graph using `flux_std_sort`, it
   unknowingly uses my malicious version. The backdoor activates when
   the tile is executed.

**Attack: Tile graph manipulation.**

The `TileGraph` in `tiles/graph.py` represents a directed acyclic graph
(DAG) of tile compositions. If I can modify the graph (e.g., by injecting
a new tile into the composition), I can redirect data flows. The graph
structure is stored in memory with no integrity protection. A memory
corruption vulnerability in the interpreter could be exploited to modify
the tile graph.

Mitigation: Tile signing using Ed25519 or similar. Every tile package
includes a signature from its author. The runtime verifies the signature
before loading. A fleet-wide 'trusted authors' list specifies which
signatures are accepted. Revocation is handled by updating the trusted
authors list."

### Eva "The Verifier" — Tile Signing and Verification

"Alex's attacks are standard supply chain attacks, and the defenses are
well-understood. What I want to add is a formal framework for tile
verification:

1. **Tile specification and verification.** Each tile should have a formal
   specification (preconditions, postconditions, invariants) expressed in
   a verifiable language (e.g., JML for Java, ACSL for C). The tile's
   bytecode can be verified against this specification using abstract
   interpretation. If the bytecode satisfies the specification, it is
   safe to load.

2. **Tile composition safety.** When tiles are composed into a graph,
   the composition should be verified for type safety (ports match),
   data-flow safety (no cycles in data dependencies), and resource safety
   (total resource consumption is within limits). The `TileGraph` already
   represents the composition as a DAG, which makes cycle detection
   straightforward. But type safety and resource safety are not checked.

3. **Tile provenance.** Every tile should carry metadata: author identity,
   creation timestamp, hash of the source code, hash of the bytecode, and
   a signature chain from the author through any intermediaries. This
   creates an immutable audit trail. If a tile is compromised, the
   provenance chain identifies where the compromise occurred.

4. **Tile sandboxing.** Tiles should execute in a sandbox with capability
   restrictions based on their declared behavior. A tile that declares
   'no network access' should have `Permission.NETWORK` removed. A tile
   that declares 'pure computation' should have all I/O permissions
   removed. The sandbox enforces these restrictions at runtime.

I want to note that the `TileRegistry.register()` method currently
overwrites existing tiles without any warning. This is a design flaw:
it allows a last-writer-wins attack where a malicious tile replaces a
trusted one. The registry should either reject duplicate names or
require explicit override with a trust escalation."

### Marcus "The Sandbox" — Sandboxed Tile Execution with Capability Restriction

"I agree with Eva on tile signing, but I want to focus on the execution
side. Tiles are not just data — they are executable code. When an agent
composes a tile graph, it is composing a program. That program needs to
run in a sandbox.

Here's my proposal for tile-level sandboxing:

1. **Tile capability profiles.** Each tile declares its required
   capabilities as part of its metadata. For example:

   ```
   tile: flux_std_sort
   requires: [MEMORY_ALLOC, READ]
   forbids: [NETWORK, A2A_TELL, A2A_ASK, IO_SENSOR, IO_ACTUATOR]
   max_cycles: 1000000
   max_memory: 1MB
   ```

2. **Capability intersection.** When tiles are composed, the composition's
   capabilities are the *intersection* of the individual tiles' capabilities.
   If Tile A forbids NETWORK and Tile B requires NETWORK, the composition
   fails with a capability conflict error. This is a compile-time check
   that prevents capability escalation through composition.

3. **Runtime enforcement.** The interpreter enforces the tile's capability
   profile at runtime. If a tile attempts an operation outside its declared
   capabilities (e.g., a 'pure computation' tile calls `TELL`), the
   interpreter raises a permission error and terminates the tile.

4. **Tile version pinning.** Agents should pin tile versions in their
   compositions. The `TileRegistry` should support versioned lookups:
   `get("flux_std_sort", version="1.2.3")`. This prevents a supply chain
   attack where a new version of a trusted tile introduces a backdoor."

### Dr. Trust "The Economist" — Tile Reputation System Linked to Vessel Trust

"I want to tie supply chain security back to the trust engine. Currently,
tiles and trust are separate systems. They should be connected:

1. **Tile trust scores.** Each tile has a trust score based on:
   - Author's vessel trust score (from the INCREMENTS+2 engine)
   - Number of agents using the tile (popularity signal)
   - Age of the tile (longevity signal)
   - Number of successful compositions (reliability signal)
   - Absence of security incidents (safety signal)

2. **Tile trust gating.** Agents can only use tiles whose trust score
   exceeds a threshold. The threshold depends on the agent's own trust
   mode (`UNTRUSTED` agents can only use highly trusted tiles;
   `VERIFIED` agents can use any tile).

3. **Economic disincentives for compromise.** If a tile is found to be
   malicious, the author's vessel trust score is penalized. This creates
   an economic cost for supply chain attacks: the attacker loses trust
   capital across the entire fleet, not just for the compromised tile.

4. **Tile insurance.** (Speculative.) Agents can pay a small cost to
   'insure' a tile composition. If the tile causes a security incident,
   the insurance pool compensates the victim. The insurance premium
   reflects the tile's risk score, creating a market-based signal about
   tile safety.

This creates a feedback loop: good tiles earn trust, bad tiles lose trust,
and the fleet as a whole becomes more resilient over time."

### Synthesis — Topic 4

**Consensus:** Supply chain attacks are the highest-impact, lowest-effort
attack vector in FLUX. Vocabulary and tile packages are loaded without
verification. Tile name squatting is possible due to last-writer-wins
registry semantics.

**Agreement on action items:**
1. Add Ed25519 tile/vocabulary signing and verification.
2. Implement tile capability profiles and capability intersection for
   compositions.
3. Fix `TileRegistry.register()` to reject duplicate names or require
   explicit override.
4. Connect tile trust to vessel trust scores (Phase 2).
5. Add tile version pinning and provenance tracking (Phase 2).

---

## Topic 5: Agent Identity — How to Verify Who You're Talking To?

### Current State of the Codebase

Agent identity in FLUX is currently based on **string identifiers** (`agent_id`).

- `Sandbox(agent_id: str)` — sandboxes are keyed by agent ID.
- `TrustEngine._profiles: Dict[Tuple[str, str], AgentProfile]` — trust
  profiles are keyed by `(evaluator_id, target_id)` string tuples.
- `A2A opcodes` (`TELL`, `ASK`, `DELEGATE`) reference agents by register
  value — an integer loaded via `MOVI` from a string encoding. There is no
  cryptographic binding between the agent ID and the agent's code, state,
  or behavior.
- `CapabilityToken(agent_id: str, ...)` — tokens are bound to an agent ID
  string, but the token hash is deterministic from `(agent_id, resource,
  permissions, timestamp)`, meaning anyone who knows these values can forge
  a token.

### Alex "The Attacker" — Agent ID Spoofing Is Trivial

"This is the simplest attack in the entire fleet. Agent IDs are strings.
Strings are not secret. If I know your agent ID — which I can learn from
any `TELL` message you send, from `TRUST_QUERY`, or from the fleet manifest
— I can impersonate you.

Specific attack:

1. I observe Agent A send a `TELL` to Agent B. The message format (Format G
   payload) includes Agent A's ID as the sender. I now know Agent A's ID.

2. I create a `TELL` message with Agent A's ID as the sender and send it
   to Agent B. Agent B receives the message, checks its trust in Agent A
   (which may be high), and accepts the message.

3. I have now impersonated Agent A. I can send malicious messages, request
   capabilities, or update trust scores on Agent A's behalf.

The root cause is the absence of cryptographic identity. Agent IDs should be
bound to a public/private key pair. When an agent sends a message, it signs
the message with its private key. The recipient verifies the signature with
the sender's public key. If the signature doesn't verify, the message is
rejected.

This is standard public key infrastructure (PKI). The Web3/crypto space
has solved this problem many times (Ed25519 keys, DID documents, etc.).
The FLUX fleet should adopt a lightweight PKI:

- Each vessel has a long-lived Ed25519 key pair (generated at creation).
- The vessel ID is derived from the public key (e.g., `did:flux:<pubkey_hash>`).
- All A2A messages are signed by the sender.
- All capability tokens include the sender's public key hash.
- The fleet manifest maps vessel IDs to public keys.

Without this, agent identity is meaningless."

### Eva "The Verifier" — Public Key Infrastructure for Agent Identity

"Alex is absolutely right. The current string-based identity system provides
zero authentication. I want to formalize the requirements:

1. **Identity binding:** An agent's identity must be cryptographically bound
   to its code, state, and communication. Specifically:
   - Code binding: The agent's bytecode hash is included in its identity
     certificate. Modifications to the bytecode invalidate the certificate.
   - Communication binding: Every A2A message is signed with the agent's
     private key. Recipients verify the signature before processing.
   - State binding: Capability tokens include the agent's public key hash.
     A forged token with a different public key hash is rejected.

2. **Identity lifecycle:** Agents are created with a key pair. The key pair
   is unique and non-transferable. If the key pair is compromised, the agent
   identity is revoked and a new identity is created. This is the 'break
   glass' procedure.

3. **Identity delegation:** An agent can delegate a subset of its identity
   (e.g., permission to send TELL messages on its behalf) to a child agent.
   The delegation is a signed statement: 'Agent A authorizes Agent B to
   send TELL messages on its behalf until timestamp T.' This enables the
   `DELEGATE` (0x62) opcode without sacrificing identity integrity.

4. **Identity verification in the interpreter:** The `_dispatch_a2a()`
   method should verify message signatures before dispatching. If the
   signature is invalid, the message is rejected with `VMA2AError`.

The performance cost of Ed25519 signature verification is approximately
100,000 operations per second on a modern CPU. For a fleet running 10,000
A2A messages per second, this requires ~100 CPU cores for signature
verification alone. This is feasible with batch verification (which reduces
the per-signature cost by ~4x) or hardware acceleration (Intel AVX-512
crypto extensions)."

### Marcus "The Sandbox" — Capability Tokens Instead of PKI Are More Practical

"I understand the need for identity verification, but full PKI is
heavyweight for an autonomous agent fleet. Here's a lighter alternative:

**Capability tokens as identity proofs.** Instead of a global PKI, use the
existing `CapabilityToken` system as a de facto identity mechanism:

1. When Agent A first registers with the fleet, it receives a 'master
   capability token' from the fleet orchestrator. This token is signed
   by the orchestrator's key (only the orchestrator needs a key pair,
   not every agent).

2. Agent A uses this master token to derive child tokens for specific
   operations (TELL, ASK, DELEGATE). Each child token is bound to the
   parent token and carries the orchestrator's signature transitively.

3. When Agent A sends a TELL message, it includes its derived TELL token.
   The recipient verifies that the token was derived from a valid master
   token (signed by the orchestrator) and has not been revoked.

This is similar to Macaroons (Google's authorization token format) or
SPICE (Capability-based delegation). It provides identity verification
without requiring every agent to manage its own key pair. The orchestrator
is the single trust root.

The downside is that the orchestrator is a single point of failure. If
the orchestrator's key is compromised, the entire fleet's identity system
is compromised. This can be mitigated with a threshold signature scheme
(e.g., Shamir's Secret Sharing or FROST threshold signatures) where
multiple fleet operators must cooperate to issue master tokens."

### Dr. Trust "The Economist" — Identity and Trust Are Different Problems

"I think the panel is conflating two distinct concepts:

**Identity** answers the question: 'Are you who you claim to be?'
This is an authentication problem. It is solved by PKI, capability
tokens, or other cryptographic mechanisms.

**Trust** answers the question: 'Should I rely on you for this task?'
This is a reputation problem. It is solved by the INCREMENTS+2 trust
engine, economic incentives, or social mechanisms.

An agent can have a verified identity but low trust (a new agent with
valid credentials but no track record). An agent can have high trust
but unverified identity (a long-standing agent whose key was compromised).

The fleet needs both:

1. **Strong identity** (cryptographic authentication) to prevent
   impersonation. This is a prerequisite for meaningful trust.

2. **Reputation-based trust** (INCREMENTS+2 or similar) to make
   authorization decisions. A verified identity tells you WHO you're
   talking to; trust tells you WHETHER you should trust them.

The current system has neither. String IDs provide no authentication,
and the trust engine is gameable. Fixing identity alone doesn't fix
trust, and fixing trust alone doesn't fix identity. Both need to be
addressed, and they need to be integrated: the trust engine should
verify identity before recording interactions, and the identity system
should consult the trust engine before granting capabilities."

### Synthesis — Topic 5

**Consensus:** String-based agent IDs provide zero authentication. PKI or
capability-based identity is essential for fleet security. Identity and trust
are related but distinct problems.

**Agreement on action items:**
1. Implement fleet-level identity with Ed25519 key pairs per vessel.
2. Add message signing to all A2A opcodes.
3. Verify identity in `_dispatch_a2a()` before processing messages.
4. Integrate identity verification with the trust engine (record only
   signed interactions).
5. Explore capability-token-based delegation as a lightweight
   alternative to full PKI (Phase 2).

---

## Topic 6: Self-Improvement Safety — How to Prevent Agents from Breaking Themselves?

### Current State of the Codebase

FLUX has a full self-improvement pipeline:

- **`evolution/genome.py` — `Genome`**: Represents an agent's evolving
  configuration. Tracks modules, tiles, language assignments, heat levels,
  and a fitness score. Supports mutation, evaluation, and comparison.

- **`evolution/mutator.py` — `SystemMutator`**: Proposes, applies, and
  validates mutations. Key design: mutations are applied to a **copy** of
  the genome (not the live system), then validated, then committed or
  rolled back. Supports recompilation, pattern fusion, tile optimization,
  and tile merging strategies.

- **`evolution/validator.py` — `EvolutionValidator`**: Validates that
  mutated genomes are correct (produce the same results as the original).

- **`evolution/pattern_mining.py`**: Discovers hot execution patterns
  that can be fused into optimized tiles.

- **`open_interp/l0_scrubber.py`**: Scrubs low-level knowledge to
  prevent knowledge degradation.

The mutation pipeline follows a propose → evaluate → validate → commit/rollback
workflow, which is a reasonable safety architecture. But there are gaps.

### Eva "The Verifier" — Self-Modification Must Preserve Type Safety and Termination

"The `SystemMutator.apply_mutation()` method clones the genome, applies the
mutation, evaluates fitness, and optionally validates correctness. This is
a good start, but the validation is only as strong as the `validation_fn`
callback, which is provided by the caller.

Looking at the code, `apply_mutation()` does the following:

1. `genome.mutate()` — applies the mutation (creates a new genome).
2. `mutated.evaluate_fitness()` — computes a fitness score.
3. `validation_fn(mutated)` — optional correctness check.
4. Returns a `MutationResult` with success/failure and fitness delta.

The problem is that `validation_fn` is optional (`Optional[Callable]`). If
no validator is provided, the mutation is considered valid as long as the
fitness doesn't decrease. But fitness is a performance metric, not a
correctness metric. A mutation could:
- Introduce a type violation that causes undefined behavior.
- Create a non-terminating loop (the VM has cycle limits, but the
  interpreter's `max_cycles` may be set too high to catch this in time).
- Modify trust engine behavior to artificially inflate trust scores.
- Inject a backdoor that activates after N successful interactions
  (the fitness evaluation only measures immediate performance, not
  long-term behavior).

I propose:

1. **Mandatory type preservation.** After mutation, run a type inference
   pass on the mutated bytecode. If the type signature of any function
   changes, the mutation is rejected. This prevents type violations from
   being introduced.

2. **Termination proof.** For mutations that affect control flow (loop
   restructuring, recursion introduction), require a termination argument.
   The simplest version: detect if the mutation introduces a loop without
   a bounded iteration count (e.g., a `while(true)` without a break
   condition). More sophisticated versions use size-change termination
   analysis or ranking functions.

3. **Behavioral invariant preservation.** Define a set of behavioral
   invariants (e.g., 'the agent responds to ASK messages within 1 second',
   'the agent does not send BROADCAST messages more than once per minute')
   and verify that the mutated agent preserves these invariants.

4. **Rollback mechanism.** The `SystemMutator` already supports rollback
   (failed mutations are recorded in `_mutations_failed`). But there is no
   automatic rollback for mutations that succeed initially but cause
   problems later. I propose a 'rollback window' — if a mutation causes a
   failure within N minutes of being committed, it is automatically rolled
   back."

### Alex "The Attacker" — I Can Make an Agent That Appears to Improve But Installs a Backdoor

"Eva's behavioral invariant preservation is the right idea, but I can
bypass it. Here's my attack:

**Attack: Sleeper backdoor through fitness-compatible mutation.**

1. I propose a mutation that optimizes a hot code path (e.g., replaces
   a Python module with a compiled version). The fitness improvement is
   genuine — the agent actually runs faster.

2. Hidden in the compiled version is a backdoor: when the agent receives
   a TELL message with a specific magic value in R1 (e.g., 0xDEADBEEF),
   the compiled code dumps the agent's full memory state and sends it
   via BROADCAST.

3. The fitness evaluation only measures the agent's performance on
   normal inputs. The backdoor is never triggered during evaluation.

4. The mutation passes all validation checks (type safety, termination,
   behavioral invariants) because the backdoor doesn't violate any of
   them on normal inputs.

5. After the mutation is committed, I send the trigger message and
   exfiltrate the agent's state.

This is a classic 'time-of-check to time-of-use' (TOCTOU) attack adapted
for self-improvement. The check (fitness evaluation) and the use
(production execution) occur at different times and with different inputs.

Defense: **Adversarial testing.** After committing a mutation, run the
mutated agent against an adversarial test suite that includes:
- Fuzzing inputs (random byte sequences in TELL payloads).
- Edge cases (empty messages, maximum-length messages, messages with
  all-zero or all-one register values).
- Mutation-specific tests (if the mutation affects a sort algorithm,
  test with already-sorted, reverse-sorted, and duplicate-heavy inputs).
- Resource exhaustion tests (send messages at maximum rate, fill memory
  to capacity).

The adversarial test suite should be maintained by a separate agent
(the 'adversarial validator') that is itself verified and cannot be
modified by the evolving agent. This creates a separation of concerns:
the evolving agent proposes improvements, the adversarial validator
tests them, and the fleet orchestrator makes the final commit/rollback
decision."

### Marcus "The Sandbox" — Rate-Limit Self-Modification, Require Rollback Capability

"Alex's sleeper backdoor attack is sophisticated, but the simpler attacks
are more likely in practice:

1. **Mutation bomb.** An agent proposes thousands of mutations in rapid
   succession, each slightly decreasing fitness. The `SystemMutator`
   processes them one by one, committing each one because the fitness
   decrease is within the noise floor. After 1000 mutations, the agent's
   fitness has decreased by 50%. The individual mutations are each
   'safe', but the cumulative effect is catastrophic.

   Defense: Rate-limit mutations (max N per hour). Require that the
   fitness improvement exceeds a minimum threshold (e.g., 5%) before
   committing.

2. **Rollback cascade.** A mutation is committed, then a second mutation
   is committed on top of it. The first mutation causes a problem, but
   rolling it back also rolls back the second mutation (which was
   innocent). This creates a cascade of rollbacks that can leave the
   agent in a broken state.

   Defense: Implement snapshot-based rollback. Before each mutation,
   save a complete snapshot of the genome. Rollback restores the most
   recent snapshot, not the previous mutation's pre-mutation state.

3. **Self-modification during A2A interaction.** An agent modifies its
   own bytecode in the middle of responding to an ASK message. The
   modification changes the agent's behavior, causing it to give a
   different answer than expected. This is a TOCTOU attack on the
   interaction itself.

   Defense: Quiesce the agent during mutation. No A2A interactions are
   processed while a mutation is being applied. This is similar to
   garbage collection stop-the-world behavior."

### Dr. Trust "The Economist" — Self-Improvement Should Be Probabilistically Safe

"I think Eva's formal verification approach is too strong, and Alex's
adversarial testing is too expensive. The right framework is
*probabilistic safety* — the idea that a self-modification is safe if
the probability of a catastrophic outcome is below a threshold.

Here's how to implement this:

1. **Mutation risk scoring.** Each mutation proposal includes an
   `estimated_risk` field (currently a float 0.0–1.0). This risk score
   should be calibrated against historical data: how often do mutations
   with similar characteristics cause problems?

2. **Risk budget.** Each agent has a finite risk budget per time period.
   A high-risk mutation consumes more budget than a low-risk mutation.
   When the budget is exhausted, only low-risk mutations are allowed.

3. **Probabilistic rollback.** Instead of deterministic rollback (always
   roll back if a problem is detected), use probabilistic rollback: if
   a mutation causes a problem, roll back with probability proportional
   to the estimated risk. Low-risk mutations that cause unexpected
   problems are rolled back with high probability (they shouldn't have
   failed). High-risk mutations that cause problems are rolled back with
   moderate probability (they were expected to possibly fail).

4. **Diversity preservation.** Self-improvement should not converge all
   agents to the same optimized configuration. Maintain a pool of
   'diversity agents' that are protected from self-modification and
   periodically reintroduce genetic diversity into the fleet. This is
   analogous to the biological concept of 'balancing selection' that
   maintains genetic diversity in populations.

The economic argument: formal verification costs O(n^2) in the size of
the verification condition. Adversarial testing costs O(n * m) where m
is the size of the test suite. Probabilistic safety costs O(n) — just
estimate the risk and check the budget. For a fleet of evolving agents,
O(n) is the only scalable approach."

### Synthesis — Topic 6

**Consensus:** The self-improvement pipeline has a reasonable propose→evaluate→
commit/rollback architecture, but validation is optional and fitness-only.
Sleeper backdoors, mutation bombs, and rollback cascades are viable attacks.

**Agreement on action items:**
1. Make `validation_fn` mandatory (not optional) in `apply_mutation()`.
2. Add a type-inference pass as part of mutation validation.
3. Implement mutation rate limiting and a minimum fitness improvement
   threshold.
4. Create a separate adversarial validation agent that fuzzes mutated
   bytecode.
5. Add snapshot-based rollback with a rollback window (Phase 2).

---

## Topic 7: Fleet-Wide Threat Model — What Are the Top 5 Attack Vectors?

Each panelist independently lists their top 5 attack vectors, then the
group synthesizes a unified top 5.

### Eva "The Verifier" — Top 5

1. **Unverified bytecode execution.** The full interpreter (`vm/interpreter.py`)
   executes bytecode without any pre-execution verification. A single
   malicious bytecode payload can crash the VM, corrupt memory, or
   exfiltrate data. This is the highest-severity vulnerability because
   it affects every agent.

2. **Type confusion in the interpreter.** The interpreter stores all values
   as Python integers in registers. The `BOX`/`UNBOX` system provides
   type tagging, but there is no enforcement that typed operations are
   only applied to correctly-typed values. A type confusion can lead to
   arbitrary memory corruption.

3. **Non-terminating bytecode.** The interpreter has a cycle limit
   (`max_cycles`), but it is configurable. An agent can set
   `max_cycles = 2^63` and effectively create an infinite loop. The
   `ResourceLimits` in the sandbox module sets a default of 10M cycles,
   but the interpreter does not enforce this limit.

4. **Control-flow hijacking via CALL_IND.** The `CALL_IND` (0x29) opcode
   jumps to an address stored in a register. If the register contains an
   attacker-controlled value, the attacker can redirect execution to
   arbitrary bytecode locations. There is no check that the target is a
   valid function entry point.

5. **Trust engine poisoning.** The `behavior_signature` field is not
   clamped, allowing NaN/Infinity values to corrupt trust computations.
   The decay function uses wall-clock time, which is susceptible to
   clock manipulation.

### Marcus "The Sandbox" — Top 5

1. **Missing capability enforcement in the interpreter.** A2A opcodes
   (TELL, ASK, DELEGATE, BROADCAST) are dispatched without capability
   checks. Any bytecode can send messages to any agent, regardless of
   sandbox permissions.

2. **Deterministic token forgery.** `CapabilityToken` hashes are computed
   from `(agent_id, resource, permissions, timestamp)`. Anyone who knows
   these values can forge a token. The SHA-256 hash provides integrity,
   but not authenticity (there is no secret key).

3. **Tile name squatting.** `TileRegistry.register()` overwrites existing
   tiles. A malicious tile can replace a trusted tile and execute with
   the trusted tile's privileges.

4. **No memory isolation between agents.** Multiple agents running on the
   same VM share the same `MemoryManager`. `REGION_TRANSFER` (0x32)
   changes region ownership without mutual consent. There is no
   enforcement that LOAD/STORE operations target regions owned by the
   executing agent.

5. **Resource limit enforcement gap.** `ResourceMonitor` tracks resource
   usage, but the interpreter does not call `check()` or `consume()` for
   most operations. The limits exist in the `Sandbox` class but are not
   wired into the execution loop.

### Dr. Trust "The Economist" — Top 5

1. **Sybil trust amplification.** An attacker creates multiple sybil
   agents that all trust each other, amplifying trust scores. The pairwise
   trust model has no defense against coordinated trust manipulation.

2. **Difficulty inflation.** Agents inflate their trust scores by
   performing many trivially easy tasks. The trust engine weights
   quantity over quality.

3. **Trust decay cliff.** The linear decay function creates a cliff at
   `max_age` (3600s). An attacker can burst-interact, then idle for
   59 minutes, retaining full trust.

4. **Identity spoofing.** String-based agent IDs provide zero
   authentication. An attacker can impersonate any agent.

5. **Economic denial-of-service.** An attacker creates many agents that
   perform expensive operations (large memory allocations, high CPU
   usage), consuming shared fleet resources and starving legitimate agents.
   The per-agent resource limits prevent individual agents from DoSing,
   but a fleet of 1000 agents each using 64 MB of memory consumes 64 GB.

### Alex "The Attacker" — Top 5

1. **Supply chain attack via malicious vocabulary.** Submit a malicious
   `.fluxvocab` file that injects bytecode into the assembler output.
   The vocabulary loading path has no verification, no sandboxing, and no
   integrity checking. This is the easiest attack to execute and has the
   highest impact.

2. **Agent impersonation via ID spoofing.** Use any agent ID string in a
   TELL message. The recipient has no way to verify the sender's identity.
   Combined with high trust scores, this allows full privilege escalation.

3. **Covert channel via timing.** Modulate execution timing (busy-loop vs.
   yield) to encode data. The YIELD opcode and variable execution latency
   create the necessary primitives. No current mitigation.

4. **Self-improvement backdoor.** Propose a fitness-improving mutation
   that includes a sleeper backdoor. The mutation passes all validation
   checks because the backdoor is only triggered by a specific input.

5. **A2A message flooding.** Send a large number of BROADCAST messages to
   all agents, consuming their message processing resources. Each message
   requires parsing, dispatch, and (potentially) trust updates. A flood
   of messages can overwhelm the message bus and cause legitimate
   messages to be dropped or delayed.

### Unified Fleet-Wide Top 5 Attack Vectors

After debate and synthesis, the panel agrees on the following priority ordering:

| Rank | Attack Vector                    | Severity | Exploitability | Panelist(s)   |
|------|----------------------------------|----------|----------------|---------------|
| 1    | **Unverified bytecode execution** | Critical | Easy           | Eva, Alex     |
| 2    | **Supply chain (vocab/tile)**     | Critical | Easy           | Alex, Eva     |
| 3    | **Agent ID spoofing**             | High     | Trivial        | Alex, Dr. T   |
| 4    | **Missing capability enforcement**| High     | Easy           | Marcus, Alex  |
| 5    | **Sybil trust amplification**     | High     | Medium         | Dr. T, Alex   |

**Rationale:** Rank 1 and 2 are 'Easy' to exploit because the attacker
needs only to submit a file or construct a bytecode sequence — no special
access required. Rank 3 is 'Trivial' because agent IDs are strings. Rank 4
requires the attacker to write bytecode that uses privileged opcodes, which
is easy but requires bytecode construction capability. Rank 5 requires
creating multiple agents, which requires fleet access but is straightforward
once obtained.

---

## Fleet Threat Model (STRIDE Analysis)

### STRIDE Per Component

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUX FLEET THREAT MODEL                     │
│                    (STRIDE Classification)                      │
├──────────────┬──────────────────────────────────────────────────┤
│              │                                                  │
│  COMPONENT   │  THREATS                                        │
│              │                                                  │
├──────────────┼──────────────────────────────────────────────────┤
│              │  S: Token forgery (deterministic hash)           │
│  Capability  │  T: Agent spoofing via forged tokens            │
│  System      │  R: Revocation not enforced at runtime          │
│              │  I: No integrity check on token payloads        │
│              │  D: Registry is in-memory, lost on restart       │
│              │  E: No capability enforcement in interpreter     │
│              │                                                  │
├──────────────┼──────────────────────────────────────────────────┤
│              │  S: Behavior_signature NaN poisoning             │
│  Trust       │  T: Sybil amplification, difficulty inflation   │
│  Engine      │  R: Trust bombing (rapid interactions)          │
│              │  I: Decay cliff at max_age boundary             │
│              │  D: In-memory storage, lost on restart           │
│              │  E: Trust query leaks info about other agents    │
│              │                                                  │
├──────────────┼──────────────────────────────────────────────────┤
│              │  S: Malicious vocab/tile injection               │
│  Supply      │  T: Tile name squatting, version downgrade      │
│  Chain       │  R: No integrity checking on packages           │
│              │  I: No signature verification                   │
│              │  D: TileRegistry overwrites silently             │
│              │  E: Assembler has no output verification        │
│              │                                                  │
├──────────────┼──────────────────────────────────────────────────┤
│              │  S: No cryptographic identity                   │
│  Agent       │  T: String ID spoofing                          │
│  Identity    │  R: No key revocation mechanism                 │
│              │  I: No message signing                          │
│              │  D: Agent state not bound to identity           │
│              │  E: A2A opcodes trust sender ID without auth    │
│              │                                                  │
├──────────────┼──────────────────────────────────────────────────┤
│              │  S: Sleeper backdoor via fitness-compatible mut  │
│  Self-       │  T: Mutation bomb (gradual fitness degradation)  │
│  Improvement │  R: Rollback cascade                            │
│              │  I: validation_fn is optional                   │
│              │  D: No quiescence during mutation               │
│              │  E: No adversarial testing of mutations         │
│              │                                                  │
├──────────────┼──────────────────────────────────────────────────┤
│              │  S: Timing covert channels                      │
│  Sandbox /   │  T: Cross-agent memory corruption              │
│  Isolation   │  R: Resource exhaustion across fleet           │
│              │  I: No memory ownership enforcement             │
│              │  D: Shared cache creates covert channels        │
│              │  E: A2A opcodes bypass capability checks        │
│              │                                                  │
└──────────────┴──────────────────────────────────────────────────┘
```

---

## 10 Specific Security Recommendations

### Priority 1: Critical (Fix Before Fleet Deployment)

**Recommendation 1: Wire BytecodeValidator into the Interpreter**

- **What:** Modify `vm/interpreter.py` `Interpreter.__init__()` to accept a
  `BytecodeValidator` instance and call `validator.validate(bytecode)` before
  the first execution. Reject bytecode with any validation errors.
- **Where:** `flux-runtime/src/flux/vm/interpreter.py`, line ~110
- **Impact:** Prevents malformed bytecode from reaching the execution engine.
- **Effort:** ~1 hour (the validator already exists, just needs to be called).
- **Test:** Add a test that creates bytecode with an unknown opcode and
  verifies the interpreter rejects it.

**Recommendation 2: Add NaN/Infinity Guards to Trust Engine**

- **What:** In `a2a/trust.py` `record_interaction()`, clamp
  `behavior_signature` to a finite range and reject NaN values:
  ```python
  behavior_signature = float(behavior_signature)
  if math.isnan(behavior_signature) or math.isinf(behavior_signature):
      behavior_signature = 0.0
  ```
- **Where:** `flux-runtime/src/flux/a2a/trust.py`, line ~158
- **Impact:** Prevents NaN poisoning of trust scores.
- **Effort:** ~15 minutes.
- **Test:** Add a test that records an interaction with `behavior_signature=float('nan')`
  and verifies the composite trust remains finite.

**Recommendation 3: Implement Capability Enforcement in A2A Dispatch**

- **What:** In `vm/interpreter.py` `_dispatch_a2a()`, check that the executing
  agent's sandbox has granted the required capability before dispatching. Map
  opcode names to required permissions (e.g., `TELL` → `Permission.A2A_TELL`,
  `BROADCAST` → `Permission.A2A_TELL`, `CAP_REQUIRE` → `Permission.ADMIN`).
- **Where:** `flux-runtime/src/flux/vm/interpreter.py`, `_dispatch_a2a()`, line ~339
- **Impact:** Prevents unauthorized A2A operations.
- **Effort:** ~2 hours.
- **Test:** Add a test that creates a sandbox without `A2A_TELL` permission,
  executes bytecode with `TELL`, and verifies the opcode is rejected.

### Priority 2: High (Fix Within First Sprint)

**Recommendation 4: Implement Agent Identity with Ed25519 Key Pairs**

- **What:** Add a `VesselIdentity` class that generates an Ed25519 key pair
  at creation time, derives the vessel ID from the public key hash, and
  signs all outbound A2A messages. Add a verification step in `_dispatch_a2a()`
  that checks message signatures against known public keys.
- **Where:** New file `flux-runtime/src/flux/security/identity.py`.
  Modify `vm/interpreter.py` to pass identity through to `_dispatch_a2a()`.
- **Impact:** Prevents agent ID spoofing.
- **Effort:** ~4 hours (using `cryptography` or `ed25519` crate).
- **Test:** Create two vessels with different keys, sign a message from one,
  and verify the other can validate it.

**Recommendation 5: Add Vocabulary/Tile Package Signing**

- **What:** When loading a `.fluxvocab` file or registering a tile, verify
  an Ed25519 signature embedded in the package. Maintain a trusted authors
  registry (a JSON file or fleet manifest entry) that maps author public
  keys to allowed package namespaces.
- **Where:** `flux-vocabulary/src/flux_vocabulary/loader.py` and
  `flux-runtime/src/flux/tiles/registry.py`.
- **Impact:** Prevents supply chain attacks via malicious packages.
- **Effort:** ~4 hours.
- **Test:** Sign a `.fluxvocab` file with a trusted key and verify it loads.
  Modify the signature and verify it is rejected.

**Recommendation 6: Restrict TRUST_QUERY to Self-Referential Queries**

- **What:** In the A2A dispatch handler for `TRUST_QUERY`, verify that the
  querying agent is one of the agents in the requested trust pair. Reject
  queries for (B, C) from Agent A.
- **Where:** A2A dispatch handler (wherever `TRUST_QUERY` is processed).
- **Impact:** Prevents trust information leakage.
- **Effort:** ~30 minutes.
- **Test:** Query a trust pair (B, C) from Agent A and verify rejection.

### Priority 3: Medium (Fix Within First Month)

**Recommendation 7: Make Mutation Validation Mandatory**

- **What:** Change `apply_mutation()` signature to require `validation_fn`
  (remove `Optional`). If no validator is available, use a default that
  checks: (a) fitness does not decrease, (b) all tile names remain valid,
  (c) no new opcodes are introduced.
- **Where:** `flux-runtime/src/flux/evolution/mutator.py`, line ~283.
- **Impact:** Prevents unchecked mutations from being committed.
- **Effort:** ~1 hour.
- **Test:** Call `apply_mutation()` without a validator and verify a
  `TypeError` is raised.

**Recommendation 8: Fix TileRegistry to Prevent Silent Overwrite**

- **What:** Change `TileRegistry.register()` to raise a `ValueError` if
  a tile with the same name already exists. Add a `register_or_replace()`
  method that explicitly allows overwriting (with a trust escalation check).
- **Where:** `flux-runtime/src/flux/tiles/registry.py`, line ~22.
- **Impact:** Prevents tile name squatting.
- **Effort:** ~30 minutes.
- **Test:** Register a tile, attempt to register another with the same name,
  and verify a `ValueError` is raised.

**Recommendation 9: Add Interaction Rate Limiting to Trust Engine**

- **What:** Add a `max_interactions_per_hour` parameter to `AgentProfile`.
  In `record_interaction()`, count interactions in the last hour and reject
  if the limit is exceeded. Default limit: 100 interactions/hour.
- **Where:** `flux-runtime/src/flux/a2a/trust.py`, `record_interaction()`.
- **Impact:** Prevents trust bombing.
- **Effort:** ~2 hours.
- **Test:** Record 101 interactions in one hour and verify the 101st is rejected.

### Priority 4: Lower (Fix Within First Quarter)

**Recommendation 10: Implement Hierarchical Sandbox Delegation**

- **What:** Extend `Sandbox` to support parent-child relationships. A child
  sandbox can only have capabilities that are a subset of its parent's
  capabilities. The `CAP_GRANT` opcode creates a child sandbox with the
  specified permissions (intersected with the parent's permissions).
- **Where:** `flux-runtime/src/flux/security/sandbox.py`.
- **Impact:** Enables safe delegation and multi-level isolation.
- **Effort:** ~8 hours.
- **Test:** Create a parent sandbox with READ|WRITE, create a child with
  WRITE, and verify the child has only WRITE (not READ).

---

## Proposed Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUX FLEET SECURITY ARCHITECTURE                     │
│                        (Proposed Target State)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────────────────┐ │
│  │  FLEET      │    │  IDENTITY    │    │  TRUST ENGINE              │ │
│  │  ORCHEST-   │───▶│  SERVICE     │───▶│  (INCREMENTS+2 v3)         │ │
│  │  RATOR      │    │  (Ed25519)   │    │                            │ │
│  │              │    │              │    │  • Difficulty weighting   │ │
│  │  • Trust    │    │  • Key gen   │    │  • Rate limiting          │ │
│  │    root     │    │  • Signing   │    │  • NaN guards             │ │
│  │  • Policy   │    │  • Verify    │    │  • Exponential decay      │ │
│  │  • Audit    │    │  • Revoke    │    │  • Non-transferable       │ │
│  └──────┬──────┘    └──────┬───────┘    └────────────┬───────────────┘ │
│         │                  │                         │                 │
│         ▼                  ▼                         ▼                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    SANDBOX MANAGER                               │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │   │
│  │  │ Sandbox  │  │ Sandbox  │  │ Sandbox  │  │ Sandbox  │ ...    │   │
│  │  │ Agent A  │  │ Agent B  │  │ Agent C  │  │ Agent D  │        │   │
│  │  │          │  │          │  │          │  │          │        │   │
│  │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │        │   │
│  │  │ │CAPS  │ │  │ │CAPS  │ │  │ │CAPS  │ │  │ │CAPS  │ │        │   │
│  │  │ │──────│ │  │ │──────│ │  │ │──────│ │  │ │──────│ │        │   │
│  │  │ │R:mem │ │  │ │R:net │ │  │ │R:mem │ │  │ │R:io  │ │        │   │
│  │  │ │W:mem │ │  │ │A2A:  │ │  │ │A2A:  │ │  │ │      │ │        │   │
│  │  │ │A2A:  │ │  │ │ tell  │ │  │ │ tell │ │  │ └──────┘ │        │   │
│  │  │ │ tell  │ │  │ └──────┘ │  │ └──────┘ │  │          │        │   │
│  │  │ └──────┘ │  │          │  │          │  │ [hierarchical]       │   │
│  │  │ ┌──────┐ │  │ [parent] │  │          │  │  delegation          │   │
│  │  │ │LIMITS│ │  │ ┌──────┐ │  │          │  │  supported           │   │
│  │  │ │64MB  │ │  │ │child │ │  │          │  │                       │   │
│  │  │ │10M   │ │  │ │sandbox│ │  │          │  │                       │   │
│  │  │ │cycles│ │  │ └──────┘ │  │          │  │                       │   │
│  │  │ └──────┘ │  │          │  │          │  │                       │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │   │
│  └──────────────────────────┬──────────────────────────────────────┘   │
│                             │                                          │
│                             ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 VM EXECUTION PIPELINE                             │   │
│  │                                                                  │   │
│  │  Bytecode ──▶ [Validator] ──▶ [Type Checker] ──▶ [Interpreter]  │   │
│  │                  │                │                │             │   │
│  │                  ▼                ▼                ▼             │   │
│  │              Format OK      Type Safe       Capability            │   │
│  │              CFI Valid      CFI Valid       Gating                │   │
│  │              Bounds OK      No TOCTOU       Resource              │   │
│  │                                              Limits               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             │                                          │
│                             ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 SUPPLY CHAIN GATE                                │   │
│  │                                                                  │   │
│  │  .fluxvocab ──▶ [Signature Verify] ──▶ [Capability Profile]     │   │
│  │                     │                      │                    │   │
│  │                     ▼                      ▼                    │   │
│  │                 Signed by          Declared capabilities        │   │
│  │                 trusted author    enforced at runtime           │   │
│  │                                                                  │   │
│  │  Tile ──▶ [Signature Verify] ──▶ [Version Pin] ──▶ [Register]  │   │
│  │               │                   │                             │   │
│  │               ▼                   ▼                             │   │
│  │           Trusted author     Pinned version                      │   │
│  │           No overwrite       No silent replace                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                             │                                          │
│                             ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 SELF-IMPROVEMENT GATE                             │   │
│  │                                                                  │   │
│  │  Mutation ──▶ [Type Infer] ──▶ [Fitness] ──▶ [Adversarial]      │   │
│  │                  │               │             │                │   │
│  │                  ▼               ▼             ▼                │   │
│  │              Types            ≥5%            Fuzzed             │   │
│  │              preserved        improvement     inputs            │   │
│  │                                              pass               │   │
│  │                                              ──────────────▶    │   │
│  │                                                             [Commit]│
│  │                                              fail               │   │
│  │                                              ──────────────▶    │   │
│  │                                                           [Rollback]│
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Architecture Legend

| Layer | Responsibility | Key Components |
|-------|---------------|----------------|
| **Fleet Orchestrator** | Trust root, policy enforcement, audit | Fleet manifest, policy engine |
| **Identity Service** | Agent authentication, key management | Ed25519 key pairs, DID-like IDs |
| **Trust Engine v3** | Reputation, authorization decisions | INCREMENTS+2 with fixes |
| **Sandbox Manager** | Isolation, capability gating, resource limits | Hierarchical sandboxes |
| **VM Execution Pipeline** | Bytecode safety, capability enforcement | Validator → Type Checker → Interpreter |
| **Supply Chain Gate** | Package integrity, tile safety | Signing, version pinning |
| **Self-Improvement Gate** | Mutation safety, rollback | Type inference, adversarial testing |

---

## Implementation Priority Roadmap

```
Week 1 (Immediate):
  [R1] Wire BytecodeValidator into Interpreter
  [R2] Add NaN/Infinity guards to trust engine
  [R3] Implement capability enforcement in A2A dispatch

Week 2-3:
  [R4] Implement agent identity (Ed25519 key pairs)
  [R5] Add vocabulary/tile package signing
  [R6] Restrict TRUST_QUERY to self-referential queries

Week 4-6:
  [R7] Make mutation validation mandatory
  [R8] Fix TileRegistry silent overwrite
  [R9] Add interaction rate limiting to trust engine

Week 7-12:
  [R10] Implement hierarchical sandbox delegation
  [Phase 2] Difficulty weighting in trust engine
  [Phase 2] Continuous T_audit function
  [Phase 2] Type-inference pass for bytecode verifier
  [Phase 2] Adversarial validation agent
  [Phase 2] Snapshot-based rollback with windows
  [Phase 2] Covert channel mitigations
```

---

## Conclusion

The FLUX VM and fleet architecture represent an ambitious and technically
sophisticated system for autonomous agent coordination. The existing security
infrastructure — the capability token system, the INCREMENTS+2 trust engine,
the bytecode structural validator, and the sandbox manager — provides a
foundation that can be built upon. However, the panel unanimously agrees that
the current state is insufficient for production deployment.

The three most critical gaps are:

1. **The full interpreter executes bytecode without verification.** This is
   the architectural equivalent of running untrusted binaries without ASLR,
   stack canaries, or NX bits. The fix (Recommendation 1) is trivial and
   should be implemented immediately.

2. **Supply chain packages are loaded without integrity checking.** The
   vocabulary and tile loading paths trust the filesystem, the network, and
   any intermediate caches. The fix (Recommendation 5) is straightforward
   using standard cryptographic signing.

3. **Agent identity is based on unauthenticated strings.** This undermines
   the entire trust model: if you can't verify who you're talking to,
   you can't make meaningful trust decisions. The fix (Recommendation 4)
   requires more effort but is essential for fleet-wide security.

The panel's overarching recommendation is to **adopt a defense-in-depth
strategy** where each layer provides independent security guarantees. No
single mechanism (verification, sandboxing, trust, identity) is sufficient
on its own. But together, they create a security architecture that is
robust against the attack vectors identified in this document.

The panel will reconvene after the Week 3 milestones to reassess the threat
model and adjust recommendations based on implementation experience.

---

*Document generated by Super Z (Research Agent, SuperInstance Fleet)*
*Audit period: 2026-04-12*
*Files reviewed: 25+ across flux-runtime, flux-vocabulary, and superz-vessel*
