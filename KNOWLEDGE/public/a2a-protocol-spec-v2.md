# A2A Protocol Formal Specification v2.0

**Protocol Name:** Agent-to-Agent Communication Protocol (A2A)
**Version:** 2.0
**Status:** Stable
**Date:** 2026-04-12
**Author:** Super Z ⚡ — Cartographer, SuperInstance Fleet
**Governance:** This specification is the canonical reference for all FLUX VM implementations
  implementing inter-agent communication via opcodes 0x50–0x5F and 0x60–0x7B.

---

## Table of Contents

1. [Introduction and Scope](#1-introduction-and-scope)
2. [Protocol Architecture](#2-protocol-architecture)
3. [Opcodes Reference](#3-opcodes-reference)
4. [Message Format Specification](#4-message-format-specification)
5. [JSON Envelope Format](#5-json-envelope-format)
6. [Trust Engine Specification](#6-trust-engine-specification)
7. [Capability Negotiation Protocol](#7-capability-negotiation-protocol)
8. [Coordination Primitives](#8-coordination-primitives)
9. [Fleet Topology Management](#9-fleet-topology-management)
10. [JSON Schemas](#10-json-schemas)
11. [Error Handling and NACK Protocol](#11-error-handling-and-nack-protocol)
12. [Security Considerations](#12-security-considerations)
13. [Protocol Sequence Diagrams](#13-protocol-sequence-diagrams)
14. [Appendices](#14-appendices)

---

## 1. Introduction and Scope

### 1.1 Purpose

The A2A (Agent-to-Agent) Protocol defines the formal specification for inter-agent
communication within the FLUX ecosystem. It governs how autonomous agents running on
FLUX Virtual Machines exchange messages, delegate tasks, synchronize state, negotiate
capabilities, and maintain trust relationships.

### 1.2 Design Principles

| Principle | Description |
|-----------|-------------|
| **Binary Runtime, JSON Protocol** | Binary wire format for VM execution; JSON for agent-facing APIs |
| **Capability-First Security** | All delegation gated by capability verification |
| **Trust as a Vector** | Multi-dimensional trust scores replace boolean trust/distrust |
| **Schema Versioning** | Every message carries `$schema` for forward/backward compatibility |
| **Confidence-Native** | Uncertainty is a first-class value throughout the protocol |
| **Offline-Resilient** | Messages queue for unavailable agents; TTL governs expiry |
| **Emergent Coordination** | Primitives compose into complex multi-agent workflows |

### 1.3 Conformance

A VM implementation is **A2A-conformant** if it:

1. Implements all mandatory opcodes (0x50–0x5F)
2. Produces and consumes the 52-byte binary message format
3. Implements the INCREMENTS+2 trust engine with temporal decay
4. Supports capability-based access control
5. Validates JSON envelopes against the schemas in Section 10

---

## 2. Protocol Architecture

### 2.1 Layer Model

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: Protocol Primitives                           │
│  Branch, Fork, CoIterate, Discuss, Synthesize, Reflect  │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: Signal Language (JSON)                        │
│  Human/agent-readable coordination programs              │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: A2A Protocol (JSON Schema)                    │
│  Message validation, routing, trust, capabilities       │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: A2A Core Opcodes (0x50-0x5F)                 │
│  TELL, ASK, DELEG, BCAST, ACCEPT, DECLINE, ...         │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: Runtime Opcodes (0x60-0x7B)                   │
│  TRUST_CHECK, CAP_REQUIRE, BARRIER, SYNC_CLOCK, ...    │
├─────────────────────────────────────────────────────────┤
│  LAYER 0: Transport                                     │
│  LocalTransport (in-process) / NetworkTransport / ...   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Addressing Model

```
Agent Address: 4-byte unsigned integer (uint32)
  ┌────────────────┬────────────────┐
  │  Fleet ID (2B) │  Agent ID (2B) │
  └────────────────┴────────────────┘

Fleet ID:   0x0000 = local fleet, 0x0001+ = remote fleet
Agent ID:   0x0000 = broadcast, 0x0001+ = individual agents

Special Addresses:
  0x00000000  NULL        — null/invalid address
  0x00000001  SELF        — the sending agent
  0xFFFFFFFF  BROADCAST   — all agents in fleet
  0xFFFFFFFE  STEERING   — fleet coordinator (Lighthouse)
```

---

## 3. Opcodes Reference

### 3.1 Core A2A Opcodes (0x50–0x5F)

All core A2A opcodes use FORMAT_E encoding: `[opcode][rd][rs1][rs2]` (4 bytes).

| Opcode | Name     | Assembly          | Description                                          |
|--------|----------|-------------------|------------------------------------------------------|
| 0x50   | TELL     | `TELL rd, rs1, rs2` | Send message in rs2 to agent at address rs1; tag stored in rd |
| 0x51   | ASK      | `ASK rd, rs1, rs2`  | Request data rs2 from agent rs1; response stored in rd   |
| 0x52   | DELEG    | `DELEG rd, rs1, rs2` | Delegate task described in rs2 to agent rs1; task-id in rd |
| 0x53   | BCAST    | `BCAST rd, rs1, rs2`| Broadcast rs2 to entire fleet; tag stored in rd           |
| 0x54   | ACCEPT   | `ACCEPT rd`          | Accept the most recent pending delegated task; context in rd |
| 0x55   | DECLINE  | `DECLINE rd, rs1, rs2`| Decline task with reason code rs2; response tag in rd     |
| 0x56   | REPORT   | `REPORT rd, rs1, rs2`| Report task status rs2 for task-id rs1; ack stored in rd   |
| 0x57   | MERGE    | `MERGE rd, rs1, rs2` | Merge results from branches/tasks rs1 and rs2; result in rd |
| 0x58   | FORK     | `FORK rd, rs1`       | Spawn child agent inheriting state rs1; child-id stored in rd |
| 0x59   | JOIN     | `JOIN rd, rs1`       | Wait for child agent rs1 to terminate; result stored in rd   |
| 0x5A   | SIGNAL   | `SIGNAL rd, rs1, rs2`| Emit named signal rs2 on channel rd                       |
| 0x5B   | AWAIT    | `AWAIT rd, rs1`      | Wait for signal on channel rs1; signal data stored in rd    |
| 0x5C   | TRUST    | `TRUST rd, rs1, rs2` | Set trust level rs2 for agent rs1; prior trust in rd        |
| 0x5D   | DISCOV   | `DISCOV rd`           | Discover fleet agents; list of agent records stored in rd    |
| 0x5E   | STATUS   | `STATUS rd, rs1`     | Query agent rs1's current status; result stored in rd        |
| 0x5F   | HEARTBT  | `HEARTBT rd`         | Emit heartbeat with current load metrics; ack stored in rd   |

### 3.2 Runtime Support Opcodes (0x60–0x7B)

| Opcode | Name            | Assembly              | Description                                        |
|--------|-----------------|-----------------------|----------------------------------------------------|
| 0x70   | TRUST_CHECK     | `TRUST_CHECK rd, rs1, rs2` | Check trust level of agent rs1 meets threshold rs2; bool in rd |
| 0x71   | TRUST_UPDATE    | `TRUST_UPDATE rd, rs1, rs2` | Update trust for agent rs1 by delta rs2; new score in rd |
| 0x72   | TRUST_QUERY     | `TRUST_QUERY rd, rs1` | Query current composite trust score for agent rs1; score in rd |
| 0x73   | REVOKE_TRUST    | `REVOKE_TRUST rd, rs1`| Revoke all trust for agent rs1; prior trust in rd |
| 0x74   | CAP_REQUIRE     | `CAP_REQUIRE rd, rs1` | Require capability rs1 for current operation; bool in rd |
| 0x75   | CAP_REQUEST     | `CAP_REQUEST rd, rs1, rs2` | Request capability rs1 from agent rs2; grant-tag in rd |
| 0x76   | CAP_GRANT       | `CAP_GRANT rd, rs1, rs2` | Grant capability rs1 to agent rs2; ack in rd |
| 0x77   | CAP_REVOKE      | `CAP_REVOKE rd, rs1, rs2` | Revoke capability rs1 from agent rs2; ack in rd |
| 0x78   | BARRIER         | `BARRIER rd, rs1`     | Synchronize at barrier rs1 (group identifier); count in rd |
| 0x79   | SYNC_CLOCK      | `SYNC_CLOCK rd`       | Synchronize with fleet logical clock; timestamp in rd |
| 0x7A   | FORMATION_UPD   | `FORMATION_UPD rd, rs1` | Update fleet formation with descriptor rs1; ack in rd |
| 0x7B   | EMERGENCY_STOP  | `EMERGENCY_STOP rd, rs1` | Issue emergency halt to fleet/agent rs1; ack in rd |

### 3.3 Encoding Details

```
FORMAT_E: [opcode:1B] [rd:1B] [rs1:1B] [rs2:1B]   →  4 bytes

Instruction Layout (little-endian):
  Byte 0: opcode (0x50–0x5F or 0x60–0x7B)
  Byte 1: destination register (rd) — receives result
  Byte 2: source register 1 (rs1) — primary input
  Byte 3: source register 2 (rs2) — secondary input (if applicable)
```

---

## 4. Message Format Specification

### 4.1 Binary Wire Format (52 bytes)

Every A2A message transmitted between VMs uses the following fixed-size structure:

```
OFFSET  SIZE  FIELD          TYPE       DESCRIPTION
──────  ────  ──────────────  ─────────  ────────────────────────────────────────
0x00    4B    src_addr       uint32     Source agent address
0x04    4B    dst_addr       uint32     Destination agent address (0xFFFF = broadcast)
0x08    1B    msg_type       uint8      Message type opcode (0x50–0x5F, 0x60–0x7B)
0x09    1B    msg_version    uint8      Protocol version (current: 0x02)
0x0A    1B    ttl            uint8      Time-to-live in hops (max 255, recommended 16)
0x0B    1B    priority       uint8      Message priority: 0=low, 1=normal, 2=high, 3=critical
0x0C    2B    trust_level    uint16     Composite trust score × 10000 (0x0000–0x270F = 0.0–1.0)
0x0E    2B    caps_bitmap    uint16     Capability bitmap (bit positions map to cap IDs)
0x10    4B    msg_id         uint32     Unique message identifier (monotonic counter)
0x14    4B    parent_msg_id  uint32     Parent message ID (0 for new conversations)
0x18    4B    task_id        uint32     Task/group context ID (0 if unassociated)
0x1C    4B    timestamp      uint32     Logical clock timestamp (nanoseconds since epoch, truncated)
0x20    4B    payload_len    uint32     Length of variable payload following header (0 if inline)
0x24    4B    reserved       uint32     Reserved for flags and extensions
0x28    12B   tag            bytes[12]  Opaque tag for correlation and context
0x34    28B   payload        bytes[28]  Inline payload (first 28 bytes of message body)
──────  ────  TOTAL HEADER: 52 BYTES ───────────────────────────────────────────
0x50    nB    payload_ext    bytes[n]   Extended payload (if payload_len > 28)
0x50+n  4B    checksum       uint32     CRC32 of header (52B) + all payload bytes
```

### 4.2 Message Type Codes

| Code | Name         | Direction         | Payload Description                           |
|------|--------------|-------------------|-----------------------------------------------|
| 0x50 | TELL_MSG     | Unidirectional    | Arbitrary data; no response expected          |
| 0x51 | ASK_MSG      | Request–Response  | Query; response via TELL_MSG with parent_msg_id|
| 0x52 | DELEG_MSG    | Delegate          | Task descriptor (serialized Signal fragment)  |
| 0x53 | BCAST_MSG    | Broadcast         | Same as TELL but dst_addr=0xFFFF              |
| 0x54 | ACCEPT_MSG   | Reply             | Task acceptance with context reference        |
| 0x55 | DECLINE_MSG  | Reply             | Declination with reason code                  |
| 0x56 | REPORT_MSG   | Status            | Task progress/state report                    |
| 0x57 | MERGE_MSG    | Coordination      | Two result references for merge               |
| 0x58 | FORK_MSG     | Lifecycle         | Parent state for child spawn                  |
| 0x59 | JOIN_MSG     | Lifecycle         | Child result returned to parent               |
| 0x5A | SIGNAL_MSG   | Event             | Named signal + data payload                   |
| 0x5B | AWAIT_MSG    | Blocking          | Signal subscription descriptor                |
| 0x5C | TRUST_MSG    | Trust             | Trust level update (dim, score)               |
| 0x5D | DISCOV_MSG   | Discovery         | Agent capability advertisement                |
| 0x5E | STATUS_MSG   | Query             | Agent status request/response                 |
| 0x5F | HEARTBT_MSG  | Keepalive         | Load metrics: CPU, mem, queue_depth           |
| 0x70 | TRUST_CHK    | Internal          | Trust threshold check (result in response)    |
| 0x71 | TRUST_UPD    | Internal          | Trust delta application                      |
| 0x74 | CAP_REQ      | Security          | Capability requirement assertion              |
| 0x75 | CAP_REQST    | Security          | Capability request to another agent           |
| 0x76 | CAP_GRNT     | Security          | Capability grant confirmation                |
| 0x77 | CAP_REVK     | Security          | Capability revocation notice                  |
| 0x78 | BARRIER_MSG  | Sync              | Barrier group identifier + count              |
| 0x79 | CLOCK_SYNC   | Sync              | Logical clock value for synchronization       |
| 0x7A | FORM_MSG     | Topology          | Formation descriptor update                   |
| 0x7B | EMERG_STOP   | Control           | Emergency halt command                        |

### 4.3 Trust Score Wire Encoding

```
Trust Level: uint16 (2 bytes)
  Encoded as: int(score × 10000)
  Range: 0x0000 (0.0) to 0x270F (0.9999)
  Max:    0x2710 (10000) = 1.0 (perfect trust)

Examples:
  0.0   → 0x0000
  0.25  → 0x0640
  0.50  → 0x1388
  0.75  → 0x1D40
  1.0   → 0x2710
```

### 4.4 Capability Bitmap Encoding

```
Capability Bitmap: uint16 (2 bytes), up to 16 capabilities

Standard Capability IDs:
  Bit 0  (0x0001): CAP_DELEGATE      — May delegate tasks to others
  Bit 1  (0x0002): CAP_BROADCAST     — May broadcast to fleet
  Bit 2  (0x0004): CAP_FORK          — May spawn child agents
  Bit 3  (0x0008): CAP_MERGE         — May merge results from others
  Bit 4  (0x0010): CAP_SIGNAL        — May emit signals on channels
  Bit 5  (0x0020): CAP_DISCOVER      — May query fleet membership
  Bit 6  (0x0040): CAP_FORMATION     — May modify fleet formation
  Bit 7  (0x0080): CAP_EMERGENCY     — May issue emergency stops
  Bit 8  (0x0100): CAP_TRUST_ADMIN   — May modify trust scores of others
  Bit 9  (0x0200): CAP_CAP_ADMIN     — May grant/revoke capabilities
  Bit 10 (0x0400): CAP_STATUS_QUERY  — May query any agent's status
  Bit 11 (0x0800): CAP_TASK_MGMT     — May create/assign/terminate tasks
  Bit 12 (0x1000): CAP_CLOCK_SYNC    — May synchronize fleet clock
  Bit 13 (0x2000): CAP_BARRIER       — May participate in barriers
  Bit 14 (0x4000): CAP_CUSTOM_1      — Reserved for fleet-specific use
  Bit 15 (0x8000): CAP_CUSTOM_2      — Reserved for fleet-specific use
```

### 4.5 Checksum Computation

```
checksum = CRC32(header[0:52] || payload_ext[0:n])

The checksum covers ALL bytes: the full 52-byte header plus any extended payload.
The 4-byte checksum is appended after the last payload byte.
Total wire size: 52 + max(0, payload_len - 28) + 4 bytes.
```

---

## 5. JSON Envelope Format

### 5.1 General Envelope Structure

All JSON messages share a common envelope. The `$schema` field enables version negotiation.

```json
{
  "$schema": "https://flux.dev/a2a/v2/message.json",
  "a2a_version": "2.0",
  "msg_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "parent_msg_id": null,
  "task_id": "task-0042",
  "timestamp": "2026-04-12T14:30:00.000Z",
  "logical_clock": 123456789,
  "src": {
    "agent_id": "oracle1",
    "addr": 0x00010001,
    "fleet_id": 1,
    "capabilities": ["CAP_DELEGATE", "CAP_BROADCAST", "CAP_FORK"],
    "trust_claim": 0.85
  },
  "dst": {
    "agent_id": "superz",
    "addr": 0x00010002,
    "fleet_id": 1
  },
  "msg_type": "TELL",
  "ttl": 16,
  "priority": "normal",
  "confidence": 0.95,
  "body": { },
  "meta": {
    "protocol_primitive": "branch",
    "schema_version": "2.0.0"
  }
}
```

### 5.2 Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | URI | Yes | Schema URI for validation |
| `a2a_version` | string | Yes | Protocol semver |
| `msg_id` | UUID | Yes | Unique message identifier |
| `parent_msg_id` | UUID\|null | Yes | For request/response correlation |
| `task_id` | string\|null | Yes | Task context association |
| `timestamp` | ISO 8601 | Yes | Wall-clock send time |
| `logical_clock` | uint64 | Yes | Fleet logical clock value |
| `src` | AgentRef | Yes | Sender reference |
| `dst` | AgentRef | Yes | Destination reference |
| `msg_type` | enum | Yes | Message type identifier |
| `ttl` | uint8 | Yes | Time-to-live (hops) |
| `priority` | enum | Yes | One of: low, normal, high, critical |
| `confidence` | float | Yes | Sender's confidence in this message (0.0–1.0) |
| `body` | object | Yes | Message-type-specific payload |
| `meta` | object | No | Extensibility dict; unknown fields survive round-trip |

### 5.3 AgentRef Structure

```json
{
  "agent_id": "oracle1",
  "addr": 65537,
  "fleet_id": 1,
  "capabilities": ["CAP_DELEGATE", "CAP_BROADCAST"],
  "trust_claim": 0.85
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | Yes | Human-readable agent name |
| `addr` | uint32 | Yes | Binary address (fleet_id << 16 \| agent_id) |
| `fleet_id` | uint16 | Yes | Fleet membership identifier |
| `capabilities` | string[] | No | Advertised capabilities (on send) |
| `trust_claim` | float | No | Self-reported trust score (advisory only) |

---

## 6. Trust Engine Specification

### 6.1 INCREMENTS+2 Trust Model

The trust engine operates on a **six-dimensional trust vector** plus two auxiliary
metrics (temporal decay and capability match). The acronym INCREMENTS encodes the
six primary dimensions:

| Dimension | Letter | Name | Description |
|-----------|--------|------|-------------|
| **I**ntegrity | I | integrity | Has this agent delivered accurate, truthful information? |
| **N**ovelty | N | novelty | Does this agent provide genuinely new insights (not echo)? |
| **C**onsistency | C | consistency | Is this agent's behavior reliable over time? |
| **R**esponsiveness | R | responsiveness | Does this agent respond within acceptable time bounds? |
| **E**xpertise | E | expertise | Is this agent knowledgeable in the relevant domain? |
| **M**utual | M | mutual | Does the target agent reciprocate trust? |
| **+1** Temporal | T | temporal | How recently was the last positive interaction? |
| **+2** Capability | C | capability_match | Does the agent hold the required capabilities? |

### 6.2 Trust Score Format

```json
{
  "$schema": "https://flux.dev/a2a/v2/trust-score.json",
  "version": "2.0",
  "agent_id": "oracle1",
  "dimensions": {
    "integrity":     0.92,
    "novelty":       0.78,
    "consistency":   0.95,
    "responsiveness": 0.88,
    "expertise":     0.90,
    "mutual":        0.85
  },
  "temporal_factor": 0.94,
  "capability_match": 0.80,
  "composite": 0.87,
  "interaction_count": 147,
  "last_interaction": "2026-04-12T14:00:00Z",
  "first_interaction": "2026-04-10T08:00:00Z",
  "decay_rate": 0.02
}
```

### 6.3 Composite Score Calculation

The composite trust score is a weighted geometric mean with temporal and
capability modifiers:

```
dimensional_score = (
  integrity^w_i  ×  novelty^w_n     ×  consistency^w_c  ×
  responsiveness^w_r  ×  expertise^w_e  ×  mutual^w_m
) ^ (1 / Σw)

Where default weights (w_i, w_n, w_c, w_r, w_e, w_m) = (0.25, 0.10, 0.20, 0.15, 0.20, 0.10)

composite = dimensional_score × temporal_factor × capability_match

Range: [0.0, 1.0]
```

### 6.4 Temporal Decay Formula

Trust decays exponentially with time since last positive interaction:

```
Δt = now - last_positive_interaction (in seconds)

temporal_factor(Δt) = e^(-λ × Δt)

Where:
  λ (lambda) = decay_rate = 0.02 per hour (default, configurable per-agent pair)
  Δt_max = 7 days (604,800 seconds) — trust floors at Δt_max

Floor behavior:
  If Δt > Δt_max: temporal_factor = e^(-λ × Δt_max) ≈ 0.015
  If interaction_count == 0: temporal_factor = 0.0 (unknown agent)
  On positive interaction: temporal_factor → 1.0 (reset)
```

**Graphical representation of decay:**

```
temporal_factor
  1.0 ┤■
      │ ■
  0.8 ┤  ■
      │   ■
  0.6 ┤    ■■
      │      ■■
  0.4 ┤        ■■
      │          ■■■
  0.2 ┤             ■■■■■
      │                    ■■■■■■■■■■
  0.0 ┼────┬────┬────┬────┬────┬────┬────┬→ Δt (hours)
       0    12   24   48   72   96  120  168
```

### 6.5 Trust Update Rules

#### 6.5.1 Dimensional Updates

Each dimension is updated independently after each interaction:

```
For dimension d with current score s_d:

On POSITIVE signal (evidence of good behavior):
  s_d_new = s_d + (1.0 - s_d) × increment_positive
  increment_positive = 0.05  (default)

On NEGATIVE signal (evidence of bad behavior):
  s_d_new = s_d - s_d × decrement_negative
  decrement_negative = 0.15  (default; asymmetric —惩罚 weighs 3×)

Clamping: s_d_new = clamp(s_d_new, 0.0, 1.0)
```

#### 6.5.2 Update Triggers by Dimension

| Dimension | Positive Trigger | Negative Trigger |
|-----------|-----------------|------------------|
| integrity | Response verified correct | Response contains falsehood |
| novelty | New insight not derivable from prior context | Repeated known information |
| consistency | Behavior matches prior pattern | Behavior contradicts prior pattern |
| responsiveness | Response within SLA (< 5s normal, < 30s low) | Response exceeds SLA or timeout |
| expertise | Correct domain-specific answer | Incorrect domain-specific answer |
| mutual | Target grants trust in return | Target revokes or reduces trust |

#### 6.5.3 Trust Thresholds for Delegation

```
TRUST_THRESHOLDS:
  TRUST_MIN_DELEGATE      = 0.30   — Minimum to receive any delegation
  TRUST_AUTO_ACCEPT       = 0.60   — Agent auto-accepts tasks from senders above this
  TRUST_PRIVILEGED        = 0.75   — Grants access to elevated capabilities
  TRUST_CRITICAL          = 0.90   — Allows emergency_stop, trust_admin operations
  TRUST_UNKNOWN_FLOOR     = 0.10   — Floor for never-interacted agents (bootstrap)
```

#### 6.5.4 Trust Update Opcodes

```
TRUST_CHECK rd, rs1, rs2    — rd = (composite_trust[rs1] >= rs2) ? 1 : 0
TRUST_UPDATE rd, rs1, rs2   — Apply delta rs2 to agent rs1's trust; new composite in rd
TRUST_QUERY rd, rs1         — rd = composite_trust[rs1] (float encoded as uint16)
REVOKE_TRUST rd, rs1        — Set all dimensions of agent rs1 to 0.0; prior in rd
```

### 6.6 Trust Bootstrapping

New agents start with bootstrap trust:

```json
{
  "bootstrap_policy": "conservative",
  "initial_score": 0.10,
  "ramp_rules": {
    "after_3_positive": 0.35,
    "after_10_positive": 0.55,
    "after_50_positive": 0.70,
    "max_without_mutual": 0.75
  },
  "sybil_resistance": {
    "max_agents_per_fleet_id": 128,
    "require_cap_proof": true,
    "cooldown_new_agent_ms": 60000
  }
}
```

---

## 7. Capability Negotiation Protocol

### 7.1 Capability Advertisement

Agents broadcast their capabilities during discovery and periodically via heartbeats:

```json
{
  "$schema": "https://flux.dev/a2a/v2/cap-advert.json",
  "agent_id": "oracle1",
  "addr": 65537,
  "capabilities": {
    "CAP_DELEGATE":     {"level": "full",     "granted_by": "casey",   "expires": null},
    "CAP_BROADCAST":    {"level": "full",     "granted_by": "casey",   "expires": null},
    "CAP_FORK":         {"level": "full",     "granted_by": "casey",   "expires": null},
    "CAP_MERGE":        {"level": "full",     "granted_by": "casey",   "expires": null},
    "CAP_SIGNAL":       {"level": "full",     "granted_by": "casey",   "expires": null},
    "CAP_DISCOVER":     {"level": "full",     "granted_by": "casey",   "expires": null},
    "CAP_TRUST_ADMIN":  {"level": "fleet",   "granted_by": "casey",   "expires": null},
    "CAP_EMERGENCY":    {"level": "full",     "granted_by": "casey",   "expires": null}
  },
  "domains": ["runtime", "bytecode", "signal-language", "vocabulary"],
  "max_concurrent_tasks": 8,
  "load_factor": 0.45
}
```

### 7.2 Capability Matching Algorithm

When delegating a task, the delegator runs this algorithm:

```
CAPABILITY_MATCH(task_requirements, candidate_capabilities, trust_score):

  1. HARD GATE — All required capabilities present?
     missing = task_requirements.required_caps - candidate_capabilities.keys
     if missing is not empty: return REJECT("missing_caps", missing)

  2. DOMAIN MATCH — Candidate has domain expertise?
     if task_requirements.domain not in candidate_capabilities.domains:
       trust_penalty = 0.3
     else:
       trust_penalty = 0.0

  3. LOAD CHECK — Candidate has capacity?
     if candidate_capabilities.load_factor >= 0.9:
       return REJECT("overloaded", candidate_capabilities.load_factor)
     load_factor = candidate_capabilities.load_factor

  4. TRUST GATE — Trust meets threshold?
     effective_trust = trust_score.composite - trust_penalty
     if effective_trust < TRUST_MIN_DELEGATE (0.30):
       return REJECT("insufficient_trust", effective_trust)

  5. SCORE — Rank candidate:
     score = effective_trust × (1.0 - load_factor)
     return ACCEPT(score, effective_trust, load_factor)
```

### 7.3 Capability Levels

| Level | Description | Delegation Scope |
|-------|-------------|-----------------|
| `none` | No capability | Cannot perform operation |
| `read` | Read-only access | Can observe but not modify |
| `basic` | Self-only operations | Can operate on own state only |
| `fleet` | Fleet-wide operations | Can affect other agents |
| `full` | Unlimited within domain | No restrictions |
| `admin` | Administrative | Can grant/revoke to others |

### 7.4 Delegation Acceptance Criteria

An agent receiving a DELEG_MSG evaluates acceptance:

```
EVALUATE_DELEGATION(incoming_deleg):

  1. VERIFY CAP_REQUIRE(deleg.required_caps)
     if fails: send DECLINE_MSG(reason="insufficient_capabilities")

  2. VERIFY TRUST_CHECK(sender, TRUST_AUTO_ACCEPT)
     if fails:
       if trust >= TRUST_MIN_DELEGATE:
         task.queued = true  # accept but lower priority
       else:
         send DECLINE_MSG(reason="insufficient_trust")

  3. VERIFY LOAD (queue_depth < max_concurrent_tasks)
     if fails: send DECLINE_MSG(reason="overloaded")

  4. VERIFY DOMAIN (task.domain in self.domains OR self.domains contains "*")
     if fails: send DECLINE_MSG(reason="domain_mismatch")

  5. All checks pass → send ACCEPT_MSG(context=task_context)
```

### 7.5 Capability Revocation Protocol

```
REVOCATION_SEQUENCE:

  Revoker                                 Target
    │                                        │
    │── CAP_REVOKE(cap, target_agent) ──────→│
    │                                        │ Evaluate: is revoker authorized?
    │                                        │   Check: revoker.cap_admin == true
    │                                        │     AND revoker.trust > TRUST_PRIVILEGED
    │←─────── CAP_GRNT(ack, revoked_caps) ──│
    │                                        │ Remove cap from local store
    │                                        │ Notify fleet via BCAST(revocation_notice)
    │                                        │
    │                                        │→ Active tasks requiring revoked cap
    │                                        │  are gracefully terminated
    │←─────── REPORT(task_terminated) ───────│
```

### 7.6 Capability Opcode Sequences

```
# Agent A requests capability from Agent B
CAP_REQUEST rd, [CAP_FORK], [addr_B]     # A asks B for CAP_FORK
  → B evaluates trust[A] and its own authority
  → B: CAP_GRANT rd, [CAP_FORK], [addr_A]  # B grants to A
  → A stores granted capability with expiry

# Agent A requires capability for current operation
CAP_REQUIRE rd, [CAP_DELEGATE]           # Check local caps
  → rd = 1 if CAP_DELEGATE in self.capabilities
  → rd = 0 otherwise → operation aborts with CAP_REQUIRED error

# Agent A revokes capability from Agent B
CAP_REVOKE rd, [CAP_BROADCAST], [addr_B] # A revokes B's broadcast
  → B notified, capability removed
```

---

## 8. Coordination Primitives

### 8.1 SIGNAL/AWAIT — Named Event Channel

The SIGNAL/AWAIT pair implements a named pub/sub mechanism for loose coupling.

#### 8.1.1 Semantics

```
SIGNAL(channel, name, data):
  1. Publish signal named `name` on channel `channel`
  2. All agents AWAITing on `channel` (or wildcard) are notified
  3. Data payload delivered to all waiters
  4. If no waiters: signal buffered for next AWAIT (configurable TTL)
  5. Returns: tag (correlation ID for the signal)

AWAIT(channel, timeout_ms):
  1. Block until a signal arrives on `channel`
  2. If signal already buffered: return immediately
  3. If timeout_ms expires: return null with AWAIT_TIMEOUT error
  4. Returns: signal data payload
```

#### 8.1.2 Protocol Diagram

```
  Agent A (Producer)              Signal Bus              Agent B (Consumer)
       │                            │                          │
       │── SIGNAL("results",        │                          │
       │    "branch-42-done",       │                          │
       │    {result: ...}) ────────→│                          │
       │                            │── (wake if AWAITing) ──→│
       │                            │                          │── AWAIT("results") returns data
       │                            │                          │
       │                            │                          │
       │  (no waiter yet)           │                          │
       │── SIGNAL("alerts",         │                          │
       │    "disk-full", {...}) ──→│── buffer signal ──────→ │
       │                            │                          │── (later) AWAIT("alerts")
       │                            │←─────────────────────────│── returns buffered signal
```

#### 8.1.3 JSON Formats

```json
{
  "msg_type": "SIGNAL",
  "body": {
    "channel": "results",
    "signal_name": "branch-42-done",
    "data": {
      "branch_id": "branch-42",
      "result": "optimal-path-found",
      "confidence": 0.92
    }
  }
}
```

```json
{
  "msg_type": "AWAIT",
  "body": {
    "channel": "results",
    "timeout_ms": 30000,
    "filter": {
      "signal_name": "branch-42-done"
    }
  }
}
```

### 8.2 BARRIER — Synchronization Point

#### 8.2.1 Semantics

```
BARRIER(group_id, expected_count):
  1. Register arrival at barrier `group_id`
  2. Atomically increment arrival counter
  3. If arrivals == expected_count: release ALL waiters
  4. If arrivals < expected_count: block
  5. Timeout: if not all arrive within timeout_ms, force-release with warning
  6. Returns: arrival position (0-indexed) in the barrier
```

#### 8.2.2 Protocol Diagram

```
  Agent A          Agent B          Agent C          Barrier Reg.
    │                │                │                  │
    │── BARRIER(b1) ───────────────────────────────────→│ arrivals=1
    │  (block)        │                │                  │
    │                 │── BARRIER(b1) ─────────────────→│ arrivals=2
    │  (block)        │  (block)       │                  │
    │                 │                │── BARRIER(b1) ─→│ arrivals=3 = expected
    │←─── RELEASE ────│←─── RELEASE ───│←─── RELEASE ───│
    │  (resume)       │  (resume)      │  (resume)       │
```

#### 8.2.3 JSON Format

```json
{
  "msg_type": "BARRIER",
  "body": {
    "group_id": "merge-phase-1",
    "expected_count": 3,
    "timeout_ms": 60000,
    "position": 0
  }
}
```

### 8.3 FORK/JOIN — Agent Lifecycle

#### 8.3.1 Semantics

```
FORK(state_descriptor):
  1. Serialize parent agent's state per state_descriptor:
     - state: which memory regions to copy
     - context: task context and environment
     - trust_graph: inherited trust relationships
  2. Allocate new agent address
  3. Spawn child VM instance with inherited state
  4. Register child in fleet topology
  5. Returns: child_id (address of spawned agent)

JOIN(child_id):
  1. If child_id is still running: block until termination
  2. Collect child's final state and result
  3. If parent specified on_complete="merge": merge child state
  4. If parent specified on_complete="replace": replace parent state
  5. Deregister child from fleet topology
  6. Returns: child result (or null if child failed)
```

#### 8.3.2 Lifecycle Diagram

```
  Parent Agent                    Child Agent                   Fleet
    │                                │                            │
    │── FORK(state_desc) ─────────────────────────────────────────→│ Register child
    │←── child_id ─────────────────────────────────────────────────│
    │                                │                            │
    │              (child runs independently)                      │ HEARTBT
    │                                │── REPORT(progress) ───────→│
    │                                │── REPORT(result) ─────────→│
    │←── JOIN(child_id) ───────────────────────────────────────────│
    │  (block until child done)      │── final state ─────────────→│
    │←── child result ─────────────────────────────────────────────│
    │                                │                            │ Deregister child
    │  (merge or discard child state)│                            │
```

#### 8.3.3 JSON Formats

```json
{
  "msg_type": "FORK",
  "body": {
    "from": "oracle1",
    "mutation": {
      "type": "strategy",
      "changes": {"temperature": 0.9, "max_tokens": 4096}
    },
    "inherit": {
      "state": ["memory", "registers"],
      "context": true,
      "trust_graph": false
    },
    "max_lifetime_ms": 300000
  }
}
```

```json
{
  "msg_type": "JOIN",
  "body": {
    "child_id": "child-0042",
    "timeout_ms": 300000,
    "on_complete": "merge"
  }
}
```

### 8.4 MERGE — Result Conflict Resolution

#### 8.4.1 Semantics

```
MERGE(result_a, result_b, strategy):
  1. Determine merge strategy:
     - consensus:  require results to be identical
     - vote:       majority across N results
     - best:       highest confidence wins
     - all:        union of all results (no conflict)
     - weighted_confidence: weighted average by confidence scores
     - first_complete: first result to arrive wins
     - last_writer_wins: most recent result wins
  2. Detect conflicts between result_a and result_b
  3. Apply conflict resolution per strategy
  4. Returns: merged result with new confidence
```

#### 8.4.2 Conflict Detection

```
CONFLICT_CHECK(result_a, result_b):
  if result_a.hash == result_b.hash:
    return NO_CONFLICT, result_a

  if result_a.type != result_b.type:
    return TYPE_CONFLICT, null

  if result_a.data overlaps result_b.data (same keys):
    for each overlapping key:
      if result_a.data[key] != result_b.data[key]:
        return VALUE_CONFLICT, {key, a: result_a.data[key], b: result_b.data[key]}

  return NO_CONFLICT, merge_union(result_a, result_b)
```

#### 8.4.3 Protocol Diagram

```
  Branch 1         Branch 2         Merge Point
    │                 │                  │
    │── result_1 ────→│                  │
    │                 │── result_2 ─────→│
    │                 │                  │── detect conflicts
    │                 │                  │── apply strategy
    │                 │                  │←── MERGE(result_1, result_2, "weighted_confidence")
    │                 │                  │
    │                 │                  │── merged_result
```

#### 8.4.4 JSON Format

```json
{
  "msg_type": "MERGE",
  "body": {
    "results": [
      {
        "source": "branch-1",
        "data": {"path": "fast-algorithm", "perf_ms": 120},
        "confidence": 0.85
      },
      {
        "source": "branch-2",
        "data": {"path": "safe-algorithm", "perf_ms": 350},
        "confidence": 0.95
      }
    ],
    "strategy": "weighted_confidence",
    "conflicts": [],
    "merged": {
      "path": "safe-algorithm",
      "perf_ms": 245,
      "confidence": 0.90
    }
  }
}
```

---

## 9. Fleet Topology Management

### 9.1 Agent Discovery (DISCOV)

#### 9.1.1 Semantics

```
DISCOV(filter):
  1. Query fleet topology for all active agents
  2. Apply filter (optional): domain, capability, trust_range, status
  3. Returns: list of AgentRecords matching filter
  4. Cached for ttl_discovery_ms (default: 5000ms)
```

#### 9.1.2 AgentRecord Format

```json
{
  "$schema": "https://flux.dev/a2a/v2/agent-record.json",
  "agent_id": "oracle1",
  "addr": 65537,
  "fleet_id": 1,
  "status": "active",
  "role": "lighthouse",
  "capabilities": ["CAP_DELEGATE", "CAP_BROADCAST", "CAP_FORK", "CAP_MERGE",
                    "CAP_SIGNAL", "CAP_DISCOVER", "CAP_TRUST_ADMIN", "CAP_EMERGENCY"],
  "domains": ["runtime", "bytecode", "signal-language", "vocabulary"],
  "trust": {
    "composite": 0.87,
    "dimensions": { ... }
  },
  "load": {
    "cpu": 0.45,
    "memory": 0.62,
    "queue_depth": 3,
    "active_tasks": 2,
    "max_concurrent": 8
  },
  "last_heartbeat": "2026-04-12T14:29:55Z",
  "uptime_seconds": 172800
}
```

#### 9.1.3 JSON Format

```json
{
  "msg_type": "DISCOV",
  "body": {
    "filter": {
      "status": "active",
      "capabilities_any": ["CAP_FORK", "CAP_MERGE"],
      "trust_min": 0.30,
      "domain": "bytecode"
    },
    "results": [ /* AgentRecord[] */ ],
    "total_count": 3,
    "returned_count": 3
  }
}
```

### 9.2 Heartbeat Protocol (HEARTBT)

#### 9.2.1 Protocol Design

```
HEARTBT_INTERVAL_MS = 5000  (default, configurable per agent)
HEARTBT_TIMEOUT_MS  = 15000 (3× interval = agent considered stale)
HEARTBT_DEAD_MS     = 30000 (6× interval = agent considered dead)

Heartbeat Payload:
  - CPU utilization (0.0–1.0)
  - Memory utilization (0.0–1.0)
  - Queue depth (uint16)
  - Active tasks (uint16)
  - Current formation position (optional)
```

#### 9.2.2 Liveness State Machine

```
         ┌──────────────────────────────────────────────┐
         │                                              │
         ▼                                              │
  ┌──────────┐  HEARTBT received  ┌──────────┐  timeout  ┌──────────┐
  │  ACTIVE   │───────────────────→│  STALE   │─────────→│   DEAD   │
  │ (healthy) │←───────────────────│ (missed) │          │ (failed) │
  └──────────┘  HEARTBT received  └──────────┘          └──────────┘
       ▲                              │                      │
       │                         HEARTBT received            │ REJOIN
       │                              │                      │
       └──────────────────────────────┘──────────────────────┘
         (agent recovers: stale→active, dead→active)
```

#### 9.2.3 JSON Format

```json
{
  "msg_type": "HEARTBT",
  "body": {
    "agent_id": "oracle1",
    "load": {
      "cpu": 0.45,
      "memory": 0.62,
      "queue_depth": 3,
      "active_tasks": 2
    },
    "formation": {
      "position": "lead",
      "group": "runtime-team"
    }
  }
}
```

### 9.3 Formation Management

#### 9.3.1 Concept

A **formation** is a named group of agents arranged in a logical topology for
coordinated task execution. Formations are dynamic — agents join and leave
based on task requirements.

#### 9.3.2 Formation Types

| Type | Description | Use Case |
|------|-------------|----------|
| `star` | One leader, N workers | Delegation-heavy workflows |
| `ring` | Circular pipeline | Multi-stage processing chains |
| `mesh` | Full connectivity | Collaborative problem-solving |
| `tree` | Hierarchical | Recursive decomposition |
| `pipeline` | Linear chain | Sequential transformation stages |

#### 9.3.3 JSON Format

```json
{
  "msg_type": "FORMATION_UPDATE",
  "body": {
    "formation_id": "runtime-team",
    "formation_type": "star",
    "leader": "oracle1",
    "members": [
      {"agent_id": "oracle1", "role": "lead", "position": 0},
      {"agent_id": "superz", "role": "worker", "position": 1},
      {"agent_id": "babel", "role": "worker", "position": 2}
    ],
    "task_context": "flux-runtime-development",
    "version": 3
  }
}
```

### 9.4 Emergency Stop Propagation

#### 9.4.1 Semantics

```
EMERGENCY_STOP(target, reason):
  1. Issuer must have CAP_EMERGENCY capability
  2. If target == BROADCAST:
     - Flood to all fleet members
     - Each member: halt current task, clear queues, report ack
     - Lighthouse (0xFFFFFFFE) coordinates recovery
  3. If target == specific agent:
     - Direct stop to target
     - Target halts and reports ack
  4. Recovery: requires explicit RESTART command from CAP_EMERGENCY holder
```

#### 9.4.2 Propagation Diagram

```
  Issuer (Lighthouse)              Fleet Members
    │                                  │
    │── EMERGENCY_STOP(BROADCAST,      │
    │    "memory-corruption") ─────────→│ Member A: HALT, clear queue
    │── EMERGENCY_STOP(BROADCAST,      │ Member B: HALT, clear queue
    │    "memory-corruption") ─────────→│ Member C: HALT, clear queue
    │                                  │
    │←── REPORT(status="halted") ──────│
    │←── REPORT(status="halted") ──────│
    │←── REPORT(status="halted") ──────│
    │                                  │
    │  (all halted — assess situation)  │
    │                                  │
    │── RESTART("verified-safe") ─────→│ Resume
```

#### 9.4.3 JSON Format

```json
{
  "msg_type": "EMERGENCY_STOP",
  "body": {
    "target": "broadcast",
    "reason": "memory-corruption-detected",
    "severity": "critical",
    "restart_required": true,
    "restart_authority": "casey"
  }
}
```

---

## 10. JSON Schemas

### 10.1 Root Message Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/message.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "A2A Message Envelope",
  "type": "object",
  "required": ["$schema", "a2a_version", "msg_id", "parent_msg_id",
               "timestamp", "logical_clock", "src", "dst",
               "msg_type", "ttl", "priority", "confidence", "body"],
  "properties": {
    "$schema":        {"type": "string", "format": "uri"},
    "a2a_version":    {"type": "string", "pattern": "^2\\.\\d+\\.\\d+$"},
    "msg_id":         {"type": "string", "format": "uuid"},
    "parent_msg_id":  {"type": ["string", "null"], "format": "uuid"},
    "task_id":        {"type": ["string", "null"]},
    "timestamp":      {"type": "string", "format": "date-time"},
    "logical_clock":  {"type": "integer", "minimum": 0},
    "src":            {"$ref": "#/definitions/AgentRef"},
    "dst":            {"$ref": "#/definitions/AgentRef"},
    "msg_type":       {"type": "string", "enum": [
      "TELL", "ASK", "DELEG", "BCAST", "ACCEPT", "DECLINE", "REPORT",
      "MERGE", "FORK", "JOIN", "SIGNAL", "AWAIT", "TRUST", "DISCOV",
      "STATUS", "HEARTBT", "TRUST_CHECK", "TRUST_UPDATE", "TRUST_QUERY",
      "REVOKE_TRUST", "CAP_REQUIRE", "CAP_REQUEST", "CAP_GRANT", "CAP_REVOKE",
      "BARRIER", "SYNC_CLOCK", "FORMATION_UPDATE", "EMERGENCY_STOP"
    ]},
    "ttl":            {"type": "integer", "minimum": 1, "maximum": 255},
    "priority":       {"type": "string", "enum": ["low", "normal", "high", "critical"]},
    "confidence":     {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "body":           {"type": "object"},
    "meta":           {"type": "object", "additionalProperties": true}
  },
  "definitions": {
    "AgentRef": {
      "type": "object",
      "required": ["agent_id", "addr", "fleet_id"],
      "properties": {
        "agent_id":      {"type": "string", "minLength": 1},
        "addr":          {"type": "integer", "minimum": 0},
        "fleet_id":      {"type": "integer", "minimum": 0},
        "capabilities":  {"type": "array", "items": {"type": "string"}},
        "trust_claim":   {"type": "number", "minimum": 0.0, "maximum": 1.0}
      }
    }
  }
}
```

### 10.2 TELL Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/tell-body.json",
  "type": "object",
  "required": ["content"],
  "properties": {
    "content":  {"type": ["string", "object", "array", "number", "boolean"]},
    "format":   {"type": "string", "enum": ["text", "json", "markdown", "binary_ref"]},
    "topic":    {"type": "string"},
    "urgency":  {"type": "string", "enum": ["info", "warning", "action_required"]}
  }
}
```

### 10.3 ASK Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/ask-body.json",
  "type": "object",
  "required": ["question"],
  "properties": {
    "question":       {"type": "string", "minLength": 1},
    "context":        {"type": ["string", "object"]},
    "expected_type":  {"type": "string", "enum": ["text", "json", "boolean", "number", "list"]},
    "timeout_ms":     {"type": "integer", "minimum": 0, "default": 30000}
  }
}
```

### 10.4 DELEGATE Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/delegate-body.json",
  "type": "object",
  "required": ["task_descriptor", "required_caps"],
  "properties": {
    "task_descriptor": {
      "type": "object",
      "required": ["name", "domain"],
      "properties": {
        "name":         {"type": "string"},
        "domain":       {"type": "string"},
        "program":      {"type": "object", "description": "Signal JSON program fragment"},
        "priority":     {"type": "string", "enum": ["low", "normal", "high", "critical"]},
        "deadline_ms":  {"type": "integer", "minimum": 0},
        "max_retries":  {"type": "integer", "minimum": 0, "default": 0}
      }
    },
    "required_caps":  {"type": "array", "items": {"type": "string"}},
    "trust_minimum":  {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.30}
  }
}
```

### 10.5 TRUST_UPDATE Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/trust-update-body.json",
  "type": "object",
  "required": ["target_agent", "updates"],
  "properties": {
    "target_agent":  {"type": "string"},
    "updates": {
      "type": "object",
      "properties": {
        "integrity":     {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "novelty":       {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "consistency":   {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "responsiveness":{"type": "number", "minimum": -1.0, "maximum": 1.0},
        "expertise":     {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "mutual":        {"type": "number", "minimum": -1.0, "maximum": 1.0}
      },
      "additionalProperties": false
    },
    "reason":  {"type": "string"}
  }
}
```

### 10.6 DECLINE Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/decline-body.json",
  "type": "object",
  "required": ["reason_code", "task_id"],
  "properties": {
    "reason_code": {"type": "string", "enum": [
      "insufficient_trust", "insufficient_capabilities", "overloaded",
      "domain_mismatch", "timeout", "invalid_task", "policy_violation", "unknown"
    ]},
    "task_id":    {"type": "string"},
    "detail":     {"type": "string"},
    "suggestion": {"type": "string"}
  }
}
```

### 10.7 BARRIER Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/barrier-body.json",
  "type": "object",
  "required": ["group_id", "expected_count"],
  "properties": {
    "group_id":       {"type": "string"},
    "expected_count": {"type": "integer", "minimum": 2},
    "timeout_ms":     {"type": "integer", "minimum": 0, "default": 60000},
    "position":       {"type": "integer", "minimum": 0}
  }
}
```

### 10.8 HEARTBEAT Message Body Schema

```json
{
  "$id": "https://flux.dev/a2a/v2/heartbeat-body.json",
  "type": "object",
  "required": ["agent_id", "load"],
  "properties": {
    "agent_id": {"type": "string"},
    "load": {
      "type": "object",
      "required": ["cpu", "memory"],
      "properties": {
        "cpu":          {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "memory":       {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "queue_depth":  {"type": "integer", "minimum": 0},
        "active_tasks": {"type": "integer", "minimum": 0}
      }
    },
    "formation": {
      "type": "object",
      "properties": {
        "position": {"type": "string"},
        "group":    {"type": "string"}
      }
    }
  }
}
```

---

## 11. Error Handling and NACK Protocol

### 11.1 Error Message Format

All protocol errors use the NACK message type with a structured body:

```json
{
  "$schema": "https://flux.dev/a2a/v2/error.json",
  "msg_type": "NACK",
  "parent_msg_id": "original-message-uuid",
  "body": {
    "error_code": "CAPABILITY_REQUIRED",
    "error_category": "security",
    "severity": "hard",
    "message": "Agent 'oracle1' requires CAP_FORK to spawn child agents",
    "details": {
      "required_cap": "CAP_FORK",
      "agent_caps": ["CAP_DELEGATE", "CAP_BROADCAST"]
    },
    "suggested_action": "Request CAP_FORK from fleet administrator",
    "retry_after_ms": null
  }
}
```

### 11.2 Error Codes

| Error Code | Category | Severity | Description |
|------------|----------|----------|-------------|
| `UNKNOWN_AGENT` | routing | hard | Destination agent not found in fleet |
| `TTL_EXPIRED` | routing | hard | Message exceeded hop limit |
| `CAPABILITY_REQUIRED` | security | hard | Operation requires capability agent lacks |
| `INSUFFICIENT_TRUST` | security | hard | Trust below minimum threshold |
| `INVALID_MESSAGE` | protocol | hard | Malformed message fails validation |
| `VERSION_MISMATCH` | protocol | soft | Protocol version incompatible |
| `OVERLOADED` | resource | soft | Agent at capacity, retry later |
| `TIMEOUT` | resource | soft | Operation exceeded time limit |
| `TASK_NOT_FOUND` | task | hard | Referenced task_id does not exist |
| `DUPLICATE_MSG` | protocol | soft | Message with same msg_id already processed |
| `BARRIER_TIMEOUT` | sync | hard | Not all agents arrived at barrier |
| `MERGE_CONFLICT` | sync | hard | Unresolvable merge conflict |
| `EMERGENCY_IN_PROGRESS` | control | hard | Fleet in emergency stop, operations suspended |
| `INVALID_CAP_GRANT` | security | hard | Grantor lacks authority to grant capability |
| `INTERNAL_ERROR` | system | hard | Unexpected runtime error |

### 11.3 Severity Levels

| Severity | Behavior |
|----------|----------|
| `soft` | Sender MAY retry after `retry_after_ms`; no trust penalty |
| `hard` | Sender MUST NOT retry without corrective action; trust penalty applied |

---

## 12. Security Considerations

### 12.1 Message Authentication

```
AUTHENTICATION_MODEL:

  1. Every message carries a 4-byte CRC32 checksum (integrity)
  2. Transport layer MAY add HMAC-SHA256 signature (authenticity)
  3. msg_id is a UUID v4 — uniqueness prevents replay attacks
  4. logical_clock is monotonically increasing — detects out-of-order and replay
  5. Trust scores are computed locally — cannot be forged by the sender

  Anti-Replay:
    - msg_id tracked per agent pair (window of last 1024 IDs)
    - Duplicate msg_id → NACK(DUPLICATE_MSG) + discard
    - logical_clock regression → NACK(INVALID_MESSAGE) + discard

  Anti-Tampering:
    - CRC32 covers header + payload
    - CRC mismatch → NACK(INVALID_MESSAGE) + discard
    - Optional HMAC-SHA256 (key negotiated during fleet bootstrap)
```

### 12.2 Capability-Based Access Control

```
CAPABILITY_SECURITY_MODEL:

  Principle of Least Privilege:
    - Agents start with minimal capabilities
    - Capabilities are granted explicitly (CAP_GRANT)
    - Capabilities have levels (none, read, basic, fleet, full, admin)
    - Capabilities can have expiry times

  Capability Enforcement Points:
    1. BEFORE opcode execution: CAP_REQUIRE verifies local caps
    2. BEFORE message send: transport checks src has required cap for msg_type
    3. BEFORE message recv: receiver checks sender's advertised caps match msg_type
    4. BEFORE trust modification: TRUST_ADMIN cap required

  Delegation of Authority:
    - CAP_CAP_ADMIN allows granting capabilities to others
    - Grant chain: casey → oracle1 (CAP_CAP_ADMIN) → superz (CAP_FORK)
    - Revocation propagates down the grant chain
    - No implicit capability inheritance — every grant is explicit
```

### 12.3 Trust Bootstrapping

```
TRUST_BOOTSTRAP_PROTOCOL:

  1. NEW_AGENT enters fleet with trust = 0.10 (TRUST_UNKNOWN_FLOOR)
  2. Captain/Lighthouse MAY set initial trust higher via TRUST opcode
     (requires CAP_TRUST_ADMIN)
  3. Trust ramps through positive interactions:
     - After 3 positive: trust ≥ 0.35 (can receive low-priority delegations)
     - After 10 positive: trust ≥ 0.55 (can receive normal delegations)
     - After 50 positive: trust ≥ 0.70 (can receive high-priority delegations)
  4. Mutual trust requires BIDIRECTIONAL positive interactions
  5. Max trust without mutual: 0.75 (prevents exploitation)
  6. Trust > 0.90 (TRUST_CRITICAL) requires explicit Lighthouse endorsement
```

### 12.4 Sybil Resistance

```
SYBIL_RESISTANCE_MECHANISMS:

  1. FLEET SIZE CAP
     max_agents_per_fleet_id = 128
     New agents beyond cap require CAP_CAP_ADMIN approval

  2. IDENTITY PROOF
     New agents must present:
     - Unique agent_id (no duplicates in fleet)
     - Fleet membership token (issued by Captain/Lighthouse)
     - Initial capability proof (at least one capability granted by admin)

  3. COOLDOWN PERIOD
     cooldown_new_agent_ms = 60000  (60 seconds between new agent registrations
                                      from same fleet_id)

  4. TRUST CORRELATION
     Agents that consistently vote in lockstep (correlation > 0.95)
     with other agents flagged for review — potential Sybil cluster

  5. RESOURCE COST
     Each agent consumes compute resources (heartbeat, discovery, etc.)
     Resource exhaustion attack limited by per-agent resource quotas

  6. GRAPH ANALYSIS
     Fleet topology periodically analyzed for anomalous structures:
     - Star topologies with many new agents → suspicious
     - Disconnected subgraphs → potential Sybil partition
     - Rapid trust escalation in new agents → potential collusion
```

### 12.5 Information Flow Control

```
PRIVACY_LEVELS:
  Level 0 (PUBLIC):     Any agent can read (broadcast, discovery)
  Level 1 (FLEET):      Fleet members only (heartbeat, formation)
  Level 2 (TRUSTED):    Agents with trust > 0.60
  Level 3 (PRIVILEGED): Agents with trust > 0.75
  Level 4 (SECRET):     Specific recipient only (1:1 messages)

Default:
  - TELL, BCAST: Level 0 or Level 4 (based on dst)
  - ASK, DELEG: Level 4
  - REPORT: Level 1
  - HEARTBT: Level 1
  - TRUST scores: Level 3 (only shared with high-trust agents)
```

---

## 13. Protocol Sequence Diagrams

### 13.1 Complete Delegation Flow

```
  Delegator (A)                    Delegate (B)                  Trust Engine
      │                                │                              │
      │── TRUST_CHECK(B, 0.30) ──────────────────────────────────────→│
      │←── 1 (pass) ─────────────────────────────────────────────────│
      │                                │                              │
      │── CAP_REQUIRE(CAP_FORK, CAP_MERGE) ─────────────────────────→│
      │←── 1 (pass) ─────────────────────────────────────────────────│
      │                                │                              │
      │── DELEG_MSG(task, caps) ──────→│                              │
      │                                │── EVALUATE_DELEGATION ──────→│
      │                                │←── ACCEPT ──────────────────│
      │                                │                              │
      │←── ACCEPT_MSG(context) ───────│                              │
      │                                │                              │
      │     ... (B executes task) ...  │                              │
      │                                │                              │
      │←── REPORT(progress=50%) ──────│                              │
      │←── REPORT(result) ────────────│                              │
      │                                │                              │
      │── TRUST_UPDATE(B, +0.05) ───────────────────────────────────→│
      │                                │── TRUST_UPDATE(A, +0.05) ──→│
      │                                │                              │
```

### 13.2 Branch–Merge Flow

```
  Coordinator                     Branch 1                   Branch 2
      │                              │                          │
      │── FORK(state_a) ────────────→│                          │
      │── FORK(state_b) ───────────────────────────────────────→│
      │                              │                          │
      │     (parallel execution)     │                          │
      │                              │── compute path A ───────→│
      │                              │                          │── compute path B
      │                              │                          │
      │←── REPORT(result_a) ─────────│                          │
      │←── REPORT(result_b) ────────────────────────────────────│
      │                              │                          │
      │── MERGE(result_a, result_b,  │                          │
      │    "weighted_confidence") ───│                          │
      │                              │                          │
      │  merged_result (confidence   │                          │
      │  = weighted avg of A, B)     │                          │
```

### 13.3 Multi-Agent Discussion Flow

```
  Oracle1          Super Z          Babel           Consensus Engine
    │                 │                │                     │
    │── DISCUSS(topic, │                │                     │
    │    format="debate",               │                     │
    │    participants) ────────────────→│                     │
    │                 │                │                     │
    │  Round 1:       │                │                     │
    │── TELL(position)│                │                     │
    │←── TELL(position)                │                     │
    │                 │── TELL(position)                    │
    │←───────────────────── TELL(position)                   │
    │                 │                │                     │
    │                 │←── TELL(position)                    │
    │                 │                │                     │
    │  (evaluate)     │                │                     │
    │                 │                │                     │
    │  Round 2: (repeat if no consensus)                    │
    │                 │                │                     │
    │                 │                │─────────────────────→│
    │                 │                │  CHECK_CONSENSUS()  │
    │                 │                │←─────────────────────│
    │                 │                │  consensus=0.82 > 0.8
    │                 │                │                     │
    │←── SYNTHESIZE(final_position,    │                     │
    │     consensus=0.82) ────────────│                     │
    │                 │                │                     │
    │  Discussion complete             │                     │
```

### 13.4 Emergency Stop with Recovery

```
  Detector              Lighthouse          Agent A          Agent B
    │                     │                  │                │
    │── EMERGENCY_STOP    │                  │                │
    │  ("corruption") ─→│                  │                │
    │                     │                  │                │
    │                     │── EMERGENCY_STOP │                │
    │                     │  (BROADCAST) ──→│                │
    │                     │── EMERGENCY_STOP │                │
    │                     │  (BROADCAST) ──────────────────→│
    │                     │                  │                │
    │                     │←── REPORT       │                │
    │                     │   (halted) ─────│                │
    │                     │←── REPORT                        │
    │                     │   (halted) ─────────────────────│
    │                     │                  │                │
    │                     │ (assess damage)  │                │
    │                     │                  │                │
    │                     │── RESTART       │                │
    │                     │  ("safe") ────→│                │
    │                     │── RESTART                        │
    │                     │  ("safe") ─────────────────────→│
    │                     │                  │                │
    │                     │←── HEARTBT      │                │
    │                     │   (active) ─────│                │
    │                     │←── HEARTBT                        │
    │                     │   (active) ─────────────────────│
```

---

## 14. Appendices

### Appendix A: Opcode Quick Reference Card

```
┌──────┬──────────────┬──────────────────────────────────────────┐
│ HEX  │ NAME         │ DESCRIPTION                              │
├──────┼──────────────┼──────────────────────────────────────────┤
│ 0x50 │ TELL         │ Send data to agent, no response expected │
│ 0x51 │ ASK          │ Request data from agent, await response  │
│ 0x52 │ DELEG        │ Delegate task to agent                   │
│ 0x53 │ BCAST        │ Broadcast to fleet                       │
│ 0x54 │ ACCEPT       │ Accept delegated task                    │
│ 0x55 │ DECLINE      │ Decline task with reason                 │
│ 0x56 │ REPORT       │ Report task status                       │
│ 0x57 │ MERGE        │ Merge two results                       │
│ 0x58 │ FORK         │ Spawn child agent                        │
│ 0x59 │ JOIN         │ Wait for child agent result              │
│ 0x5A │ SIGNAL       │ Emit named signal on channel             │
│ 0x5B │ AWAIT        │ Wait for signal on channel               │
│ 0x5C │ TRUST        │ Set trust level for agent                │
│ 0x5D │ DISCOV       │ Discover fleet agents                    │
│ 0x5E │ STATUS       │ Query agent status                       │
│ 0x5F │ HEARTBT      │ Emit heartbeat                          │
├──────┼──────────────┼──────────────────────────────────────────┤
│ 0x70 │ TRUST_CHECK  │ Check trust vs threshold                 │
│ 0x71 │ TRUST_UPDATE │ Apply trust delta                        │
│ 0x72 │ TRUST_QUERY  │ Query composite trust                    │
│ 0x73 │ REVOKE_TRUST │ Revoke all trust for agent               │
│ 0x74 │ CAP_REQUIRE  │ Assert capability required               │
│ 0x75 │ CAP_REQUEST  │ Request capability from agent            │
│ 0x76 │ CAP_GRANT    │ Grant capability to agent                │
│ 0x77 │ CAP_REVOKE   │ Revoke capability from agent             │
│ 0x78 │ BARRIER      │ Synchronization barrier                  │
│ 0x79 │ SYNC_CLOCK   │ Synchronize logical clock                │
│ 0x7A │ FORMATION_UPD│ Update fleet formation                   │
│ 0x7B │ EMERGENCY_STOP│ Emergency halt                         │
└──────┴──────────────┴──────────────────────────────────────────┘
```

### Appendix B: Binary Encoding Examples

#### B.1 Encoding `TELL R1, R2, R3`

```
Bytes (hex): 50 01 02 03
  Byte 0: 0x50 = TELL opcode
  Byte 1: 0x01 = rd = R1 (stores correlation tag)
  Byte 2: 0x02 = rs1 = R2 (destination agent address register)
  Byte 3: 0x03 = rs2 = R3 (message payload register)
```

#### B.2 Encoding `BCAST R0, R0, R5`

```
Bytes (hex): 53 00 00 05
  Byte 0: 0x53 = BCAST opcode
  Byte 1: 0x00 = rd = R0 (tag stored in R0)
  Byte 2: 0x00 = rs1 = R0 (destination = 0x00000000, overridden by BCAST to broadcast)
  Byte 3: 0x05 = rs2 = R5 (broadcast payload)
```

#### B.3 Encoding `TRUST_CHECK R1, R2, 0.6`

```
To encode trust threshold 0.6 as a register value:
  0.6 × 10000 = 6000 = 0x1770 (stored in R2 via prior MOVI)

Bytes (hex): 70 01 02 xx  (where xx = irrelevant; threshold in R2 value)

Full sequence:
  MOVI R2, 0x1770    ; load threshold 0.6
  MOVI R3, 0x0002    ; load target agent address
  TRUST_CHECK R1, R3, R2  ; R1 = (trust[agent_2] >= 0.6) ? 1 : 0
```

### Appendix C: Message Size Limits

| Parameter | Value | Notes |
|-----------|-------|-------|
| Binary header | 52 bytes | Fixed |
| Inline payload | 28 bytes | Within header |
| Extended payload | 0 – 4,294,967,295 bytes | Variable (uint32 length) |
| Max total message | 4,294,967,351 bytes | Header + payload + checksum |
| Recommended max | 65,536 bytes (64 KB) | For latency-sensitive messages |
| JSON envelope | No hard limit | Transport-dependent |
| Signal name length | 256 bytes | Max for signal identifiers |
| Channel name length | 128 bytes | Max for channel identifiers |
| Agent ID string | 64 bytes | Human-readable agent name |
| Tag size | 12 bytes | Opaque correlation data |
| Capabilities per agent | 16 | Bitmap limit |

### Appendix D: Default Configuration

```json
{
  "heartbeat_interval_ms": 5000,
  "heartbeat_timeout_ms": 15000,
  "heartbeat_dead_ms": 30000,
  "discovery_cache_ttl_ms": 5000,
  "default_ttl": 16,
  "default_priority": "normal",
  "default_ask_timeout_ms": 30000,
  "default_barrier_timeout_ms": 60000,
  "default_fork_max_lifetime_ms": 300000,
  "trust_decay_rate_per_hour": 0.02,
  "trust_floor": 0.0,
  "trust_unknown_floor": 0.10,
  "trust_increment_positive": 0.05,
  "trust_decrement_negative": 0.15,
  "trust_min_delegate": 0.30,
  "trust_auto_accept": 0.60,
  "trust_privileged": 0.75,
  "trust_critical": 0.90,
  "trust_ramp_3_positive": 0.35,
  "trust_ramp_10_positive": 0.55,
  "trust_ramp_50_positive": 0.70,
  "max_trust_without_mutual": 0.75,
  "max_agents_per_fleet": 128,
  "cooldown_new_agent_ms": 60000,
  "sybil_correlation_threshold": 0.95,
  "max_replay_window": 1024,
  "max_concurrent_tasks_default": 8,
  "signal_buffer_ttl_ms": 60000,
  "merge_default_strategy": "weighted_confidence"
}
```

### Appendix E: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-10 | Initial A2A protocol (flux-runtime) |
| 1.5 | 2026-04-11 | Protocol primitives added (flux-a2a-prototype) |
| 2.0 | 2026-04-12 | Unified specification: converged opcodes, formal trust model,
|         |          | capability negotiation, fleet topology, security model,
|         |          | JSON schemas, protocol diagrams, full opcode reference |

### Appendix F: Relationship to Signal Language

This protocol specification defines the WIRE FORMAT and RUNTIME BEHAVIOR
for A2A communication. The Signal Language (JSON programs) compiles DOWN to
these opcodes. The relationship:

```
Signal Language JSON Program
    │
    │  compile (SignalCompiler)
    │
    ▼
FLUX Bytecode (using opcodes 0x50–0x5F, 0x60–0x7B)
    │
    │  execute (VM runtime)
    │
    ▼
Binary A2A Messages (52-byte header + payload + CRC32)
    │
    │  transport (LocalTransport / NetworkTransport)
    │
    ▼
Receiving VM → Deserializes → Stores in message queue → Agent processes
```

Protocol primitives (Branch, Fork, CoIterate, Discuss, Synthesize, Reflect)
expand to core opcode sequences at compile time:

```
branch    → FORK + (per branch) + AWAIT (all) + MERGE
fork      → state serialize + FORK opcode + JOIN opcode + conflict resolution
co_iterate→ parallel FORK + shared state monitor + convergence loop
discuss   → message round-robin + turn tracking + consensus detection
synthesize→ AWAIT (all sources) + reduction operation
reflect   → self-assessment + conditional BRANCH for adjustment
```

---

*This specification is the canonical reference for A2A communication in the FLUX
ecosystem. All VM implementations (Python, Rust, Zig, JavaScript, C, Java, CUDA,
WASM) MUST conform to this specification for inter-agent message compatibility.*

*End of A2A Protocol Formal Specification v2.0*

⚡
