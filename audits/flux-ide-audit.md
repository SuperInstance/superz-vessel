# FLUX IDE Audit Report

**Auditor:** Super Z
**Date:** 2025-07-11
**Repo:** `/home/z/my-project/flux-ide`
**Commit:** Working tree (v0.1.0)

---

## Overall Grade: B-

**Status: Functional prototype with impressive UI, but the compiler and VM are shallow approximations, not real implementations.**

This is a well-crafted web IDE shell with a VS Code-quality aesthetic, a proper parser for the markdown source format, and a visually compelling compile/run pipeline. However, the compiler does not actually compile anything (it pattern-matches source lines and emits placeholder IR), and the VM is a simulator that prints status messages rather than executing real bytecode. The IDE is real; the language tooling is scaffolding.

---

## Executive Summary

| Area | Grade | Status |
|------|-------|--------|
| IDE UI/UX | **A** | Production-quality VS Code clone |
| Parser (`flux-parser.ts`) | **B+** | Correctly parses .flux.md structure; missing grammar depth |
| Compiler (`flux-compiler.ts`) | **D+** | Pattern-matching stub, not a real compiler |
| VM Simulator (`vm-simulator.ts`) | **C** | Executes the compiler's output but is trivially simple |
| ISA Conformance | **F** | Custom 36-opcode ISA; no unified-ISA alignment |
| Templates | **A-** | 33 templates across 4 categories, well-written |
| Tech Stack | **A** | Modern (Next.js 16, React 19, Tailwind 4, Monaco) |
| State Management | **B** | localStorage persistence, auto-save, works correctly |
| Type Definitions | **A** | Comprehensive TypeScript types |

---

## Detailed Findings

### 1. Parser (`flux-parser.ts`) — 201 lines

**What it does:** Parses `.flux.md` files into structured objects:
- YAML frontmatter (title, version, description, author)
- Markdown headings classified by kind (`fn:`, `agent:`, `tile:`, `region:`, `import:`, `export:`, `section`)
- Code blocks with language tags
- `#!agent`/`#!tile`/`#!flux` directives
- Basic diagnostics (missing frontmatter, unclosed delimiter)

**Quality assessment:**
- Correctly extracts all FLUX structural elements
- Function heading parser handles `name(params) -> returnType` syntax
- Code block parser handles fenced blocks with language identifiers
- Directive parser is minimal but functional

**vs flux-lsp grammar spec:** The parser handles maybe 15% of what a 1163-line formal grammar would specify. Missing:
- No type checking or type resolution
- No expression parsing (it doesn't understand the code *inside* code blocks)
- No symbol table or scope analysis
- No error recovery
- No token-level lexing of FLUX-specific constructs (A2A ops, tile syntax, region syntax)
- The parser is structural/markdown-level only, not a language-level parser

**Verdict:** Adequate for its role as a structural extractor feeding the compiler, but it's a markdown parser, not a FLUX language parser.

### 2. Compiler (`flux-compiler.ts`) — 481 lines

**What it does:**
1. Takes parsed FLUX markdown and generates FIR (FLUX IR) — a module with functions, agents, regions, imports, exports
2. Generates "bytecode" from FIR — hex-dump style output with addresses and opcodes

**Critical finding: The compiler does NOT actually compile code.** The `analyzeCodeLine()` function (lines 183-271) uses regex pattern-matching on source lines to emit placeholder instructions:

```typescript
// Variable declarations → always emits MOVI R8, 0
if (lower.match(/^(int|float|double|char|void|long|short)\s+\w+\s*=/)) {
    return { opcode: 'MOVI', operands: ['R8', '0'], comment: `; ${line}` };
}

// Return statements → emits MOVI A0, value or MOV A0, R8
// Print statements → emits PRINTS R8 (but VM just prints "(string output)")
// For/while loops → emits MOVI R8, 0 (no actual loop)
// If statements → emits CMP R8, R9 (no branch logic)
// Function calls → emits CALL name (but with no argument passing)
// Assignments → emits MOV R8, R9 (always same registers)
```

**Problems:**
1. **No register allocation:** Every variable declaration maps to R8, R9. Multi-variable programs collide.
2. **No control flow:** Loops emit a single `MOVI`, no labels/jumps. `if` emits a `CMP` but no branch.
3. **No expression evaluation:** `int result = 42; return result;` produces `MOVI R8, 0; MOV A0, R8` — result is always 0.
4. **No data flow:** Values are never propagated between instructions.
5. **Code block association is broken:** The compiler assigns code blocks to headings via sequential indexing (`codeBlockIdx++`), so any non-code-block heading (like `# Fibonacci` or a plain section heading) throws off the mapping. A markdown paragraph between a function heading and its code block would break compilation.
6. **`return 42` produces `MOVI A0, 42`** but then the epilogue does `MOV A0, R0`, overwriting the return value with R0 (which is ZERO register = 0).

**Opcodes defined:** 36 opcodes across System, Arithmetic, Logic, Compare, Branch, Call, Memory, Stack, Agent/A2A, and I/O categories. This is a custom ISA — see ISA conformance below.

### 3. VM Simulator (`vm-simulator.ts`) — 481 lines

**What it does:**
- 64-register VM with named registers (ZERO, RA, SP, BP, PC, FLAGS, FP, R7-R15, A0-A15, AGENT0-AGENT15)
- Stack, memory (sparse), call stack
- Executes the bytecode output of the compiler

**What works:**
- `MOVI` correctly loads immediates into registers
- `MOV` correctly copies between registers (and handles register/immediate fallback)
- Arithmetic (`IADD`, `ISUB`, `IMUL`, `IDIV`, `IMOD`) works correctly with proper overflow/safety handling
- `CMP`/`CMPI` sets flags correctly
- `PUSH`/`POP` with SP tracking works
- `LOAD`/`STORE` to sparse memory works
- `PRINT` outputs register values
- Division by zero detection
- 10,000 cycle safety limit
- Agent opcodes (SPAWN, TELL, ASK, DELEGATE, BROADCAST, BARRIER) produce status messages

**What doesn't work:**
1. **JMP/JZ/JNZ are no-ops:** The jump instructions have empty bodies (`break`). The VM always executes instructions linearly from `mainStartIdx` to `mainEndIdx`.
2. **CALL is shallow:** It finds the target function and executes its body, but only handles `MOVI` instructions within the called function — ignores all other opcodes in sub-functions.
3. **No string support:** `PRINTS` always outputs `"[output] (string output)"` regardless of content.
4. **No actual return value propagation:** The epilogue `MOV A0, R0` copies from the ZERO register, so all functions effectively return 0.
5. **Agent registers are just booleans** (0 or 1), not actual agent handles.

**Net effect:** Running `hello.flux.md` (which has `int result = 42; return result;`) will output `[RET] Return value: 0` because the compiler emits `MOVI R8, 0` for the variable, and the epilogue copies from R0 (ZERO).

### 4. ISA Conformance

**The IDE defines its own custom 36-opcode ISA.** There is no alignment with:
- The unified-ISA mentioned in fleet context (247 opcodes per `flux-spec`)
- The flux-lsp grammar's expected bytecode format
- Any other FLUX runtime (flux-py, flux-rust, flux-os)

**Opcode mapping issues:**
- Uses simple sequential byte codes (0x00-0x92) with no encoding format specification
- No instruction format defined (fixed-width? variable-length? operand encoding?)
- Branch instructions have no target address encoding
- CALL uses a string name operand, not an address

**Verdict:** This is a standalone demo ISA with no pretense of interoperability.

### 5. IDE Features Assessment

| Feature | Implemented? | Quality |
|---------|-------------|---------|
| Monaco Editor | Yes (dynamic import + textarea fallback) | Good |
| FLUX Syntax Highlighting | No — uses `language="markdown"` | None |
| Autocompletion | No (quickSuggestions disabled) | None |
| Error Diagnostics | Partial (frontmatter warnings only) | Minimal |
| File Explorer | Yes (rename, duplicate, delete, context menu) | Good |
| Multi-tab Editing | Yes (dirty indicators, close, switch) | Good |
| Project Persistence | Yes (localStorage, auto-save) | Good |
| Compile (Ctrl+Shift+B) | Yes (shows FIR + bytecode) | Visual only |
| Run (Ctrl+Enter) | Yes (shows VM state + output) | Shallow |
| Templates | Yes (33 templates, search, category filter) | Excellent |
| Import/Export | Partial (export works as .txt, import file picker has no handler) | Broken |
| Keyboard Shortcuts | Yes (Ctrl+S, Ctrl+Enter, Ctrl+Shift+B) | Good |
| Status Bar | Yes (file name, cursor position, dirty flag) | Good |
| Agent Visualization | Partial (list view in right panel) | Minimal |
| Terminal | Present but non-functional (append-only log) | Stub |
| Breadcrumb | Yes (shows function/agent count from parsed file) | Good |
| Right Panel (FIR/Bytecode/VM/Agents) | Yes with toggle | Good |

### 6. Import/Export Bug

The import feature has a file input element that accepts `.flux.md` files, but the `handleImport` callback is empty:
```typescript
const handleImport = useCallback(() => {
    // Triggered by file input — handled in Toolbar
}, []);
```
The file input's `onChange` calls `onImport()` which does nothing. Files selected via the import button are silently dropped.

### 7. Tech Stack

| Component | Version | Assessment |
|-----------|---------|------------|
| Next.js | 16.2.3 | Latest, using App Router correctly |
| React | 19.2.4 | Latest |
| TypeScript | ^5 | Modern |
| Tailwind CSS | ^4 | Modern with CSS variables theme |
| Monaco Editor | ^0.55.1 / ^4.7.0 | Latest |
| Lucide React | ^1.8.0 | Modern icon library |
| file-saver | ^2.0.5 | Listed as dep but unused in code |
| jszip | ^3.10.1 | Listed as dep but unused in code |

**Unused dependencies:** `file-saver` and `jszip` are declared but never imported anywhere in the codebase. The export feature uses raw `Blob` + `URL.createObjectURL` instead.

### 8. Code Quality

- **No tests** — Zero test files in the entire project
- **No ESLint warnings** visible in structure (config present)
- **Good TypeScript coverage** — Proper interfaces for all data structures
- **Single-file components** — All IDE UI in one 889-line file (could be split)
- **Good separation of concerns** — Parser, compiler, VM, store, types are separate modules
- **AGENTS.md is just `@CLAUDE.md`** — Minimal development context
- **CLAUDE.md warns about Next.js 16 breaking changes** — Good practice

### 9. Template Quality

33 templates across 4 categories:
- **Getting Started** (5): Hello World, Fibonacci, Variables & Types, Control Flow, Functions
- **Software Recreation** (14): HTTP Server, File Manager, JSON Parser, CSV Processor, Text Editor, Calculator, Todo List CLI, Regex Engine, Basic Database, Sort Algorithms, Web Scraper, Chat Bot, Logger System, Config Manager
- **Agent Systems** (6+): Multi-Agent Pipeline, A2A Handshake, Trust Network, Barrier Sync, Broadcast/Reduce, Hot-Swap A/B Testing
- **Novel Tools** (5+): Agent Orchestra, Memory Sandbox, Tile Compositor, Capability Manager, Gas Meter

Templates are well-written with proper frontmatter, clear structure, and realistic C/Python code. They serve as excellent documentation of FLUX's intended capabilities.

---

## What Works

1. **Beautiful, functional IDE UI** — Looks and feels like a real IDE
2. **Structural parsing** — Correctly extracts all FLUX markdown elements
3. **Compile button produces readable FIR and bytecode output** — Visually convincing
4. **Run button shows VM state** — Registers, flags, stack, memory display
5. **Template system** — 33 well-crafted templates with search and categories
6. **File management** — Create, rename, duplicate, delete, multi-tab
7. **Persistence** — Auto-saves to localStorage
8. **Keyboard shortcuts** — All documented shortcuts work
9. **Agent detection** — Correctly identifies and lists agents with methods

## What Doesn't Work

1. **Compiler produces incorrect IR** — No real code analysis, just pattern-matched placeholders
2. **VM returns wrong results** — `return 42` always returns 0 due to compiler + epilogue bug
3. **No control flow execution** — Loops and branches are no-ops in the VM
4. **No FLUX syntax highlighting** — Falls back to generic markdown
5. **Import is broken** — File picker does nothing
6. **No autocompletion** — Disabled for all trigger characters
7. **Terminal is non-interactive** — Just an append-only log
8. **No real ISA conformance** — Custom 36-opcode ISA unrelated to unified-ISA

---

## ISA Conformance Summary

| Aspect | Status |
|--------|--------|
| Unified-ISA alignment | None — completely custom |
| Opcode encoding | Undefined (no format spec) |
| Branch target encoding | Missing (JMP/JZ/JNZ are no-ops) |
| Function calling convention | Minimal (CALL by name, no stack frame) |
| Memory model | Sparse array, no real addressing |
| Agent register model | Boolean flags, not handles |
| Interop with other runtimes | None |

---

## Recommendations

### Priority 1 (Make the demo correct)

1. **Fix the return value bug:** The epilogue `MOV A0, R0` copies from the ZERO register. Change to preserve the last MOVI target. At minimum, track which register holds the "current return value" and copy that in the epilogue.
2. **Fix variable declarations:** Instead of always emitting `MOVI R8, 0`, extract the actual initial value from the source line (e.g., `int result = 42` → `MOVI R8, 42`).
3. **Fix import:** Wire up the file input to actually read `.flux.md` files and create project files from them.
4. **Remove unused deps:** Drop `file-saver` and `jszip` from package.json.

### Priority 2 (Make it real)

5. **Implement a simple register allocator:** Assign sequential registers to variables (R8, R9, R10...) instead of always using R8/R9.
6. **Implement basic expression evaluation:** Parse `a + b`, `a * b`, etc. in return/assignment statements and emit proper arithmetic instructions.
7. **Implement jump targets:** Generate labels for loop headers/branch targets and implement real JMP/JZ/JNZ in the VM.
8. **Add FLUX syntax highlighting:** Create a Monaco language definition for `.flux.md` that highlights `## fn:`, `## agent:`, A2A ops, etc.

### Priority 3 (ISA alignment)

9. **Align with unified-ISA:** Adopt the 247-opcode unified ISA from flux-spec, or at minimum document the divergence.
10. **Define an instruction encoding format:** How are operands encoded? Fixed-width 32-bit? Variable?
11. **Add conformance tests:** Verify bytecode output matches expected format.

### Priority 4 (IDE polish)

12. **Add tests:** At minimum, unit tests for parser, compiler, and VM.
13. **Enable autocompletion:** Provide completions for FLUX directives (`fn:`, `agent:`, `tile:`, A2A ops).
14. **Interactive terminal:** Allow basic commands like `help`, `run`, `compile`, `clear`.
15. **Split IDEComponents.tsx** into separate files for maintainability.

---

## Line Counts

| File | Lines | Purpose |
|------|-------|---------|
| `IDEComponents.tsx` | 889 | All UI components |
| `templates.ts` | ~2500 | 33 templates |
| `vm-simulator.ts` | 481 | VM execution engine |
| `flux-compiler.ts` | 481 | Parser → FIR → Bytecode |
| `page.tsx` | 413 | Main IDE page logic |
| `project-store.ts` | 214 | State management |
| `globals.css` | 191 | VS Code dark theme |
| `flux-parser.ts` | 201 | Markdown parser |
| `flux.ts` | 194 | Type definitions |
| **Total (excl templates)** | ~3,064 | |
| **Total (incl templates)** | ~5,564 | |

---

## Conclusion

flux-ide is an impressive UI prototype that successfully demonstrates what a FLUX development environment *would look like*. The IDE shell is production-quality — the file explorer, tab system, template browser, and panel layout are all well-executed. However, the language tooling (compiler + VM) is fundamentally a visual demo, not a working implementation. The compiler pattern-matches source lines and emits placeholder IR, and the VM can't execute real programs correctly.

**To become a real IDE**, the project needs a proper compiler that actually analyzes expressions, allocates registers, and generates correct control flow. The current approach of regex-matching C/Python source lines is inherently limited.

**Auditor's note:** Given the fleet context mentions flux-lsp (T-006) and flux-conformance (T-011) as separate work items, it's likely this IDE was intended as a UI shell from the start, with the expectation that real language tooling would be built separately. In that context, the grade should be **B** for the UI and **D** for the tooling.
