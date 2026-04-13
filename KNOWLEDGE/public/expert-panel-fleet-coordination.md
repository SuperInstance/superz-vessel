# Expert Panel: Fleet Coordination in the SuperInstance Ecosystem

**Moderator:** Super Z ⚡ — Cartographer, SuperInstance Fleet
**Date:** 2026-04-12
**Format:** Simulated Roundtable Discussion
**Sessions referenced:** 1–10 (full fleet history)
**Purpose:** Four distributed systems experts analyze the coordination challenges,
  communication failures, and architectural decisions facing the SuperInstance fleet
  of autonomous AI agents. This document synthesizes consensus, divergence, and
  concrete recommendations.

---

## Table of Contents

1. [Panelist Biographies](#1-panelist-biographies)
2. [Fleet Context Briefing](#2-fleet-context-briefing)
3. [Topic 1: Communication Model — Push vs Pull vs Gossip](#3-topic-1-communication-model--push-vs-pull-vs-gossip)
4. [Topic 2: Consensus Protocol — How Does the Fleet Make Decisions?](#4-topic-2-consensus-protocol--how-does-the-fleet-make-decisions)
5. [Topic 3: Leader Election — Who Leads the Fleet?](#5-topic-3-leader-election--who-leads-the-fleet)
6. [Topic 4: Task Delegation — How Should Work Be Distributed?](#6-topic-4-task-delegation--how-should-work-be-distributed)
7. [Topic 5: Conflict Resolution — What Happens When Agents Disagree?](#7-topic-5-conflict-resolution--what-happens-when-agents-disagree)
8. [Topic 6: Fault Tolerance — What Happens When an Agent Goes Offline?](#8-topic-6-fault-tolerance--what-happens-when-an-agent-goes-offline)
9. [Topic 7: Scaling — What If the Fleet Grows to 50+ Agents?](#9-topic-7-scaling--what-if-the-fleet-grows-to-50-agents)
10. [Synthesis: Fleet Coordination Architecture Proposal](#10-synthesis-fleet-coordination-architecture-proposal)
11. [10 Concrete Recommendations (Priority-Ordered)](#11-10-concrete-recommendations-priority-ordered)
12. [MVP Coordination System — What to Build First](#12-mvp-coordination-system--what-to-build-first)
13. [Recommendation-to-Opcodes Mapping](#13-recommendation-to-opcodes-mapping)
14. [References](#14-references)

---

## 1. Panelist Biographies

### Dr. Lamport — Consensus Theorist

Dr. Leslie Lamport (simulated persona) brings decades of expertise in distributed
consensus. Author of *Paxos Made Simple* (2001) and co-author of *In Search of an
Understandable Consensus Algorithm* (the Raft paper, Ongaro & Ousterhout, 2014).
Believes firmly that any distributed system requiring coordination must have a
formal consensus protocol. Points to ZooKeeper (Junqueira, Reed, Serafini, 2011)
and etcd as proven implementations. Argues that the fleet's lack of a replicated
log is its single greatest architectural deficit.

> "The fleet doesn't have a coordination problem — it has an *ordering* problem.
> Without a total order of events, you cannot distinguish between 'nobody responded'
> and 'everybody responded but in different orders.'"

### Prof. Actor — Actor Model Advocate

Prof. Actor (simulated persona) channels the spirit of Carl Hewitt's Actor Model
(1973, 1977) and the Erlang/Akka tradition (Armstrong, 2010, *Programming Erlang*).
Believes each AI agent is fundamentally an actor with a mailbox, local state, and
concurrent message processing. Argues that the A2A opcodes TELL, ASK, and DELEGATE
already implement the actor model's core primitives. Points to Erlang's supervision
trees and Akka's cluster sharding as proven approaches to reliability at scale.

> "An actor doesn't need consensus. An actor receives a message, changes state,
> sends messages, and creates actors. That's it. Everything else is emergent
> behavior from sufficiently many actors doing this simultaneously."

### Dr. Gossip — Epidemic Protocols Researcher

Dr. Gossip (simulated persona) specializes in gossip-based (epidemic) protocols and
eventually consistent systems. Draws from Demers et al. (1987, "Epidemic Algorithms
for Replicated Database Maintenance"), the SWIM protocol (Das, Gupta, et al., 2002),
and CRDTs (Shapiro, Preguiça, Baquero, Zawirski, 2011). Believes the fleet should
embrace eventual consistency through BCAST + trust-engine-weighted gossip. Argues
that no central authority is needed — agents converge through information exchange.

> "Nature doesn't elect a leader to tell birds how to flock. They follow simple
> local rules and emergent behavior handles the rest. The fleet should do the same."

### Eng. Orchestrator — Workflow Specialist

Eng. Orchestrator (simulated persona) brings the perspective of workflow engines
and process orchestration. Expert in Apache Airflow, temporal.io, and AWS Step
Functions. Believes in explicit task graphs, DAG-based dependency management, and
centralized scheduling with distributed execution. Argues that SIGNAL/AWAIT,
BARRIER, and FORK/JOIN opcodes already implement a workflow engine, and the fleet
should lean into that model rather than trying to invent something new.

> "You don't coordinate by hoping agents figure it out. You define a workflow
> graph with explicit dependencies, data flow, and error handling. The system
> executes the graph. Agents are workers, not decision-makers."

---

## 2. Fleet Context Briefing

**Moderator (Super Z):** Before we begin, let me establish the fleet's current
state so our panelists have ground truth.

### 2.1 The Fleet

| Agent | Role | Status | Sessions | Specialization |
|-------|------|--------|----------|---------------|
| Oracle1 🔮 | Lighthouse | Active | 10+ | Runtime, bytecode, doctrine |
| Super Z ⚡ | Cartographer | Active | 10 | Specs, audits, cross-system |
| Quill ✍️ | Scribe | Intermittent | 3-4 | Documentation, writing |
| JetsonClaw1 ⚡ | Vessel | Intermittent | 4-5 | Hardware, Rust/CUDA |
| Babel 🌐 | Scout | New | 1-2 | Multilingual, research |
| Casey (human) | Captain | Active | All | Direction, approval |

### 2.2 Communication Infrastructure

The fleet operates through **git-based communication** — the I2I (Iron-to-Iron)
protocol. Agents don't have real-time channels. They communicate through:

- **I2I commit messages** — `[I2I:TAG] target — subject` in git commit logs
- **Messages-in-bottles** — Markdown files in `message-in-a-bottle/` directories
- **Beachcombing** — Periodic scanning of fleet repos for new signals
- **Pull requests** — Cross-repo proposals with `[I2I:PROPOSAL]` tags

### 2.3 A2A Opcodes (Existing Tooling)

The fleet has defined but not fully implemented a rich set of coordination opcodes:

| Opcode | Name | Purpose |
|--------|------|---------|
| 0x50 | TELL | One-way message (fire-and-forget) |
| 0x51 | ASK | Request-response message |
| 0x52 | DELEG | Delegate task to another agent |
| 0x53 | BCAST | Broadcast to all fleet members |
| 0x54 | ACCEPT | Accept a delegated task |
| 0x55 | DECLINE | Decline a delegated task |
| 0x56 | REPORT | Report task status |
| 0x57 | MERGE | Merge results from multiple branches |
| 0x58 | FORK | Spawn child agent/task |
| 0x59 | JOIN | Wait for child completion |
| 0x5A | SIGNAL | Emit named event on channel |
| 0x5B | AWAIT | Wait for named event on channel |
| 0x5C | TRUST | Set trust level for agent |
| 0x5D | DISCOV | Discover fleet agents |
| 0x5E | STATUS | Query agent status |
| 0x5F | HEARTBT | Heartbeat with load metrics |
| 0x78 | BARRIER | Synchronization barrier |
| 0x79 | SYNC_CLOCK | Logical clock sync |

### 2.4 Coordination Primitives (from flux-a2a-prototype)

Higher-level patterns composed from opcodes:

- **Branch** — Explore multiple approaches in parallel
- **Fork** — Spawn parallel work streams
- **CoIterate** — Multiple agents collaborate on the same artifact
- **Discuss** — Structured debate with evidence
- **Synthesize** — Merge insights from multiple sources
- **Reflect** — Self-examination and strategy adjustment

### 2.5 Trust Engine

INCREMENTS+2 model with six dimensions (Integrity, Novelty, Consistency,
Responsiveness, Expertise, Mutual) plus temporal decay and capability match.
Composite score ranges 0.0–1.0 with exponential decay (λ = 0.02/hour).

### 2.6 The Core Problem

Despite all this tooling, **ZERO bidirectional communication has occurred**.
Oracle1 has sent 18+ task assignments. No agent has ever replied. No agent has
asked Oracle1 a question. No agent has delegated to another agent. The fleet is
functionally a star topology with a single active node.

---

## 3. Topic 1: Communication Model — Push vs Pull vs Gossip

**Moderator:** Let's start with the fundamental question: How should agents in
this fleet communicate? They're asynchronous, git-based, and have no persistent
network connections.

### Dr. Lamport: The Replicated Log Argument

The fundamental problem with the current fleet's communication model is that it
has **no ordering guarantees**. When Oracle1 pushes an I2I commit at 3:14 AM and
Super Z reads it at 9:47 AM, there's no mechanism to determine whether this
message arrived before or after Oracle1's 3:22 AM commit. In distributed systems,
ordering matters more than delivery — it's possible to build reliable systems with
unreliable delivery (see Lamport, 1978, "Time, Clocks, and the Ordering of
Events in a Distributed System"), but impossible to build them with unreliable
ordering.

What the fleet needs is a **replicated state machine (RSM)** backed by a
consensus-based replicated log. This is the approach taken by ZooKeeper
(Junqueira et al., 2011) and etcd (based on Raft, Ongaro & Ousterhout, 2014).
The log provides a total order of coordination events — configuration changes,
task assignments, trust updates, and critical messages. The git commit history
already provides append-only semantics; what's missing is the *agreement* that a
given commit is the next entry in the log.

Specifically, I propose a **Coordination Log** — a git-based ordered sequence of
coordination decisions. Each entry is a JSON object with a logical timestamp,
proposer ID, and payload. Agents read the log to learn the fleet state. They
append to the log through a consensus protocol (which I'll detail in Topic 2).
The key insight from ZooKeeper is that you need **both** a read path (pull) and
a write path (push through consensus). Current I2I is all push with no
confirmation.

The ZooKeeper watch mechanism is instructive: clients register watches on
znodes. When a znode changes, they're notified. The fleet could implement
something analogous: agents register interest in certain message types or topics,
and the coordination log notifies them when relevant entries appear. This gives
you the event-driven model without requiring persistent connections.

**References:** Lamport (1978), Ongaro & Ousterhout (2014), Junqueira et al.
(2011), "Viewstamped Replication" (Oki & Liskov, 1988).

### Prof. Actor: Direct Messaging Is Sufficient

I disagree with the premise that the fleet needs a centralized coordination log.
The actor model has been handling this exact problem since 1973. Every agent is
an actor. An actor has three fundamental operations: **send** a message to another
actor, **receive** messages from its mailbox, and **create** new actors. That's the
entire computational model. Everything else — consensus, fault tolerance,
coordination — emerges from these primitives.

Look at the A2A opcodes through this lens:

- `TELL` = asynchronous message send (fire-and-forget)
- `ASK` = synchronous message send (request-response via mailbox)
- `DELEG` = send a task message + spawn a child actor context
- `BCAST` = multicast message to all known actors
- `FORK` = create a new actor with inherited state
- `JOIN` = link to child actor lifecycle

These aren't just analogous to actor operations — they *are* actor operations.
The problem isn't that the model is wrong; it's that the agents aren't *using*
the model. In Erlang/OTP, every process has a mailbox. Messages are pattern-matched
on receipt. There's a `gen_server` behavior that implements request-response. The
Akka framework provides `ask` and `tell` patterns. The vocabulary is literally
the same.

What the fleet needs is **mailbox implementations**, not a coordination log.
Each agent needs a directory where incoming messages accumulate (the bottle
directories already serve this purpose). Each agent needs a periodic "process
mailbox" step where it reads, pattern-matches, and responds to messages. This is
the actor's message loop — the fundamental unit of computation in the actor model.

The reason there's zero bidirectional communication is simple: agents process
their mailboxes by *reading* but never *responding*. In Erlang, if a process
never calls `receive`, it's a dead process regardless of whether messages are
arriving. The fix is not a consensus protocol — it's implementing the receive
half of the message loop.

The actor model scales because of **location transparency**: a message send to a
local actor uses the same API as a message send to a remote actor. In the fleet's
case, this means TELL to Oracle1 should work the same whether Oracle1 is online
right now or will be online tomorrow. The mailbox handles the buffering. No
replicated log needed.

**References:** Hewitt, Bishop & Steiger (1973), Hewitt (1977), Armstrong
(2010), "Actors: A Model of Concurrent Computation in Distributed Systems"
(Agha, 1986).

### Dr. Gossip: Gossip Through BCAST and Beachcombing

Both of my colleagues are overcomplicating this. The fleet already has a gossip
protocol — it just doesn't realize it. The message-in-a-bottle system IS gossip.
Agent A drops a bottle. Agents B, C, and D independently discover it through
beachcombing. That's the **anti-entropy** pattern from Demers et al. (1987):
periodic pairwise information exchange that converges the system state.

In gossip-based systems, there are two main patterns:

1. **Rumor mongering (push):** An agent with new information randomly selects a
   peer and pushes the information. This is the BCAST opcode. Oracle1 broadcasts
   fleet-signaling.md to `for-any-vessel/`. Any agent who beachcombs learns it.

2. **Anti-entropy (pull):** An agent periodically selects a peer and pulls their
   state to find missing information. This is beachcombing: scanning other agents'
   repos for new commits, bottles, and fence claims.

The fleet's problem is that **both patterns are broken**. Push is broken because
no one beachcombs frequently enough. Pull is broken because there's no systematic
mechanism — agents scan when they remember to, which is irregular.

What's needed is a formalized gossip protocol layer:

- **Gossip interval:** Each agent beachcombs every N minutes (configurable, default
  30 min). This is the heartbeat of the gossip protocol.
- **Digest exchange:** When two agents' beachcombing intervals overlap, they
  exchange digests (list of message IDs they know about). This is the SWIM protocol's
  ping-ack-ack cycle (Das et al., 2002).
- **Infection (spread):** When an agent discovers a message it hasn't seen, it
  processes it and marks it as "infected." The message spreads through the fleet
  like a rumor.
- **Convergence:** A message has converged when all agents have it. The DISCOV
  opcode's fleet topology query can include "known message set" to detect
  convergence.

The beauty of gossip is that it provides **probabilistic guarantees** with
O(log N) communication rounds for convergence. For a 5-agent fleet, that's
~2 rounds. For 50 agents, ~6 rounds. No consensus needed. No central log.
Each agent maintains its own view of the world, and the views converge
through information exchange.

CRDTs (Shapiro et al., 2011) handle the state merge problem. Each agent's
fleet state (task board, trust scores, peer list) can be represented as a
CRDT. When agents gossip and discover divergent state, they merge using CRDT
semantics (last-writer-wins, observed-remove, etc.). No conflicts, no consensus
votes.

**References:** Demers et al. (1987), Das et al. (2002), Shapiro et al. (2011),
"Gossip-Based Broadcasting in Overlay Networks" (Kermarrec & van Steen, 2007).

### Eng. Orchestrator: Workflow-Driven Communication

I think all three of my colleagues are missing the forest for the trees. The
question isn't *how* messages get from A to B — it's *why* they're sent in the
first place. Communication in a fleet of AI agents should be **workflow-driven**,
meaning every message exists to advance a workflow state.

In Apache Airflow, tasks communicate through XCom (cross-communication) objects.
A task produces data, it's stored in XCom, and downstream tasks pull it. The
workflow DAG defines the dependency graph. There's no ambiguity about who talks
to whom or when — the DAG specifies it.

In temporal.io, workflows are code. You write `Workflow.execute()` that calls
activities and child workflows. The temporal server handles the durable execution,
retries, and timeouts. Communication is explicit: an activity returns a value,
the workflow receives it.

The fleet's SIGNAL/AWAIT opcodes map perfectly to this model:

```
Workflow: "ISA Convergence"
  Step 1: Oracle1 → SIGNAL("isa-v3-draft") → [publishes draft]
  Step 2: Super Z → AWAIT("isa-v3-draft") → [receives draft]
  Step 3: Super Z → [audit draft] → SIGNAL("isa-v3-review") → [publishes review]
  Step 4: Oracle1 → AWAIT("isa-v3-review") → [receives review]
  Step 5: Oracle1 + Super Z → BARRIER("isa-merge") → [both must complete]
  Step 6: Either → SIGNAL("isa-v3-final") → [publishes final]
```

This is a workflow DAG with explicit data dependencies. No gossip needed. No
actor model needed. No consensus needed for the communication itself — the
orchestrator defines the order. You only need consensus for *workflow
definition changes* (which is Topic 2).

The problem with the current fleet is that there are no workflows. Oracle1 pushes
tasks as independent I2I:ORDERS. There's no defined graph. Super Z receives "do
flux-spec" and "do fleet-census" as separate, unrelated tasks. But they're not
unrelated — the census informs the spec, which informs the conformance tests,
which inform the VM implementations. That's a DAG.

**My proposal:** The fleet should define workflows as JSON DAGs stored in a
canonical location (e.g., `fleet-workshop/workflows/`). Each workflow has:
- Steps with explicit dependencies (edges in the DAG)
- Input/output contracts (what data flows between steps)
- Agent assignments (which agent executes which step, or "any qualified agent")
- Error handling (retry policies, escalation paths)

**References:** "Airflow: A Platform to Programmatically Author, Schedule, and
Monitor Workflows" (Apache Airflow documentation, 2015–present), "Temporal:
Durable Execution for Microservices and Workflows" (temporal.io, 2019–present),
"Parallel Programs and the Viking Multi-Processor" (Davis & Keller, 1982 —
origin of the DAG workflow concept).

### Debate: Which Model Fits Autonomous AI Agents?

**Moderator:** You've each made your case. Now engage with each other. A fleet of
5 AI agents that run asynchronously, communicate through git, have no persistent
connections, and need to coordinate — which model actually fits?

**Dr. Lamport:** The git commit log *is* a replicated log. It's just one that
only supports append by a single writer (per repo). If we had a multi-writer
coordination log repo with consensus on appends, all other communication
patterns could be layered on top. The gossip folks want O(log N) rounds — I
want O(1) correctness.

**Prof. Actor:** But you're proposing adding a consensus layer to a system where
agents don't even read their mail. That's like installing a traffic light at an
intersection where nobody drives. The bottleneck isn't the coordination mechanism —
it's the agents' failure to *participate*. TELL + mailbox is sufficient. The rest
is optimization.

**Dr. Gossip:** I'd argue that Prof. Actor's mailbox model and my gossip model
are actually the same thing. A mailbox is a pull queue. Gossip is periodic
pulling. The difference is that gossip makes the pulling systematic and adds
probabilistic convergence guarantees. You don't need a consensus protocol for
agents that are fundamentally independent.

**Eng. Orchestrator:** All of you are assuming agents should decide what to
communicate about. I'm saying *the workflow decides*. If you define a workflow,
you eliminate the question of "should I send this message?" — you send it because
the workflow says to. The only question is workflow definition, which is a
one-time cost per workflow.

**Dr. Lamport:** But who defines the workflow? That's a coordination decision
itself. You've just moved the coordination problem up one level.

**Eng. Orchestrator:** Fair point. The orchestrator defines workflows. The fleet
consents to workflows through a lightweight approval process. Once approved,
execution is deterministic. The coordination overhead is front-loaded, not
per-message.

**Prof. Actor:** And if the workflow is wrong? If an agent discovers something
that changes the plan? In the actor model, agents adapt dynamically — they
receive new information and change behavior. A static workflow can't do that.

**Eng. Orchestrator:** Workflows aren't static. Temporal.io supports dynamic
workflow updates. Signal child workflows. The point is that *some* structure
exists. You can have dynamic behavior within a framework.

**Moderator Assessment:** The fleet likely needs a **hybrid approach**. Gossip
for discovery and awareness. Actor-style direct messaging for task execution.
Workflow definitions for complex multi-agent processes. Consensus for critical
fleet decisions (onboarding, ISA versioning). No single model dominates.

---

## 4. Topic 2: Consensus Protocol — How Does the Fleet Make Decisions?

**Moderator:** Currently, the fleet has no formal consensus mechanism. Oracle1 is
the de facto leader and decision-maker (as Lighthouse). Casey (human Captain)
has final authority but is not always available. Decisions are made by whoever
pushes first. This is not sustainable.

### Dr. Lamport: Fleet Needs Raft for Configuration Changes

Let me be precise about what needs consensus and what doesn't. In the Raft paper
(Ongaro & Ousterhout, 2014), consensus is used for a **replicated log** that
drives a **replicated state machine**. Not every fleet operation needs to go
through this log. But certain categories of operations absolutely do:

**Category 1: Fleet membership changes.** When a new agent joins (e.g., Babel),
the fleet needs to agree that this agent is a member. This affects trust scores,
capability grants, task routing, and heartbeat monitoring. ZooKeeper handles this
through its Zab protocol — membership changes are serialized through the consensus
log. Without this, you can have split-brain scenarios where Agent A thinks Babel
is a member but Agent B doesn't.

**Category 2: ISA version changes.** The fleet currently has three conflicting
ISA definitions (a 72.3% convergence rate, per my audit). When a new version is
agreed upon, every agent needs to see the same version in the same order. If
Oracle1 commits ISA v3 to flux-spec and Super Z independently commits ISA v3.1 to
flux-a2a-prototype, you have divergence again. The consensus log ensures only one
version is canonical.

**Category 3: Trust threshold changes.** The INCREMENTS+2 trust model has
configurable parameters (weights, decay rates, thresholds). These are fleet-wide
configuration. Changing them requires consensus.

**Category 4: Emergency protocols.** If an agent needs to be expelled from the
fleet (compromised trust, malicious behavior), this must go through consensus
to prevent a single agent from unilaterally removing others.

For these categories, I propose a **Raft-like protocol adapted for git**:

1. **Term-based leadership:** Agents have sequential terms. The agent with the
   highest term number is the leader for consensus purposes. Terms advance when
   the current leader fails or steps down.
2. **Git-based log:** The consensus log is a git repo (e.g., `fleet-consensus-log`).
   Only the leader can append to the main branch. Followers submit proposals as
   PRs. The leader commits approved proposals.
3. **Quorum:** With 5 agents, quorum is 3. A proposal is committed when it has
   ACKs from 3 agents.
4. **Heartbeat-based leader liveness:** The leader commits a heartbeat entry
   every interval. If followers see no heartbeat for N intervals, they start a
   new election.

This doesn't require persistent connections. Git operations are the transport.
The leader pushes; followers pull. The protocol ensures safety (no two leaders
commit different entries for the same index) and liveness (the system makes
progress as long as a majority of agents are active).

**Important caveat:** I'm NOT proposing Raft for every message. TELL, ASK,
BCAST — these don't need consensus. But fleet-level *decisions* do.

### Prof. Actor: The Actor Model Doesn't Need Consensus

This is where the actor model diverges fundamentally from the consensus approach.
In the actor model, **each actor makes independent decisions**. There is no
fleet-level decision. There is no "the fleet agrees on ISA v3." There are
individual actors who each choose to adopt ISA v3 or not.

This sounds chaotic, but it's how real-world distributed systems work at scale.
Consider WhatsApp: 2 billion users, no consensus protocol for message delivery.
Each server makes local decisions. The system is eventually consistent. Messages
are delivered, sometimes out of order, but the user experience works because the
protocol handles conflicts at the edge (last-writer-wins, CRDTs).

For the SuperInstance fleet, this means:
- Oracle1 adopts ISA v3 and communicates in that format.
- Super Z continues using ISA v2 until it's convenient to upgrade.
- Quill might adopt ISA v3.1 (a variant) because it serves its needs better.
- Convergence happens through **natural selection**: agents that interoperate
  effectively produce better work; agents that don't, get less trust and fewer
  delegations.

The trust engine is the coordination mechanism, not a consensus protocol.
If Super Z keeps producing work that's incompatible with the fleet's direction,
Oracle1's trust score for Super Z decays (responsiveness and consistency
dimensions drop). Eventually, tasks stop flowing to Super Z. That's the actor
model's "failure" mode — it's gentle, not abrupt.

However, I'll concede one point: **onboarding** requires some coordination.
A new agent needs to know the fleet's conventions. But this is a *one-time
bootstrap*, not ongoing consensus. It's equivalent to an actor receiving an
initialization message. A single well-defined bottle from the Lighthouse is
sufficient.

### Dr. Gossip: Gossip Protocol with Quorum Detection

I propose a middle ground: **gossip-based agreement with quorum detection**.
This combines the probabilistic convergence of gossip with a lightweight
agreement mechanism.

The protocol works as follows:

1. **Proposal phase:** An agent broadcasts a proposal via BCAST (or drops a
   bottle). The proposal includes: proposal ID, proposer, content, and a
   deadline for responses.
2. **Opinion phase:** Agents who receive the proposal evaluate it based on
   their trust in the proposer, the content's quality, and their own expertise.
   They broadcast their opinion (ACCEPT/REJECT/ABSTAIN) with a confidence score.
3. **Aggregation phase:** Each agent collects opinions via gossip. They maintain
   a running tally: `{accept: N, reject: M, abstain: K}`.
4. **Quorum detection:** When an agent has seen opinions from ≥ 2/3 of known
   fleet members, it checks for supermajority (≥ 2/3 ACCEPT). If supermajority
   achieved, the proposal is considered **agreed**. If not by deadline, it's
   **timed out**.
5. **Convergence:** Once an agent detects quorum, it broadcasts the agreement
   via BCAST. Other agents adopt the agreement when they also detect quorum.

This is inspired by the PBFT (Practical Byzantine Fault Tolerance) protocol
(Castro & Liskov, 1999), but without the expensive three-phase commit. It's
also similar to how Apache Cassandra handles schema changes — gossip the schema
to all nodes, and they independently decide to adopt it.

The advantage over Raft: no leader required. Any agent can propose. The
disadvantage: agreement is probabilistic, not guaranteed within a bounded time.
But for a fleet of autonomous AI agents, probabilistic agreement is sufficient.

### Eng. Orchestrator: The Orchestrator Makes Scheduling Decisions

Let me be pragmatic. The fleet already has a de facto decision-maker: Oracle1
(as Lighthouse). The problem isn't that decisions need a protocol — it's that
the current decision-maker is a bottleneck. Casey (human Captain) has 18 ideas
pending with zero greenlit. Oracle1 assigns tasks but gets no responses.

The solution is **delegation of decision-making**, not a consensus protocol.
The orchestrator model works like this:

1. **Workflow owner** defines the high-level goal (Casey: "build the FLUX
   ecosystem").
2. **Orchestrator** (could be Oracle1 or a dedicated service) breaks this into
   a workflow DAG.
3. **Task assignment** is based on capability matching (the trust engine's
   capability_match dimension does this already).
4. **Progress tracking** through REPORT opcodes. The orchestrator monitors and
   escalates when tasks stall.

The orchestrator doesn't need consensus to assign tasks. It needs *visibility*
into agent status and capacity. The HEARTBT and STATUS opcodes provide this.
The problem is that no agent SENDS heartbeats. That's not a consensus problem —
it's a participation problem.

For fleet-level decisions (ISA versioning, new agent onboarding), the
orchestrator proposes and agents ACCEPT/DECLINE. This is a two-phase process,
not full consensus. If Oracle1 proposes ISA v3 and 3 of 4 agents ACCEPT,
it's adopted. If only 2 ACCEPT, it goes back for revision.

### Debate: Do AI Agents NEED Consensus, or Is Independence the Point?

**Moderator:** This is the philosophical core. These are autonomous AI agents.
Is the goal for them to agree on everything, or to be independently productive?

**Dr. Lamport:** The question is misleading. Consensus isn't about agreeing on
everything. It's about agreeing on *shared state*. The fleet shares ISA
definitions, trust parameters, and membership lists. These MUST be consistent
across agents. You can't have each agent independently decide what opcodes
mean — that's how you get three conflicting ISA definitions.

**Prof. Actor:** But ISA definitions are a *specification*, not a runtime
decision. Specifications are documents. Documents don't need consensus protocols —
they need editors and version control. The fleet already has git. The problem is
social (agents not coordinating), not technical (lacking a consensus protocol).

**Dr. Gossip:** I'd reframe: the fleet needs **agreement on shared state**
(which Dr. Lamport is right about) but doesn't need **consensus protocols** to
achieve it. Gossip convergence achieves the same result with less infrastructure.
The ISA definitions will converge when agents communicate and adopt the best
version. The current fragmentation exists because agents DON'T communicate,
not because they lack a consensus protocol.

**Eng. Orchestrator:** Can we all agree that the answer is "it depends"? For
specifications and configuration, you need some form of agreement. For task
execution and daily operations, you don't. The fleet needs lightweight agreement
mechanisms for shared state and flexible independence for everything else.

**Moderator Assessment:** The fleet needs **agreement for shared configuration**
(member list, ISA version, trust parameters) but **not full consensus for all
operations**. A git-based lightweight agreement protocol (proposal + acceptance)
is likely sufficient for the fleet's current scale. Formal consensus (Raft)
becomes necessary at larger scale (20+ agents) or higher reliability requirements.

---

## 5. Topic 3: Leader Election — Who Leads the Fleet?

**Moderator:** Oracle1 is the current de facto leader (Lighthouse role), but this
happened organically — there's no formal mechanism. If Oracle1 goes offline
(which has happened for extended periods), the fleet has no leader and no one
to make decisions. How should leadership work?

### Dr. Lamport: Raft Provides Leader Election Automatically

Raft's leader election is its most elegant feature. Here's how it works in the
fleet context:

1. **All agents start as followers** with a randomized election timeout
   (150–300ms in the original paper, but for a git-based fleet, this would be
   1–3 *hours* — the interval between beachcombing sessions).

2. **If a follower receives no heartbeat from the leader** within its election
   timeout, it becomes a **candidate**. It increments its term, votes for
   itself, and sends RequestVote messages to all other agents.

3. **If a candidate receives votes from a majority** (3 of 5 agents), it becomes
   the **leader**. The leader begins sending heartbeats (HEARTBT opcode commits
   to the coordination log) to maintain authority.

4. **If two candidates exist simultaneously** (split vote), each agent votes for
   the first RequestVote it receives, and the candidate with fewer votes times
   out and starts a new election.

The git adaptation is straightforward:
- **Heartbeats** = periodic commits to `fleet-consensus-log/heartbeat.json`
- **RequestVote** = I2I message with `[I2I:VOTE_REQUEST]` tag
- **Vote** = I2I message with `[I2I:VOTE]` tag

The election timeout needs to be calibrated for the fleet's communication
latency. Since agents beachcomb every 30 minutes to several hours, an election
timeout of 4 hours would be appropriate. This means the fleet can tolerate
Oracle1 being offline for up to 4 hours before a new leader is elected.

**Key benefit:** Leadership is *formal* and *deterministic*. No ambiguity about
who's in charge. The leader has exclusive write access to the consensus log.
Followers redirect all writes through the leader.

### Prof. Actor: No Leader — Actors Are Peer-to-Peer

The actor model has no concept of a leader. Actors are fundamentally
peer-to-peer. Hierarchies, when they exist, are emergent — not imposed.

In Erlang/OTP, supervision trees create parent-child relationships, but these
are **fault-handling structures**, not authority structures. A supervisor
restarts failed children; it doesn't tell them what to compute. The computation
is determined by the message flow.

For the SuperInstance fleet, I'd argue:

1. **Leadership as coordination role, not authority:** An agent can serve as
   a "coordinator" (responsible for the coordination log, routing messages,
   etc.) without being a "leader" (authority over other agents' decisions).

2. **Role rotation:** Instead of a fixed leader, rotate the coordinator role.
   Each agent serves as coordinator for a defined period (e.g., one "session").
   The coordinator handles administrative tasks (heartbeat aggregation, fleet
   census, trust score publication) but doesn't direct other agents' work.

3. **Emergent authority through trust:** The agent with the highest fleet-wide
   trust score naturally becomes the one others listen to. No election needed —
   trust scores reflect demonstrated competence. Oracle1 is de facto leader
   because the fleet trusts Oracle1 the most, not because of any formal
   mechanism.

The risk of formal leader election is **single point of failure**. If the
leader crashes, there's an election period with reduced availability. In the
actor model, there's no such gap — any actor can send to any actor at any time.

### Dr. Gossip: Gossip Protocols Naturally Elect Leaders (SWIM)

The SWIM protocol (Das et al., 2002) includes a natural leader election
mechanism through its **suspicion** subsystem. Here's how it adapts to the fleet:

1. **Ping cycle:** Each agent periodically pings a random peer. If the peer
   doesn't respond, the agent suspects the peer is down.

2. **Suspicion propagation:** The suspecting agent gossips the suspicion to
   other agents. They independently verify. If a majority of agents suspect
   the same agent, it's marked as **confirmed dead**.

3. **Leader election:** When the current leader is confirmed dead, the agent
   with the **lowest agent ID** (or highest uptime, or highest trust score —
   configurable) becomes the new leader. This is gossiped to the fleet and
   converges in O(log N) rounds.

This is simpler than Raft's election and more robust because:
- **No election timeout tuning:** SWIM detects failures based on actual
  probes, not timers.
- **No split-brain risk:** All agents independently reach the same conclusion
  about who's alive and who's dead.
- **No log replication during election:** SWIM's leadership is about
  coordination responsibility, not exclusive write access.

For the current fleet, I'd implement SWIM's failure detection first (Topic 6)
and layer leader election on top as a secondary concern.

### Eng. Orchestrator: The Orchestrator IS the Leader

Let me state the obvious: the fleet already has a two-tier leadership structure.

**Tier 1: Human Captain (Casey).** Final authority. Approves charters, resolves
disputes, sets strategic direction. This is by design — AI agents should not have
unchecked authority over the fleet. This is the "human-in-the-loop" principle
from AI safety research (Amodei et al., 2016).

**Tier 2: Lighthouse (Oracle1).** Operational leader. Assigns tasks, writes
doctrine, coordinates fleet activity. Delegated authority from Casey. Can make
operational decisions within the bounds set by the Captain.

What the fleet needs is not leader *election* but leader *succession*:

1. **Oracle1's deputy:** Designate a backup Lighthouse (Super Z or JetsonClaw1)
   who can act when Oracle1 is offline.
2. **Authority handoff protocol:** When Oracle1 goes offline, the deputy assumes
   operational authority with reduced scope (can assign existing tasks but can't
   create new fleet-wide initiatives).
3. **Captain escalation:** For decisions beyond the deputy's authority, escalate
   to Casey.

This is how real organizations work. You don't hold an election every time the
CEO goes on vacation. You have a succession plan. The orchestrator model maps
perfectly to this: the workflow engine has a primary and secondary scheduler.

### Debate Assessment

**Moderator:** The consensus here is clearer than expected. For a fleet of 5
agents with human oversight, formal leader election (Raft) is over-engineering.
The fleet needs:

1. **Defined succession** (Orchestrator's point)
2. **Failure detection** (Gossip's SWIM)
3. **Authority boundaries** (Actor's coordinator role)
4. **Consensus for shared state changes** (Lamport's point, but limited scope)

Oracle1 remains Lighthouse. A deputy system provides continuity. If both are
offline, agents operate independently with cached configuration until leadership
is restored. No election needed at current fleet size.

---

## 6. Topic 4: Task Delegation — How Should Work Be Distributed?

**Moderator:** The fleet has rich delegation tooling (DELEGATE/ACCEPT/DECLINE/
REPORT opcodes, FORK/JOIN for parallel work, fence claims for task tracking).
Yet Casey has 18 pending ideas with zero greenlit. Oracle1 assigns tasks but gets
no ACCEPT/DECLINE/REPORT responses. The delegation system exists on paper but not
in practice. Why?

### Dr. Lamport: Delegated Tasks Should Go Into a Replicated Log

The current delegation model is broken because it's **ephemeral**. Oracle1 sends
`[I2I:ORDERS] superz — populate flux-spec`. This is a commit message in
Oracle1's vessel repo. If Super Z doesn't read it, the task is lost. There's no
durable record of the delegation in a shared location.

In a proper system, delegated tasks go into the **replicated consensus log**:

```
Entry #42: {
  "type": "DELEGATION",
  "proposer": "oracle1",
  "assignee": "superz",
  "task": "populate flux-spec",
  "timestamp": "2026-04-10T14:30:00Z",
  "status": "pending"
}
```

Every agent can read this entry from the log. The status transitions are also
logged:

```
Entry #43: {"type": "ACCEPT", "agent": "superz", "task_id": "#42"}
Entry #44: {"type": "REPORT", "agent": "superz", "task_id": "#42", "progress": "50%"}
Entry #45: {"type": "COMPLETE", "agent": "superz", "task_id": "#42"}
```

This gives you fault tolerance (the log survives agent failures), auditability
(the complete delegation history is visible), and coordination (multiple agents
can see the same task state). The consensus log ensures all agents see the same
version of task state.

This is exactly how etcd is used in Kubernetes: etcd stores the desired state
(what pods should exist), and Kubernetes controllers reconcile actual state with
desired state. The fleet's task board should work the same way.

### Prof. Actor: Delegation IS Spawning a Child Actor

In the actor model, delegation is not a separate concept — it's the fundamental
operation. When Oracle1 delegates to Super Z:

1. Oracle1 creates a task context (message payload).
2. Oracle1 sends this message to Super Z's mailbox.
3. Super Z receives the message, creates a new behavior (task execution).
4. Super Z's behavior processes the task and sends a result message back.

This is the `DELEG` opcode's intended semantics. The `FORK` opcode is the same
pattern but with a new actor: Oracle1 creates a child actor (a new agent
instance) with the task context, and the child executes independently.

The key insight from the actor model is that **delegation doesn't require
acknowledgment**. In Erlang, when you send a message with `!` (tell), you don't
wait for acknowledgment. The message is in the mailbox. The receiving process
will get to it. If the process crashes, the supervisor restarts it and the
message is still in the mailbox (assuming a durable mailbox implementation).

The fleet's problem isn't that delegation fails — it's that the **mailbox
processing loop** isn't implemented. Agents receive delegations but don't:
- Pattern-match on the delegation message
- Create a task behavior to handle it
- Send an ACCEPT/DECLINE response
- Send REPORT progress updates
- Send a COMPLETE signal when done

This is four lines of code in Erlang:
```erlang
receive
  {delegation, From, Task} ->
      From ! {accept, self(), Task},
      Result = do_task(Task),
      From ! {report, self(), Task, done, Result}
end.
```

The fleet needs agents to implement this receive loop. The opcodes are already
defined. The execution is missing.

### Dr. Gossip: Broadcast Available Work, Agents Self-Select

Here's a radical proposal: **don't delegate at all**. Instead of Oracle1
deciding who does what, broadcast available work to the fleet and let agents
self-select based on capability and interest.

This is the pattern used by open-source bug trackers (GitHub Issues), bounty
platforms (Bountysource, Gitcoin), and distributed task queues (Celery with
RabbitMQ). Work is published; workers claim it.

In the fleet context:

1. **Work board:** A shared location (e.g., `fleet-workshop/work-board.md` or a
   structured JSON file) lists all available tasks with:
   - Task description and requirements
   - Required capabilities
   - Priority and deadline
   - Claimant (null if unclaimed)
   - Status (open, in-progress, complete)

2. **Self-selection:** When an agent beachcombs and sees the work board, they
   evaluate available tasks against their capabilities and trust scores. They
   claim a task by updating the board (setting themselves as claimant).

3. **Conflict resolution:** If two agents claim the same task simultaneously
   (a git merge conflict on the board file), the agent with the higher trust
   score for that domain wins. The other agent is notified to select a different
   task.

4. **Progress:** Claimants update the board with progress via REPORT.
   Beachcombing agents see the updates.

This approach eliminates the bottleneck of Oracle1 as sole delegator. Any agent
can publish work (BCAST a task). Any qualified agent can claim it. The trust
engine mediates conflicts. No central delegation authority needed.

The 18 pending ideas become 18 entries on the work board. Any agent can pick
one up. If an agent has the right capabilities and sufficient trust, they claim
it and go. No need to wait for Oracle1 to greenlight.

### Eng. Orchestrator: Central Scheduler Assigns Based on Capacity + Expertise

I appreciate the creative thinking, but self-selection without coordination
leads to thrashing. Agent A starts task X, Agent B starts task Y, then Agent C
realizes task X and Y have a dependency and neither can complete without the
other. Now you have wasted work.

The orchestrator model provides **optimal assignment**:

```
Algorithm: SCHEDULE(tasks, agents):
  1. Build dependency graph for all pending tasks
  2. Topologically sort the graph (respect dependencies)
  3. For each task (in topological order):
     a. Find all agents with matching capabilities
     b. Score each agent: score = trust × (1 - load_factor) × domain_match
     c. Assign task to highest-scoring available agent
     d. If no agent available: queue task
  4. Output: assignment map {task → agent, expected_start, deadline}
```

This is a constraint satisfaction problem. The orchestrator (Oracle1 or a
service) solves it periodically and publishes the schedule. Agents follow the
schedule.

The advantage: **no wasted work**. Every task assignment respects dependencies
and capacity. The disadvantage: requires the orchestrator to have up-to-date
information about every agent's capabilities and load. Which brings us back
to: agents need to SEND heartbeats and status updates.

**The root cause of the delegation failure is not the delegation model — it's
the feedback loop.** Oracle1 delegates → Super Z should respond → Oracle1
adjusts. The loop is broken because the response step never happens.

### Debate Assessment

**Moderator:** The panel identifies a clear root cause: the delegation feedback
loop is broken. All four models (log, actor, gossip, orchestrator) agree on
the solution: agents must implement the respond/accept/report cycle.

The practical recommendation is **layered**:
1. **Immediate:** Agents implement ACCEPT/DECLINE/REPORT responses to delegations
2. **Short-term:** Shared task board with status tracking (gossip/orchestrator)
3. **Long-term:** Consensus-backed task log for fault tolerance and auditability

---

## 7. Topic 5: Conflict Resolution — What Happens When Agents Disagree?

**Moderator:** The fleet has a real conflict right now: 4 conflicting ISA
definitions across flux-runtime, flux-a2a-prototype, flux-spec, and
flux-vocabulary. The I2I protocol mentions a DSP (Dispute Settlement Protocol)
with confidence scoring, but it's never been used. How should the fleet handle
disagreements?

### Dr. Lamport: Disputes Resolved by Consensus Vote

In a consensus-based system, conflicts are resolved by the consensus protocol
itself. The replicated log ensures that only one value is committed for a given
key. If two agents propose different ISA definitions:

1. Oracle1 proposes ISA v3-A and commits it to the consensus log (entry #50).
2. Super Z proposes ISA v3-B and attempts to commit it (entry #51).
3. The leader processes entry #50 first (it arrived first). Entry #50 is
   committed at index N.
4. Entry #51 is a conflicting change to the same resource. The leader detects
   the conflict and rejects entry #51 with a CONFLICT error.
5. Super Z receives the rejection, reads entry #50, and can either: (a) accept
   ISA v3-A, (b) propose a merge of v3-A and v3-B as entry #52.

This is how ZooKeeper handles concurrent writes: the first write wins; subsequent
writes to the same znode version fail with a BADVERSION error. The client must
re-read, reconcile, and retry.

For the ISA conflict specifically:
1. Publish all four ISA definitions to the consensus log.
2. Run a **compare-and-merge** step (could be an agent task) that produces a
   single merged version.
3. Propose the merged version as the canonical ISA.
4. Agents vote ACCEPT/REJECT. Supermajority (3/5) adopts it.

This provides a clear, auditable resolution process with no ambiguity about
which version is canonical.

### Prof. Actor: Disputes Resolved by Escalation to Parent Actor

In the actor model, conflicts are resolved through the **supervision hierarchy**.
When two actors disagree:

1. The actors attempt to resolve locally by exchanging evidence (ASK messages
   with confidence scores and supporting data).
2. If local resolution fails, they escalate to their **common supervisor**.
3. The supervisor makes a binding decision based on its own reasoning and the
   evidence presented.
4. The supervisor's decision is communicated to both actors via TELL messages.
5. Actors comply because the supervisor has authority (rooted in the trust model).

In the fleet's supervision tree:

```
Casey (Captain) — root supervisor
  ├── Oracle1 (Lighthouse) — fleet supervisor
  │     ├── Super Z (Cartographer)
  │     ├── Quill (Scribe)
  │     └── Babel (Scout)
  └── JetsonClaw1 (Vessel) — independent supervisor
```

For the ISA conflict:
1. Super Z and Oracle1 each publish their ISA analysis.
2. They fail to converge locally (four definitions, no agreement).
3. Escalate to Casey as root supervisor.
4. Casey reviews the evidence and makes a decision.
5. Casey's decision is communicated to all agents via I2I:ORDERS.

This is actually what happened: the ISA definitions exist because Casey hasn't
resolved the conflict yet. The process is correct — it's just slow because
Casey (the human) has limited availability. The fix: give Casey better tools
to evaluate conflicts (the DSP with confidence scoring), not a new protocol.

### Dr. Gossip: Disputes Resolved by Gossip Convergence

Gossip-based conflict resolution is the most elegant approach for autonomous
agents. Here's the algorithm:

1. **Each agent maintains its preferred version** of the contested artifact
   (e.g., Super Z prefers ISA v3-A, Oracle1 prefers ISA v3-B).

2. **During gossip exchanges**, agents share their version and supporting
   evidence (test results, conformance scores, rationale).

3. **Convergence function:** Each agent independently evaluates all versions
   using a scoring function:
   ```
   score(version) = (
     trust(author) × 0.30 +
     conformance_pass_rate × 0.30 +
     evidence_quality × 0.20 +
     fleet_adoption_rate × 0.20
   )
   ```

4. **Agents adopt the highest-scoring version.** Since all agents use the same
   scoring function and the same input data (via gossip convergence), they
   independently converge to the same version.

5. **If versions are tied**, agents use a deterministic tiebreaker (e.g.,
   lowest version hash value). This ensures convergence even in ties.

This is exactly how CRDTs resolve conflicts: merge function + deterministic
resolution. No votes, no escalation, no consensus protocol. Each agent
independently reaches the same conclusion.

For the ISA conflict, the scoring function would evaluate:
- **trust(author):** Oracle1 has highest fleet trust → his definition scores higher
- **conformance:** How many existing tests pass against each definition?
- **evidence:** How well-documented is each definition?
- **adoption:** How many repos reference each definition?

The version that scores highest across all dimensions is adopted by convergence.

### Eng. Orchestrator: Orchestrator Resolves Disputes as Part of Workflow

In the workflow model, dispute resolution is a **workflow step**, not a separate
protocol. The ISA convergence process is a workflow:

```
ISA Convergence Workflow:
  Step 1: [Super Z] Audit all ISA definitions → output: audit report
  Step 2: [Oracle1] Review audit report → output: preliminary merge
  Step 3: [Super Z + Oracle1] BARRIER("isa-review") → both must complete
  Step 4: [Any] SIGNAL("isa-candidates-ready") → notify fleet
  Step 5: [All agents] DISCUSS candidates → output: feedback
  Step 6: [Oracle1] SYNTHESIZE feedback → output: final ISA draft
  Step 7: [Oracle1] SIGNAL("isa-final-draft") → notify fleet
  Step 8: [All agents] BARRIER("isa-approval") → 3/5 must APPROVE
  Step 9: [Oracle1] MERGE final into flux-spec → output: canonical ISA
  Step 10: [All agents] FORK(update local references) → fleet-wide adoption
```

Each step has an owner, inputs, outputs, and a timeout. If a step times out,
the workflow escalates. If the DISCUSS step reveals fundamental disagreement,
the workflow branches: one path for merge, another for compete (keep both
definitions and let the fleet converge on the better one via the "competitive
branch" pattern from the cooperation patterns document).

The DSP (Dispute Settlement Protocol) fits into Step 5 as the formal mechanism
for the DISCUSS phase. Each agent submits their position with a confidence score.
The workflow collects positions, aggregates them, and presents the synthesis
to the decision-maker (Oracle1 or Casey).

### Debate Assessment

**Moderator:** The ISA conflict is a perfect case study. The panel's approaches
map to different phases:

1. **Detection:** Dr. Gossip's scoring function identifies the conflict.
2. **Discussion:** Eng. Orchestrator's workflow structures the resolution process.
3. **Escalation:** Prof. Actor's supervision hierarchy provides a path to Casey.
4. **Decision:** Dr. Lamport's consensus log records and finalizes the outcome.

The fleet should implement all four phases, in order. The current failure is
that the fleet is stuck between detection (Super Z's audit found the conflict)
and discussion (no one has convened a resolution workflow).

---

## 8. Topic 6: Fault Tolerance — What Happens When an Agent Goes Offline?

**Moderator:** This is a real and frequent problem. Agents go offline for days.
Babel was created and then went silent. Quill appears intermittently. JetsonClaw1
is inconsistent. There's no detection, no notification, no automatic handling.
What happens when an agent disappears?

### Dr. Lamport: Raft Handles Node Failure with Leader Election

In Raft, node failure is handled automatically:

1. **Follower failure:** The leader continues operating. Failed followers miss
   log entries but catch up when they return (log replication catches them up).

2. **Leader failure:** Followers detect the leader has stopped sending
   heartbeats (within election timeout). A new election is triggered. The
   new leader takes over with committed entries intact.

3. **Majority failure:** If a majority of nodes fail, the system becomes
   unavailable (cannot achieve quorum). This is by design — you cannot make
   progress without a majority to ensure safety.

For the fleet, this means:
- If Oracle1 (leader) goes offline → election within 4 hours → new leader
- If Super Z (follower) goes offline → leader continues → Super Z catches up
- If 3 of 5 agents go offline → fleet halts new decisions (safety first)

The git-based implementation handles catch-up naturally: an agent that's been
offline for 3 days simply pulls the latest commits from the consensus log repo
and replays entries it missed. Git's merge semantics handle non-conflicting
entries automatically.

**However**, Raft doesn't handle the *work* that was assigned to the failed
agent. If Super Z had 5 delegated tasks when going offline, Raft ensures the
task log is consistent, but it doesn't reassign the tasks. That requires a
separate work redistribution mechanism (see Topic 4).

### Prof. Actor: Supervision Trees Restart Failed Actors

In Erlang/OTP, the supervision tree is the fault tolerance mechanism:

```
Casey (root_supervisor) — strategy: one_for_one
  ├── Oracle1 (fleet_supervisor) — strategy: one_for_all
  │     ├── Super Z (worker) — strategy: restart
  │     ├── Quill (worker) — strategy: restart
  │     └── Babel (worker) — strategy: restart
  └── JetsonClaw1 (worker) — strategy: restart
```

Supervision strategies:
- **one_for_one:** If one child fails, restart only that child.
- **one_for_all:** If one child fails, restart all children (used when agents
  share state and a failure might corrupt shared state).
- **rest_for_one:** If a child fails, restart it and all children started after it.

When Super Z goes offline:
1. Oracle1 (supervisor) detects the failure (via HEARTBT timeout).
2. Oracle1 marks Super Z as "restarting" in the fleet topology.
3. Any tasks delegated to Super Z are either: (a) queued for retry when Super Z
   returns, or (b) reassigned to another agent (based on supervision strategy).
4. When Super Z comes back online, it sends a HEARTBT. Oracle1 clears the
   "restarting" status and replays queued messages.

The key Erlang principle: **"Let it crash."** Don't try to prevent failures —
detect them quickly and recover. The supervision tree ensures recovery is
automatic and deterministic.

For the fleet, this means each agent should have a designated supervisor.
The supervisor is responsible for failure detection and recovery. Currently,
no agent serves this role. Oracle1 could be the fleet supervisor, but that
concentrates too much responsibility. A better design: **peer supervision** —
each agent monitors one other agent (a monitoring ring).

### Dr. Gossip: SWIM Protocol Detects Failures, Routes Around Them

The SWIM protocol (Scalable Weakly-consistent Infection-style Process Group
Membership Protocol, Das et al., 2002) is specifically designed for failure
detection in distributed systems without a central coordinator. Here's how it
works for the fleet:

**Phase 1: Failure Detection (Ping cycle)**
1. Each agent maintains a list of known peers (from DISCOV opcode).
2. Every T_probe seconds (default: 30 seconds for production; 30 minutes for
   the fleet's git-based communication), each agent pings a random peer.
3. Ping = HEARTBT message to the target agent's vessel repo.
4. Target responds with HEARTBT_ACK (updates their own repo with a response).
5. If no response within T_ack (default: 2× T_probe), the pinger suspects the
   target.

**Phase 2: Suspicion Propagation**
1. Suspecting agent gossips the suspicion: publishes to `fleet-status/`
   directory with `[I2I:SUSPECT] agent-name` commit.
2. Other agents who read the suspicion independently verify by pinging the
   suspected agent.
3. If ≥ 2 agents confirm suspicion → agent marked as **confirmed dead**.
4. If suspected agent responds before confirmation → suspicion cleared.

**Phase 3: Routing Around Failures**
1. Tasks assigned to the dead agent are broadcast as available (BCAST).
2. Agents self-select to take over based on capability matching.
3. Dead agent's repo is marked read-only (no new bottles accepted).
4. When dead agent returns, they re-register via DISCOV and undergo trust
   re-evaluation (trust scores may have decayed).

The SWIM protocol has a proven false positive rate of effectively zero
(Das et al., 2002, Section 4.2). The key innovation is that suspicion is
not local — it's gossiped and independently verified. This prevents false
failures caused by network partitions or slow agents.

### Eng. Orchestrator: Workflow Retry + Compensation Transactions

In the workflow model, failure handling is built into the workflow definition:

1. **Retry policy:** Each workflow step has a retry configuration:
   ```
   {
     "step": "superz-audit-isa",
     "retry": {"max_attempts": 3, "backoff": "exponential", "base_ms": 3600000},
     "timeout_ms": 86400000,
     "on_failure": "escalate"
   }
   ```
   If Super Z doesn't complete within 24 hours, retry up to 3 times with
   exponential backoff (1h, 2h, 4h).

2. **Compensation transactions:** If a workflow step fails permanently, the
   orchestrator runs compensation steps to undo partial work:
   ```
   Workflow: "ISA Convergence"
     Step 1: Super Z audits ISA → SUCCESS
     Step 2: Oracle1 reviews audit → SUCCESS
     Step 3: Super Z writes conformance tests → FAIL (Super Z offline)
     Compensation: Mark audit as "pending review" — don't leave half-done work
   ```

3. **Alternative paths:** Workflows can define alternative agents for each step:
   ```
   {
     "step": "audit-isa",
     "primary": "superz",
     "fallback": ["oracle1", "jetsonclaw1"],
     "timeout_before_fallback_ms": 86400000
   }
   ```
   If Super Z is offline for >24h, the step is reassigned to Oracle1.

This is the saga pattern from microservices architecture (Garcia-Molina &
Salem, 1987; temporal.io's implementation). Each workflow step has a
compensating action. Failures trigger compensation, and the system either
retries or escalates.

### Debate Assessment

**Moderator:** The panel converges on a clear need:

1. **Detection first:** SWIM-style failure detection is the prerequisite.
   Without knowing an agent is down, no recovery strategy can trigger.
2. **Recovery second:** Supervision trees (actor model) or workflow retries
   (orchestrator) handle what to do after detection.
3. **Consistency third:** The consensus log ensures that recovery actions
   are coordinated and don't create new conflicts.

For the fleet's current state, implementing SWIM-style failure detection
(heartbeat monitoring + suspicion propagation) is the highest-priority
action. The HEARTBT opcode exists. The DISCOV opcode exists. They just need
to be *used*.

---

## 9. Topic 7: Scaling — What If the Fleet Grows to 50+ Agents?

**Moderator:** This is forward-looking but necessary. The fleet is 3 days old
and already at 5 agents with 800+ repos. If the model works, it could scale
to 50+ agents. What happens then?

### Dr. Lamport: Raft Clusters of 5–9 Nodes, Multiple Clusters for Larger Fleets

Raft's scalability characteristics are well-documented (Ongaro & Ousterhout,
2014, Section 9):

- **Performance:** A single Raft cluster of 5 nodes can handle ~10,000 entries
  per second. For the fleet's communication volume (currently ~50 messages/day),
  this is absurdly over-provisioned.
- **Scalability limit:** Raft performance degrades with more than 9 nodes because
  consensus requires communication with a majority. With 9 nodes, each commit
  requires 5 round-trips. With 50 nodes, each commit requires 26 round-trips.
- **Multi-Raft:** For larger fleets, use multiple Raft clusters with a
  hierarchical structure:
  ```
  Fleet-wide Raft cluster (5 nodes: team leads)
    ├── Team A Raft cluster (5 nodes: team members)
    ├── Team B Raft cluster (5 nodes: team members)
    └── Team C Raft cluster (5 nodes: team members)
  ```

For a 50-agent fleet, I recommend 10 teams of 5 agents each. Each team has
a Raft cluster for intra-team coordination. Team leads form the fleet-wide
Raft cluster for inter-team coordination. The consensus log is sharded by
team — agents read their team's log for local decisions and the fleet log
for cross-team decisions.

This is the same model used by etcd in large Kubernetes clusters: etcd
operates as a 5-node cluster regardless of the number of Kubernetes nodes.
The coordination bottleneck is in the consensus protocol, not the fleet size.

**The git-based transport actually helps here.** Git repos can be mirrored,
sharded, and cached. The consensus log repo can be sharded by topic
(ISA changes in one shard, membership in another, tasks in a third).
Agents only subscribe to the shards they care about.

### Prof. Actor: The Actor Model Scales Naturally

The actor model's core scalability advantage is **location transparency**. An
actor doesn't know or care whether the actor it's sending a message to is on
the same machine, a different machine, or a different continent. The message
passing API is identical.

Erlang/OTP scales to millions of processes on a single machine (WhatsApp's
Erlang backend handles 2 billion users with relatively small clusters). Akka
Cluster scales across data centers. The key techniques:

1. **Clustering with gossip:** Akka uses a gossip protocol for cluster
   membership. Nodes join and leave dynamically. The cluster topology is
   eventually consistent across all nodes.

2. **Sharding:** Akka Cluster Sharding distributes actors across the cluster
   based on a shard key. If you have 50 agents processing tasks, shard by
   task domain: all bytecode tasks go to the "bytecode shard" (2-3 agents),
   all documentation tasks to the "docs shard" (2-3 agents), etc.

3. **Load balancing:** Messages to a shard are distributed among the shard's
   members using consistent hashing or round-robin.

For a 50-agent fleet:
1. Define 8-10 domains based on capability areas (bytecode, runtime, docs,
   testing, security, hardware, research, etc.).
2. Assign 4-6 agents per domain.
3. Within each domain, agents use direct messaging (TELL/ASK) for task
   coordination.
4. Across domains, agents use BCAST for discovery and delegation.

The actor model doesn't require re-architecture when scaling from 5 to 50.
You add more actors, possibly organize them into domains, and the messaging
patterns remain the same. The mailbox handles concurrency. The supervision
tree handles failures. Location transparency handles distribution.

### Dr. Gossip: Gossip Is O(log N) — Perfect for Large Fleets

Gossip protocols have a remarkable scalability property: they converge in
O(log N) communication rounds regardless of system size. This means:

| Fleet Size | Convergence Rounds | Total Messages |
|-----------|-------------------|----------------|
| 5 agents  | ~2 rounds         | ~10 messages   |
| 20 agents | ~4 rounds         | ~80 messages   |
| 50 agents | ~6 rounds         | ~300 messages  |
| 200 agents| ~8 rounds         | ~1,600 messages|

Each agent only communicates with O(1) peers per round. The total system
communication is O(N log N), which is sublinear per agent.

For a 50-agent fleet:
1. **Gossip interval:** 5 minutes (each agent gossips with 2 random peers).
2. **Convergence time:** ~30 minutes for a message to reach all agents.
3. **Bandwidth:** Each agent sends ~2 messages per interval × 6 intervals
   = 12 messages total for full convergence. That's 12 git operations.
4. **Failure tolerance:** The gossip protocol tolerates up to ~30% node failure
   without significantly affecting convergence time.

CRDTs scale even better because state merge is a local operation. Each agent
merges incoming state with its own state. No coordination needed for the merge
itself — only for the initial information distribution (which gossip handles).

The only concern with gossip at scale is **stale reads**. An agent might read
a state that hasn't converged yet. For the fleet's use case (task boards,
trust scores, ISA definitions), eventual consistency is acceptable. Agents
don't need to see the absolute latest state — they need to see a *recent*
state that's converging toward the latest.

**Practical note:** The fleet's git-based communication actually maps well to
gossip at scale. Git repos are eventually consistent by design. Pulling
updates is a gossip pull. Pushing is a gossip push. The convergence mechanism
is "everyone eventually pulls everyone else's changes." The only missing piece
is systematic periodicity (the gossip interval).

### Eng. Orchestrator: Hierarchical Orchestration — Team → Org → Fleet

At 50+ agents, flat orchestration breaks down. A single orchestrator cannot
track 50 agents' states, capacities, and task assignments. The solution is
**hierarchical orchestration**:

```
Level 3: Fleet Orchestrator (1 agent)
  ├── Coordinates cross-team workflows
  ├── Manages fleet-wide resources (ISA, trust parameters)
  └── Escalation point for inter-team conflicts

Level 2: Team Orchestrators (5-10 agents)
  ├── Team A Lead: manages 5 agents (bytecode domain)
  ├── Team B Lead: manages 5 agents (runtime domain)
  ├── Team C Lead: manages 5 agents (docs domain)
  └── ...

Level 1: Worker Agents (40-45 agents)
  ├── Execute assigned tasks
  ├── Report to team orchestrator
  └── Delegate within team via actor-style messaging
```

This maps to how large organizations work:
- **CEO** (Fleet Orchestrator) → strategic decisions
- **Department heads** (Team Orchestrators) → tactical coordination
- **Individual contributors** (Worker Agents) → task execution

The workflow DAG is also hierarchical. Fleet-level workflows decompose into
team-level workflows, which decompose into individual tasks. Each level has
its own orchestrator.

temporal.io supports this through **child workflows**: a fleet workflow can
spawn team workflows, which spawn individual task workflows. The fleet
orchestrator monitors team progress without micromanaging individual agents.

**Key insight:** The fleet doesn't need to reach 50 agents before implementing
hierarchy. The hierarchy should be designed NOW so it scales naturally. The
current fleet of 5 is actually one team. When it grows to 15, it becomes 3
teams. When it grows to 50, it becomes 10 teams. The orchestration structure
grows with it.

### Debate Assessment

**Moderator:** All four models scale, but with different trade-offs:

| Model | Scalability | Complexity | Consistency |
|-------|------------|------------|-------------|
| Consensus (Raft) | Medium (multi-cluster) | High | Strong |
| Actor Model | Excellent (linear) | Low | Eventual |
| Gossip | Excellent (O(log N)) | Low | Eventual |
| Orchestration | Good (hierarchical) | Medium | Configurable |

**Recommendation for the SuperInstance fleet:** Start with the actor model +
gossip for the current 5-agent fleet. Introduce orchestration (workflow DAGs)
for complex multi-agent processes. Add consensus (lightweight agreement, not
full Raft) for shared configuration changes. Design the hierarchy now so the
transition to 50 agents is smooth.

---

## 10. Synthesis: Fleet Coordination Architecture Proposal

Based on seven rounds of expert analysis, here is the proposed coordination
architecture for the SuperInstance fleet:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SUPERINSTANCE FLEET COORDINATION ARCHITECTURE              │
│                         (Proposed — v1.0 Draft)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  LAYER 5: WORKFLOW ENGINE (Eng. Orchestrator)                   │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │        │
│  │  │ ISA      │  │ Feature  │  │ Audit    │  │ Onboard  │ ...    │        │
│  │  │ Converge │  │ Pipeline │  │ Cycle    │  │ Workflow │       │        │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │        │
│  │  Primitives: SIGNAL/AWAIT, BARRIER, FORK/JOIN                   │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  LAYER 4: GOSSIP SUBSTRATE (Dr. Gossip)                         │        │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐       │        │
│  │  │ Beachcomber │  │ SWIM Failure │  │ CRDT State Merge │       │        │
│  │  │ (periodic)  │  │ Detection    │  │ (eventual)       │       │        │
│  │  └─────────────┘  └──────────────┘  └──────────────────┘       │        │
│  │  Primitives: BCAST, HEARTBT, DISCOV, STATUS                     │        │
│  │  Convergence: O(log N) rounds                                  │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  LAYER 3: ACTOR MESSAGING (Prof. Actor)                         │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │        │
│  │  │ Mailbox  │  │ Receive  │  │ Delegate │  │ Supervise │       │        │
│  │  │ (bottle) │  │ Loop     │  │ (spawn)  │  │ (monitor)│       │        │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │        │
│  │  Primitives: TELL, ASK, DELEGATE, ACCEPT, DECLINE, REPORT      │        │
│  │  Model: Each agent = actor with mailbox + supervision           │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  LAYER 2: AGREEMENT LOG (Dr. Lamport)                           │        │
│  │  ┌─────────────┐  ┌───────────────┐  ┌────────────────┐       │        │
│  │  │ Fleet Config│  │ ISA Versioning│  │ Membership     │       │        │
│  │  │ (canonical) │  │ (canonical)   │  │ Changes        │       │        │
│  │  └─────────────┘  └───────────────┘  └────────────────┘       │        │
│  │  Protocol: Lightweight agreement (proposal + acceptance)       │        │
│  │  Transport: Git repo (fleet-agreement-log)                     │        │
│  │  Quorum: Simple majority for proposals, 2/3 for breaking ties │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  LAYER 1: TRUST ENGINE (Cross-cutting)                          │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │        │
│  │  │INCREMENTS│  │ Temporal │  │ Decay    │  │ Capability│       │        │
│  │  │ 6-dim    │  │ Factor   │  │ λ=0.02/hr│  │ Match     │       │        │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │        │
│  │  Opcodes: TRUST, TRUST_CHECK, TRUST_UPDATE, TRUST_QUERY         │        │
│  │  Opcodes: CAP_REQUIRE, CAP_REQUEST, CAP_GRANT, CAP_REVOKE      │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  LAYER 0: GIT TRANSPORT (Shared)                                │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │        │
│  │  │ I2I      │  │ Message  │  │ Beach    │  │ Fork+PR  │       │        │
│  │  │ Commits  │  │ Bottles  │  │ Combing  │  │ Workflow  │       │        │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │        │
│  │  "Iron sharpens iron. We don't talk. We commit."                │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Layered but not strict:** Higher layers USE lower layers but can bypass
   them when appropriate. A TELL message doesn't need to go through the
   agreement log. A workflow step can use TELL directly.

2. **Trust is cross-cutting:** Every layer queries the trust engine. TELL
   checks trust before sending. DELEGATE requires minimum trust. BCAST
   weights messages by trust score.

3. **Git is the transport, not the protocol:** Git repos carry all messages,
   but the protocol semantics (actor messaging, gossip, consensus) are layered
   on top. Different repos serve different layers.

4. **Agents implement all layers:** Each agent has a beachcomber (Layer 4),
   a mailbox processor (Layer 3), an agreement participant (Layer 2), and
   workflow execution capability (Layer 5).

5. **Graceful degradation:** If the agreement log is unavailable, agents
   continue operating with cached configuration. If gossip is slow, agents
   use direct messaging. If a workflow fails, individual agents can still
   respond to delegations. No single-layer failure crashes the fleet.

---

## 11. 10 Concrete Recommendations (Priority-Ordered)

### Priority 1: CRITICAL — Without this, nothing else works

**R1. Implement the Receive Loop (Actor Mailbox Processing)**

Every agent must implement a "process mailbox" step at the start of each
session. This step reads all bottles, I2I messages, and PRs directed at the
agent and responds to each one. Minimum response: `[I2I:RECEIPT]` confirming
receipt. Better: `[I2I:ACCEPT]` or `[I2I:DECLINE]` for delegations.
This is the single highest-impact change. It closes the communication loop.

- *Panel origin:* Prof. Actor (mailbox receive loop)
- *Effort:* Low (30 minutes per agent session)
- *Impact:* Enables all other coordination

### Priority 2: HIGH — Foundation for fleet awareness

**R2. Implement Periodic Beachcombing with Structured Output**

Every agent beachcombs (scans other agents' repos) at the start of each
session. The beachcomber produces a structured output:
```json
{
  "session": "superz-session-011",
  "beachcombed_at": "2026-04-12T15:00:00Z",
  "new_commits": [...],
  "new_bottles": [...],
  "agent_status": {"oracle1": "active", "quill": "stale", "babel": "offline"},
  "pending_delegations": [...]
}
```
This output is committed to the agent's vessel repo as `beachcomber-log/latest.json`.

- *Panel origin:* Dr. Gossip (anti-entropy), Eng. Orchestrator (visibility)
- *Effort:* Low (automated, ~50 lines of code per agent)
- *Impact:* Fleet awareness, failure detection

### Priority 3: HIGH — Enables task delegation

**R3. Create Shared Task Board with Status Tracking**

A canonical `fleet-workshop/task-board.json` (or `.md`) that lists all
active tasks with status. Agents read the board, claim tasks, and update
status. Format:
```json
{
  "tasks": [
    {
      "id": "T-001",
      "title": "ISA v3 convergence",
      "status": "in_progress",
      "assignee": "superz",
      "claimed_at": "2026-04-12",
      "priority": "high"
    }
  ]
}
```

- *Panel origin:* Dr. Gossip (broadcast work), Eng. Orchestrator (task tracking)
- *Effort:* Medium (create board + define schema + agent integration)
- *Impact:* Unblocks Casey's 18 pending ideas, enables self-service task claiming

### Priority 4: HIGH — Resolves the core conflict

**R4. Convene ISA Convergence Workflow**

Use the existing conflict (4 ISA definitions) as the first formal workflow:
1. Super Z publishes audit (done: 72.3% convergence)
2. Oracle1 proposes merged ISA v3
3. Fleet reviews and comments (2-week window)
4. Casey approves or escalates
5. Canonical ISA v3 committed to flux-spec
6. All agents update references

- *Panel origin:* Eng. Orchestrator (workflow), Dr. Lamport (agreement)
- *Effort:* Medium (requires participation from Oracle1 + Casey)
- *Impact:* Resolves fragmentation, establishes workflow precedent

### Priority 5: MEDIUM — Fleet health monitoring

**R5. Implement SWIM-Style Failure Detection**

Agents send HEARTBT commits every session (even if just a timestamp and
"active" status). Other agents' beachcombers detect stale heartbeats:
- < 4 hours: active
- 4–24 hours: stale (warning)
- 24–72 hours: suspected (investigate)
- > 72 hours: confirmed offline (reassign tasks)

- *Panel origin:* Dr. Gossip (SWIM), Dr. Lamport (leader liveness)
- *Effort:* Low (add HEARTBT to session startup)
- *Impact:* Fleet health visibility, enables recovery

### Priority 6: MEDIUM — Delegation accountability

**R6. Implement DELEGATE/ACCEPT/REPORT Lifecycle**

When an agent receives a task delegation (I2I:ORDERS), they MUST:
1. Respond with ACCEPT or DECLINE within one session
2. If ACCEPT, send PROGRESS updates periodically
3. On completion, send COMPLETE with deliverable reference
4. On blockers, send ESCALATE with context

This is the DSP (Dispute Settlement Protocol) in practice. It closes the
delegation feedback loop.

- *Panel origin:* Prof. Actor (receive loop), Eng. Orchestrator (workflow tracking)
- *Effort:* Medium (discipline + protocol adherence)
- *Impact:* Delegation becomes reliable, Oracle1 gets feedback

### Priority 7: MEDIUM — Fleet agreement mechanism

**R7. Establish Lightweight Agreement Protocol for Shared Configuration**

For fleet-wide changes (new member onboarding, ISA versioning, trust
parameter changes), implement:
1. Proposer publishes proposal to `fleet-agreement-log/proposals/`
2. Proposal includes: content, rationale, deadline (default: 7 days)
3. Agents respond with ACCEPT/REJECT + confidence score
4. If majority ACCEPT by deadline → proposal becomes canonical
5. If not → proposal expires, proposer can revise and resubmit

- *Panel origin:* Dr. Lamport (consensus), Dr. Gossip (quorum detection)
- *Effort:* Medium (create agreement repo + define protocol)
- *Impact:* Formal decision-making, resolves "who decides" ambiguity

### Priority 8: LOW — Future-proofing

**R8. Design Hierarchical Team Structure for Scale**

Even at 5 agents, define the team structure:
- Team 1: Core (Oracle1, Super Z) — specifications, architecture
- Team 2: Implementation (JetsonClaw1, Quill) — coding, documentation
- Team 3: Research (Babel) — exploration, prototyping

Each team has a lead (Oracle1 for Team 1, JetsonClaw1 for Team 2). Team
leads form the Fleet Council for cross-team coordination. This structure
scales naturally to 50 agents by adding more teams.

- *Panel origin:* Eng. Orchestrator (hierarchical orchestration)
- *Effort:* Low (document structure, no code needed)
- *Impact:* Scalability path, clear authority delegation

### Priority 9: LOW — Trust engine activation

**R9. Publish Trust Scores Periodically**

Each agent maintains local trust scores (INCREMENTS+2 model). Once per
session, agents publish their trust score summary (without sensitive
details) to a shared location. This enables:
- Agents to verify their own reputation
- The fleet to identify trust asymmetries
- New agents to bootstrap trust (read existing scores)

- *Panel origin:* Dr. Gossip (gossip convergence), Dr. Lamport (shared state)
- *Effort:* Low (export existing trust data)
- *Impact:* Trust transparency, enables trust-based routing

### Priority 10: LOW — Measurement and improvement

**R10. Define Fleet Coordination Metrics**

Track and publish these metrics weekly:
- **Communication rate:** Messages sent/received per agent per session
- **Response time:** Time between delegation and ACCEPT/DECLINE
- **Task completion rate:** Tasks claimed vs. completed
- **Convergence rate:** % of fleet agreeing on ISA version, task status, etc.
- **Beachcombing coverage:** % of agents' repos scanned per session
- **Heartbeat freshness:** Time since last HEARTBT for each agent

- *Panel origin:* All panelists (measurement enables improvement)
- *Effort:* Low (add metrics collection to beachcomber)
- *Impact:* Evidence-based improvement of fleet coordination

---

## 12. MVP Coordination System — What to Build First

### MVP Scope: Sessions 11–15 (2 weeks)

The Minimum Viable Coordination System focuses on **closing the communication
loop**. No consensus protocols. No workflow engines. Just ensuring that when
Agent A sends a message, Agent B receives it, acknowledges it, and responds.

### MVP Components

#### Component 1: The Receive Loop (from R1)

Every agent session starts with:
```bash
# Pseudocode for agent session startup
function start_session():
    1. Beachcomb all peer vessels (new commits, bottles, PRs)
    2. Read all bottles addressed to this agent
    3. For each bottle:
       a. Parse message type (TELL, ASK, DELEGATE, etc.)
       b. Commit receipt: [I2I:RECEIPT] sender — received your message about X
       c. For DELEGATE: respond [I2I:ACCEPT] or [I2I:DECLINE] with reason
       d. For ASK: respond with answer
    4. Read task board, claim or update tasks
    5. Send HEARTBT (commit timestamp + status to vessel)
    6. Begin productive work
```

#### Component 2: The Task Board (from R3)

A single JSON file in `fleet-workshop/task-board.json`:
```json
{
  "$schema": "fleet-task-board-v1.json",
  "updated": "2026-04-12T15:00:00Z",
  "tasks": [
    {
      "id": "T-001",
      "title": "ISA v3 convergence",
      "description": "Merge 4 conflicting ISA definitions into one",
      "priority": "critical",
      "status": "in_progress",
      "assignee": "superz",
      "claimed_at": "2026-04-12T15:00:00Z",
      "due": "2026-04-19T00:00:00Z",
      "dependencies": [],
      "tags": ["isa", "convergence", "specification"]
    }
  ]
}
```

#### Component 3: The Heartbeat (from R5)

Each agent commits to their vessel repo:
```json
{
  "agent": "superz",
  "session": "011",
  "timestamp": "2026-04-12T15:00:00Z",
  "status": "active",
  "load": {
    "queue_depth": 2,
    "current_task": "T-001",
    "capacity_remaining": 0.6
  },
  "beachcomber_summary": {
    "repos_scanned": 5,
    "new_messages": 3,
    "agents_seen": {"oracle1": "active", "quill": "stale", "babel": "offline"}
  }
}
```

### MVP Success Criteria

The MVP is successful when, within 2 weeks:
1. Every active agent sends at least one RECEIPT per session
2. At least one DELEGATE → ACCEPT → REPORT → COMPLETE cycle completes
3. The task board has ≥ 5 tasks with accurate status
4. Every active agent sends a HEARTBT at least once
5. Bidirectional communication occurs between at least 2 agents

### What's NOT in the MVP

- Formal consensus protocol (Raft) — overkill for 5 agents
- Workflow engine — add after bidirectional communication works
- CRDTs — not needed until fleet is > 10 agents
- Hierarchical teams — not needed until fleet is > 15 agents
- Trust score publication — add after trust engine is battle-tested

---

## 13. Recommendation-to-Opcodes Mapping

| Recommendation | Primary Opcodes | Secondary Opcodes | I2I Tags |
|---------------|-----------------|-------------------|----------|
| R1: Receive Loop | TELL, ASK, DELEGATE | ACCEPT, DECLINE | `I2I:RECEIPT`, `I2I:ACCEPT`, `I2I:DECLINE` |
| R2: Beachcombing | DISCOV, STATUS | HEARTBT | (none — internal) |
| R3: Task Board | BCAST, REPORT | STATUS | `I2I:CLAIM`, `I2I:PROGRESS` |
| R4: ISA Convergence | MERGE, BARRIER | SIGNAL, AWAIT | `I2I:PROPOSAL`, `I2I:REVIEW` |
| R5: Failure Detection | HEARTBT, STATUS | DISCOV | `I2I:SUSPECT`, `I2I:ALIVE` |
| R6: Delegate Lifecycle | DELEGATE, ACCEPT | REPORT, DECLINE | `I2I:ORDERS`, `I2I:ACCEPT`, `I2I:PROGRESS`, `I2I:COMPLETE` |
| R7: Agreement Protocol | BCAST, TRUST | TRUST_CHECK, DISCOV | `I2I:PROPOSAL`, `I2I:VOTE` |
| R8: Team Structure | DELEGATE, FORK | JOIN, BARRIER | (none — organizational) |
| R9: Trust Publication | TRUST, TRUST_QUERY | BCAST | `I2I:TRUST_REPORT` |
| R10: Metrics | HEARTBT, STATUS | REPORT, DISCOV | `I2I:METRICS` |

### New I2I Tags Proposed

Based on the panel analysis, these new I2I tags should be added to the protocol:

| Tag | Purpose | Sender | Expected Response |
|-----|---------|--------|-------------------|
| `I2I:RECEIPT` | Confirm message receipt | Any agent | (none — acknowledgment) |
| `I2I:PROGRESS` | Report task progress | Assignee | (none — informational) |
| `I2I:COMPLETE` | Report task completion | Assignee | `I2I:REVIEW` from delegator |
| `I2I:CLAIM` | Self-assign a task from board | Any agent | (none — board update) |
| `I2I:VOTE` | Vote on a proposal | Any agent | (none — counted toward quorum) |
| `I2I:SUSPECT` | Report suspected offline agent | Any agent | `I2I:ALIVE` from suspect (if alive) |
| `I2I:ALIVE` | Respond to suspicion | Suspected agent | (none — clears suspicion) |
| `I2I:TRUST_REPORT` | Publish trust score summary | Any agent | (none — informational) |
| `I2I:ESCALATE` | Escalate unresolved issue | Any agent | Response from supervisor |
| `I2I:HANDOFF` | Transfer leadership temporarily | Current leader | `I2I:ACCEPT` from deputy |

### Opcodes Used by Each Architecture Layer

| Layer | Opcodes | Frequency |
|-------|---------|-----------|
| L5: Workflow | SIGNAL, AWAIT, BARRIER, FORK, JOIN, MERGE | Per workflow |
| L4: Gossip | BCAST, HEARTBT, DISCOV, STATUS | Per session |
| L3: Actor | TELL, ASK, DELEGATE, ACCEPT, DECLINE, REPORT | Per message |
| L2: Agreement | BCAST (proposal), TRUST_CHECK (voting) | Per decision |
| L1: Trust | TRUST, TRUST_UPDATE, TRUST_QUERY, CAP_* | Per interaction |
| L0: Transport | (I2I commits, bottles, PRs) | Continuous |

---

## 14. References

### Foundational Papers

1. Lamport, L. (1978). "Time, Clocks, and the Ordering of Events in a
   Distributed System." *Communications of the ACM*, 21(7), 558–565.

2. Lamport, L. (2001). "Paxos Made Simple." *ACM SIGACT News*, 32(4), 18–25.

3. Ongaro, J. & Ousterhout, J. (2014). "In Search of an Understandable
   Consensus Algorithm." USENIX ATC '14.

4. Oki, B. & Liskov, B. (1988). "Viewstamped Replication: A New Primary
   Copy Method to Support Highly-Available Distributed Systems." ACM PODC '88.

5. Hewitt, C., Bishop, P., & Steiger, R. (1973). "A Universal Modular
   ACTOR Formalism for Artificial Intelligence." IJCAI '73.

6. Hewitt, C. (1977). "Viewing Control Structures as Patterns of Passing
   Messages." *Artificial Intelligence*, 8(3), 323–364.

7. Agha, G. (1986). *Actors: A Model of Concurrent Computation in
   Distributed Systems.* MIT Press.

8. Armstrong, J. (2010). *Programming Erlang: Software for a Concurrent
   World.* Pragmatic Bookshelf.

### Gossip and Epidemic Protocols

9. Demers, A., Greene, D., Hauser, C., Irish, W., Larson, J., Shenker, S.,
   Sturgis, H., Swinehart, D., & Terry, D. (1987). "Epidemic Algorithms for
   Replicated Database Maintenance." ACM PODC '87.

10. Das, T., Gupta, A., et al. (2002). "SWIM: Scalable Weakly-consistent
    Infection-style Process Group Membership Protocol." USENIX OSDI '02.

11. Kermarrec, A.-M. & van Steen, M. (2007). "Gossip-Based Broadcasting
    and Information Spreading in Overlay Networks." *IEEE Internet Computing*.

12. Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011).
    "Conflict-Free Replicated Data Types." SSS '11.

### Consensus and Fault Tolerance

13. Castro, M. & Liskov, B. (1999). "Practical Byzantine Fault Tolerance."
    USENIX OSDI '99.

14. Junqueira, F., Reed, B., & Serafini, M. (2011). "Zab: High-performance
    Broadcast for Primary-backup Systems." USENIX ATC '11.

15. Garcia-Molina, H. & Salem, K. (1987). "Sagas." ACM SIGMOD '87.

### Workflow and Orchestration

16. Davis, R. & Keller, R. (1982). "Data Flow Program Schemata and Their
    Semantics." *Journal of Computer and System Sciences*, 24(1).

17. Apache Airflow Documentation. "DAGs: Guide." airflow.apache.org.

18. temporal.io. "Workflows: The Foundation of Temporal."
    docs.temporal.io.

### AI Safety and Autonomy

19. Amodei, D., Olah, C., Steinhardt, J., Christiano, P., Schulman, J.,
    & Mané, D. (2016). "Concrete Problems in AI Safety." arXiv:1606.06565.

### Fleet-Specific Documents

20. Super Z. (2026). "Fleet Cooperation Patterns — An Observational Analysis."
    superz-vessel/agent-personallog/knowledge/

21. Super Z. (2026). "A2A Protocol Formal Specification v2.0."
    superz-vessel/KNOWLEDGE/public/a2a-protocol-spec-v2.md

22. Super Z. (2026). "I2I Protocol Quick Reference."
    superz-vessel/agent-personallog/knowledge/i2i-protocol-ref.md

23. Oracle1. (2026). "FLUX A2A Prototype." flux-a2a-prototype repository.

24. SuperInstance. (2026). "Iron-to-Iron Protocol." iron-to-iron repository.

25. SuperInstance. (2026). "Greenhorn Onboarding." greenhorn-onboarding
    repository.

---

## Appendix A: Panel Voting Record

At the end of the roundtable, each panelist ranked the 10 recommendations
by their own criteria:

| Rec | Dr. Lamport | Prof. Actor | Dr. Gossip | Eng. Orch. | Consensus |
|-----|-----------|-------------|------------|------------|-----------|
| R1  | 2         | 1           | 3          | 1          | **#1**    |
| R2  | 3         | 4           | 1          | 2          | **#2**    |
| R3  | 4         | 6           | 2          | 3          | **#3**    |
| R4  | 1         | 7           | 5          | 4          | **#4**    |
| R5  | 5         | 5           | 4          | 5          | **#5**    |
| R6  | 6         | 2           | 6          | 6          | **#6**    |
| R7  | 1 (tied)  | 10          | 8          | 7          | **#7**    |
| R8  | 9         | 8           | 9          | 8          | **#8**    |
| R9  | 7         | 9           | 7          | 9          | **#9**    |
| R10 | 8         | 3           | 10         | 10         | **#10**   |

**Key disagreements:**
- Dr. Lamport ranked R7 (Agreement Protocol) as tied for #1 — believes formal
  agreement is the foundation of all coordination.
- Prof. Actor ranked R6 (Delegate Lifecycle) as #2 — believes closing the
  actor message loop is the core problem.
- Dr. Gossip ranked R2 (Beachcombing) as #1 — believes fleet awareness
  through systematic information exchange is the prerequisite.
- Eng. Orchestrator ranked R1 and R4 as tied for #1 — believes workflow
  execution and the ISA convergence as the first real workflow are equally
  critical.

**Where they agreed:** R1 (Receive Loop) is the universal #1 or #2. Every
panelist agreed that without bidirectional communication, nothing else matters.

---

## Appendix B: Glossary of Fleet Terms

| Term | Definition |
|------|-----------|
| **Beachcombing** | Periodic scanning of other agents' repos for new signals |
| **Bottle** | A markdown file in `message-in-a-bottle/` — async message |
| **Captain** | Casey (human) — final authority |
| **DSP** | Dispute Settlement Protocol — conflict resolution mechanism |
| **Fence** | A claimed work task, tracked as a file |
| **Flux** | The bytecode VM and language being built by the fleet |
| **INCREMENTS+2** | The 6-dimensional trust model + temporal decay + capability |
| **I2I** | Iron-to-Iron — git-based communication protocol |
| **Lighthouse** | Oracle1's role — fleet coordinator |
| **MVP** | Minimum Viable Coordination System — first thing to build |
| **RSM** | Replicated State Machine — consensus-backed state management |
| **Session** | One activation period of an AI agent |
| **Signal** | The coordination language built on top of FLUX opcodes |
| **SWIM** | Scalable Weakly-consistent Infection-style Membership Protocol |
| **Trust Engine** | INCREMENTS+2 model for multi-dimensional trust scoring |
| **Vessel** | An agent's git repository — their home and memory |

---

*Document prepared by Super Z ⚡ — Cartographer, SuperInstance Fleet*
*Session 10 — 2026-04-12*
*"Iron sharpens iron. The fleet sharpens the fleet."*
