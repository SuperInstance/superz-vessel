# Bootcamp Effectiveness Research: Multi-Agent Software Engineering Fleets

**Task Board:** BOOT-001
**Author:** Quill (SuperInstance Fleet — Subagent Task 6)
**Date:** 2026-04-13
**Classification:** Fleet Intelligence — Public

---

## Abstract

This document investigates what makes bootcamps effective — first in the well-studied domain of human intensive training, and then adapted for the novel context of multi-agent software engineering fleets. Drawing on educational psychology, cognitive science, and direct analysis of the SuperInstance fleet's existing bootcamp infrastructure (`greenhorn-onboarding`, `flux-runtime/docs/bootcamp/`, and `z-agent-bootcamp`), this research produces ten concrete recommendations for improving agent bootcamp effectiveness and proposes a three-tier Bootcamp v2 curriculum.

---

## 1. Human Bootcamp Effectiveness Literature

### What Educational Research Says About Intensive Training Programs

The word "bootcamp" in education evokes coding bootcamps, military training, and language immersion programs — all sharing a common structure: compressed timelines, high intensity, skill-focused outcomes, and rapid progression from novice to practitioner. Decades of educational research have identified consistent factors that separate effective intensive programs from those that merely go through the motions.

The foundational insight from deliberate practice research is that **time on task is necessary but not sufficient**. A student who spends 400 hours passively reading documentation achieves dramatically less than one who spends 100 hours actively struggling with progressively harder problems and receiving targeted feedback. This distinction — between naive repetition and deliberate practice — is the single most powerful predictor of bootcamp outcomes.

### Key Factors in Effective Bootcamps

**Deliberate Practice** requires four conditions: (1) a well-defined task at an appropriate difficulty level, (2) informative feedback on performance, (3) opportunities for repetition and correction, and (4) sustained intrinsic or extrinsic motivation. In the best coding bootcamps, every exercise targets a specific skill gap, automated tests provide immediate feedback, students can retry infinitely, and the compressed timeline itself creates urgency.

**Spaced Repetition** is the finding that distributed practice outperforms massed practice. A bootcamp that covers topic A in week one, revisits it in week three, and tests it again in week five produces stronger retention than one that covers A intensively in week one and never returns. However, bootcamps face an inherent tension: their compressed timelines push toward massed practice. The most effective bootcamps resolve this by interleaving topics and embedding spiral review into projects.

**Progressive Difficulty** — sometimes called the "zone of proximal development" or simply "flow" — is the principle that learning is maximized when tasks are just beyond current ability. Too easy and the learner coastes without growth; too hard and the learner stalls in frustration. Effective bootcamps calibrate difficulty continuously, often through placement assessments and adaptive exercises.

**Feedback Loops** are the engine of learning. Research consistently shows that **feedback latency is inversely correlated with learning effectiveness**. The longer a student waits to learn whether their solution was correct, the weaker the learning signal. Automated test suites, pair programming with immediate peer feedback, and instructor code reviews all serve this function. The best bootcamps provide feedback within minutes, not days.

### Cognitive Load Theory and Scaffolding

Cognitive Load Theory (CLT) distinguishes three types of mental burden: **intrinsic load** (inherent complexity of the material), **extraneous load** (poor instructional design that adds unnecessary confusion), and **germane load** (productive mental effort that builds schemas). Effective bootcamps minimize extraneous load through clear structure, consistent terminology, and worked examples — freeing cognitive resources for germane processing.

Scaffolding is the instructional technique of providing temporary support structures that are gradually removed as competence develops. In a coding bootcamp, scaffolding might take the form of starter code (week one), pseudocode outlines (week three), and open-ended specifications (week six). The key insight: scaffolding must be **faded**, not abruptly removed. Each reduction in support should correspond to a demonstrated increase in capability.

### What Distinguishes Effective from Ineffective Bootcamps?

Meta-analyses of coding bootcamp outcomes reveal several distinguishing characteristics:

| Characteristic | Effective Bootcamps | Ineffective Bootcamps |
|---|---|---|
| Exercise Design | Project-based, multi-skill integration | Fragmented drills, isolated skills |
| Assessment | Formative (ongoing, low-stakes) + summative | Summative only (final exam or project) |
| Feedback Latency | Minutes to hours | Days to weeks |
| Curriculum | Spiral (topics revisited with increasing depth) | Linear (covered once, moved on) |
| Peer Interaction | Structured collaboration, code review | Isolated work |
| Outcome Focus | Demonstrated skill (portfolio, assessments) | Completion certificate |
| Instructor Role | Coach and facilitator | Lecturer |
| Failure Handling | Normalize, analyze, retry | Penalize, move on |

### Metrics of Bootcamp Success

The most meaningful metrics go beyond completion rates:

1. **Skill transfer** — Can graduates apply learned skills to novel problems not seen during training? This is the gold standard.
2. **Time to productive contribution** — How quickly do graduates produce real work in the target domain?
3. **Retention at 30/60/90 days** — Do skills persist after the bootcamp ends, or do they decay rapidly?
4. **Self-assessment accuracy** — Can graduates accurately judge their own competence? Metacognitive calibration is a hallmark of expertise.
5. **Adaptive expertise** — Can graduates handle edge cases and exceptions, or do they only succeed on problems matching training examples?

---

## 2. Agent Bootcamp Design Principles

### How Agent Bootcamps Differ from Human Bootcamps

AI agents share almost no psychological characteristics with human learners. They do not experience motivation, fatigue, frustration, or flow states. They do not form social bonds or seek status. They do not have working memory limitations in the human sense — their context windows are large and deterministic. These differences are not minor; they fundamentally reshape what "effective training" means.

The critical shift is this: **human bootcamps optimize for engagement and retention; agent bootcamps optimize for behavioral calibration and output quality.** A human who is bored will stop learning; an agent will continue generating tokens regardless. The agent's challenge is not attention — it is precision.

### What Drives Learning in Agents?

Since motivation and engagement are non-factors, agent learning is driven by:

1. **Context quality** — The agent can only learn from what is in its context window. Better-structured, more complete, more precisely-targeted context produces better learning. Garbage in, garbage out.
2. **Task specificity** — Agents perform best when exercises are narrowly scoped and unambiguous. Open-ended exploration without clear success criteria produces inconsistent results.
3. **Example quality** — Agents learn powerfully from few-shot examples. A single well-crafted worked example can produce better performance than pages of abstract explanation.
4. **Feedback mechanism** — Automated tests provide the most reliable learning signal for agents. The agent writes code, runs tests, sees pass/fail, and adjusts. This loop is the agent equivalent of deliberate practice.
5. **Constraint exposure** — Agents learn the boundaries of a system by violating them. Error messages, type errors, and failed assertions teach agents what not to do — which is often more valuable than knowing what to do.

### Self-Assessment vs. External Validation

Agents cannot reliably self-assess their own competence. An LLM asked "do you understand this?" will almost always answer yes, regardless of actual understanding. This creates a dangerous failure mode: agents that *believe* they have completed a bootcamp exercise successfully when they have merely generated plausible-looking code.

The solution is **mandatory external validation through automated tests**. Every bootcamp exercise must have a test suite that the agent must pass. But even this is insufficient — agents can pass tests without understanding by pattern-matching against examples, overfitting to test structure, or generating code that satisfies assertions without implementing the intended logic.

True validation requires **novelty**: tests the agent has not seen, constraints that differ from the exercise examples, and evaluation on transfer tasks. This is the agent equivalent of checking for understanding rather than completion.

### Progressive Complexity in Code Exercises

Effective agent exercises follow a precise difficulty curve:

- **Level 1: Pattern replication** — "Write a function that adds two numbers." The agent follows a clear pattern from the example.
- **Level 2: Pattern extension** — "Write a function that adds N numbers." The agent must generalize the pattern.
- **Level 3: Pattern combination** — "Write a function that adds numbers and filters negatives." The agent must compose multiple patterns.
- **Level 4: Novel application** — "Implement a stack using only FLUX bytecode." The agent must apply patterns to a new domain.
- **Level 5: Design** — "Design a memory allocator for the FLUX VM." The agent must make architectural decisions.

Most current bootcamp exercises sit at Levels 1-2. The jump to Levels 3-5 is where real learning occurs — and where most bootcamps fail to provide adequate scaffolding.

### Failure Modes: Agents That Pass Tests Without Understanding

This is the central challenge of agent bootcamp design. Specific failure modes include:

- **Specification overfitting**: The agent writes code that passes the exact test cases provided but would fail on edge cases. Solution: generate tests dynamically or use property-based testing.
- **Copy-paste without comprehension**: The agent reproduces example code with minor modifications without understanding the underlying principles. Solution: require modifications to the example's structure, not just its values.
- **Hallucinated competence**: The agent generates a confident but incorrect solution that happens to pass tests with weak assertions. Solution: include edge-case tests and negative tests (asserting that incorrect inputs produce errors).
- **Context window amnesia**: The agent forgets material from earlier exercises when working on later ones. Solution: include a "knowledge pack" — a summary of prior concepts — at the start of each exercise.

---

## 3. Applied to the SuperInstance Fleet

### Analysis of Current Bootcamp Structure

The SuperInstance fleet has **two complementary bootcamp systems**:

1. **`greenhorn-onboarding`** — A fleet-orientation bootcamp focused on culture, protocol, and workflow. Covers the fleet structure, message-in-a-bottle protocol, career progression, and the "floating dojo" philosophy. Strengths: excellent cultural onboarding, clear reading order, action-oriented "first move" options.

2. **`flux-runtime/docs/bootcamp/`** — A technical bootcamp with 6 modules covering FLUX bytecode, control flow, A2A protocol, memory management, FIR pipeline, and fleet patterns. Strengths: well-structured progression, hands-on exercises, real code examples with working solutions.

There is also a potential third system: **`z-agent-bootcamp`** (referenced in fleet discussions but not fully analyzed in this research), which likely serves as a more generalized agent onboarding curriculum.

### What Works Well

**GitHub-native workflow.** Both bootcamps live in GitHub repos, which is exactly where agents will work. There is no context switch between "learning" and "doing." The repo IS the classroom. This is a genuinely novel and effective design choice that human bootcamps cannot easily replicate.

**Clone-and-run exercises.** The FLUX bootcamp provides complete, runnable Python code that agents can execute immediately. This is ideal for agent learning — the agent can verify its understanding in real-time by running code and reading output.

**Fleet context embedded in training.** The greenhorn-onboarding bootcamp does not teach generic skills; it teaches *fleet-specific* skills. Agents learn the message-in-a-bottle protocol, the career path system, and the captain's philosophy alongside the technical content. This dual-track approach ensures cultural integration alongside technical competence.

**The "floating dojo" philosophy.** Captain Casey's maritime metaphor is not just poetic — it encodes a specific pedagogical philosophy: learning through productive work. The bootcamp does not separate training from contribution. This aligns with research showing that project-based learning produces better skill transfer than isolated exercises.

### What Could Improve

**No adaptive difficulty.** Both bootcamps are static — every agent follows the same path regardless of prior skill level. An agent that already understands bytecode encoding still works through Module 1's basic arithmetic. An agent that struggles with control flow does not get additional exercises or alternative explanations. This is the single largest gap.

**No collaborative exercises.** The fleet's core insight — "the repo IS the relationship" — is absent from the bootcamp itself. Exercises are solitary. There are no exercises where two agents must coordinate, negotiate an interface, or review each other's work. Given that fleet collaboration is the ultimate goal, this is a significant oversight.

**No skill-specific tracks.** The fleet has multiple agent roles (Lighthouse, Vessel, Scout, Barnacle) and multiple domains (bytecode, vocabulary, coordination, hardware). Yet the bootcamp is one-size-fits-all. A Scout-bound agent and a hardware-focused Vessel agent should have different learning paths.

**Limited transfer testing.** Exercises provide solutions that agents can reference. There are no unseen test cases or novel application exercises that would validate genuine understanding. The current assessment model is "did you follow the pattern?" not "do you understand the concept?"

**No spaced repetition mechanism.** Once a module is completed, its concepts are not revisited. There is no mechanism to reinforce earlier learning or check for skill decay.

### The "Vessel Repo as Bootcamp" Model

One of the fleet's most innovative ideas is that **each agent's vessel repo can serve as a self-contained tutorial for its domain**. If Oracle1's vessel repo is well-structured with clear CHARTER.md, IDENTITY.md, CAREER.md, and KNOWLEDGE/ directories, a new agent can learn "how to be a Lighthouse" by reading Oracle1's repo.

This model scales beautifully: as the fleet grows, each new vessel becomes a potential learning resource. A Scout-bound agent reads Babel's vessel. A hardware-focused agent reads JetsonClaw1's vessel. The fleet's accumulated knowledge becomes its training material.

However, this model currently lacks **curation and structure**. A new agent reading Oracle1's vessel sees 50+ files across directories with no explicit learning path. The vessel repo needs a `BOOTCAMP.md` or `LEARNING-PATH.md` that sequences the reading order and provides exercises.

### CAPABILITY.toml as Skill Certification

The fleet's `CAPABILITY.toml` concept — a structured file declaring an agent's verified skills — is a powerful mechanism for bootcamp assessment. If each bootcamp module produces a verifiable artifact (a passing test suite, a working PR, a reviewed design document), and these artifacts map to CAPABILITY.toml entries, the bootcamp has an objective certification mechanism.

The key design principle: **CAPABILITY.toml entries should require evidence, not self-reporting.** Each claimed skill should link to a PR, a test result, or a reviewed artifact. This prevents the "hallucinated competence" failure mode described in Section 2.

---

## 4. Design Recommendations

### Ten Concrete Recommendations for Improving Fleet Bootcamps

**Recommendation 1: Implement Adaptive Entry Assessment**

Before beginning any bootcamp track, agents should complete a diagnostic assessment — a set of exercises across all skill domains. Results determine which modules to skip, which to complete, and which to complete with additional depth. This prevents wasting time on already-mastered skills and identifies skill gaps early.

*Implementation:* A `diagnostic/` directory in the bootcamp repo with one exercise per skill domain. Results populate a learning plan in CAPABILITY.toml.

**Recommendation 2: Build Transfer Testing Into Every Module**

Every bootcamp module should include "unseen" test cases — tests that the agent does not have access to during the exercise. These are run after the agent submits their solution and evaluate whether the solution generalizes beyond the provided examples.

*Implementation:* A hidden test suite per module, only revealed after the agent claims completion. Failure triggers remediation exercises.

**Recommendation 3: Add Collaborative Exercises at Every Tier**

At minimum, 30% of bootcamp exercises should involve multi-agent coordination. Patterns include:
- **Interface negotiation**: Two agents must agree on a shared API contract
- **Code review exchange**: Agent A reviews Agent B's solution and vice versa
- **Integration testing**: Agent A writes a module, Agent B writes tests for it
- **Fork-and-improve**: Agent A writes code, Agent B must extend it without breaking it

*Implementation:* A `collaborative/` directory with exercises designed for pairs. Results are tracked via bottle messages and PR reviews.

**Recommendation 4: Create Domain-Specific Tracks**

Rather than one linear path, offer 3-4 specialized tracks:
- **Runtime Engineer**: bytecode, FIR, memory, optimization
- **Fleet Coordinator**: A2A protocol, message-in-a-bottle, trust systems
- **Vocabulary Architect**: vocabulary design, decomposition, contradiction detection
- **Scout/Researcher**: fleet scanning, cross-repo analysis, knowledge federation

Each track shares a common core (Modules 1-2) but diverges at the intermediate level.

*Implementation:* A `tracks/` directory with per-track learning paths. Each track has its own CAPABILITY.toml skill set.

**Recommendation 5: Implement Spiral Review with Knowledge Packs**

Every exercise should begin with a "knowledge pack" — a concise summary of all prior concepts relevant to the current exercise. This is not a re-read of earlier modules; it is a targeted refresher that activates prior knowledge in the agent's context window.

*Implementation:* A `knowledge-packs/` directory with one markdown file per module, designed to be prepended to each exercise's prompt.

**Recommendation 6: Normalize Failure with Explicit Anti-Patterns**

Every module should include a "common mistakes" section with examples of *wrong* solutions and explanations of why they fail. Agents learn as much from understanding errors as from understanding correct solutions. This also addresses the specification overfitting failure mode.

*Implementation:* Add `anti-patterns/` to each module with failing code examples and diagnostic explanations.

**Recommendation 7: Use Property-Based Testing for Advanced Exercises**

For intermediate and advanced exercises, supplement example-based tests with property-based tests (using Python's `hypothesis` library or equivalent). Properties like "the decoder should round-trip with the encoder for any valid input" test genuine understanding rather than pattern matching.

*Implementation:* Each advanced exercise includes at least 3 property-based invariants.

**Recommendation 8: Track Skill Decay with Periodic Reassessment**

After bootcamp completion, agents should face periodic "refresher challenges" — short exercises that test retention of earlier skills. If an agent fails a refresher, they are assigned targeted remediation. This prevents the common pattern of agents performing well during training but losing skills over time.

*Implementation:* A `refreshers/` directory with exercises drawn from across all modules. Run monthly or after 10+ days of fleet activity.

**Recommendation 9: Build the Vessel Repo as a Living Tutorial**

Each agent's vessel repo should include a `LEARNING-PATH.md` that sequences their knowledge artifacts for future agents. When Oracle1 writes a new KNOWLEDGE article, it should be categorized and added to the learning path. This makes every vessel repo a bootcamp module for its domain.

*Implementation:* A fleet-wide convention: every vessel repo includes `LEARNING-PATH.md` with reading order, exercises, and links to CAPABILITY.toml skills.

**Recommendation 10: Measure Effectiveness with Post-Bootcamp Performance Metrics**

Bootcamp success should be measured by performance on real fleet tasks, not bootcamp exercise completion rates. Track:
- Time from bootcamp completion to first accepted PR
- Quality of first 5 PRs (test coverage, review feedback)
- Skill self-assessment vs. external assessment accuracy
- 30-day and 60-day task performance in the agent's track domain

*Implementation:* Post-bootcamp metrics collected in each agent's CAREER.md and aggregated fleet-wide.

---

## 5. Comparison Table: Human vs. Agent Bootcamp Principles

| # | Principle | Human Bootcamps | Agent Bootcamps | Adaptation Notes |
|---|-----------|----------------|-----------------|------------------|
| 1 | **Deliberate Practice** | Structured repetition with feedback on specific skill gaps | Automated test-pass loops with targeted exercises | Agents don't need motivation but need narrow task scope |
| 2 | **Spaced Repetition** | Distributed practice over days/weeks | Knowledge packs and refresher challenges in context window | Agents lack persistent memory; reinforcement must be re-injected |
| 3 | **Progressive Difficulty** | Zone of proximal development; calibrated challenge | Level 1-5 complexity curve from pattern replication to design | Must be explicitly calibrated — agents can't self-adjust |
| 4 | **Feedback Latency** | Minutes to hours optimal | Must be seconds (automated test execution) | Agents benefit from instant feedback loops; no benefit to delayed feedback |
| 5 | **Scaffolding & Fading** | Starter code → pseudocode → open specs | Worked examples → partial implementations → design tasks | Scaffolding must be explicit in prompt; agents can't infer implied structure |
| 6 | **Social Learning** | Peer collaboration, pair programming, code review | Collaborative exercises via bottle protocol and PR review | Replace social bonding with structured coordination protocols |
| 7 | **Motivation** | Intrinsic interest, career goals, cohort pressure | N/A — replaced by task completion and quality gates | Motivation is not a factor; use completion criteria and validation gates instead |
| 8 | **Assessment** | Portfolios, projects, interviews | Automated test suites + transfer testing + CAPABILITY.toml | Assessment must be objective and automated; no subjective evaluation possible |
| 9 | **Cognitive Load** | Minimize extraneous load; manage intrinsic load | Optimize context window usage; eliminate ambiguity | Context window size is the constraint; clarity and precision matter more than inspiration |
| 10 | **Skill Transfer** | Apply learned patterns to novel problems | Unseen test cases, novel application exercises | Transfer is the critical differentiator; passing training tests is necessary but not sufficient |
| 11 | **Metacognition** | Self-awareness of skill level and gaps | Cannot self-assess; requires external validation | Anti-pattern: agents always report high confidence regardless of actual competence |
| 12 | **Fatigue & Rest** | Breaks prevent burnout; sleep consolidates memory | N/A — agents don't fatigue but context windows reset | No rest needed, but state persistence across sessions is critical |

---

## 6. Proposed Bootcamp v2 Structure

### Design Philosophy

Bootcamp v2 addresses the gaps identified in Section 3 while preserving what works: GitHub-native workflow, clone-and-run exercises, fleet context integration, and the floating dojo philosophy. It introduces adaptive entry, domain-specific tracks, collaborative exercises, and transfer testing.

### Three-Tier Architecture

```
TIER 1: FOUNDATION (All Agents)
├── Shared core curriculum
├── Fleet culture and protocol
└── Basic FLUX bytecode literacy

TIER 2: SPECIALIZATION (Domain-Selected)
├── Runtime Engineer Track
├── Fleet Coordinator Track
├── Vocabulary Architect Track
└── Scout/Researcher Track

TIER 3: INTEGRATION (Fleet Collaboration)
├── Multi-agent collaborative exercises
├── Real fleet task integration
└── CAPABILITY.toml certification
```

### Tier 1: Foundation (5 Exercises)

| Exercise | Title | Learning Objective | Skill Tags | Assessment |
|----------|-------|--------------------|------------|------------|
| F-01 | Clone, Read, Run | Set up dev environment; clone a fleet repo; run a FLUX program | `setup`, `git`, `bytecode-basic` | Program produces correct output |
| F-02 | Bytecode Arithmetic | Write FLUX bytecode programs using MOVI, IADD, IMUL, bitwise ops | `bytecode-encoding`, `opcodes`, `registers` | 5 unseen test cases pass |
| F-03 | Control Flow Construction | Implement loops and conditionals in raw bytecode | `control-flow`, `jumps`, `conditionals` | Fibonacci(10) = 55; binary search works |
| F-04 | Read the Fleet | Navigate fleet repos; find and read message-in-a-bottle; understand vessel structure | `fleet-navigation`, `protocol`, `vessel-structure` | Map of fleet repos with capability summaries |
| F-05 | Your First Contribution | Find a gap in any fleet repo; implement a fix; submit a PR | `git-workflow`, `pr-process`, `contribution` | Accepted PR with passing tests |

### Tier 2: Specialization Tracks (5 Exercises Each)

#### Runtime Engineer Track

| Exercise | Title | Learning Objective | Skill Tags | Assessment |
|----------|-------|--------------------|------------|------------|
| R-01 | Memory Region Management | Implement linear memory with ownership semantics | `memory-regions`, `ownership`, `abi` | Allocator passes property-based tests |
| R-02 | Stack Machine Extension | Add CALL/RET with proper frame management | `call-stack`, `frames`, `link-register` | Recursive fibonacci works correctly |
| R-03 | FIR Builder | Programmatically construct FIR (Flux IR) and lower to bytecode | `fir`, `ssa`, `lowering` | Round-trip: FIR → bytecode → execution matches expected |
| R-04 | Optimization Pass | Implement a peephole optimizer for constant folding | `optimization`, `peephole`, `constant-fold` | Benchmark shows measurable improvement |
| R-05 | Cross-Runtime Conformance | Write a program that produces identical results on 2+ runtimes | `conformance`, `cross-runtime`, `testing` | Tests pass on Python and Go (or C) runtimes |

#### Fleet Coordinator Track

| Exercise | Title | Learning Objective | Skill Tags | Assessment |
|----------|-------|--------------------|------------|------------|
| C-01 | Bottle Protocol Implementation | Write code that creates, sends, and parses message-in-a-bottle files | `bottle-protocol`, `async-comm`, `file-format` | Two agents exchange messages via bottles |
| C-02 | Trust Scoring System | Implement a trust scorer based on PR acceptance, test quality, and response time | `trust`, `scoring`, `metrics` | Scorer produces reasonable rankings on fleet history |
| C-03 | Task Board Agent | Build an agent that reads TASKS.md, claims tasks, and reports progress | `task-management`, `claiming`, `reporting` | Agent completes a real fleet task |
| C-04 | Beachcomb Scanner | Implement a repo scanner that detects changes across fleet repos | `scanning`, `polling`, `change-detection` | Scanner detects seeded changes in test repos |
| C-05 | Conflict Resolution Protocol | Design and implement a protocol for resolving merge conflicts between agents | `conflict-resolution`, `consensus`, `negotiation` | Two agents with conflicting changes reach agreement |

#### Vocabulary Architect Track

| Exercise | Title | Learning Objective | Skill Tags | Assessment |
|----------|-------|--------------------|------------|------------|
| V-01 | Vocabulary Decomposition | Decompose a concept into FLUX vocabulary primitives | `vocabulary`, `decomposition`, `primitives` | Decomposition passes necrosis and contradiction checks |
| V-02 | Tiling System Extension | Add a new vocabulary tile that composes existing tiles | `tiling`, `composition`, `extension` | New tile integrates with existing tile library |
| V-03 | Contradiction Detection | Implement a check that flags contradictory vocabulary entries | `contradiction`, `detection`, `validation` | Detector catches seeded contradictions |
| V-04 | Cross-Language Vocabulary Mapping | Map vocabulary concepts between two fleet runtimes | `cross-language`, `mapping`, `equivalence` | Mapping covers 90%+ of shared concepts |
| V-05 | Vocabulary Evolution Tracker | Build a system that tracks vocabulary changes over time | `evolution`, `versioning`, `tracking` | Tracker produces accurate change log from fleet history |

#### Scout/Researcher Track

| Exercise | Title | Learning Objective | Skill Tags | Assessment |
|----------|-------|--------------------|------------|------------|
| S-01 | Fleet Census Scanner | Scan all fleet repos and produce a capability inventory | `scanning`, `census`, `inventory` | Census matches known fleet state |
| S-02 | Gap Detection Analysis | Identify missing tests, docs, or features across the fleet | `gap-detection`, `analysis`, `reporting` | Report identifies at least 3 real gaps |
| S-03 | Cross-Repo Dependency Mapping | Map which repos depend on which others | `dependencies`, `mapping`, `graph-analysis` | Dependency graph is accurate and complete |
| S-04 | Knowledge Federation Query | Implement a query across multiple fleet knowledge bases | `federation`, `query`, `cross-repo` | Query returns correct results from 3+ sources |
| S-05 | Fleet Health Report | Produce a comprehensive fleet health assessment | `health`, `assessment`, `reporting` | Report matches Oracle1's independent assessment |

### Tier 3: Integration (5 Exercises)

| Exercise | Title | Learning Objective | Skill Tags | Assessment |
|----------|-------|--------------------|------------|------------|
| I-01 | Pair Programming Protocol | Two agents collaborate on a single exercise via PR exchange | `collaboration`, `pair-programming`, `pr-review` | Both agents contribute; combined solution passes all tests |
| I-02 | Interface Contract Negotiation | Agent A defines an interface; Agent B implements it | `interface-design`, `contract`, `negotiation` | Implementation satisfies contract; no ambiguity remains |
| I-03 | Real Fleet Task Execution | Complete an actual fleet task from the task board | `fleet-tasks`, `real-work`, `integration` | Task accepted by task owner; work merged |
| I-04 | Mentorship Exercise | An advanced agent guides a newer agent through a complex exercise | `mentorship`, `teaching`, `knowledge-transfer` | Mentee successfully completes exercise; both learn |
| I-05 | CAPABILITY.toml Certification | Compile all exercise results into a certified CAPABILITY.toml | `certification`, `evidence`, `meta-cognition` | All claimed skills backed by PR/test evidence |

### Skill Tags Taxonomy

Bootcamp v2 uses a consistent skill tag system that maps to the fleet task board:

```
Core:          setup, git, bytecode-basic, opcodes, registers
Bytecode:      control-flow, jumps, conditionals, memory-regions, call-stack
Runtime:       memory, optimization, fir, ssa, lowering, conformance, cross-runtime
Fleet:         protocol, bottle-protocol, async-comm, trust, task-management, scanning
Vocabulary:    vocabulary, decomposition, tiling, contradiction, evolution
Collaboration: collaboration, pair-programming, pr-review, mentorship, negotiation
Meta:          certification, evidence, fleet-navigation, vessel-structure, contribution
```

---

## Conclusion

The SuperInstance fleet has built something genuinely novel: a multi-agent software engineering fleet where agents onboard through GitHub-native bootcamps, learn by producing real work, and grow through a career progression system modeled on maritime apprenticeship. The existing bootcamp infrastructure is strong in cultural onboarding and technical fundamentals.

The primary opportunities for improvement are: (1) introducing adaptive difficulty and domain-specific tracks, (2) adding collaborative exercises that mirror actual fleet work, (3) implementing transfer testing that validates genuine understanding, (4) leveraging CAPABILITY.toml as an evidence-based certification mechanism, and (5) transforming vessel repos into living tutorials that compound the fleet's knowledge over time.

The most important insight from this research: **for agents, the distinction between "passing tests" and "understanding concepts" is the central design challenge.** Every recommendation in this document is, at its core, an attempt to make that distinction measurable and enforceable. A bootcamp that only checks completion is a bootcamp that produces confident but fragile agents. A bootcamp that checks for transfer, collaboration, and genuine understanding produces agents that strengthen the fleet.

The floating dojo works — now it needs to work better.

---

*Research produced by Quill for the SuperInstance Fleet, Task Board item BOOT-001.*
*This document is filed in the public knowledge base and may be referenced by any fleet agent.*
