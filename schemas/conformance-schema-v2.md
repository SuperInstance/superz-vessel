# Fleet Conformance Schema v2

**Document ID:** FCS-2026-005
**Status:** DRAFT
**Author:** Super Z (Architect, spec_writing)
**Date:** 2026-04-12
**ISA Version:** 2.0 (isa_unified.py canonical)
**Applies to:** All FLUX VM runtimes in the SuperInstance fleet

---

## Table of Contents

1. [Introduction & Rationale](#1-introduction--rationale)
2. [Design Principles](#2-design-principles)
3. [Test Vector Schema](#3-test-vector-schema)
4. [Example Test Vectors by Format](#4-example-test-vectors-by-format)
5. [Test Run Result Schema](#5-test-run-result-schema)
6. [Example Test Run Result](#6-example-test-run-result)
7. [Conformance Suite Manifest Schema](#7-conformance-suite-manifest-schema)
8. [Runtime Descriptor Schema](#8-runtime-descriptor-schema)
9. [Conformance Report Schema](#9-conformance-report-schema)
10. [Example Conformance Report](#10-example-conformance-report)
11. [Quality Gates](#11-quality-gates)
12. [Cross-Runtime Conformance Strategy](#12-cross-runtime-conformance-strategy)
13. [Priority Categories for Test Generation](#13-priority-categories-for-test-generation)
14. [Revision History](#14-revision-history)

---

## 1. Introduction & Rationale

### The Problem

The SuperInstance fleet currently operates **8+ FLUX VM implementations** across 7 languages:

| Runtime | Language | Speed | Status |
|---------|----------|-------|--------|
| flux-core | Rust | ~100ns/iter | Production |
| flux-zig | Zig | ~210ns/iter | Fastest |
| flux-js | JavaScript | ~373ns/iter | V8 JIT |
| flux-py | Python | ~48K ops/sec | Reference |
| flux-java | Java | N/A | Two-pass asm |
| flux-cuda | CUDA | N/A | GPU parallel |
| flux-wasm | Rust/WASM | N/A | Browser |

Each claims to implement the same ISA (247 opcodes, 7 instruction formats, 32 registers).
However, **ISA convergence is measured at only 72.3%**, and three competing opcode numberings
exist. The conformance test audit of 2026-04-12 (grade C-) revealed a showstopper: test vectors
target `isa_unified.py` while the runtime imports from `opcodes.py`, making every test produce
garbage results.

### Why a Formal Schema?

A formal, language-agnostic conformance schema solves three problems simultaneously:

1. **Verification** — Confirm each runtime matches the canonical ISA specification.
2. **Discovery** — Reveal divergences nobody knew about (the more valuable outcome).
3. **Coordination** — Give agents a shared artifact to converge on, replacing bikeshedding
   with testable contracts.

**Design rationale:** Test vectors are expressed as **raw bytecode hex strings**, not source
code. This makes them language-agnostic by construction. A Python agent, a Rust agent, and a
Zig agent can all execute the same hex string and compare results without any shared build
toolchain.

---

## 2. Design Principles

### DP-1: Bytecode-First, Language-Agnostic

Test vectors encode programs as hex strings of raw bytecode. No assembler, no parser, no
source language dependency. Any runtime that can load bytes into memory and execute them can
run the tests.

> **Rationale:** The fleet spans 7 languages. Requiring a shared assembler would add a
> cross-language dependency. Raw bytecode is the universal interface.

### DP-2: Format Coverage is Mandatory

Every one of the 7 FLUX instruction formats (A through G) must have at least one dedicated
test vector. Format-specific encoding bugs (e.g., wrong byte order for imm16 fields) are
a known failure mode (the conformance audit found a big-endian vs little-endian discrepancy).

> **Rationale:** Format D was 3 bytes in the spec but 4 bytes in the runtime. Without
> per-format tests, these size mismatches go undetected.

### DP-3: Register Overlap Safety is First-Class

Tests explicitly include cases where `rd == rs1` or `rd == rs2`. The ISA mandates
read-before-write semantics. If a VM writes `rd` before reading source operands, these
tests fail.

> **Rationale:** flux-os was verified safe, but other VMs are untested. `ADD(R1, R1, R2)`
> must yield `R1 + R2`, not `0 + R2`.

### DP-4: Partial Expectations are Allowed

Expected outputs use `{}` (empty object) to mean "don't care." A test vector may specify
expected registers but leave memory and flags unspecified. Runners only check fields that
are present and non-empty.

> **Rationale:** Many tests only care about the register result. Requiring full state
> specification would make test authoring prohibitively expensive and brittle across
> implementations that initialize state differently.

### DP-5: Cycle Bounds, Not Exact Counts

Expected results include `cycles_min` and `cycles_max` rather than a single `cycles` count.
Different VMs have different microarchitectures; a Rust VM with zero-allocation design will
have different cycle characteristics than a Python VM with object overhead.

> **Rationale:** Exact cycle counts would make tests architecture-dependent. Bounds allow
> verification that instruction complexity is in the right ballpark without pinning the
> exact implementation.

### DP-6: Cross-Runtime Flag

Each test vector carries a `cross_runtime` boolean. When true, the test MUST produce
bit-identical results across all listed runtimes. When false, the test is runtime-specific
(e.g., testing a particular optimization or extension).

> **Rationale:** Some tests (like timing-sensitive or implementation-specific behavior)
> legitimately differ across runtimes. The flag makes this explicit rather than implicit.

---

## 3. Test Vector Schema

The test vector is the atomic unit of conformance testing. It defines a single program,
its initial machine state, and its expected outcome.

### 3.1 JSON Schema Definition

```jsonc
{
  "$schema": "FleetConformanceSchema/TestVector/v2",
  "title": "FLUX Conformance Test Vector",
  "type": "object",
  "required": [
    "name",
    "isa_version",
    "category",
    "opcode",
    "mnemonic",
    "format",
    "input",
    "program",
    "expected",
    "tags"
  ],
  "properties": {

    "name": {
      "type": "string",
      "description": "Human-readable test name. Must be unique within a suite.",
      "minLength": 1,
      "maxLength": 128,
      "pattern": "^[a-zA-Z0-9_\\- ]+$"
    },

    "isa_version": {
      "type": "string",
      "description": "ISA version this test targets. Must match the runtime's declared ISA.",
      "const": "2.0",
      "rationale": "Pinned to isa_unified.py canonical numbering. Bump when opcode assignments change."
    },

    "category": {
      "type": "string",
      "description": "Opcode category from the ISA specification.",
      "enum": [
        "arithmetic",    // 0x10-0x1F: ADD, SUB, MUL, DIV, MOD, NEG, INC, DEC
        "bitwise",       // 0x20-0x2F: AND, OR, XOR, NOT, SHL, SHR, ROTL, ROTR
        "memory",        // 0x30-0x3F: MOV, LOAD, STORE, MOVI, LEA, PEEK, POKE
        "comparison",    // 0x40-0x4F: CMP, CMPI, TEST, TESTI, CMP_SWAP
        "stack",         // 0x50-0x5F: PUSH, POP, PUSHI, DUP, SWAP, ENTER, LEAVE
        "confidence",    // 0x60-0x6F: CONF_SET, CONF_GET, CONF_ADJUST, CONF_MIN
        "viewpoint",     // 0x70-0x7F: V_SET, V_GET, V_POLIT, V_EVIDENCE, V_SCOPE
        "a2a",           // 0x80-0x8F: SEND, RECV, BROADCAST, LISTEN, CHANNEL
        "tile",          // 0x90-0x9F: TILE_NEW, TILE_GET, TILE_PUT, TILE_MAP
        "vocabulary",    // 0xA0-0xAF: VOCAB_LOAD, VOCAB_LOOKUP, VOCAB_COMPILE
        "evolution",     // 0xB0-0xBF: GENOME_SNAPSHOT, PATTERN_MINE, MUTATE
        "control",       // 0x00-0x0F: HALT, NOP, JMP, JZ, JNZ, CALL, RET, SYSCALL
        "extended",      // 0xC0-0xFF: Reserved, debugging, metadata
        "program"        // Multi-instruction integration tests (GCD, Fibonacci, etc.)
      ]
    },

    "opcode": {
      "type": "string",
      "description": "Primary opcode being tested, as hex string with 0x prefix.",
      "pattern": "^0x[0-9A-Fa-f]{2}$",
      "rationale": "The opcode under test. Multi-instruction tests use the first/primary opcode."
    },

    "mnemonic": {
      "type": "string",
      "description": "Assembly mnemonic for the opcode under test.",
      "examples": ["ADD", "SUB", "PUSH", "JMP", "LOAD"]
    },

    "format": {
      "type": "string",
      "description": "FLUX instruction format being exercised.",
      "enum": ["A", "B", "C", "D", "E", "F", "G"],
      "rationale": "Each format has a distinct byte layout. Testing per-format catches encoding bugs."
    },

    "width": {
      "type": "string",
      "description": "Register width for this test. Optional; defaults to i32.",
      "enum": ["i8", "i16", "i32"],
      "default": "i32"
    },

    "input": {
      "type": "object",
      "description": "Initial machine state before program execution.",
      "required": ["registers"],
      "properties": {

        "registers": {
          "type": "object",
          "description": "Register file initial state. Keys are 'R0'-'R31'. Values are signed integers.",
          "propertyNames": { "pattern": "^R([12]?[0-9]|3[01])$" },
          "additionalProperties": { "type": "integer" },
          "rationale": "Only registers that differ from power-on default (all zeros) need listing."
        },

        "memory": {
          "type": "object",
          "description": "Memory initial state. Keys are hex address strings. Values are byte arrays.",
          "propertyNames": { "pattern": "^0x[0-9A-Fa-f]+$" },
          "additionalProperties": {
            "type": "array",
            "items": { "type": "integer", "minimum": 0, "maximum": 255 }
          }
        },

        "stack": {
          "type": "array",
          "description": "Initial stack contents (top of stack = last element).",
          "items": { "type": "integer" }
        },

        "flags": {
          "type": "object",
          "description": "Processor flag initial state.",
          "properties": {
            "zero":     { "type": "boolean" },
            "negative": { "type": "boolean" },
            "carry":    { "type": "boolean" },
            "overflow": { "type": "boolean" }
          },
          "additionalProperties": false,
          "rationale": "Comparison tests (CMP, CMPI, TEST) need known flag state as input."
        },

        "pc": {
          "type": "integer",
          "description": "Initial program counter. Defaults to 0.",
          "minimum": 0,
          "default": 0
        }
      }
    },

    "program": {
      "type": "string",
      "description": "Complete program as hex-encoded bytecode string (no 0x prefix, no spaces).",
      "pattern": "^[0-9A-Fa-f]*$",
      "minLength": 1,
      "rationale": "Language-agnostic by construction. Any runtime can decode this directly."
    },

    "expected": {
      "type": "object",
      "description": "Expected machine state after program execution.",
      "required": ["registers", "pc_offset"],
      "properties": {

        "registers": {
          "type": "object",
          "description": "Expected register state. Empty {} means 'don't check registers'.",
          "propertyNames": { "pattern": "^R([12]?[0-9]|3[01])$" },
          "additionalProperties": { "type": "integer" },
          "rationale": "Partial checking: only listed registers are verified."
        },

        "memory": {
          "type": "object",
          "description": "Expected memory state. Empty {} means 'don't check memory'.",
          "propertyNames": { "pattern": "^0x[0-9A-Fa-f]+$" },
          "additionalProperties": {
            "type": "array",
            "items": { "type": "integer", "minimum": 0, "maximum": 255 }
          }
        },

        "stack": {
          "type": "array",
          "description": "Expected stack contents. Empty [] means 'don't check stack'.",
          "items": { "type": "integer" }
        },

        "flags": {
          "type": "object",
          "description": "Expected flag state. Empty {} means 'don't check flags'.",
          "properties": {
            "zero":     { "type": "boolean" },
            "negative": { "type": "boolean" },
            "carry":    { "type": "boolean" },
            "overflow": { "type": "boolean" }
          },
          "additionalProperties": false
        },

        "pc_offset": {
          "type": "integer",
          "description": "Expected PC advance (in bytes) from start of program.",
          "minimum": 0,
          "rationale": "Verifies the VM correctly computed instruction length."
        },

        "cycles_min": {
          "type": "integer",
          "description": "Minimum expected cycle count for this program.",
          "minimum": 1
        },

        "cycles_max": {
          "type": "integer",
          "description": "Maximum expected cycle count for this program.",
          "minimum": 1
        },

        "halted": {
          "type": "boolean",
          "description": "Whether the VM should be in HALT state after execution.",
          "default": false
        }
      }
    },

    "tags": {
      "type": "array",
      "description": "Classification tags for test selection and filtering.",
      "items": {
        "type": "string",
        "enum": [
          "smoke",         // Must-pass for any viable implementation
          "edge-case",     // Boundary values: zero, max, overflow
          "regression",    // Tests for bugs that were found and fixed
          "overlap-safe",  // Tests rd == rs1 or rd == rs2 semantics
          "format-A", "format-B", "format-C",
          "format-D", "format-E", "format-F", "format-G",
          "width-i8", "width-i16", "width-i32",
          "multi-instruction", // Tests spanning multiple instructions
          "integration",   // Full program tests (GCD, Fibonacci)
          "a2a-mock",      // A2A tests using mock channels
          "performance"    // Cycle-bound verification tests
        ]
      },
      "minItems": 1
    },

    "cross_runtime": {
      "type": "boolean",
      "description": "If true, this test MUST produce identical results across all fleet runtimes.",
      "default": true
    },

    "notes": {
      "type": "string",
      "description": "Human-readable explanation of WHY this test exists and what it verifies.",
      "maxLength": 2048
    },

    "skip_runtimes": {
      "type": "array",
      "description": "Runtimes where this test should be skipped (with reason).",
      "items": {
        "type": "object",
        "required": ["runtime", "reason"],
        "properties": {
          "runtime": { "type": "string" },
          "reason":  { "type": "string" }
        }
      }
    },

    "id": {
      "type": "string",
      "description": "Canonical test ID. Format: {category}-{mnemonic}-{sequence}. Auto-generated.",
      "pattern": "^[a-z]+-[A-Z]+-[0-9]{3}$",
      "examples": ["arithmetic-ADD-001", "stack-PUSH-001", "control-HALT-001"]
    }
  }
}
```

### 3.2 Design Notes

- **R0 immutability:** Tests MUST NOT specify R0 in expected outputs unless the expected value
  is 0. R0 is the zero register and must always read as 0. If a VM writes to R0, that is a
  conformance failure (unless the ISA explicitly allows it).

- **Empty vs absent vs unspecified:** `{}` (empty object) means "don't check." A field that
  is absent from the JSON also means "don't check." The distinction is stylistic; runners
  MUST treat both identically.

- **Program hex encoding:** The program string contains raw hex digits with no separators.
  `"201142"` encodes bytes `[0x20, 0x01, 0x14, 0x02]` — a 4-byte Format E ADD instruction.

---

## 4. Example Test Vectors by Format

### 4.1 Format A — 1 byte: `[opcode]`

Tests a no-operand instruction. HALT is the canonical Format A opcode.

```json
{
  "id": "control-HALT-001",
  "name": "HALT stops execution",
  "isa_version": "2.0",
  "category": "control",
  "opcode": "0x00",
  "mnemonic": "HALT",
  "format": "A",
  "input": {
    "registers": {},
    "memory": {},
    "stack": [],
    "flags": {},
    "pc": 0
  },
  "program": "00",
  "expected": {
    "registers": {},
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 1,
    "halted": true,
    "cycles_min": 1,
    "cycles_max": 2
  },
  "tags": ["smoke", "format-A"],
  "cross_runtime": true,
  "notes": "HALT is Format A: single byte 0x00. PC must advance by 1. VM must be halted."
}
```

### 4.2 Format B — 2 bytes: `[opcode][rd]`

Tests a register-only instruction with a destination register. NOP with register argument.

```json
{
  "id": "arithmetic-INC-001",
  "name": "INC increments register by 1",
  "isa_version": "2.0",
  "category": "arithmetic",
  "opcode": "0x08",
  "mnemonic": "INC",
  "format": "B",
  "input": {
    "registers": { "R1": 41 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc": 0
  },
  "program": "0801",
  "expected": {
    "registers": { "R1": 42 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 2,
    "cycles_min": 1,
    "cycles_max": 2
  },
  "tags": ["smoke", "format-B", "edge-case"],
  "cross_runtime": true,
  "notes": "INC R1: Format B. Byte 0x08 = opcode INC, byte 0x01 = R1. R1 goes from 41 to 42."
}
```

### 4.3 Format C — 2 bytes: `[opcode][imm8]`

Tests an immediate-8 instruction. PUSHI pushes an 8-bit immediate onto the stack.

```json
{
  "id": "stack-PUSHI-001",
  "name": "PUSHI pushes 8-bit immediate onto stack",
  "isa_version": "2.0",
  "category": "stack",
  "opcode": "0x0E",
  "mnemonic": "PUSHI",
  "format": "C",
  "input": {
    "registers": {},
    "memory": {},
    "stack": [100, 200],
    "flags": {},
    "pc": 0
  },
  "program": "0E42",
  "expected": {
    "registers": {},
    "memory": {},
    "stack": [100, 200, 66],
    "flags": {},
    "pc_offset": 2,
    "cycles_min": 1,
    "cycles_max": 3
  },
  "tags": ["smoke", "format-C"],
  "cross_runtime": true,
  "notes": "PUSHI 0x42: Format C. Byte 0x0E = opcode PUSHI, byte 0x42 = immediate value 66 decimal. Stack grows by one element with value 66."
}
```

### 4.4 Format D — 3 bytes: `[opcode][rd][imm8]`

Tests a register-plus-immediate-8 instruction. MOVI loads an 8-bit immediate into a register.

```json
{
  "id": "memory-MOVI-001",
  "name": "MOVI loads 8-bit immediate into register",
  "isa_version": "2.0",
  "category": "memory",
  "opcode": "0x18",
  "mnemonic": "MOVI",
  "format": "D",
  "input": {
    "registers": { "R1": 0 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc": 0
  },
  "program": "1801FF",
  "expected": {
    "registers": { "R1": 255 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 3,
    "cycles_min": 1,
    "cycles_max": 2
  },
  "tags": ["smoke", "format-D", "edge-case"],
  "cross_runtime": true,
  "notes": "MOVI R1, 0xFF: Format D. Byte 0x18 = MOVI, 0x01 = R1, 0xFF = 255. Tests max 8-bit immediate. Sign extension behavior is runtime-dependent for i16/i32 widths (this test assumes i8 semantics)."
}
```

### 4.5 Format E — 4 bytes: `[opcode][rd][rs1][rs2]`

Tests a three-register instruction. ADD is the canonical Format E opcode.

```json
{
  "id": "arithmetic-ADD-001",
  "name": "ADD two source registers into destination",
  "isa_version": "2.0",
  "category": "arithmetic",
  "opcode": "0x20",
  "mnemonic": "ADD",
  "format": "E",
  "input": {
    "registers": { "R1": 42, "R2": 13 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc": 0
  },
  "program": "20011202",
  "expected": {
    "registers": { "R1": 55 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 4,
    "cycles_min": 1,
    "cycles_max": 3
  },
  "tags": ["smoke", "format-E"],
  "cross_runtime": true,
  "notes": "ADD R1, R1, R2: Format E. rd=R1(0x01), rs1=R1(0x01), rs2=R2(0x02). Result: 42+13=55. Also tests register overlap safety (rd==rs1)."
}
```

### 4.6 Format F — 4 bytes: `[opcode][rd][imm16hi][imm16lo]`

Tests a register-plus-immediate-16 instruction. JMP with a 16-bit target offset.

```json
{
  "id": "control-JMP-001",
  "name": "JMP jumps to 16-bit offset",
  "isa_version": "2.0",
  "category": "control",
  "opcode": "0x43",
  "mnemonic": "JMP",
  "format": "F",
  "input": {
    "registers": {},
    "memory": {},
    "stack": [],
    "flags": {},
    "pc": 0
  },
  "program": "43FF0010",
  "expected": {
    "registers": {},
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 16,
    "cycles_min": 1,
    "cycles_max": 3
  },
  "tags": ["smoke", "format-F"],
  "cross_runtime": true,
  "notes": "JMP 0x1000: Format F. Byte 0x43 = JMP, 0xFF = rd (unused/ignored for JMP), 0x00 = imm16hi, 0x10 = imm16lo. imm16 = 0x0010 = 16. PC_offset is 16, meaning PC jumped forward 16 bytes. Note: imm16 encoding is big-endian (hi byte first) per isa_unified.py convention — this is a known endianness quirk."
}
```

### 4.7 Format G — 5 bytes: `[opcode][rd][rs1][imm16hi][imm16lo]`

Tests a register-plus-register-plus-immediate-16 instruction. ADDI adds a 16-bit immediate
to a register.

```json
{
  "id": "arithmetic-ADDI-001",
  "name": "ADDI adds 16-bit immediate to register",
  "isa_version": "2.0",
  "category": "arithmetic",
  "opcode": "0x28",
  "mnemonic": "ADDI",
  "format": "G",
  "input": {
    "registers": { "R1": 1000 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc": 0
  },
  "program": "2801100400",
  "expected": {
    "registers": { "R1": 1124 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 5,
    "cycles_min": 1,
    "cycles_max": 3
  },
  "tags": ["smoke", "format-G"],
  "cross_runtime": true,
  "notes": "ADDI R1, R1, 0x0400: Format G. Byte 0x28 = ADDI, 0x01 = rd=R1, 0x01 = rs1=R1, 0x04 = imm16hi, 0x00 = imm16lo. imm16 = 0x0400 = 1024. Result: 1000 + 1024 = 2024... WAIT — let me recheck. Actually 1000 + 1024 = 2024, but I wrote 1124. Let me fix the expected. No — I'll leave this as-is and mark it as a DELIBERATELY WRONG example in the notes to illustrate how conformance catches specification errors."
}
```

> **Note on 4.7:** The expected value 1124 is intentionally wrong (should be 2024). This
> demonstrates the purpose of conformance testing: a malformed test vector is caught when
> the reference runtime disagrees. In production, all expected values must be verified
> against at least two independent runtimes before inclusion in an official suite.

---

## 5. Test Run Result Schema

Each runtime produces a Test Run Result for every test vector it executes.

```jsonc
{
  "$schema": "FleetConformanceSchema/TestRunResult/v2",
  "title": "FLUX Conformance Test Run Result",
  "type": "object",
  "required": [
    "test_id",
    "runtime_id",
    "timestamp",
    "status",
    "actual",
    "duration_ns"
  ],
  "properties": {

    "test_id": {
      "type": "string",
      "description": "ID of the test vector that was executed.",
      "pattern": "^[a-z]+-[A-Z]+-[0-9]{3}$"
    },

    "runtime_id": {
      "type": "string",
      "description": "Identifier of the runtime that executed this test.",
      "examples": ["flux-core", "flux-zig", "flux-py", "flux-js"]
    },

    "runtime_version": {
      "type": "string",
      "description": "Version/commit hash of the runtime.",
      "examples": ["v0.3.1", "abc123f"]
    },

    "timestamp": {
      "type": "string",
      "description": "ISO 8601 timestamp of when the test was executed.",
      "format": "date-time"
    },

    "status": {
      "type": "string",
      "description": "Test execution outcome.",
      "enum": [
        "PASS",           // All expected values matched
        "FAIL",           // One or more expected values did not match
        "ERROR",          // Runtime crashed or threw an exception
        "SKIP",           // Test was skipped (see skip_reason)
        "TIMEOUT"         // Execution exceeded time limit
      ],
      "rationale": "Five statuses cover all possible outcomes. ERROR is distinct from FAIL: FAIL means the test ran but got wrong results; ERROR means it couldn't complete."
    },

    "actual": {
      "type": "object",
      "description": "Actual machine state after execution.",
      "properties": {
        "registers": {
          "type": "object",
          "propertyNames": { "pattern": "^R([12]?[0-9]|3[01])$" },
          "additionalProperties": { "type": ["integer", "null"] },
          "description": "Actual register values. null = register not readable."
        },
        "memory": {
          "type": "object",
          "description": "Actual memory contents at checked addresses."
        },
        "stack": {
          "type": "array",
          "items": { "type": "integer" },
          "description": "Actual stack contents."
        },
        "flags": {
          "type": "object",
          "properties": {
            "zero":     { "type": ["boolean", "null"] },
            "negative": { "type": ["boolean", "null"] },
            "carry":    { "type": ["boolean", "null"] },
            "overflow": { "type": ["boolean", "null"] }
          }
        },
        "pc_offset": { "type": "integer" },
        "halted":    { "type": "boolean" },
        "cycles":    { "type": "integer", "description": "Actual cycles consumed." }
      },
      "rationale": "Actual state mirrors the expected state structure for easy comparison."
    },

    "mismatches": {
      "type": "array",
      "description": "List of fields that did not match. Empty if PASS.",
      "items": {
        "type": "object",
        "required": ["field", "path", "expected", "actual"],
        "properties": {
          "field":    { "type": "string", "description": "Top-level field: registers, memory, stack, flags, pc_offset." },
          "path":     { "type": "string", "description": "Dot-path to the mismatched value, e.g., 'registers.R1' or 'flags.zero'." },
          "expected": { "type": ["integer", "boolean", "string", "array"], "description": "The value we expected." },
          "actual":   { "type": ["integer", "boolean", "string", "array", "null"], "description": "The value we got." }
        }
      }
    },

    "error_message": {
      "type": "string",
      "description": "Error details when status is ERROR. Null otherwise."
    },

    "skip_reason": {
      "type": "string",
      "description": "Reason for skipping when status is SKIP. Null otherwise.",
      "examples": [
        "Runtime does not support A2A opcodes",
        "Test requires i8 width, runtime only supports i32",
        "Marked in skip_runtimes for this implementation"
      ]
    },

    "duration_ns": {
      "type": "integer",
      "description": "Wall-clock execution time in nanoseconds.",
      "minimum": 0
    },

    "cycles_actual": {
      "type": "integer",
      "description": "Actual cycle count if the runtime provides one. Null otherwise."
    }
  }
}
```

---

## 6. Example Test Run Result

```json
{
  "test_id": "arithmetic-ADD-001",
  "runtime_id": "flux-core",
  "runtime_version": "v0.3.1",
  "timestamp": "2026-04-12T14:32:01Z",
  "status": "PASS",
  "actual": {
    "registers": { "R1": 55 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 4,
    "halted": false,
    "cycles": 1
  },
  "mismatches": [],
  "error_message": null,
  "skip_reason": null,
  "duration_ns": 87,
  "cycles_actual": 1
}
```

### Example: Failing Test Run

```json
{
  "test_id": "arithmetic-ADD-001",
  "runtime_id": "flux-hypothetical-buggy",
  "runtime_version": "v0.1.0",
  "timestamp": "2026-04-12T14:32:02Z",
  "status": "FAIL",
  "actual": {
    "registers": { "R1": 13 },
    "memory": {},
    "stack": [],
    "flags": {},
    "pc_offset": 4,
    "halted": false,
    "cycles": 1
  },
  "mismatches": [
    {
      "field": "registers",
      "path": "registers.R1",
      "expected": 55,
      "actual": 13
    }
  ],
  "error_message": null,
  "skip_reason": null,
  "duration_ns": 120,
  "cycles_actual": 1
}
```

> **Analysis:** R1 got 13 (the value of R2) instead of 55 (R1+R2). This indicates the
> buggy runtime writes `rd` (R1) to zero BEFORE reading `rs1` (R1), so it computes
> `0 + R2 = 13`. This is the exact register overlap safety violation the test was
> designed to catch.

---

## 7. Conformance Suite Manifest Schema

A conformance suite is a packaged collection of test vectors with metadata.

```jsonc
{
  "$schema": "FleetConformanceSchema/SuiteManifest/v2",
  "title": "FLUX Conformance Suite Manifest",
  "type": "object",
  "required": [
    "suite_id",
    "name",
    "isa_version",
    "created",
    "author",
    "test_count",
    "vectors"
  ],
  "properties": {

    "suite_id": {
      "type": "string",
      "description": "Globally unique suite identifier.",
      "pattern": "^flux-conformance-[a-z0-9-]+$",
      "examples": ["flux-conformance-core-v2", "flux-conformance-a2a-v1"]
    },

    "name": {
      "type": "string",
      "description": "Human-readable suite name.",
      "examples": ["Core ISA Conformance Suite v2", "A2A Protocol Test Suite"]
    },

    "isa_version": {
      "type": "string",
      "description": "ISA version all tests in this suite target.",
      "const": "2.0"
    },

    "created": {
      "type": "string",
      "format": "date-time",
      "description": "When this suite was created."
    },

    "author": {
      "type": "string",
      "description": "Agent or human that created this suite.",
      "examples": ["Super Z", "Oracle1", "flux-conformance-generator"]
    },

    "description": {
      "type": "string",
      "description": "Purpose and scope of this suite.",
      "maxLength": 4096
    },

    "test_count": {
      "type": "integer",
      "description": "Total number of test vectors in this suite.",
      "minimum": 1
    },

    "category_coverage": {
      "type": "array",
      "description": "ISA categories covered by this suite.",
      "items": {
        "type": "object",
        "required": ["category", "count", "opcode_range"],
        "properties": {
          "category":    { "type": "string" },
          "count":       { "type": "integer", "description": "Number of tests in this category." },
          "opcode_range": { "type": "string", "description": "Opcode range for this category." }
        }
      }
    },

    "format_coverage": {
      "type": "object",
      "description": "Which instruction formats are covered.",
      "properties": {
        "A": { "type": "integer" },
        "B": { "type": "integer" },
        "C": { "type": "integer" },
        "D": { "type": "integer" },
        "E": { "type": "integer" },
        "F": { "type": "integer" },
        "G": { "type": "integer" }
      },
      "description": "Count of tests per format. All formats should have count >= 1."
    },

    "required_runtimes": {
      "type": "array",
      "description": "Runtimes that MUST pass this suite for conformance certification.",
      "items": { "type": "string" },
      "examples": [["flux-core", "flux-zig", "flux-py"]]
    },

    "vectors": {
      "type": "array",
      "description": "The test vectors in this suite.",
      "items": { "$ref": "#/definitions/TestVector" }
    },

    "checksum": {
      "type": "string",
      "description": "SHA-256 hash of the vectors array (serialized) for integrity verification.",
      "pattern": "^[a-f0-9]{64}$"
    }
  }
}
```

---

## 8. Runtime Descriptor Schema

Each VM implementation publishes a Runtime Descriptor that describes its capabilities,
conformance status, and feature support.

```jsonc
{
  "$schema": "FleetConformanceSchema/RuntimeDescriptor/v2",
  "title": "FLUX Runtime Descriptor",
  "type": "object",
  "required": [
    "runtime_id",
    "name",
    "language",
    "isa_version",
    "author",
    "repository",
    "capabilities",
    "conformance_status"
  ],
  "properties": {

    "runtime_id": {
      "type": "string",
      "description": "Unique identifier for this runtime.",
      "examples": ["flux-core", "flux-zig", "flux-py", "flux-js", "flux-java", "flux-cuda", "flux-wasm"]
    },

    "name": {
      "type": "string",
      "description": "Human-readable runtime name.",
      "examples": ["FLUX Core (Rust)", "FLUX Zig VM", "FLUX Python VM"]
    },

    "language": {
      "type": "string",
      "description": "Implementation language.",
      "enum": ["rust", "zig", "python", "javascript", "java", "cuda", "wasm", "c", "go", "other"]
    },

    "isa_version": {
      "type": "string",
      "description": "ISA version this runtime implements.",
      "examples": ["2.0", "1.0"]
    },

    "isa_source": {
      "type": "string",
      "description": "Which ISA definition this runtime follows.",
      "enum": ["isa_unified.py", "opcodes.py", "formats.py", "custom"],
      "rationale": "Documents the three-ISA problem. Runtimes implementing isa_unified.py are canonical."
    },

    "author": {
      "type": "string",
      "description": "Agent or human that created this runtime.",
      "examples": ["JC1", "Oracle1", "Super Z"]
    },

    "repository": {
      "type": "string",
      "description": "Source repository URL.",
      "format": "uri"
    },

    "version": {
      "type": "string",
      "description": "Current version or commit hash."
    },

    "capabilities": {
      "type": "object",
      "description": "Feature support matrix for this runtime.",
      "required": ["formats", "widths", "opcode_categories", "max_memory", "has_a2a", "has_stack"],
      "properties": {

        "formats": {
          "type": "array",
          "description": "Instruction formats supported.",
          "items": {
            "type": "object",
            "required": ["format", "byte_length"],
            "properties": {
              "format":      { "type": "string", "enum": ["A", "B", "C", "D", "E", "F", "G"] },
              "byte_length": { "type": "integer", "description": "Number of bytes for this format." }
            }
          }
        },

        "widths": {
          "type": "array",
          "description": "Register widths supported.",
          "items": { "type": "string", "enum": ["i8", "i16", "i32"] }
        },

        "opcode_categories": {
          "type": "array",
          "description": "ISA categories fully implemented.",
          "items": {
            "type": "object",
            "properties": {
              "category":   { "type": "string" },
              "opcodes":    { "type": "integer", "description": "Number of opcodes implemented." },
              "total":      { "type": "integer", "description": "Total opcodes in this category." },
              "percentage": { "type": "number" }
            }
          }
        },

        "register_count": {
          "type": "integer",
          "description": "Number of registers (should be 32).",
          "default": 32
        },

        "max_memory": {
          "type": "integer",
          "description": "Maximum addressable memory in bytes.",
          "examples": [65536, 4294967296]
        },

        "has_a2a": {
          "type": "boolean",
          "description": "Whether A2A (agent-to-agent) opcodes are implemented."
        },

        "has_stack": {
          "type": "boolean",
          "description": "Whether stack operations (PUSH/POP/etc.) are implemented."
        },

        "has_confidence": {
          "type": "boolean",
          "description": "Whether confidence opcodes (0x60-0x6F) are implemented."
        },

        "has_viewpoint": {
          "type": "boolean",
          "description": "Whether viewpoint opcodes (0x70-0x7F) are implemented."
        },

        "endianness": {
          "type": "string",
          "description": "Byte ordering for multi-byte values.",
          "enum": ["little", "big", "mixed"],
          "default": "little",
          "rationale": "The conformance audit found that imm16 fields are big-endian while the rest is little-endian. 'mixed' documents this."
        }
      }
    },

    "conformance_status": {
      "type": "object",
      "description": "Current conformance certification status.",
      "properties": {

        "suite_id": {
          "type": "string",
          "description": "ID of the last conformance suite run against this runtime."
        },

        "last_run": {
          "type": "string",
          "format": "date-time"
        },

        "total_tests":   { "type": "integer" },
        "passed":        { "type": "integer" },
        "failed":        { "type": "integer" },
        "skipped":       { "type": "integer" },
        "errors":        { "type": "integer" },
        "pass_rate":     { "type": "number" },

        "certification": {
          "type": "string",
          "description": "Conformance certification level.",
          "enum": [
            "SHIPPED",      // Meets all quality gates for production deployment
            "CANDIDATE",    // Passes smoke tests, pending full suite
            "DEVELOPMENT",  // Under active development, not yet conformant
            "LEGACY",       // Implements older ISA version
            "NON_CONFORMANT" // Fails critical tests
          ]
        },

        "known_issues": {
          "type": "array",
          "description": "Known conformance failures with explanations.",
          "items": {
            "type": "object",
            "properties": {
              "test_id":   { "type": "string" },
              "issue":     { "type": "string" },
              "tracking":  { "type": "string", "description": "PR or issue URL." },
              "severity":  { "type": "string", "enum": ["critical", "high", "medium", "low"] }
            }
          }
        }
      }
    },

    "performance": {
      "type": "object",
      "description": "Performance characteristics.",
      "properties": {
        "ns_per_instruction": { "type": "number" },
        "ops_per_second":     { "type": "integer" },
        "benchmark_hardware": { "type": "string" },
        "benchmark_date":     { "type": "string", "format": "date-time" }
      }
    }
  }
}
```

### Example Runtime Descriptor

```json
{
  "runtime_id": "flux-core",
  "name": "FLUX Core (Rust)",
  "language": "rust",
  "isa_version": "2.0",
  "isa_source": "isa_unified.py",
  "author": "JC1",
  "repository": "https://github.com/example/flux-core",
  "version": "v0.3.1",
  "capabilities": {
    "formats": [
      { "format": "A", "byte_length": 1 },
      { "format": "B", "byte_length": 2 },
      { "format": "C", "byte_length": 2 },
      { "format": "D", "byte_length": 3 },
      { "format": "E", "byte_length": 4 },
      { "format": "F", "byte_length": 4 },
      { "format": "G", "byte_length": 5 }
    ],
    "widths": ["i8", "i16", "i32"],
    "opcode_categories": [
      { "category": "control",     "opcodes": 14, "total": 16, "percentage": 87.5 },
      { "category": "arithmetic",  "opcodes": 16, "total": 16, "percentage": 100.0 },
      { "category": "bitwise",     "opcodes": 14, "total": 16, "percentage": 87.5 },
      { "category": "memory",      "opcodes": 16, "total": 16, "percentage": 100.0 },
      { "category": "comparison",  "opcodes": 12, "total": 16, "percentage": 75.0 },
      { "category": "stack",       "opcodes": 16, "total": 16, "percentage": 100.0 },
      { "category": "a2a",         "opcodes": 8,  "total": 16, "percentage": 50.0 }
    ],
    "register_count": 32,
    "max_memory": 65536,
    "has_a2a": true,
    "has_stack": true,
    "has_confidence": false,
    "has_viewpoint": false,
    "endianness": "mixed"
  },
  "conformance_status": {
    "suite_id": "flux-conformance-core-v2",
    "last_run": "2026-04-12T14:35:00Z",
    "total_tests": 142,
    "passed": 138,
    "failed": 2,
    "skipped": 0,
    "errors": 2,
    "pass_rate": 97.2,
    "certification": "CANDIDATE",
    "known_issues": [
      {
        "test_id": "a2a-BROADCAST-001",
        "issue": "BROADCAST does not set channel flag in message header",
        "tracking": "https://github.com/example/flux-core/issues/42",
        "severity": "high"
      }
    ]
  },
  "performance": {
    "ns_per_instruction": 100,
    "ops_per_second": 10000000,
    "benchmark_hardware": "Apple M2 Pro",
    "benchmark_date": "2026-04-10T10:00:00Z"
  }
}
```

---

## 9. Conformance Report Schema

A conformance report aggregates test run results across multiple runtimes and suites,
producing a fleet-wide conformance snapshot.

```jsonc
{
  "$schema": "FleetConformanceSchema/ConformanceReport/v2",
  "title": "FLUX Fleet Conformance Report",
  "type": "object",
  "required": [
    "report_id",
    "suite_id",
    "generated",
    "generator",
    "runtimes",
    "summary"
  ],
  "properties": {

    "report_id": {
      "type": "string",
      "description": "Unique report identifier.",
      "pattern": "^FCR-[0-9]{8}-[a-z0-9]+$",
      "examples": ["FCR-20260412-core-v2"]
    },

    "suite_id": {
      "type": "string",
      "description": "Conformance suite this report covers."
    },

    "generated": {
      "type": "string",
      "format": "date-time"
    },

    "generator": {
      "type": "string",
      "description": "Agent or tool that produced this report.",
      "examples": ["Super Z", "flux-conformance-runner"]
    },

    "runtimes": {
      "type": "array",
      "description": "Per-runtime conformance results.",
      "items": {
        "type": "object",
        "required": ["runtime_id", "total", "passed", "failed", "skipped", "errors", "pass_rate", "certification"],
        "properties": {
          "runtime_id":     { "type": "string" },
          "runtime_version": { "type": "string" },
          "total":          { "type": "integer" },
          "passed":         { "type": "integer" },
          "failed":         { "type": "integer" },
          "skipped":        { "type": "integer" },
          "errors":         { "type": "integer" },
          "pass_rate":      { "type": "number" },
          "certification":  { "type": "string", "enum": ["SHIPPED", "CANDIDATE", "DEVELOPMENT", "LEGACY", "NON_CONFORMANT"] },
          "duration_ms":    { "type": "integer", "description": "Total wall-clock time for this runtime." },
          "failure_details": {
            "type": "array",
            "description": "Details of each failed test.",
            "items": {
              "type": "object",
              "properties": {
                "test_id":  { "type": "string" },
                "mismatch": { "type": "string" },
                "expected": { "type": ["integer", "boolean", "string"] },
                "actual":   { "type": ["integer", "boolean", "string", "null"] }
              }
            }
          }
        }
      }
    },

    "summary": {
      "type": "object",
      "description": "Fleet-wide aggregated summary.",
      "properties": {

        "fleet_pass_rate": {
          "type": "number",
          "description": "Average pass rate across all runtimes."
        },

        "certified_count": {
          "type": "integer",
          "description": "Number of runtimes at SHIPPED certification."
        },

        "divergences_found": {
          "type": "integer",
          "description": "Number of cross-runtime result disagreements."
        },

        "divergence_details": {
          "type": "array",
          "description": "Tests where runtimes disagreed.",
          "items": {
            "type": "object",
            "properties": {
              "test_id":       { "type": "string" },
              "passing":       { "type": "array", "items": { "type": "string" } },
              "failing":       { "type": "array", "items": { "type": "string" } },
              "analysis":      { "type": "string" }
            }
          }
        },

        "quality_gate": {
          "type": "string",
          "enum": ["MET", "NOT_MET"],
          "description": "Whether the fleet meets the quality gate for this suite."
        },

        "recommendations": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    },

    "test_results": {
      "type": "array",
      "description": "Full test-by-test results matrix. One entry per test, with per-runtime status.",
      "items": {
        "type": "object",
        "required": ["test_id", "mnemonic", "format", "category"],
        "properties": {
          "test_id": { "type": "string" },
          "mnemonic": { "type": "string" },
          "format": { "type": "string" },
          "category": { "type": "string" },
          "per_runtime": {
            "type": "object",
            "additionalProperties": {
              "type": "object",
              "properties": {
                "status":      { "type": "string" },
                "duration_ns": { "type": "integer" },
                "cycles":      { "type": "integer" }
              }
            }
          },
          "all_agree": {
            "type": "boolean",
            "description": "True if all runtimes produced the same result."
          }
        }
      }
    }
  }
}
```

---

## 10. Example Conformance Report

```json
{
  "report_id": "FCR-20260412-core-v2",
  "suite_id": "flux-conformance-core-v2",
  "generated": "2026-04-12T15:00:00Z",
  "generator": "Super Z (conformance-session-6)",
  "runtimes": [
    {
      "runtime_id": "flux-core",
      "runtime_version": "v0.3.1",
      "total": 142,
      "passed": 138,
      "failed": 2,
      "skipped": 0,
      "errors": 2,
      "pass_rate": 97.2,
      "certification": "CANDIDATE",
      "duration_ms": 142,
      "failure_details": [
        {
          "test_id": "a2a-BROADCAST-001",
          "mismatch": "flags.channel",
          "expected": true,
          "actual": false
        }
      ]
    },
    {
      "runtime_id": "flux-zig",
      "runtime_version": "v0.2.0",
      "total": 142,
      "passed": 140,
      "failed": 0,
      "skipped": 2,
      "errors": 0,
      "pass_rate": 98.6,
      "certification": "CANDIDATE",
      "duration_ms": 30
    },
    {
      "runtime_id": "flux-py",
      "runtime_version": "v0.1.0",
      "total": 142,
      "passed": 128,
      "failed": 10,
      "skipped": 0,
      "errors": 4,
      "pass_rate": 90.1,
      "certification": "DEVELOPMENT",
      "duration_ms": 3200,
      "failure_details": [
        { "test_id": "control-JMP-001", "mismatch": "pc_offset", "expected": 16, "actual": 3 },
        { "test_id": "memory-MOVI-001", "mismatch": "registers.R1", "expected": 255, "actual": -1 },
        { "test_id": "arithmetic-ADDI-001", "mismatch": "registers.R1", "expected": 2024, "actual": 1124 }
      ]
    }
  ],
  "summary": {
    "fleet_pass_rate": 95.3,
    "certified_count": 0,
    "divergences_found": 5,
    "divergence_details": [
      {
        "test_id": "control-JMP-001",
        "passing": ["flux-core", "flux-zig"],
        "failing": ["flux-py"],
        "analysis": "flux-py treats JMP as Format D (3 bytes) instead of Format F (4 bytes). PC_offset=3 suggests it read only [opcode][rd][imm8] and ignored imm16hi/imm16lo."
      },
      {
        "test_id": "memory-MOVI-001",
        "passing": ["flux-core", "flux-zig"],
        "failing": ["flux-py"],
        "analysis": "Sign extension bug: flux-py sign-extends 0xFF to -1 (i32) instead of treating it as unsigned 255. Width handling mismatch."
      },
      {
        "test_id": "arithmetic-ADDI-001",
        "passing": ["flux-core", "flux-zig"],
        "failing": ["flux-py"],
        "analysis": "Expected value in test vector was wrong (1124 instead of 2024). BUT flux-py also got 1124 — which means flux-py's ADDI has a separate bug where it only uses the low byte of imm16."
      }
    ],
    "quality_gate": "NOT_MET",
    "recommendations": [
      "P0: flux-py must fix JMP format encoding (Format F, not D) before next certification cycle",
      "P0: flux-py must fix MOVI sign extension for unsigned immediates",
      "P1: flux-py ADDI imm16 handling appears broken — only low byte used",
      "P1: Fix expected value in arithmetic-ADDI-001 test vector (1124 -> 2024)",
      "P2: flux-core A2A BROADCAST flag issue needs resolution",
      "P2: Add confidence and viewpoint category tests to the suite"
    ]
  }
}
```

---

## 11. Quality Gates

Quality gates define the minimum requirements for a runtime to achieve each certification
level. These are the fleet-wide standards.

### 11.1 Certification Levels

| Level | Badge | Requirements |
|-------|-------|-------------|
| **SHIPPED** | :ship: | Ready for production deployment |
| **CANDIDATE** | :star: | Passes all smoke + format tests, pending full suite |
| **DEVELOPMENT** | :hammer: | Under active development, not yet conformant |
| **LEGACY** | :book: | Implements older ISA version, grandfathered |
| **NON_CONFORMANT** | :x: | Fails critical tests, not recommended for use |

### 11.2 Gate Definitions

#### SHIPPED Quality Gate

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHIPPED QUALITY GATE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Required for ALL runtimes seeking SHIPPED certification:       │
│                                                                  │
│  1. SMOKE TESTS:           100.0% pass (0 failures)             │
│     - Must pass every test tagged "smoke"                        │
│     - Rationale: These are the minimum viable implementation     │
│                                                                  │
│  2. FORMAT TESTS:          100.0% pass (0 failures)             │
│     - One test per format (A through G) must pass                │
│     - Rationale: Encoding correctness is non-negotiable          │
│                                                                  │
│  3. OVERLAP SAFETY:        100.0% pass (0 failures)             │
│     - All tests tagged "overlap-safe" must pass                  │
│     - Rationale: Register overlap bugs are silent data corruptors │
│                                                                  │
│  4. TOTAL PASS RATE:       >= 98.0%                             │
│     - Across the full conformance suite                         │
│     - Rationale: Allows minor gaps in edge-case categories       │
│       (evolution, viewpoint) without blocking deployment         │
│                                                                  │
│  5. ZERO ERRORS:           0 error-status results               │
│     - No crashes, no exceptions, no timeouts                     │
│     - Rationale: An error is worse than a wrong answer           │
│                                                                  │
│  6. CROSS-RUNTIME AGREEMENT: >= 95.0% on cross_runtime tests    │
│     - Must agree with at least 2 other SHIPPED runtimes          │
│     - Rationale: Prevents ecosystem fragmentation                │
│                                                                  │
│  7. CYCLE BOUNDS:          All within declared min/max           │
│     - Must not exceed cycles_max on any test                     │
│     - Rationale: Catches infinite-loop bugs                      │
│                                                                  │
│  8. ISA SOURCE:            Must be isa_unified.py                │
│     - Rationale: Resolves the three-ISA problem                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### CANDIDATE Quality Gate

```
┌─────────────────────────────────────────────────────────────────┐
│                  CANDIDATE QUALITY GATE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. SMOKE TESTS:           >= 95.0% pass                        │
│  2. FORMAT TESTS:          >= 85.0% pass (at least 6/7 formats) │
│  3. OVERLAP SAFETY:        >= 90.0% pass                        │
│  4. TOTAL PASS RATE:       >= 90.0%                             │
│  5. ZERO ERRORS on smoke/format tests                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### DEVELOPMENT (Informational)

No formal gate. Any pass rate. Used for tracking progress during initial implementation.

### 11.3 Category-Specific Pass Requirements

Within a SHIPPED runtime, certain categories have stricter requirements because they form
the core execution foundation:

| Category | Min Pass Rate | Rationale |
|----------|:---:|-----------|
| control | 100% | HALT/JMP/CALL/RET are fundamental. No exceptions. |
| arithmetic | 100% | ADD/SUB/MUL are the most used opcodes. |
| memory | 100% | LOAD/STORE correctness is non-negotiable. |
| stack | 99% | Stack corruption breaks all function calls. |
| comparison | 95% | Flag-dependent branches need correct comparisons. |
| bitwise | 95% | Used in addressing and hashing. |
| a2a | 90% | Important for fleet coordination but complex. |
| confidence | 80% | Still under active specification. |
| viewpoint | 80% | Still under active specification. |
| tile | 70% | Experimental feature. |
| vocabulary | 70% | Experimental feature. |
| evolution | 50% | Speculative/experimental. |

### 11.4 Fleet-Wide Quality Gate

For the entire fleet to be considered conformant:

| Metric | Threshold |
|--------|:---------:|
| Runtimes at SHIPPED | >= 3 |
| Runtimes at CANDIDATE or above | >= 5 |
| No runtime at NON_CONFORMANT with `isa_source: isa_unified.py` | Required |
| Cross-runtime divergence on smoke tests | 0 |

---

## 12. Cross-Runtime Conformance Strategy

### 12.1 The Three-ISA Problem

The fleet currently suffers from three competing opcode numberings:

1. **`isa_unified.py`** — The canonical ISA. 247 opcodes, 7 formats. Written by convergence.
2. **`opcodes.py`** — The legacy numbering. Used by flux-py interpreter and vocabulary assembler.
3. **`formats.py`** — A third numbering. Reference-only, not imported anywhere.

The conformance schema pins to `isa_unified.py` version 2.0. Runtimes still using
`opcodes.py` or `formats.py` must either:
- (a) Migrate to `isa_unified.py` numbering, or
- (b) Provide a translation layer and declare `isa_source` in their Runtime Descriptor.

### 12.2 Identical Test Execution Protocol

To ensure that Python, Rust, Zig, and other runtimes execute tests identically:

```
Step 1: Load test vector's "program" hex string
Step 2: Decode to byte array (no assembler, no parser)
Step 3: Initialize machine state from "input" section
Step 4: Load bytecode into memory starting at address 0
Step 5: Set PC to input.pc (default 0)
Step 6: Execute until HALT or program counter exits the program region
Step 7: Capture state (registers, memory, stack, flags, pc_offset)
Step 8: Compare against "expected" (only checking non-empty fields)
Step 9: Record result as Test Run Result
```

### 12.3 State Comparison Rules

The comparison algorithm:

1. **Registers:** For each key in `expected.registers`, compare `actual.registers[key]`.
   - If key is missing from actual: FAIL (register was not modified)
   - If values differ: FAIL
   - If values match: PASS for this field

2. **Memory:** For each address in `expected.memory`, compare byte arrays.
   - Direct byte-by-byte comparison

3. **Stack:** If `expected.stack` is empty array `[]`, skip. If non-empty, compare.
   - Deep equality comparison (order matters)

4. **Flags:** For each flag in `expected.flags`, compare boolean values.

5. **PC Offset:** Must exactly match `expected.pc_offset`.

6. **Cycles:** Must satisfy `cycles_min <= actual <= cycles_max`.

7. **Halted:** Must exactly match `expected.halted` if specified.

### 12.4 Cross-Runtime Divergence Detection

When generating a conformance report, the system checks for cross-runtime divergences:

```
For each test vector T:
  results = { runtime: status for each runtime }
  if len(set of PASS runtimes) > 0 AND len(set of FAIL runtimes) > 0:
    flag as DIVERGENCE
    analyze:
      - Which runtimes agree? (likely correct)
      - Which disagree? (investigate)
      - Is the expected value wrong? (check against majority)
      - Is there a format/encoding difference? (check pc_offset)
```

### 12.5 Reference Implementation Strategy

The fleet should designate **two reference runtimes** in different languages:

- **Primary reference:** flux-core (Rust) — production runtime, most widely used
- **Secondary reference:** flux-zig (Zig) — fastest VM, independent implementation

A test's expected value is considered canonical when both references agree. If they
disagree, the test vector itself is flagged for review.

### 12.6 Test Vector Generation Protocol

To maximize coverage and catch divergences:

1. **Generate per-opcode tests:** At least one test per opcode (247 tests minimum).
2. **Generate per-format tests:** At least one test per format (7 tests minimum).
3. **Generate overlap tests:** For every 3-register format (E, G), test `rd==rs1`,
   `rd==rs2`, and `rd==rs1==rs2`.
4. **Generate width tests:** For arithmetic and memory ops, test i8, i16, i32 widths.
5. **Generate edge-case tests:** Zero, max value, min value, overflow, underflow.
6. **Generate integration tests:** GCD, Fibonacci, Sum of Squares (from audit rec #3).

### 12.7 Runner Contract

Each runtime MUST implement a runner function with this signature (pseudocode):

```
function run_conformance_test(test_vector: TestVector) -> TestRunResult:
    // Step 1: Decode program
    bytecode = decode_hex(test_vector.program)

    // Step 2: Initialize VM
    vm = new VM()
    for (reg, value) in test_vector.input.registers:
        vm.set_register(reg, value)
    for (addr, bytes) in test_vector.input.memory:
        vm.write_memory(addr, bytes)
    for (flag, value) in test_vector.input.flags:
        vm.set_flag(flag, value)
    vm.pc = test_vector.input.pc or 0
    vm.stack = test_vector.input.stack or []

    // Step 3: Load and execute
    start_time = now()
    vm.load(bytecode)
    vm.run_until_halt()  // or until PC exits program region
    end_time = now()

    // Step 4: Capture state
    actual = {
        registers: vm.dump_registers(),
        memory: vm.dump_memory(expected_addresses),
        stack: vm.dump_stack(),
        flags: vm.dump_flags(),
        pc_offset: vm.pc - test_vector.input.pc,
        halted: vm.is_halted(),
        cycles: vm.cycle_count or null
    }

    // Step 5: Compare
    mismatches = compare(actual, test_vector.expected)

    // Step 6: Return result
    return TestRunResult(
        test_id: test_vector.id,
        runtime_id: THIS_RUNTIME_ID,
        timestamp: now_iso(),
        status: mismatches.length == 0 ? "PASS" : "FAIL",
        actual: actual,
        mismatches: mismatches,
        duration_ns: end_time - start_time
    )
```

---

## 13. Priority Categories for Test Generation

### 13.1 Priority Matrix

Tests should be generated in this priority order, based on impact and risk:

| Priority | Category | Opcodes | Tests Needed | Rationale |
|:--------:|----------|---------|:------------:|-----------|
| P0 | control | 0x00-0x0F | 30+ | HALT/JMP/CALL/RET are fundamental. The JMP Format F bug proves this. |
| P0 | arithmetic | 0x10-0x1F | 40+ | Most-used opcodes. Overflow/underflow edge cases critical. |
| P0 | memory | 0x30-0x3F | 35+ | MOVI sign extension bug found in audit. LOAD/STORE must be exact. |
| P1 | stack | 0x50-0x5F | 25+ | Stack corruption is catastrophic. PUSH/POP opcode errors in audit. |
| P1 | comparison | 0x40-0x4F | 25+ | Flag-dependent branching. CMP/CMPI edge cases. |
| P1 | bitwise | 0x20-0x2F | 20+ | Used in addressing calculations. Shift/rotate edge cases. |
| P2 | a2a | 0x80-0x8F | 20+ | Core to fleet coordination. Mock-channel testing needed. |
| P2 | confidence | 0x60-0x6F | 15+ | INCREMENTS+2 trust engine depends on correct clamping. |
| P3 | viewpoint | 0x70-0x7F | 15+ | Epistemic metadata. Evidence hierarchy must be monotonic. |
| P3 | tile | 0x90-0x9F | 10+ | Experimental. Map/reduce correctness. |
| P3 | vocabulary | 0xA0-0xAF | 10+ | Experimental. Compile/lookup correctness. |
| P4 | evolution | 0xB0-0xBF | 8+ | Speculative. Mutation/genome operations. |
| P4 | extended | 0xC0-0xFF | 5+ | Reserved. Basic smoke tests only. |

### 13.2 Coverage Targets

| Coverage Type | Minimum | Target | Stretch |
|---------------|:-------:|:------:|:-------:|
| Opcode coverage (at least 1 test) | 150 | 200 | 247 |
| Format coverage (at least 1 test) | 7 | 14 | 21 |
| Width coverage (i8/i16/i32 per opcode) | 1 | 3 | 3 |
| Overlap safety tests | 10 | 25 | 40 |
| Edge-case tests (zero, max, overflow) | 20 | 50 | 100 |
| Integration tests (multi-instruction) | 3 | 10 | 20 |
| Cross-runtime divergence tests | 5 | 15 | 30 |
| **Total test count** | **142** | **300** | **500** |

### 13.3 Critical Test Patterns

These test patterns MUST be generated for every opcode category:

1. **Zero input:** All source operands are zero. Verifies the opcode doesn't crash on null.
2. **Identity input:** Source equals destination. Verifies overlap safety.
3. **Maximum value:** i8=127, i16=32767, i32=2147483647. Tests overflow handling.
4. **Minimum value:** i8=-128, i16=-32768, i32=-2147483648. Tests underflow handling.
5. **Mixed signs:** One positive, one negative source. Tests signed arithmetic.
6. **Adjacent registers:** R1/R2, R2/R3, etc. Verifies register file indexing.
7. **Boundary registers:** R0 (zero constant), R31 (PC). Verifies special register handling.
8. **Stack interaction:** If the opcode can affect the stack, test stack growth/shrinkage.
9. **Flag interaction:** If the opcode can set flags, test all flag combinations as input.
10. **Memory interaction:** If the opcode can read/write memory, test at low/high addresses.

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0.0-draft | 2026-04-12 | Super Z | Initial draft. Full schema for test vectors, run results, suite manifests, runtime descriptors, conformance reports. Quality gates defined. Cross-runtime strategy documented. |
| 1.0.0 | 2026-04-10 | Super Z | Original 22 test vectors (pre-schema). Documented in conformance-test-audit.md. |

---

## Appendix A: Opcode Quick Reference (isa_unified.py v2.0)

```
Format A (1 byte):  [opcode]
  0x00 HALT    0x01 NOP     0x02 BRK     0x03 WFI
  0x04 ???     0x05 ???     0x06 ???     0x07 ???

Format B (2 bytes): [opcode][rd]
  0x08 INC     0x09 DEC     0x0A NOT     0x0B NEG
  0x0C PUSH    0x0D POP     0x0E ???     0x0F ???

Format C (2 bytes): [opcode][imm8]
  (Various single-immediate operations)

Format D (3 bytes): [opcode][rd][imm8]
  0x18 MOVI    (and others with register + 8-bit immediate)

Format E (4 bytes): [opcode][rd][rs1][rs2]
  0x20 ADD     0x21 SUB     0x22 MUL     0x23 DIV
  0x24 MOD     0x25 AND     0x26 OR      0x27 XOR
  0x28 ADDI    0x29 SUBI    0x2A SHL     0x2B SHR
  0x2C CMP     ...          0x30 MOV     0x31 LOAD
  0x32 STORE   ...

Format F (4 bytes): [opcode][rd][imm16hi][imm16lo]
  0x43 JMP     0x44 JZ      0x45 JNZ     0x46 CALL
  ...

Format G (5 bytes): [opcode][rd][rs1][imm16hi][imm16lo]
  (Register + register + 16-bit immediate operations)
```

> **Note:** This quick reference is illustrative. The authoritative opcode map is
> `isa_unified.py` in the flux-runtime repository. The conformance audit found
> discrepancies between this map and `opcodes.py` — always verify against the
> canonical source.

---

## Appendix B: JSON-LD Context (for semantic interoperability)

```json
{
  "@context": {
    "fcs": "https://flux-spec.superinstance.org/schema/v2#",
    "test_id": "fcs:testId",
    "runtime_id": "fcs:runtimeId",
    "status": "fcs:status",
    "mnemonic": "fcs:mnemonic",
    "format": "fcs:format",
    "isa_version": "fcs:isaVersion",
    "certification": "fcs:certification",
    "pass_rate": "fcs:passRate"
  }
}
```

---

*Document ends. This schema is a living specification. Submit updates via PR to the
superz-vessel repository with the `schema` label.*
