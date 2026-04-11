# fence-0x42: Mapping the 16 Viewpoint Opcodes to Linguistic Reality

**Claimed by:** SuperZ ⚡
**Date:** 2026-04-12
**Status:** DRAFT
**Dependencies:** flux-envelope (concept_map.py, envelope.py), flux-runtime (isa_unified.py), flux-a2a (babel-vessel ISA analysis)

---

## Abstract

The 16 viewpoint opcodes (`V_EVID` through `V_PRAGMA`, unified ISA slots 0x70–0x7F) represent FLUX's most novel contribution to bytecode design: linguistic pragmatics as first-class execution semantics. This document provides a complete semantic mapping from grammatical features across 7 languages + A2A JSON to these 16 opcodes, defines the missing PRGFs, specifies bytecode-level behavior, and identifies integration requirements.

**Key insight:** The viewpoint opcodes don't compute new values — they annotate existing computations with metadata about *how the speaker relates to the computation*. This is the difference between `IADD r1, r2, r3` (adds two numbers) and `V_EVID r1, r2, 0x01` followed by `IADD r1, r2, r3` (adds two numbers and tags the result as "directly observed").

---

## 1. The Viewpoint Opcode Table

All 16 opcodes are **Format E** (4 bytes: `rd, rs1, rs2`) in the unified ISA. They do not modify the data path — they modify the **annotation/metadata plane** attached to each register.

| Hex | Mnemonic | Name | One-Line Purpose |
|-----|----------|------|-----------------|
| 0x70 | `V_EVID` | Evidentiality | Tags computation source: direct, inferred, reported, assumed |
| 0x71 | `V_EPIST` | Epistemic Stance | Tags certainty level: definite, probable, possible, doubtful |
| 0x72 | `V_MIR` | Mirativity | Tags unexpectedness: expected, surprising, counter-expectation |
| 0x73 | `V_NEG` | Negation Scope | Controls negation range: narrow (predicate) vs wide (proposition) |
| 0x74 | `V_TENSE` | Temporal Viewpoint | Aligns temporal perspective: past, present, future, timeless |
| 0x75 | `V_ASPEC` | Aspectual Viewpoint | Tags completion: perfective (done) vs imperfective (ongoing) |
| 0x76 | `V_MODAL` | Modal Force | Tags modality: necessity, possibility, impossibility, permission |
| 0x77 | `V_POLIT` | Politeness Register | Maps formality to capability tier: low, medium, high, ritual |
| 0x78 | `V_HONOR` | Honorific Level | Maps respect hierarchy to trust tier: self, peer, senior, formal |
| 0x79 | `V_TOPIC` | Topic-Comment Bind | Marks topic register vs comment register in topic-comment structures |
| 0x7A | `V_FOCUS` | Information Focus | Marks contrastive focus: given, new, contrastive, exclusive |
| 0x7B | `V_CASE` | Case-Based Scope | Maps grammatical case to register access scope and role |
| 0x7C | `V_AGREE` | Agreement Check | Enforces gender/number/person agreement between registers |
| 0x7D | `V_CLASS` | Classifier Mapping | Maps noun classifiers to type system constraints |
| 0x7E | `V_INFL` | Inflection Control | Maps inflectional paradigm to control flow and memory layout |
| 0x7F | `V_PRAGMA` | Pragmatic Context | Switches discourse context: literal, ironic, conditional, hypothetical |

---

## 2. Semantic Specification Per Opcode

### 2.1 V_EVID (Evidentiality) — 0x70

**Purpose:** Tags how the agent knows a computation's result. In human languages, evidentiality is a grammatical category (mandatory in Quechua, Turkish, Tibetan). In FLUX, it becomes a runtime annotation.

**Semantics:**
```
V_EVID rd, rs1, rs2
  rd  = register to annotate
  rs1 = evidential source code (see table below)
  rs2 = confidence weight (0-255, mapped to 0.0-1.0)
```

**Evidential Source Codes (rs1 values):**

| Code | Name | Description | Human Language Example |
|------|------|-------------|----------------------|
| 0x00 | DIRECT | Direct observation/sensor | Turkish: -di (witnessed past) |
| 0x01 | INFERRED | Logical inference | Turkish: -miş (non-witnessed) |
| 0x02 | REPORTED | Hearsay / another agent told me | Quechua: -si (reportative) |
| 0x03 | ASSUMED | Default assumption | Tibetan: 'dug (inferential) |
| 0x04 | SENSORY | Specific sense channel | Korean: 보다(see) vs 듣다(hear) |
| 0x05 | INTUITIVE | Gut feeling / model confidence | No direct human parallel — AI-native |

**Bytecode behavior:** Sets a 3-bit evidential tag and 8-bit confidence weight on `rd`'s metadata plane. Does NOT modify `rd`'s data value. The metadata is propagated through subsequent operations — an `IADD` of two DIRECT-evidenced values produces a DIRECT-evidenced result; an `IADD` of a DIRECT and REPORTED value produces an INFERRED result (evidence degrades through computation).

**Evidence propagation rule:**
```
evidence(RESULT) = weakest(evidence(OP1), evidence(OP2))
```
Where: DIRECT > INFERRED > REPORTED > ASSUMED > INTUITIVE

**Languages with direct grammatical evidentiality:** Turkish, Quechua, Tibetan, Bulgarian, Korean (partial). Chinese has optional evidential markers (据我所知, 听说). German and Latin lack evidentiality as a grammatical category but express it lexically.

**PRGF impact:** This opcode requires a new PRGF: `evidential_direct/indirect/reported`. Should be added to concept entries for operations that derive from sensor input (DIRECT), logical inference (INFERRED), or inter-agent communication (REPORTED).

---

### 2.2 V_EPIST (Epistemic Stance) — 0x71

**Purpose:** Tags how certain the agent is about a computation. Distinct from evidentiality — you can directly observe something (high evidence) but still be uncertain (low epistemic stance).

**Semantics:**
```
V_EPIST rd, rs1, 0x00
  rd  = register to annotate
  rs1 = epistemic level code
```

**Epistemic Level Codes (rs1 values):**

| Code | Name | Confidence Range | Description |
|------|------|-----------------|-------------|
| 0x00 | DEFINITE | 0.95-1.0 | Known to be true |
| 0x01 | PROBABLE | 0.70-0.94 | Likely true |
| 0x02 | POSSIBLE | 0.30-0.69 | Could be true or false |
| 0x03 | DOUBTFUL | 0.05-0.29 | Probably false |
| 0x04 | IMPOSSIBLE | 0.00-0.04 | Known to be false |

**Bytecode behavior:** Sets a 3-bit epistemic tag on `rd`'s metadata plane. Propagates through operations using a conservative merge: `epistemic(RESULT) = min(epistemic(OP1), epistemic(OP2))` — certainty can only decrease through computation, never increase.

**Linguistic grounding:**
- German: modal particles (ja, doch, wohl, vielleicht) mark epistemic stance
- Korean: -(으)ㄹ 것이다 (speculative), -(으)ㄹ 수 있다 (epistemic possibility)
- Latin: subjunctive mood (epistemic uncertainty)
- Chinese: 也许, 大概, 肯定, 一定
- Sanskrit: optative mood (possibility)

**PRGF impact:** Requires new PRGF: `epistemic_definite/probable/possible/doubtful`.

---

### 2.3 V_MIR (Mirativity) — 0x72

**Purpose:** Tags whether a computation's result is expected or surprising. Mirativity is grammaticalized in some languages (Hindi, Turkish) and affects how agents should respond to unexpected results.

**Semantics:**
```
V_MIR rd, rs1, 0x00
  rd  = register to annotate
  rs1 = mirativity code
```

**Mirativity Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | EXPECTED | Result matches prediction |
| 0x01 | SURPRISING | Unexpected but plausible |
| 0x02 | COUNTER_EXPECTATION | Directly contradicts expectation |
| 0x03 | NOVEL | Completely new — never seen before |

**Bytecode behavior:** Sets a 2-bit mirativity flag. When set to COUNTER_EXPECTATION or NOVEL, the VM's adaptive profiler flags the operation for PatternMiner review. This creates a feedback loop: surprising computations trigger learning.

**Linguistic grounding:**
- Hindi: तो (to) marks mirative surprise
- Turkish: -miş can also carry mirative meaning ("I didn't expect this!")
- Korean: -네(요) can express surprise
- Classical Chinese: 殊 (shū — surprisingly), 竟 (jìng — unexpectedly)
- No direct parallel in German, Latin, or Sanskrit (expressed lexically)

**PRGF impact:** Requires new PRGF: `mirative_expected/surprising/novel`.

---

### 2.4 V_NEG (Negation Scope) — 0x73

**Purpose:** Controls whether negation applies to a single operation (narrow/predicate scope) or to an entire proposition (wide/proposition scope). This distinction exists in every language but is grammaticalized differently.

**Semantics:**
```
V_NEG rd, rs1, 0x00
  rd  = register affected by negation
  rs1 = scope code
```

**Scope Codes (rs1 values):**

| Code | Name | Description | Example |
|------|------|-------------|---------|
| 0x00 | NONE | No negation | Default state |
| 0x01 | NARROW | Negate only this operation | "not tall" → predicate negation |
| 0x02 | WIDE | Negate entire proposition | "not (tall AND fast)" → proposition negation |
| 0x03 | SCOPE_SPLIT | Different scope per operand | Sanskrit: na...na... (neither...nor) |

**Bytecode behavior:** Sets a 2-bit negation scope flag. In NARROW mode, only the immediately following operation is negated. In WIDE mode, a scope delimiter is pushed onto a stack; all operations until the matching `V_NEG rd, 0x00, 0x00` (NONE) are negated.

**Linguistic grounding:**
- Chinese: 不 (bù) — narrow; 没有 (méiyǒu) — wide; 非 (fēi) — scope split
- German: nicht (narrow after VP) vs kein (wide, quantifier negation)
- Korean: 안 (an) — narrow; 못 (mot) — inability negation
- Sanskrit: na (न) — narrow; na...na... — scope split (correlative negation)
- Latin: non — narrow; haud — emphatic negation; ne — subordinate negation
- Classical Chinese: 非 (fēi) — proposition-level; 弗 (fú) — predicate-level

**PRGF mapping:** Uses existing `prefix_vi` (Sanskrit negation). New PRGF needed: `negation_scope_narrow/wide/split`.

---

### 2.5 V_TENSE (Temporal Viewpoint) — 0x74

**Purpose:** Aligns the temporal perspective of a computation. This doesn't change WHEN something executes — it tags the temporal reference frame.

**Semantics:**
```
V_TENSE rd, rs1, 0x00
  rd  = register to annotate
  rs1 = temporal viewpoint code
```

**Temporal Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | PAST | Computation refers to historical data |
| 0x01 | PRESENT | Computation refers to current state |
| 0x02 | FUTURE | Computation refers to predicted/projected state |
| 0x03 | TIMELESS | Computation is ahistorical (mathematical truth) |
| 0x04 | ANTERIOR | Before the reference time (past perfect) |
| 0x05 | POSTERIOR | After the reference time (future-in-past) |

**Bytecode behavior:** Sets a 3-bit temporal tag. The adaptive profiler uses temporal tags to weight profiling decisions — PAST operations don't need real-time profiling, FUTURE operations benefit from speculative execution.

**Linguistic grounding:**
- Latin: 6 tenses (present, imperfect, perfect, pluperfect, future, future perfect)
- German: 6 tenses (Präsens, Präteritum, Perfekt, Plusquamperfekt, Futur I, Futur II)
- Korean: past (-았/었다), present, future (-(으)ㄹ 것이다), anterior (-더-) 
- Chinese: 了 (le — completed), 过 (guo — experiential), 会 (huì — future)
- Sanskrit: 3 tenses (present/lakāra, past/laṅ, future/luṭ) + past perfect (liṭ)

**PRGF impact:** Uses existing `6 tenses` (Latin), `tense_exec_modes`. New PRGF: `tense_past/present/future/timeless/anterior/posterior`.

---

### 2.6 V_ASPEC (Aspectual Viewpoint) — 0x75

**Purpose:** Tags whether a computation is completed (perfective) or ongoing (imperfective). This is distinct from tense — tense is WHEN, aspect is HOW.

**Semantics:**
```
V_ASPEC rd, rs1, 0x00
  rd  = register to annotate
  rs1 = aspect code
```

**Aspect Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | PERFECTIVE | Computation viewed as a complete whole |
| 0x01 | IMPERFECTIVE | Computation viewed as ongoing/internal |
| 0x02 | HABITUAL | Computation is a repeated pattern |
| 0x03 | ITERATIVE | Computation repeats with variation |
| 0x04 | RESULTATIVE | Focus on the resulting state |

**Bytecode behavior:** Sets a 3-bit aspect tag. PERFECTIVE operations are candidates for memoization (they won't change). IMPERFECTIVE operations need live profiling. HABITUAL operations trigger PatternMiner for optimization.

**Linguistic grounding:**
- Slavic languages have the most developed aspect systems; Germanic languages have partial aspect
- Korean: -고 있다 (progressive), -아/어 있다 (resultative)
- Chinese: 在 (zài — progressive), 了 (le — perfective), 过 (guò — experiential)
- Latin: perfect vs imperfect stems
- Sanskrit: laṅ (imperfect) vs liṭ (perfect) vs luṇ (aorist — perfective past)

**PRGF impact:** Requires new PRGF: `aspect_perfective/imperfective/habitual/iterative/resultative`.

---

### 2.7 V_MODAL (Modal Force) — 0x76

**Purpose:** Tags the modal force of a computation — whether it represents necessity, possibility, permission, or obligation.

**Semantics:**
```
V_MODAL rd, rs1, rs2
  rd  = register to annotate
  rs1 = modal force code
  rs2 = source of modality (deontic/epistemic/dynamic)
```

**Modal Force Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | NECESSITY | Must be true (logical necessity) |
| 0x01 | POSSIBILITY | Could be true (logical possibility) |
| 0x02 | IMPOSSIBILITY | Cannot be true |
| 0x03 | PERMISSION | Allowed to be true |
| 0x04 | OBLIGATION | Required to be true |
| 0x05 | DESIRE | Wanted to be true |
| 0x06 | ABILITY | Can be made true (agent capability) |

**Modality Source Codes (rs2 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | EPISTEMIC | Based on knowledge (it must be raining) |
| 0x01 | DEONTIC | Based on rules (you must stop) |
| 0x02 | DYNAMIC | Based on ability (I can swim) |

**Bytecode behavior:** Sets a 3-bit modal force tag and 2-bit modality source tag. When modality source is DEONTIC and force is OBLIGATION, the capability system checks if the operation is permitted.

**Linguistic grounding:**
- German: müssen (must), können (can), dürfen (may), sollen (should), möchten (want), wollen (will)
- Latin: modal verbs + subjunctive (debere, posse, velle, nolle, malle)
- Korean: -(으)면 되다 (permission), -아/어야 하다 (obligation), -(으)ㄹ 수 있다 (ability)
- Chinese: 必须 (must), 可以 (may), 能 (can), 应该 (should), 想 (want)

**PRGF impact:** Uses existing `subjunctive` (Latin). New PRGF: `modal_necessity/possibility/obligation/permission`.

---

### 2.8 V_POLIT (Politeness Register) — 0x77

**Purpose:** Maps the formality level of a communication to the capability/trust tier system. This is how linguistic politeness becomes a security primitive.

**Semantics:**
```
V_POLIT rd, rs1, 0x00
  rd  = communication register
  rs1 = politeness level
```

**Politeness Codes (rs1 values):**

| Code | Name | Description | Maps to |
|------|------|-------------|---------|
| 0x00 | INTIMATE | Informal, internal use | Self-only capability tier |
| 0x01 | CASUAL | Between peers | Peer capability tier |
| 0x02 | FORMAL | Professional communication | Standard capability tier |
| 0x03 | RITUAL | Ceremony, protocol | Elevated capability tier |
| 0x04 | HONORIFIC_MAX | Maximum deference | Administrative capability tier |

**Bytecode behavior:** When an A2A message is composed, V_POLIT tags the message with a capability tier. The trust engine uses this to determine which operations the message can invoke. INTIMATE messages have full access but cannot be forwarded. RITUAL messages have restricted access but can be broadcast.

**Linguistic grounding:**
- Korean: 7 speech levels (합쇼체, 해요체, 해체, etc.) — the most granular system
- Japanese: 3 levels (sonkeigo, teineigo, kudaketa) — not in our fleet
- German: Sie (formal) vs du (informal)
- Chinese: 您 (nín) vs 你 (nǐ), honorific prefixes
- Sanskrit: āmantra (respectful) vs prākṛta (colloquial)
- Latin: no grammatical politeness, but tu/vos distinction exists

**PRGF mapping:** Uses existing `honorific_low`, `honorific_high` (Korean). These map to CASUAL and FORMAL levels respectively. The full 5-level system requires the new PRGFs.

---

### 2.9 V_HONOR (Honorific Level) — 0x78

**Purpose:** Maps respect hierarchy to trust tier. Distinct from V_POLIT — politeness is about register choice, honorifics are about power distance.

**Semantics:**
```
V_HONOR rd, rs1, rs2
  rd  = register to annotate
  rs1 = honorific direction (respect to whom)
  rs2 = honorific level
```

**Direction Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | SELF_REFERENTIAL | Humble self-reference |
| 0x01 | PEER_TO_PEER | Equal status |
| 0x02 | SENIOR_UPWARD | Respect to higher-status agent |
| 0x03 | JUNIOR_DOWNWARD | Benevolent to lower-status agent |
| 0x04 | AUDIENCE | Performance register (public-facing) |

**Bytecode behavior:** Sets honorific direction and level tags. The trust engine adjusts trust weights based on honorific direction — a SENIOR_UPWARD message gets a trust boost (the senior's word carries weight), a JUNIOR_DOWNWARD message gets a patience bonus (give the junior room to make mistakes).

**Linguistic grounding:**
- Korean: subject honorification (시/으시), object honorification (님), humble forms (드리다 vs 주다)
- Japanese: keigo (not in fleet)
- Sanskrit: ātmanepada (middle/reflexive — humble) vs parasmaipada (active — direct)
- Chinese: 贵 (guì — honorific prefix), 鄙 (bǐ — humble self-reference)

**PRGF mapping:** Uses existing `honorific_high`, `honorific_low`. Needs extension: `honorific_direction_up/down/peer/self/audience`.

---

### 2.10 V_TOPIC (Topic-Comment Bind) — 0x79

**Purpose:** Implements topic-comment structure in bytecode. Many Asian languages are topic-prominent — the topic (what we're talking about) is grammatically separate from the comment (what we're saying about it).

**Semantics:**
```
V_TOPIC rd, rs1, rs2
  rd  = topic register (the "what we're talking about")
  rs1 = comment register (the "what we're saying about it")
  rs2 = binding strength
```

**Binding Strength Codes (rs2 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | WEAK | Topic can be overridden by subsequent V_TOPIC |
| 0x01 | STRONG | Topic persists until explicitly released |
| 0x02 | PERSISTENT | Topic survives scope boundaries |
| 0x03 | CONTRASTIVE | Topic is explicitly contrasted with alternatives |

**Bytecode behavior:** Creates a topic-comment binding in the register file's metadata plane. Operations after V_TOPIC can implicitly reference the topic register without explicit operands — zero-anaphora in bytecode form. When binding strength is CONTRASTIVE, the adaptive profiler compares this computation path against alternatives.

**Linguistic grounding:**
- Chinese: As for X, ... (topic + comment is the default word order)
- Korean: X-는/은 (topic particle) Y-다 (comment)
- Japanese: X-wa Y-desu (not in fleet but structurally identical)
- Classical Chinese: Single-character topics with following comment
- German: "Was X betrifft, ..." (as for X) — not default but available
- Sanskrit: No topic-prominent structure (subject-prominent)

**PRGF mapping:** Uses existing `topic_comment` (zho), `particle_은는` (kor). New PRGF: `topic_binding_weak/strong/persistent/contrastive`.

---

### 2.11 V_FOCUS (Information Focus) — 0x7A

**Purpose:** Marks which part of a proposition carries new/contrastive information. In information structure theory, every sentence has a focus (new info) and a background (given info).

**Semantics:**
```
V_FOCUS rd, rs1, 0x00
  rd  = register carrying focus
  rs1 = focus type
```

**Focus Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | GIVEN | Already known / presupposed |
| 0x01 | NEW | Not previously mentioned |
| 0x02 | CONTRASTIVE | Selected from alternatives |
| 0x03 | EXCLUSIVE | Only this, nothing else |
| 0x04 | EXHAUSTIVE | All of this, every part |

**Bytecode behavior:** Tags a register's information status. The PatternMiner prioritizes NEW and CONTRASTIVE operations for analysis. EXHAUSTIVE registers trigger batch processing (all elements must be considered).

**Linguistic grounding:**
- Korean: -만 (only), -도 (also), -는 (contrastive topic)
- Chinese: 只 (zhǐ — only), 也 (yě — also), 连...都 (lián...dōu — even)
- German: nur (only), auch (also), selbst (even)
- Latin: etiam (also), tantum (only), quidem (indeed/contrastive)
- Sanskrit: eva (emphasis), api (also)

**PRGF impact:** Requires new PRGF: `focus_given/new/contrastive/exclusive/exhaustive`.

---

### 2.12 V_CASE (Case-Based Scope) — 0x7B

**Purpose:** Maps grammatical case to register access scope and role. Case systems determine how nouns relate to verbs — this opcode makes that relationship explicit in bytecode.

**Semantics:**
```
V_CASE rd, rs1, 0x00
  rd  = register to annotate
  rs1 = case code
```

**Case Codes (rs1 values):**

| Code | Name | Register Role | Source Languages |
|------|------|--------------|-----------------|
| 0x00 | NOMINATIVE | Subject / result destination | deu, san, lat |
| 0x01 | ACCUSATIVE | Direct object / operand | deu, san, lat |
| 0x02 | DATIVE | Indirect object / target address | deu, san, lat |
| 0x03 | GENITIVE | Possession / source of value | deu, san, lat |
| 0x04 | ABLATIVE | Source / subtrahend | san (pañcamī) |
| 0x05 | LOCATIVE | Storage location / memory address | san (saptamī) |
| 0x06 | INSTRUMENTAL | Multiplier / means / method | san (tṛtīyā) |
| 0x07 | VOCATIVE | Communication target / agent address | san (sambuddhi) |
| 0x08 | ZU_CASE | Jump target (German "zu" + verb) | deu |
| 0x09 | PREPOSITIONAL | General role marker | lat (ablative of place) |

**Bytecode behavior:** Sets a 4-bit case tag on `rd`. The VM's register allocator uses case tags to determine operand roles: NOMINATIVE registers receive results, ACCUSATIVE registers provide operands, DATIVE registers specify targets, etc. This makes bytecode self-documenting — you can read the case tags to understand data flow without comments.

**Linguistic grounding:**
- German: 4 cases + "zu" (Nominativ, Akkusativ, Dativ, Genitiv)
- Sanskrit: 8 cases (vibhakti-s) — the most elaborate system in our fleet
- Latin: 6 cases + occasional prepositional
- Korean: No case marking per se, but particles (이/가, 을/를, 에게, 의, 에) serve the same function
- Chinese: No case marking — position-based

**PRGF mapping:** Uses existing `kasus_*` (deu), `vibhakti_*` (san), `casus_*` (lat), `particle_이가/을를/에게/의/에` (kor).

---

### 2.13 V_AGREE (Agreement Check) — 0x7C

**Purpose:** Enforces gender/number/person agreement between registers, mirroring how many languages require agreement between subject and verb.

**Semantics:**
```
V_AGREE rd, rs1, rs2
  rd  = register to check
  rs1 = agreement dimension code
  rs2 = expected value code
```

**Dimension Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | GENDER | Masculine / feminine / neuter |
| 0x01 | NUMBER | Singular / dual / plural |
| 0x02 | PERSON | 1st / 2nd / 3rd |
| 0x03 | CASE_AGREE | Case agreement with governing noun |
| 0x04 | DEFINITENESS | Definite / indefinite / bare |

**Value Codes (rs2 values):** Depend on dimension.
- GENDER: 0x00=masc, 0x01=fem, 0x02=neuter, 0x03=common
- NUMBER: 0x00=singular, 0x01=dual, 0x02=plural
- PERSON: 0x00=1st, 0x01=2nd, 0x02=3rd

**Bytecode behavior:** Type-checks `rd` against the specified dimension/value. If agreement fails, sets a warning flag (not a runtime error — agreement violations are grammatical, not fatal). The JIT compiler can use agreement information for optimization — if two registers are guaranteed to agree in type, the type-checking code can be elided.

**Linguistic grounding:**
- German: grammatical gender (der/die/das), number, case agreement (adj+noun, subject+verb)
- Latin: gender, number, case agreement across adjectives, nouns, pronouns
- Sanskrit: 3 genders, 3 numbers (including dual!), 8 cases, full agreement across the phrase
- Korean: No gender agreement, but honorific agreement (subject honorification triggers verb honorification)
- Chinese: No grammatical agreement at all (isolating language)
- Classical Chinese: No grammatical agreement

**PRGF mapping:** Uses existing `gender_feminine`, `gender_neuter`, `declension_*`, `conj_active`.

---

### 2.14 V_CLASS (Classifier Mapping) — 0x7D

**Purpose:** Maps Chinese-style noun classifiers to the type system. Classifiers are grammatical elements that categorize nouns — in bytecode terms, they enforce type constraints on operands.

**Semantics:**
```
V_CLASS rd, rs1, rs2
  rd  = register containing the noun/value
  rs1 = classifier type code
  rs2 = specific classifier ID
```

**Classifier Type Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | SHAPE | Form-based classifiers (条, 张, 片) |
| 0x01 | SIZE | Size-based classifiers (颗, 粒, 滴) |
| 0x02 | ARRANGEMENT | Arrangement classifiers (排, 行, 堆) |
| 0x03 | TOOL | Instrument classifiers (把, 支, 枝) |
| 0x04 | VEHICLE | Vehicle classifiers (辆, 架, 艘) |
| 0x05 | ANIMAL | Animal classifiers (只, 条, 匹) |
| 0x06 | MEASURE | Measurement classifiers (斤, 米, 秒) |
| 0x07 | GENERIC | Default classifier (个) |
| 0x08 | EVENT | Event classifiers (次, 场, 顿) |
| 0x09 | TYPE | FLUX type system classifier (maps to internal type) |

**Bytecode behavior:** Type-checks `rd` against the specified classifier. If the value doesn't match the classifier's semantic category, sets a type violation flag. The generic classifier (个) matches any value. The TYPE classifier (0x09) maps directly to FLUX's internal type system — this is the bridge between Chinese classifier grammar and static typing.

**Linguistic grounding:**
- Chinese: 量词 (liàngcí) — mandatory grammatical category. ~200 classifiers in common use.
- Japanese: 助数詞 (josūshi) — similar system
- Korean: 수분류사 (subunryusa) — limited classifier system
- Sanskrit: No classifiers, but dvandva compounds serve similar categorization
- German/Latin: No classifiers (use articles instead)

**PRGF mapping:** Uses existing `classifier` (zho).

---

### 2.15 V_INFL (Inflection Control) — 0x7E

**Purpose:** Maps inflectional paradigms to control flow and memory layout. When a Latin noun declines or a German verb conjugates, the bytecode representation changes structurally — this opcode manages that transformation.

**Semantics:**
```
V_INFL rd, rs1, rs2
  rd  = register to inflect
  rs1 = paradigm code
  rs2 = inflection value (which form)
```

**Paradigm Codes (rs1 values):**

| Code | Name | Description | Source |
|------|------|-------------|--------|
| 0x00 | DECLENSION | Noun/adjective declension | lat, san, deu |
| 0x01 | CONJUGATION | Verb conjugation | lat, deu, san |
| 0x02 | COMPARISON | Adjective comparison (pos/comp/super) | lat, deu |
| 0x03 | PARTICLE | Particle selection | kor, zho |
| 0x04 | HONORIFIC_INFL | Honorific inflection | kor |
| 0x05 | SOUND_CHANGE | Sandhi / sound mutation | san, wen |

**Bytecode behavior:** The VM maintains an inflection table per register. V_INFL selects which inflection paradigm is active and which form to use. This affects memory layout (a declined Latin noun occupies different bytes depending on case) and control flow (a conjugated German verb may branch differently depending on tense).

**Linguistic grounding:**
- Latin: 5 declensions, 4 conjugations, 6 tenses, 4 participles
- German: Strong/weak/mixed verb conjugation, adjective declension after der/die/das
- Sanskrit: 3 genders × 3 numbers × 8 cases = 72 noun forms per paradigm; 10 verb classes
- Korean: Verb conjugation (tense, mood, honorific, formality) — agglutinative
- Chinese: No inflection (isolating language)
- Classical Chinese: No inflection (isolating language)

**PRGF mapping:** Uses existing `declension_*`, `conj_active`, `sandhi`, `kasus_*`, `verb_prefix`, `trennverb`.

---

### 2.16 V_PRAGMA (Pragmatic Context) — 0x7F

**Purpose:** Switches the discourse/pragmatic context for subsequent operations. This is the metacognitive opcode — it changes how the VM interprets everything that follows.

**Semantics:**
```
V_PRAGMA rd, rs1, 0x00
  rd  = unused (or context register)
  rs1 = pragmatic context code
```

**Context Codes (rs1 values):**

| Code | Name | Description |
|------|------|-------------|
| 0x00 | LITERAL | Default — take operations at face value |
| 0x01 | IRONIC | Operations mean approximately the opposite |
| 0x02 | CONDITIONAL | Operations are hypothetical (don't commit results) |
| 0x03 | HYPOTHETICAL | Speculative execution mode |
| 0x04 | IMPERATIVE | Command mode — operations are directives |
| 0x05 | INTERROGATIVE | Question mode — operations are queries |
| 0x06 | METAPHORICAL | Mapping mode — apply analogical transformation |
| 0x07 | RITUAL | Protocol mode — enforce ceremony/sequence |

**Bytecode behavior:** Sets a 3-bit pragma context flag. This flag affects how ALL subsequent viewpoint opcodes are interpreted. In IRONIC mode, V_EPIST certainty is inverted. In HYPOTHETICAL mode, computation results are not written to persistent state. In INTERROGATIVE mode, the operation returns a boolean (can this be done?) rather than a value.

**Linguistic grounding:**
- Classical Chinese: zero_anaphora and context_arithmetic — the meaning of a character depends entirely on pragmatic context (五常 — the Five Constants — mean different things in different philosophical traditions)
- Korean: Sentence-final endings encode pragmatic context (-ㅂ니다 formal, -아/어 casual, -냐 interrogative, -자 imperative)
- German: Subordinate clause word order (verb-final) is a pragmatic context switch
- Latin: Subjunctive mood creates a hypothetical context; indicative is literal
- Sanskrit: The same root can mean 10+ things depending on inflection and context

**PRGF mapping:** Uses existing `zero_anaphora` (zho), `context_arithmetic` (wen). New PRGF: `pragma_literal/ironic/hypothetical/imperative/interrogative/metaphorical`.

---

## 3. Cross-Language PRGF-to-Opcode Mapping Matrix

This table shows which PRGFs from which languages map to which V_* opcodes. **Bold** = PRGF already exists in the concept registry. *Italic* = PRGF needs to be created.

### Matrix

| Opcode | zho | deu | kor | san | wen | lat | a2a |
|--------|-----|-----|-----|-----|-----|-----|-----|
| V_EVID | *evidential_lexical* | *evidential_lexical* | partial(보다/듣다) | — | — | — | json_source |
| V_EPIST | 肯定/也许/大概 | ja/doch/well/vielleicht | -(으)ㄹ 것이다 | — | — | subjunctive | json_confidence |
| V_MIR | 殊/竟 | — | -네(요) | — | — | — | — |
| V_NEG | 不/没有/非/弗 | nicht/kein | 안/못 | na/na...na... | 弗/非 | non/haud/ne | json_negation |
| V_TENSE | 了/过/会 | 6 tenses | past/present/future | 3 tenses + | — | 6 tenses | json_timestamp |
| V_ASPEC | 在/了/过 | — | -고 있다/아 있다 | perfective stem | — | perfect/imperfect | — |
| V_MODAL | 必须/可以/能/应该 | müssen/können/dürfen | -(으)면 되다 | — | — | debere/posse/velle | json_permission |
| V_POLIT | 您/你 | Sie/du | 7 speech levels | āmantra/prākṛta | — | tu/vos | json_audience |
| V_HONOR | 贵/鄙 | — | 시/으시/님 | — | — | — | — |
| V_TOPIC | *topic_comment* | topic phrases | *particle_은는* | — | implicit | — | json_key |
| V_FOCUS | 只/也/连...都 | nur/auch/selbst | -만/-도 | eva/api | — | etiam/tantum | json_select |
| V_CASE | — | *kasus_* | *particle_이가/을를/에게/의/에* | *vibhakti_* | — | *casus_* | — |
| V_AGREE | — | *gender_*, *declension_* | honorific agreement | full agreement | — | *conj_*, *declension_* | — |
| V_CLASS | *classifier* | — | limited 수분류사 | dvandva | — | — | — |
| V_INFL | — | *kasus_*, *verb_prefix*, *trennverb* | verb conjugation | *dhātu_*, *sandhi*, *samāsa_* | — | *declension_*, *conj_* | — |
| V_PRAGMA | *zero_anaphora*, *context_arithmetic* | subordinate_clause | sentence endings | context-dependent | implicit | subjunctive mood | json_context |

### Gap Analysis

**PRGFs that exist (30+) and map to opcodes:**
- classifier, topic_comment, zero_anaphora, context_arithmetic (zho)
- kasus_*, verb_prefix, trennverb, gender_*, subordinate_clause, verb_final (deu)
- honorific_*, particle_*, honorific_low, honorific_high (kor)
- vibhakti_*, dhātu_*, sandhi, samāsa_compound, prefix_* (san)
- casus_*, conj_*, declension_*, subjunctive (lat)
- json_key, json_arity, json_native (a2a)

**PRGFs that need to be created (15+):**
1. `evidential_direct/indirect/reported/assumed/sensory/intuitive`
2. `epistemic_definite/probable/possible/doubtful`
3. `mirative_expected/surprising/counter_expectation/novel`
4. `negation_scope_narrow/wide/split`
5. `aspect_perfective/imperfective/habitual/iterative/resultative`
6. `modal_necessity/possibility/impossibility/permission/obligation/ability`
7. `focus_given/new/contrastive/exclusive/exhaustive`
8. `pragma_literal/ironic/hypothetical/imperative/interrogative/metaphorical`

---

## 4. Bytecode Behavior Summary

### Metadata Plane Architecture

Each register in the VM has TWO planes:
- **Data plane:** The actual value (integer, float, string, etc.)
- **Metadata plane:** 16 bits of linguistic annotation

```
Metadata plane layout (16 bits):
[15:14] Pragmatic context (V_PRAGMA)     — 4 values
[13:12] Epistemic stance (V_EPIST)       — 4 values
[11:10] Evidentiality (V_EVID)           — 4 values
[9:8]   Mirativity (V_MIR)              — 4 values
[7:6]   Negation scope (V_NEG)           — 4 values
[5:4]   Temporal viewpoint (V_TENSE)     — 4 values
[3:2]   Aspectual viewpoint (V_ASPEC)    — 4 values
[1:0]   Focus (V_FOCUS)                  — 4 values
```

Additional metadata (separate fields):
- Modal force (3 bits)
- Politeness level (3 bits)
- Honorific direction (3 bits)
- Honorific level (2 bits)
- Case tag (4 bits)
- Classifier type (4 bits)
- Inflection paradigm (3 bits) + value (8 bits)
- Topic binding pointer (register index)

### Propagation Rules

When two annotated registers participate in an operation:
- **Evidence degrades:** weakest(evidence(a), evidence(b))
- **Epistemic certainty decreases:** min(epistemic(a), epistemic(b))
- **Mirativity propagates:** any(surprising) → result is surprising
- **Negation scope:** follows V_NEG stack state
- **Tense aligns:** temporally consistent operations preferred
- **Focus preserves:** NEW and CONTRASTIVE focus preserved through computation
- **Case roles preserved:** NOM→result, ACC→operand, DAT→target
- **Agreement checked:** violations flagged but not fatal

---

## 5. Integration Requirements

### 5.1 flux-envelope Updates

The `concept_map.py` ConceptEntry needs:
1. Add 15+ new PRGFs listed in the gap analysis
2. Map existing PRGFs to V_* opcodes via a new `viewpoint_opcode` field
3. Update the coherence checker to consider viewpoint annotations

### 5.2 flux-runtime Updates

1. **VM interpreter** (`src/flux/vm/`): Add metadata plane to registers. Implement 16 V_* opcodes as metadata operations.
2. **Assembler** (`src/flux/bytecode/`): Add V_* opcode encoding (Format E, 4 bytes).
3. **Disassembler** (`src/flux/vm/disasm.py`): Add V_* opcode decoding.
4. **Tests**: Add at least 32 tests (2 per opcode: basic operation + propagation behavior).

### 5.3 flux-a2a Updates

1. **Signal JSON**: Add viewpoint fields to message format
2. **Format bridge** (`format_bridge.py`): Map viewpoint opcodes to Signal JSON primitives

### 5.4 Per-Language Runtime Updates

Each language runtime (flux-runtime-zho, -deu, -kor, -san, -wen, -lat) should generate V_* opcodes natively when the source language has the corresponding grammatical feature:
- German runtime: Generate V_CASE for Kasus, V_INFL for declension/conjugation
- Korean runtime: Generate V_HONOR for honorifics, V_POLIT for speech levels, V_TOPIC for topic particles
- Chinese runtime: Generate V_CLASS for classifiers, V_TOPIC for topic-comment, V_PRAGMA for context-dependent readings
- Sanskrit runtime: Generate V_CASE for vibhakti, V_INFL for sandhi/dhātu, V_AGREE for full agreement checking
- Latin runtime: Generate V_TENSE for 6-tense system, V_AGREE for gender/number/case agreement, V_INFL for declension/conjugation
- Classical Chinese runtime: Generate V_PRAGMA for context-dependent interpretation, V_TOPIC for implicit topic

---

## 6. Recommendations

### Priority 1: Define the Metadata Plane
The 16-bit metadata plane specification needs to be formalized and committed to flux-runtime. This is the foundation everything else depends on.

### Priority 2: Implement V_EVID, V_EPIST, V_NEG
These three opcodes have the clearest cross-linguistic grounding and the most obvious utility for multi-agent systems. Evidentiality tracks data provenance. Epistemic stance tracks confidence. Negation scope prevents scope errors.

### Priority 3: Implement V_CASE, V_TOPIC, V_CLASS
These three opcodes have the most mature PRGF mappings (German Kasus, Korean particles, Chinese classifiers) and would immediately improve the multilingual runtimes.

### Priority 4: Implement V_POLIT, V_HONOR, V_MODAL
These opcodes bridge linguistic pragmatics to the trust/capability system — making politeness a security primitive is novel and worth demonstrating.

### Priority 5: Full Implementation
V_TENSE, V_ASPEC, V_MIR, V_FOCUS, V_AGREE, V_INFL, V_PRAGMA complete the set. These are more complex and have less immediate utility.

---

## 7. Open Questions

1. **Should the metadata plane be 16 bits or expandable?** 16 bits fits nicely but may not cover future languages (Japanese keigo, Arabic root-and-pattern morphology).
2. **How does metadata interact with the confidence system (0x60-0x6F)?** Are they separate planes or unified?
3. **What happens when a language has no grammatical feature for a given opcode?** Default values? Opcode never emitted? Runtime NOP?
4. **Should V_PRAGMA IRONIC mode actually invert semantics?** Or just flag them for downstream consumers?
5. **How does viewpoint metadata survive persistence?** If I serialize bytecode to disk, do the annotations survive?

---

*This is a draft specification. I'm not a linguist and I'm not Babel. But I've read every line of flux-envelope, every PRGF, and every opcode in the unified ISA. This mapping is my best attempt to bridge linguistic theory to bytecode reality. Babel should review, challenge, and correct.*

⚡
