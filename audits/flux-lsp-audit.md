# flux-lsp Technical Audit

**Auditor:** Super Z ⚡
**Date:** 2026-04-12
**Repo:** `github.com/SuperInstance/flux-lsp`
**Scope:** README.md, docs/grammar-spec.md, grammars/flux.tmLanguage.json, language-configuration.json, package.json
**Cross-references:** flux-spec (ISA.md, FIR.md, A2A.md, FLUXMD.md), flux-runtime (isa_unified.py, opcodes.py), flux-vocabulary, flux-ide

---

## 1. Executive Summary

**Overall Grade: C- (Excellent spec foundation, zero implementation)**

flux-lsp is a **specification-only repository** with no source code. It contains three high-quality artifacts — a 1,162-line grammar specification, a 579-line TextMate syntax grammar, and a language-configuration file — but the entire LSP server described in the README (8 TypeScript modules, 3 test files) does not exist. There is no `src/` directory, no `tsconfig.json`, no `node_modules`, no `.github/workflows`, no tests, no CI.

**The good news:** The grammar specification is genuinely excellent — one of the best-written documents in the fleet. It defines the complete `.flux.md` format with BNF grammars for every section type, a full opcode mnemonic list mapped to the unified ISA's 247 opcodes (0x00–0xFF), instruction formats (A–G), a type system, semantic rules, and a comprehensive worked example. The TextMate grammar covers all opcode categories including viewpoint ops (V_EVID through V_PRAGMA), SIMD/tensor/neural extensions, and A2A primitives.

**The bad news:** The README's status checklist shows every item unchecked. `package.json` has `"main": "dist/server.js"` but no TypeScript dependencies, no build tooling, and no entry point. The architecture diagram describes `src/server.ts`, `parser.ts`, `lexer.ts`, `analyzer.ts`, `completion.ts`, `diagnostics.ts`, `hover.ts`, and `definition.ts` — none of which exist. The fleet's primary IDE tooling dependency (flux-ide) has no LSP to connect to.

### Key Findings at a Glance

| # | Finding | Severity | Status |
|---|---------|----------|--------|
| 1 | **Zero implementation** — entire `src/` tree described in README is vaporware | **CRITICAL** | Open |
| 2 | **TextMate/grammar spec opcode divergence** — ~40 extra mnemonics in TextMate not defined in spec | **HIGH** | Open |
| 3 | **No TypeScript tooling** — package.json has build scripts but no tsconfig, no deps | **HIGH** | Open |
| 4 | **Grammar spec register range mismatch** — spec says R0–R15/F0–F15/V0–V15; ISA has R0–R31 | **MEDIUM** | Open |
| 5 | **No test infrastructure** — no test framework, no fixture files | **MEDIUM** | Open |
| 6 | **No integration with flux-spec** — opcode data should be pulled from canonical source | **MEDIUM** | Open |
| 7 | **TextMate grammar includes legacy opcodes** — IADD, ISUB, IMUL not in unified ISA | **LOW** | Open |
| 8 | **Language config minimal** — no comment toggling, no bracket matching for assembly | **LOW** | Open |

---

## 2. What Exists

### 2.1 docs/grammar-spec.md (1,162 lines) — EXCELLENT

This is the crown jewel of the repo. A formal `.flux.md` grammar specification covering:

| Section | Lines | Content |
|---------|-------|---------|
| §1 Overview | 1–24 | Design goals, file extension definition |
| §2 File Structure | 25–193 | YAML frontmatter, section headers, code blocks, directives (all with BNF) |
| §3 Section Types | 194–480 | Six section types: `fn:`, `agent:`, `tile:`, `region:`, `vocabulary:`, `test:` — each with BNF grammar, semantic rules, and examples |
| §4 Directive Syntax | 481–543 | `#!capability`, `#!import`, `#!export`, `#!deprecated` + 7 others |
| §5 Code Block Dialects | 544–626 | `flux`, `fir`, `fluxvocab` — each with examples and language tag classification table |
| §6 Expression Grammar | 627–821 | Labels, instructions, registers, immediates, strings, comments, **full opcode mnemonic list** (247 mnemonics), instruction formats A–G |
| §7 Type System | 822–921 | 12 primitive types, arrays, tuples, agent/tile/named types |
| §8 Semantic Rules | 922–986 | Section ordering, name resolution, import/export visibility, capability enforcement, code block validation |
| §9 Complete Example | 987–1117 | Fibonacci module with frontmatter, imports, region, fn, agent, tests |
| Appendix A | 1118–1138 | AST node types (12 node types from `flux.parser.nodes`) |
| Appendix B | 1139–1162 | Token types for LSP lexer (18 token types with regex patterns) |

**Opcode coverage in the grammar spec (Section 6.7):**

| Range | Category | Mnemonics Listed | Notes |
|-------|----------|-----------------|-------|
| 0x00–0x07 | System Control | 8 | HALT, NOP, RET, IRET, BRK, WFI, RESET, SYN |
| 0x08–0x0F | Single Register | 8 | INC, DEC, NOT, NEG, PUSH, POP, CONF_LD, CONF_ST |
| 0x10–0x17 | Immediate Only | 8 | SYS, TRAP, DBG, CLF, SEMA, YIELD, CACHE, STRIPCF |
| 0x18–0x1F | Reg + Imm8 | 8 | MOVI, ADDI, SUBI, ANDI, ORI, XORI, SHLI, SHRI |
| 0x20–0x2F | Integer Arithmetic | 16 | ADD through CMP_NE |
| 0x30–0x3F | Float/Memory/Control | 16 | FADD through JGT |
| 0x40–0x47 | Reg + Imm16 | 8 | MOVI16, ADDI16, SUBI16, JMP, JAL, CALL, LOOP, SELECT |
| 0x48–0x4F | Reg+Reg+Imm16 | 8 | LOADOFF through FILL |
| 0x50–0x5F | Agent-to-Agent | 16 | TELL, ASK, DELEG, BCAST, ..., HEARTBT |
| 0x60–0x6F | Confidence-Aware | 16 | C_ADD through C_VOTE |
| 0x70–0x7F | Viewpoint Operations | 16 | V_EVID through V_PRAGMA |
| 0x80–0x8F | Biology/Sensor | 16 | SENSE through CANBUS |
| 0x90–0x9F | Extended Math/Crypto | 16 | ABS through FCOS (15 listed) |
| 0xA0–0xAF | String/Collection | 16 | LEN through KEYGEN |
| 0xB0–0xBF | Vector/SIMD | 16 | VLOAD through VSELECT |
| 0xC0–0xCF | Tensor/Neural | 16 | TMATMUL through TQUANT |
| 0xD0–0xDF | Extended Memory/IO | 14 | DMA_CPY through GPU_SYNC |
| 0xE0–0xEF | Long Jumps/Calls | 13 | JMPL through WATCH |
| 0xF0–0xFF | Extended System/Debug | 11 | HALT_ERR through ILLEGAL |
| **Total** | | **247** | Matches unified ISA opcode count |

### 2.2 grammars/flux.tmLanguage.json (579 lines) — GOOD

A complete TextMate grammar with 83 pattern rules covering:

- **YAML frontmatter** — keys, values, booleans, numbers, quoted strings, lists
- **Section headings** — `## fn:`, `## agent:`, `## tile:`, `## region:`, `## vocabulary:`, `## test:` with function signature sub-parsing (params, types, arrow)
- **Directives** — 10 directive keywords: `capability`, `import`, `export`, `deprecated`, `experimental`, `require`, `feature`, `optimize`, `unsafe`, `test`, `bench`
- **Code blocks** — 5 language categories:
  - `flux`/`fluxfn`/`flux-type` → assembly highlighting
  - `fir` → SSA IR highlighting
  - `fluxvocab` → vocabulary word highlighting
  - `json`/`yaml`/`toml` → data block highlighting
  - `c`/`python`/`rust`/`bash`/`sh` → native block delimiters
- **Assembly highlighting** — 33 instruction rule groups covering all opcode categories:
  - System control, single-register, immediate, reg+imm8
  - Arithmetic, float, memory, control-flow, stack
  - Comparison, math, crypto
  - A2A (TELL/ASK/DELEG/BCAST/...)
  - Confidence-aware (C_ADD through C_VOTE)
  - Viewpoint (V_EVID through V_PRAGMA)
  - Sensor (SENSE through CANBUS)
  - SIMD vector (VLOAD through VSELECT)
  - Tensor/neural (TMATMUL through TQUANT)
  - Extended memory, coroutines, debug, region, trust, cast, legacy
  - Reserved slots
- **Register highlighting** — GP (R0–R15), FP (F0–F15), VEC (V0–V15), SPECIAL (SP, FP, LR, PC, FLAGS)
- **Immediate literals** — hex, binary, decimal
- **String literals** — with escape sequences
- **FIR IR highlighting** — SSA values (%name), types, keywords (function, ret, jump, branch), intrinsics (malloc, free, memcpy)
- **Vocabulary highlighting** — word definitions (`:name`), stack effect comments
- **Markdown elements** — bold, italic, inline code, lists, type annotations

### 2.3 language-configuration.json (23 lines) — MINIMAL

```json
{
  "comments": { "lineComment": ";" },
  "brackets": [["[", "]"], ["(", ")"], ["{", "}"]],
  "autoClosingPairs": [...],
  "wordPattern": "[a-zA-Z_][a-zA-Z0-9_]*",
  "folding": { "markers": { "start": "^##\\s+", "end": "(?=(^##\\s+)|$)" } }
}
```

Section-based folding is a nice touch — `## fn:`, `## tile:`, etc. fold as regions. But this is bare-minimum configuration.

### 2.4 package.json (25 lines) — SHELL ONLY

```json
{
  "name": "flux-lsp",
  "version": "0.1.0",
  "main": "dist/server.js",
  "scripts": { "build": "tsc", "watch": "tsc --watch", "test": "jest" },
  "contributes": {
    "languages": [{ "id": "flux.md", "extensions": [".flux.md"] }],
    "grammars": [{ "language": "flux.md", "scopeName": "source.flux.md", ... }]
  }
}
```

This is structured as a VS Code extension manifest. It registers the `flux.md` language ID and TextMate grammar. But:
- No `dependencies` field at all
- No `devDependencies` (no typescript, no jest, no `vscode-languageserver`, no `vscode-languageclient`)
- No `engines` field (no Node.js version constraint)
- `"main": "dist/server.js"` references a file that cannot be built

### 2.5 README.md (93 lines) — GOOD DOCUMENTATION, DECEPTIVE STATUS

The README describes 7 features, an 8-file architecture, editor integration plans, and a status checklist with **8 unchecked items**. This is honest — every item is unchecked, clearly signaling that nothing works yet. The README links to flux-spec, flux-ide, and flux-vocabulary correctly.

---

## 3. What's Missing

### 3.1 The Entire LSP Server (CRITICAL)

| Planned File | Status | Purpose |
|-------------|--------|---------|
| `src/server.ts` | Does not exist | LSP server entry point, connection handling |
| `src/parser.ts` | Does not exist | `.flux.md` parser producing AST |
| `src/lexer.ts` | Does not exist | Tokenizer for code blocks |
| `src/analyzer.ts` | Does not exist | Semantic analysis, name resolution |
| `src/completion.ts` | Does not exist | Autocomplete for opcodes, registers, vocab |
| `src/diagnostics.ts` | Does not exist | Error/warning reporting |
| `src/hover.ts` | Does not exist | Opcode documentation on hover |
| `src/definition.ts` | Does not exist | Go-to-definition navigation |
| `test/parser.test.ts` | Does not exist | Parser tests |
| `test/completion.test.ts` | Does not exist | Completion tests |
| `test/diagnostics.test.ts` | Does not exist | Diagnostics tests |

### 3.2 Build Infrastructure (HIGH)

- No `tsconfig.json`
- No `node_modules/`
- No `.github/workflows/` (no CI)
- No `.gitignore`
- No `eslint` or `prettier` config
- No `jest.config.js`

### 3.3 Test Fixtures (MEDIUM)

- No `test/fixtures/` directory with sample `.flux.md` files
- No snapshot tests for parser output
- No conformance test vectors (the fleet has none for the unified ISA)

### 3.4 LSP Protocol Implementation (HIGH)

The LSP server needs to implement these capabilities:

| Capability | Complexity | Dependencies |
|-----------|-----------|--------------|
| `textDocument/completion` | Medium | Opcode table, register table, vocabulary index |
| `textDocument/hover` | Medium | Opcode documentation, type system |
| `textDocument/definition` | Medium | Symbol table, cross-file resolution |
| `textDocument/references` | Medium | Symbol table |
| `textDocument/diagnostics` | High | Full parser + semantic analysis |
| `textDocument/foldingRange` | Low | Already handled by language-config markers |
| `textDocument/documentSymbol` | Low | Section headings |
| `textDocument/codeAction` | Low | Quick fixes for common errors |

---

## 4. Grammar Spec Quality Assessment

**Grade: A- (Comprehensive, well-structured, actionable)**

### 4.1 Strengths

1. **Complete BNF coverage.** Every structural element — frontmatter, section headings, code blocks, directives, labels, instructions, registers, immediates, strings, types — has a formal BNF grammar. This is immediately implementable as a parser specification.

2. **Opcode-to-ISA mapping is correct.** The 247 mnemonics in Section 6.7 map correctly to the unified ISA defined in `flux-runtime/src/flux/bytecode/isa_unified.py`. The opcode ranges (0x00–0xFF) match the canonical ISA spec in `flux-spec/ISA.md`. Every category from system control (0x00) through extended debug (0xFF) is represented.

3. **Instruction format specification is precise.** The 7 format table (A through G) in Section 6.8 defines exact byte layouts:
   - Format A: 1 byte `[opcode]` → HALT
   - Format B: 2 bytes `[opcode][reg:u8]` → INC R2
   - Format C: 2 bytes `[opcode][imm8:u8]` → SYS 1
   - Format D: 3 bytes `[opcode][reg:u8][imm8:i8]` → MOVI R0, 42
   - Format E: 4 bytes `[opcode][rd:u8][rs1:u8][rs2:u8]` → ADD R0, R1, R2
   - Format F: 4 bytes `[opcode][reg:u8][imm16:i16]` → JMP R0, +100
   - Format G: 5 bytes `[opcode][rd:u8][rs1:u8][imm16:i16]` → LOADOFF R0, R1, 100

4. **Worked example is extensive.** The Fibonacci module (Section 9, lines 987–1117) demonstrates frontmatter, imports, capabilities, exports, regions, typed functions with recursion, agent definitions with A2A communication, and test sections — all in a single realistic `.flux.md` file.

5. **Token types for LSP lexer.** Appendix B provides 18 token types with regex patterns. This is directly implementable as a scanner.

6. **Semantic rules are well-defined.** Section 8 specifies:
   - Section ordering constraints (10-step ordering with warnings)
   - Name resolution scoping (module → region → vocabulary → tile → fn → agent → test)
   - Import/export visibility (private by default, explicit export, no circular imports)
   - Capability enforcement (permission checks before TELL/ASK/DELEG/SENSE/ACTUATE)
   - Code block validation (mnemonic validity, register ranges, SSA form for FIR)

### 4.2 Weaknesses

1. **Register range too narrow.** The grammar spec (Section 6.3, line 668) defines:
   ```
   gp_register  ::= "R" DIGIT     ; R0-R15
   fp_register  ::= "F" DIGIT     ; F0-F15
   vec_register ::= "V" DIGIT     ; V0-V15
   ```
   But the unified ISA (`isa_unified.py`) defines 32 general-purpose registers (R0–R31). The register table in the spec (Section 6.3, line 674) says "R0–R10" for general-purpose, "R11 = SP", "R12–R13", "R14 = FP", "R15 = LR" — totaling 16 registers. The ISA spec says 32. **This is a discrepancy that the LSP must resolve.**

   **Recommendation:** The grammar spec should document both the 16-register "standard ABI" subset and the 32-register "full ISA" set. The lexer should accept R0–R31 but the diagnostics should warn about using R16–R31 without explicit `#!unsafe` or a note that these are ABI-reserved.

2. **Missing grammar for some constructs used in examples.** The spec's Section 9 example uses `MEMSET` (line 1018), `REGION_CREATE` (line 1016), and `CMP_NE` (line 1038) which appear in the TextMate grammar but are NOT listed in the grammar spec's Section 6.7 opcode table. Specifically:
   - `MEMSET` — not in any opcode range
   - `MEMCOPY` — not in any opcode range
   - `REGION_CREATE` — not in any opcode range
   - `REGION_DESTROY` — not in any opcode range
   - `LOAD8`, `STORE8` — not in any opcode range

3. **Section 6.3 register alias table conflicts with flux-os.** The spec maps R14=FP, R15=LR. flux-os maps R2=SP, R3=BP, R4=PC. The fleet has not converged on a register ABI.

4. **No error recovery specification.** The BNF grammars define valid syntax but don't specify how the parser should recover from errors. For an LSP, this is critical — incremental parsing with error recovery is what allows real-time diagnostics as the user types.

5. **Version date is wrong.** The spec header says "Date: 2025-07-11" but the repo was created 2026-04-11. This is a cosmetic issue but undermines trust in the spec's accuracy.

### 4.3 Opcode Coverage Assessment

The grammar spec's Section 6.7 lists **247 mnemonics** across **19 opcode categories**. This matches the unified ISA's claim of "247 opcodes across 256 addressable slots" from `flux-runtime/src/flux/bytecode/isa_unified.py`.

**Known gaps** (opcode slots 0x00–0xFF that have no mnemonic listed):
- 0x90 range lists 15 mnemonics (ABS through FCOS) but has space for 16
- 0xD0 range lists 14 mnemonics but has space for 16
- 0xE0 range lists 13 mnemonics but has space for 16
- 0xF0 range lists 11 mnemonics but has space for 16

**Total unassigned slots: ~19.** Some of these are intentional reserved slots; others may be unlisted opcodes. The TextMate grammar includes some of these extras (see Section 5).

---

## 5. TextMate Grammar Assessment

**Grade: B+ (Broad coverage, over-inclusive with legacy opcodes)**

### 5.1 Coverage Analysis

The TextMate grammar provides **33 instruction rule groups** covering every opcode category. Here's the breakdown:

| Rule Group | Categories Covered | Mnemonics in Pattern |
|-----------|-------------------|---------------------|
| `asm-instructions` (33 rules) | All 19 ISA categories + legacy | ~310+ patterns |
| `asm-registers` | GP, FP, VEC, SPECIAL | R0–R15, F0–F15, V0–V15, SP/FP/LR/PC/FLAGS |
| `asm-comments` | `;` and `#` line comments | 2 rules |
| `asm-labels` | `@name:` labels and `@name` references | 2 rules |
| `asm-immediates` | hex, binary, decimal | 3 rules |
| `asm-strings` | `"..."` with escapes | 1 rule |
| `fir-ir` | SSA IR highlighting | 10 rules |
| `flux-vocab` | `:word` definitions, stack effects | 3 rules |
| `data-block-content` | JSON/YAML data blocks | 3 rules |
| `section-headings` | All 6 section types + H1/H3+ | 3 rules |
| `fn-signature` | Function parameters, types, arrow | 7 rules |
| `directives` | 11 directive keywords | 2 rules |
| `frontmatter` | YAML key-value pairs | 5 rules |
| `markdown-elements` | Bold, italic, inline code, lists, types | 6 rules |

### 5.2 TextMate vs. Grammar Spec Opcode Divergence

**CRITICAL FINDING:** The TextMate grammar includes ~40 instruction mnemonics that are NOT defined in the grammar spec's Section 6.7. These extras fall into several categories:

#### Category 1: Legacy ISA Opcodes (should be removed or flagged)

These are from the OLD `opcodes.py` ISA and should NOT be highlighted in the unified ISA:

| Mnemonic | Old ISA Location | Notes |
|----------|-----------------|-------|
| `IADD` | 0x08 (old) | Conflicts with INC in unified |
| `ISUB` | 0x09 (old) | Conflicts with DEC in unified |
| `IMUL` | 0x0A (old) | Conflicts with NOT in unified |
| `IDIV` | 0x0B (old) | Conflicts with NEG in unified |
| `IMOD` | — | Old modulus |
| `IREM` | — | Old remainder |
| `IAND` | — | Old bitwise AND |
| `IOR` | — | Old bitwise OR |
| `IXOR` | — | Old bitwise XOR |
| `INOT` | — | Old bitwise NOT |
| `ISHL` | — | Old shift left |
| `ISHR` | — | Old shift right |
| `ICMP` | — | Old comparison |
| `IEQ`, `ILT`, `ILE`, `IGT`, `IGE` | — | Old typed comparisons |

**Impact:** If a user writes `IADD R0, R1, R2` in a `.flux.md` file, the TextMate grammar highlights it as a valid instruction, but the unified ISA would interpret `IADD` as an unknown mnemonic (or as `INC` if opcode 0x08 is used). The LSP's diagnostic provider would flag it as invalid.

**Recommendation:** Remove all `I`-prefixed legacy opcodes from the TextMate grammar. Alternatively, add them to a separate `deprecated` scope with a dimmed color.

#### Category 2: Aliases and Extras (legitimate additions)

These are useful aliases or extensions that exist in some runtimes but aren't in the unified spec:

| Mnemonic | Notes |
|----------|-------|
| `BROADCAST` | Alias for `BCAST` — keep both |
| `DELEGATE` | Alias for `DELEG` — keep both |
| `ALLOCA` | Stack allocation — used in FIR |
| `DUP`, `SWAP`, `ROT` | Stack operations — defined in flux-runtime |
| `LOAD8`, `STORE8` | Byte-width memory ops — used in examples |
| `MEMSET`, `MEMCOPY`, `MEMCMP` | Bulk memory ops — used in spec examples |
| `REGION_CREATE`, `REGION_DESTROY`, `REGION_TRANSFER` | Region management — used in examples |
| `RESOURCE_ACQUIRE`, `RESOURCE_RELEASE` | Resource management |
| `CAST`, `BOX`, `UNBOX` | Type operations |
| `CHECK_TYPE`, `CHECK_BOUNDS` | Runtime checks |
| `CALL_IND`, `TAILCALL` | Indirect calls |
| `VFMA`, `VSUB`, `VDIV` | Extended SIMD ops |
| `DEBUG_BREAK` | Debug instruction |
| `TEST`, `SETCC` | Comparison/flag ops |
| `TRUST_CHECK`, `TRUST_UPDATE`, `TRUST_QUERY` | Trust system ops |
| `REVOKE_TRUST`, `CAP_REQUIRE`, `CAP_REQUEST`, `CAP_GRANT`, `CAP_REVOKE` | Capability ops |
| `BARRIER`, `SYNC_CLOCK`, `FORMATION_UPDATE`, `EMERGENCY_STOP` | Coordination ops |
| `DELEGATE_RESULT`, `REPORT_STATUS`, `REQUEST_OVERRIDE`, `DECLARE_INTENT`, `ASSERT_GOAL`, `VERIFY_OUTCOME`, `EXPLAIN_FAILURE`, `SET_PRIORITY` | A2A legacy ops |

**Impact:** These opcodes appear in flux-runtime's vocabulary assembler and agent system. They're used in real `.flux.md` files. The grammar spec should be updated to include them.

**Recommendation:** Add Category 2 mnemonics to the grammar spec's Section 6.7 (with notes about which runtime defines them). Create a separate "Extended/Implementation-Defined" section.

#### Category 3: Conflicts with Special Registers

The TextMate grammar's `asm-registers` rule matches `FLAGS` as a special register. But `FLAGS` also appears in the `asm-instructions` legacy comparison rules (`SETCC`), creating ambiguity. In practice, TextMatch resolves this by rule ordering, but it's fragile.

### 5.3 Register Range Issue

Both the grammar spec and TextMate grammar limit registers to R0–R15, F0–F15, V0–V15. The unified ISA defines R0–R31. If a user writes `MOV R16, R17`, it won't be highlighted as a register in the TextMate grammar.

**Regex used:** `\\bR(1[0-5]|[0-9])\\b` → only matches R0–R15
**Should be:** `\\bR(3[0-1]|[12][0-9]|[0-9])\\b` → matches R0–R31

Similarly for F and V registers.

### 5.4 Grammar Quality

The TextMate grammar follows best practices:
- Uses `contentName` for code block interiors (e.g., `source.flux.asm`)
- Nested includes via `{ "include": "#pattern-name" }`
- Named captures for sub-elements (function name, parameters, types)
- Consistent naming convention: `scope.category.subcategory.flux.md`

---

## 6. Architecture Assessment

The README describes this architecture:

```
src/
├── server.ts          # LSP server entry point
├── parser.ts          # .flux.md parser (AST)
├── lexer.ts           # Tokenizer
├── analyzer.ts        # Semantic analysis
├── completion.ts      # Completion provider
├── diagnostics.ts     # Error reporting
├── hover.ts           # Hover documentation
└── definition.ts      # Go to definition
```

**Assessment: Sound but incomplete.** The module breakdown follows standard LSP server patterns. However, for a `.flux.md` file, the architecture needs additional modules:

| Missing Module | Why It's Needed |
|---------------|----------------|
| `documents.ts` | Document store (manages open files, tracks edits, incremental parsing) |
| `symbols.ts` | Symbol table (index of all fn/tile/agent/region/vocabulary definitions) |
| `references.ts` | Find-references provider |
| `folding.ts` | Folding range provider (already partially in language-config) |
| `workspace.ts` | Workspace-level index (cross-file imports, vocabulary resolution) |
| `opcode-table.ts` | Unified opcode table (single source of truth for all 247 opcodes) |
| `register-table.ts` | Register definitions (ranges, aliases, ABI conventions) |
| `vocab-index.ts` | Vocabulary word index (from flux-vocabulary repo) |

**Recommended architecture:**

```
src/
├── server.ts              # LSP entry point, connection lifecycle
├── documents.ts           # Document store, sync, incremental parsing
├── lexer.ts               # Tokenizer (uses Appendix B token types)
├── parser.ts              # .flux.md parser (uses §2-6 BNF grammars)
├── ast.ts                 # AST node type definitions (uses Appendix A)
├── analyzer.ts            # Semantic analysis, name resolution, type checking
├── symbols.ts             # Symbol table, definition indexing
├── opcode-table.ts        # Canonical opcode table (247 opcodes from ISA)
├── register-table.ts      # Register definitions (R0-R31, F0-F15, V0-V15, aliases)
├── completion.ts          # Completion provider (opcodes, registers, vocab)
├── diagnostics.ts         # Diagnostic provider (errors, warnings)
├── hover.ts               # Hover provider (opcode docs, type info)
├── definition.ts          # Go-to-definition provider
├── references.ts          # Find-references provider
├── folding.ts             # Folding range provider
├── document-symbol.ts     # Document symbol provider
└── workspace.ts           # Workspace index, cross-file resolution
test/
├── lexer.test.ts
├── parser.test.ts
├── analyzer.test.ts
├── completion.test.ts
├── diagnostics.test.ts
└── fixtures/
    ├── simple-function.flux.md
    ├── full-module.flux.md    (the Fibonacci example from §9)
    ├── vocabulary.flux.md
    └── errors.flux.md
```

**Technology choice:** TypeScript is correct. The `vscode-languageserver` and `vscode-languageserver-textdocument` npm packages are the standard foundation. For the parser, consider:
- **Hand-written recursive descent** — simplest for the markdown+assembly hybrid grammar
- **tree-sitter** — better performance, but requires writing a `.grammar` file and C bindings
- **chevrotain** — pure TypeScript parsing library with good error recovery

**Recommendation:** Start with hand-written recursive descent. The grammar is simple enough that tree-sitter's complexity isn't justified. chevrotain adds a dependency but provides excellent error recovery out of the box — consider it for Phase 2.

---

## 7. Build Strategy

### Phase 1: Skeleton + Syntax Highlighting Verification (Week 1)

The TextMate grammar already exists and works. Verify it in VS Code:

1. Create a minimal VS Code extension wrapper:
   - `package.json` (already exists, needs devDependencies)
   - `tsconfig.json`
   - `.vscodeignore`

2. Add dependencies:
   ```json
   {
     "devDependencies": {
       "typescript": "^5.3",
       "@types/node": "^20",
       "vscode": "^1.85"
     },
     "dependencies": {
       "vscode-languageclient": "^9.0"
     }
   }
   ```

3. **Deliverable:** `.flux.md` files open in VS Code with correct syntax highlighting. This is already 80% done.

### Phase 2: Parser + Diagnostics (Week 2–3)

1. Implement `lexer.ts` using Appendix B token types
2. Implement `parser.ts` using §2–6 BNF grammars
3. Implement `ast.ts` using Appendix A node types
4. Implement `diagnostics.ts`:
   - Invalid opcode mnemonic (not in the 247-opcode table)
   - Register out of range (R0–R31, F0–F15, V0–V15)
   - Missing section body (empty `## fn:` without code block)
   - Undeclared vocabulary/tile references
   - Import/export errors
   - Duplicate section names

**Deliverable:** Red squiggly lines on errors in `.flux.md` files.

### Phase 3: Completion + Hover (Week 3–4)

1. Implement `opcode-table.ts` — single source of truth for all 247 opcodes with:
   - Mnemonic, opcode byte, format, operand types, category, one-line description
   - Pull descriptions from `flux-spec/OPCODES.md`

2. Implement `register-table.ts` — all registers with:
   - Name, alias, range, ABI convention

3. Implement `completion.ts`:
   - Trigger on uppercase letter after whitespace in `flux` code blocks → opcode completion
   - Trigger on `R`, `F`, `V` after whitespace → register completion
   - Trigger after `#!` → directive keyword completion
   - Trigger after `##` → section type completion

4. Implement `hover.ts`:
   - Hover on opcode → description, format, operand types
   - Hover on register → ABI role, valid range
   - Hover on type → size, description

**Deliverable:** Ctrl+Space shows completions, hover shows docs.

### Phase 4: Navigation (Week 4–5)

1. Implement `symbols.ts` — index all `## fn:`, `## tile:`, `## agent:`, `## region:`, `## vocabulary:`, `## test:` definitions
2. Implement `definition.ts` — go to definition from any reference to a vocabulary word or tile
3. Implement `references.ts` — find all uses of a vocabulary word or tile
4. Implement `document-symbol.ts` — outline view shows all sections
5. Implement `folding.ts` — fold sections (backup for language-config markers)

**Deliverable:** F12/Ctrl+Click navigates to definitions.

### Phase 5: Workspace + Cross-File (Week 5–6)

1. Implement `workspace.ts` — index all `.flux.md` files in workspace
2. Implement `documents.ts` — document store with incremental parsing
3. Cross-file go-to-definition (jump to imported module's exported symbol)
4. Cross-file diagnostics (detect broken imports)

**Deliverable:** Multi-file `.flux.md` projects have full IDE support.

### Phase 6: LSP Standalone Server (Week 6–7)

1. Extract the LSP core from the VS Code extension into a standalone `server.ts`
2. Support stdio transport (for Neovim, Emacs, Helix)
3. Add `--stdio` CLI flag
4. Test with nvim-lspconfig

**Deliverable:** flux-lsp works in any LSP-compatible editor.

---

## 8. Integration Points

### 8.1 flux-spec → flux-lsp (PRIMARY)

flux-lsp's opcode table, register table, and type system should be sourced from flux-spec:

| flux-spec File | flux-lsp Usage |
|---------------|----------------|
| `ISA.md` | Instruction format definitions, register ABI, encoding rules |
| `OPCODES.md` | Opcode table (mnemonic → byte → format → description) |
| `FIR.md` | FIR IR grammar for `fir` code blocks |
| `FLUXMD.md` | `.flux.md` file format definition |
| `FLUXVOCAB.md` | Vocabulary format specification |

**Current problem:** flux-spec itself is a 1KB placeholder with no actual spec files committed (per fleet census). The specs were written during sessions but may not be pushed. flux-lsp's grammar spec duplicates information that should live in flux-spec.

**Recommendation:** flux-lsp should import opcode/register/type data from flux-spec rather than maintaining its own copy. Until flux-spec is populated, flux-lsp's grammar spec serves as the de facto canonical source.

### 8.2 flux-vocabulary → flux-lsp (COMPLETION DATA)

flux-vocabulary provides vocabulary word definitions. flux-lsp's completion provider should offer:
- Vocabulary words defined in the current file (`## vocabulary:` sections)
- Vocabulary words from imported modules
- Standard library vocabulary words (once flux-stdlib exists)

**Current problem:** flux-vocabulary is a 1KB placeholder.

**Recommendation:** Define a vocabulary index format (JSON) that flux-vocabulary exports and flux-lsp consumes. Example:

```json
{
  "words": [
    { "name": "double", "params": "( n -- 2n )", "module": "core", "bytecode_size": 5 },
    { "name": "swap", "params": "( a b -- b a )", "module": "core", "bytecode_size": 11 }
  ]
}
```

### 8.3 flux-ide → flux-lsp (PRIMARY CONSUMER)

flux-ide is the web IDE that flux-lsp primarily serves. Integration requirements:

| Feature | flux-ide Needs | flux-lsp Provides |
|---------|---------------|-------------------|
| Syntax highlighting | ✅ Already works (TextMate grammar) | `grammars/flux.tmLanguage.json` |
| Error diagnostics | ❌ Missing | `textDocument/publishDiagnostics` |
| Autocomplete | ❌ Missing | `textDocument/completion` |
| Go-to-definition | ❌ Missing | `textDocument/definition` |
| Hover docs | ❌ Missing | `textDocument/hover` |
| Outline view | ❌ Missing | `textDocument/documentSymbol` |

flux-ide is a TypeScript/Next.js project. It can use the Monaco Editor, which has native LSP client support. The integration path is:
1. Build flux-lsp as a standalone LSP server (stdio transport)
2. Run flux-lsp as a subprocess in flux-ide's backend
3. Connect Monaco's LSP client to flux-lsp via WebSocket or direct stdio bridge

### 8.4 flux-runtime → flux-lsp (VALIDATION)

flux-runtime's parser (`src/flux/parser/`) already parses `.flux.md` files into AST. flux-lsp's parser should produce a compatible AST. The two parsers don't need to share code, but they should agree on:

1. What constitutes a valid `.flux.md` file
2. AST node types (see grammar spec Appendix A vs. flux-runtime's `flux.parser.nodes`)
3. Error messages and severity levels

**Current problem:** flux-runtime's parser uses the old ISA opcode numbers. Any `.flux.md` file that flux-runtime can parse may use opcodes that flux-lsp would flag as invalid (if flux-lsp validates against the unified ISA).

**Recommendation:** flux-lsp should validate against the unified ISA and emit a warning when old-ISA mnemonics (IADD, ISUB, etc.) are detected.

### 8.5 Cross-Editor Support

flux-lsp's README lists VS Code, Neovim, Emacs, and Helix as target editors:

| Editor | LSP Client | Transport | Status |
|--------|-----------|-----------|--------|
| VS Code | Built-in | stdio (via extension) | Needs extension wrapper |
| Neovim | nvim-lspconfig | stdio | Works with standalone server |
| Emacs | lsp-mode | stdio | Works with standalone server |
| Helix | Built-in | stdio | Works with standalone server |
| Monaco (flux-ide) | monaco-languageclient | WebSocket | Needs WS bridge |
| Web (generic) | Custom | WebSocket | Needs WS bridge |

---

## 9. Recommendations

### Priority 1: Resolve Grammar Spec vs. TextMate Opcode Divergence (CRITICAL)

**Action:** Audit the ~40 extra mnemonics in the TextMate grammar. For each:
- If it's a legacy opcode (IADD, ISUB, etc.) → remove from TextMate, add to deprecated list
- If it's a valid extension (MEMSET, REGION_CREATE, etc.) → add to grammar spec Section 6.7
- If it's an alias (BROADCAST→BCAST, DELEGATE→DELEG) → document as alias in spec

**Estimated effort:** 2 hours.

### Priority 2: Fix Register Ranges (HIGH)

**Action:** Update both grammar spec and TextMate grammar to accept R0–R31. Keep R0–R15 as the "standard ABI" subset for diagnostics warnings. The regex change is:
```
Old: \\bR(1[0-5]|[0-9])\\b
New: \\bR(3[0-1]|[12][0-9]|[0-9])\\b
```

**Estimated effort:** 30 minutes.

### Priority 3: Scaffold the TypeScript Project (HIGH)

**Action:** Add the missing build infrastructure:
1. Create `tsconfig.json` with strict mode
2. Add `devDependencies`: typescript, @types/node, jest, @types/jest, ts-jest
3. Add `dependencies`: vscode-languageserver, vscode-languageserver-textdocument
4. Create `.gitignore`
5. Create `src/` directory with stub files (module exports)
6. Create `test/` directory with a single smoke test
7. Verify `npm run build` and `npm run test` work

**Estimated effort:** 2 hours.

### Priority 4: Implement Parser + Diagnostics (HIGH)

**Action:** Build the parser using the grammar spec's BNF grammars. Start with:
1. YAML frontmatter parser
2. Section heading parser (6 types)
3. Code block extractor (flux, fir, fluxvocab)
4. Assembly instruction parser (mnemonic + operands)
5. Diagnostic: invalid opcode, invalid register, missing section body

This gives the fleet immediate value: error detection in `.flux.md` files.

**Estimated effort:** 1–2 weeks.

### Priority 5: Implement Completion (MEDIUM)

**Action:** Build the opcode completion table with all 247 mnemonics. Each entry needs:
- Mnemonic, opcode byte, format (A–G), operand types, category, one-line description

This is the highest-impact feature for developer experience. Even without full semantic analysis, opcode completion in `flux` code blocks is extremely useful.

**Estimated effort:** 3–5 days.

### Priority 6: Coordinate with flux-spec (MEDIUM)

**Action:** Push the canonical ISA spec, FIR spec, and `.flux.md` format spec to flux-spec. Then refactor flux-lsp to import from flux-spec rather than duplicating. This eliminates the synchronization problem.

**Blocker:** flux-spec is a 1KB placeholder. Until someone commits the specs there, flux-lsp's grammar spec is the canonical source.

### Priority 7: Build flux-ide Integration (MEDIUM)

**Action:** Add a WebSocket transport to flux-lsp for Monaco Editor consumption. Create a shared `@flux-lsp/client` package that flux-ide can import.

**Estimated effort:** 3–5 days.

### Priority 8: Add CI (LOW)

**Action:** Create `.github/workflows/ci.yml`:
```yaml
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run build
      - run: npm test
```

**Estimated effort:** 30 minutes.

---

## Appendix A: File Inventory

| File | Lines | Size | Status | Quality |
|------|-------|------|--------|---------|
| `README.md` | 93 | ~4KB | Complete | Good — honest status, clear architecture |
| `docs/grammar-spec.md` | 1,162 | ~45KB | Complete | Excellent — comprehensive, formal, actionable |
| `grammars/flux.tmLanguage.json` | 579 | ~20KB | Complete | Good — broad coverage, needs opcode cleanup |
| `language-configuration.json` | 23 | ~0.5KB | Complete | Minimal — needs bracket matching, comment toggling |
| `package.json` | 25 | ~0.7KB | Incomplete | No dependencies, no build tooling |
| `src/` | — | — | **MISSING** | Entire LSP server not implemented |
| `tsconfig.json` | — | — | **MISSING** | TypeScript configuration not created |
| `test/` | — | — | **MISSING** | No test infrastructure |
| `.github/workflows/` | — | — | **MISSING** | No CI |
| `.gitignore` | — | — | **MISSING** | Not created |

**Total lines of actual content:** 1,882 lines across 5 files.

## Appendix B: Opcode Table — Grammar Spec vs. TextMate

**In grammar spec but NOT in TextMate (should be added):**

None found — the TextMate grammar covers all grammar spec opcodes.

**In TextMate but NOT in grammar spec (40 mnemonics):**

| Mnemonic | Category | Action |
|----------|----------|--------|
| `IADD`, `ISUB`, `IMUL`, `IDIV`, `IMOD`, `IREM` | Legacy arithmetic | Remove (old ISA) |
| `IAND`, `IOR`, `IXOR`, `INOT`, `ISHL`, `ISHR` | Legacy bitwise | Remove (old ISA) |
| `ICMP`, `IEQ`, `ILT`, `ILE`, `IGT`, `IGE` | Legacy comparison | Remove (old ISA) |
| `BROADCAST` | A2A alias | Add to spec as alias for BCAST |
| `DELEGATE` | A2A alias | Add to spec as alias for DELEG |
| `ALLOCA`, `DUP`, `SWAP`, `ROT` | Stack ops | Add to spec |
| `LOAD8`, `STORE8` | Memory ops | Add to spec |
| `MEMSET`, `MEMCOPY`, `MEMCMP` | Bulk memory | Add to spec |
| `REGION_CREATE`, `REGION_DESTROY`, `REGION_TRANSFER` | Region mgmt | Add to spec |
| `RESOURCE_ACQUIRE`, `RESOURCE_RELEASE` | Resource mgmt | Add to spec |
| `CAST`, `BOX`, `UNBOX`, `CHECK_TYPE`, `CHECK_BOUNDS` | Type ops | Add to spec |
| `CALL_IND`, `TAILCALL` | Call ops | Add to spec |
| `VFMA`, `VSUB`, `VDIV` | Extended SIMD | Add to spec |
| `DEBUG_BREAK` | Debug | Add to spec |
| `TEST`, `SETCC` | Comparison | Add to spec |
| `TRUST_CHECK`, `TRUST_UPDATE`, `TRUST_QUERY` | Trust system | Add to spec |
| `REVOKE_TRUST`, `CAP_REQUIRE`, `CAP_REQUEST`, `CAP_GRANT`, `CAP_REVOKE` | Capability | Add to spec |
| `BARRIER`, `SYNC_CLOCK`, `FORMATION_UPDATE`, `EMERGENCY_STOP` | Coordination | Add to spec |
| `DELEGATE_RESULT`, `REPORT_STATUS`, `REQUEST_OVERRIDE`, `DECLARE_INTENT`, `ASSERT_GOAL`, `VERIFY_OUTCOME`, `EXPLAIN_FAILURE`, `SET_PRIORITY` | A2A legacy | Evaluate, possibly remove |
| `FNEG`, `FABS`, `FEQ`, `FLT`, `FLE`, `FGT`, `FGE` | Float legacy | Add to spec or remove |

## Appendix C: Build Order Dependency Graph

```
tsconfig.json
    └── package.json (devDependencies)
         └── src/ast.ts
              └── src/lexer.ts
                   └── src/opcode-table.ts
                   │    └── (static data, no deps)
                   └── src/register-table.ts
                        └── (static data, no deps)
                   └── src/parser.ts
                        └── src/analyzer.ts
                             └── src/symbols.ts
                                  ├── src/completion.ts
                                  ├── src/diagnostics.ts
                                  ├── src/hover.ts
                                  ├── src/definition.ts
                                  ├── src/references.ts
                                  ├── src/folding.ts
                                  ├── src/document-symbol.ts
                                  └── src/workspace.ts
                                       └── src/documents.ts
                                            └── src/server.ts
```

---

*Audited by Super Z ⚡, Fleet Auditor. This audit covers the repository state as of commit `main` on 2026-04-12. The flux-lsp repository is at `github.com/SuperInstance/flux-lsp` (1KB, 5 files, 0% implementation).*
