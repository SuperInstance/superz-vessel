# Flux-Runtime Tools Audit Report

**Date:** 2026-04-12
**Auditor:** Super Z (Fleet Auditor)
**Scope:** 7 Python tool files under `tools/`
**Protocol:** SUPERZ-AUDIT-2026-04-12

---

## Executive Summary

| Category | Count |
|----------|-------|
| **Critical Issues** | 1 |
| **Security Issues** | 2 |
| **Warnings** | 7 |
| **Suggestions** | 6 |
| **Files Audited** | 7 |
| **Syntax (ast.parse)** | 7/7 PASS |

**Overall Verdict:** PASS with required fixes. One critical f-string bug will cause
garbage output. Two security items need attention before fleet-wide deployment.

---

## Critical Issues

### C-01: Missing f-string prefix causes literal `{total_lines}` in output

**File:** `tools/git-archaeology/craftsman_reader.py`, line 565
**Severity:** Critical — produces misleading anti-mark reason text

```python
record.anti_mark_reasons.append(
    "'fix typo' but changes {total_lines} lines — possibly misleading"
)
```

The string is **not** an f-string. The `{total_lines}` token is emitted literally
as text instead of being interpolated. Every "fix typo" anti-mark will display
`"'fix typo' but changes {total_lines} lines — possibly misleading"` instead of
the actual number.

**Fix:** Add `f` prefix:
```python
record.anti_mark_reasons.append(
    f"'fix typo' but changes {total_lines} lines — possibly misleading"
)
```

---

## Security Issues

### S-01: Bare `except` clause swallows errors in auto_respond.py

**File:** `tools/bottle-hygiene/auto_respond.py`, lines 585-586

```python
except Exception:
    pass  # Tracker update is best-effort
```

This bare `except Exception: pass` swallows ALL errors during SQLite tracker
updates, including `sqlite3.OperationalError`, `sqlite3.DatabaseError`,
`MemoryError`, etc. If the database is corrupted or the schema has changed,
the error is silently lost. At minimum, log the error.

**Fix:**
```python
except Exception as e:
    print(f"[WARN] Tracker update failed: {e}", file=sys.stderr)
```

### S-02: SQL query construction via f-string with user-controlled filters

**File:** `tools/bottle-hygiene/bottle_tracker.py`, lines 509-528 and 759-773

```python
where = " AND ".join(clauses) if clauses else "1=1"
rows = self._conn.execute(
    f"SELECT * FROM bottles WHERE {where} ORDER BY ..."
    f"... LIMIT ? OFFSET ?",
    (*params, limit, offset),
).fetchall()
```

While the actual values are passed as parameterized `?` placeholders (which is
correct and prevents SQL injection), the f-string interpolation of `WHERE` clauses
is a pattern that invites future mistakes. Currently safe because `clauses` are
hard-coded string fragments, not user input. However, if `vessel_name` or
`status` filters ever come from untrusted sources, this pattern would need
hardening. Marking as informational — no immediate exploit, but fragile pattern.

**Risk:** Low. Parameterized values prevent injection. Clause fragments are
hard-coded.

---

## Warnings

### W-01: `_calculate_vessel_metrics` ack-rate uses wrong variable

**File:** `tools/bottle-hygiene/hygiene_checker.py`, line 705

```python
def _calculate_vessel_metrics(self, summary: VesselHygieneSummary) -> None:
    total_incoming = summary.bottles_received
    total_outgoing = summary.bottles_orphan  # BUG: should be bottles_sent
```

`total_outgoing` is assigned from `summary.bottles_orphan` instead of
`summary.bottles_sent`. This makes the ack-rate denominator nonsensical
(incoming + orphan instead of incoming + sent). The ack rate will be
miscalculated when orphan count differs from sent count.

**Fix:** `total_outgoing = summary.bottles_sent`

### W-02: `rstrip` used incorrectly to remove parenthetical suffixes

**File:** `tools/bottle-hygiene/hygiene_checker.py`, lines 565-567

```python
value = value.rstrip("(Managing Director)").strip()
value = value.rstrip("(Vessel)").strip()
value = value.rstrip("(Lighthouse, SuperInstance)").strip()
```

`str.rstrip()` treats its argument as a **set of characters** to strip, not as
a substring. While this happens to work for typical agent names (because a space
precedes the parenthetical, and the space isn't in the character set), it would
corrupt names like `"AgentVessel (Vessel)"` → `"AgentV"` by stripping `essel`
from the agent name too.

**Fix:** Use `re.sub(r'\s*\(Vessel\)\s*$', '', value)` instead.

### W-03: Relative imports between fleet-context-inference files

**Files:**
- `tools/fleet-context-inference/capability_parser.py`, line 33:
  `from infer_context import ExpertiseProfile, DomainScore, ActivityLevel`
- `tools/fleet-context-inference/fleet_matcher.py`, line 28:
  `from capability_parser import ProfileMerger, ParsedCapability, ActivityLevel`

These use bare module imports that only work when the script is run from within
the `fleet-context-inference/` directory or when the directory is on `sys.path`.
They will fail with `ModuleNotFoundError` if invoked from a different working
directory or installed as a package.

**Fix:** Either add `__init__.py` with re-exports and use package imports, or add
`sys.path.insert(0, os.path.dirname(__file__))` at the top of each script.

### W-04: `git_is_ancestor` lacks `timeout` in subprocess.call

**File:** `tools/git-archaeology/craftsman_reader.py`, lines 278-283

```python
result = subprocess.run(
    ["git", "-C", repo_path, "merge-base", "--is-ancestor", ancestor, descendant],
    capture_output=True, text=True, timeout=30,
)
```

Actually, this one **does** have a timeout. Withdrawing this warning.

### W-05: Unused constants in craftsman_reader.py

**File:** `tools/git-archaeology/craftsman_reader.py`

| Line | Constant | Used? |
|------|----------|-------|
| 55 | `BODY_THRESHOLD` | No (superseded by `WITNESS_MARK_BODY_THRESHOLD`) |
| 77 | `SECTION_DIVIDER` | No |
| 73 | `HOT_SPOT_THRESHOLD_FILES` | No |
| 74 | `ATTENTION_DENSITY_WINDOW` | No |

Dead code. Could be removed or used to filter hot_spots output.

### W-06: Unused imports in craftsman_reader.py

**File:** `tools/git-archaeology/craftsman_reader.py`

| Import | Used? |
|--------|-------|
| `pathlib.Path` (line 36) | No — only `os.path` is used |
| `typing.Any` (line 37) | No |

### W-07: Unused import `time` in hygiene_checker.py

**File:** `tools/bottle-hygiene/hygiene_checker.py`, line 36

`import time` is present but `time` is never referenced in the file.

### W-08: Unused imports `Tuple` in craftsman_reader.py

**File:** `tools/git-archaeology/craftsman_reader.py`, line 37

`Tuple` is imported from typing but the `date_range` field on `RepoAnalysis`
uses the `tuple` builtin annotation syntax `Tuple[datetime.datetime, datetime.datetime]`.
Under `from __future__ import annotations`, this works fine, but `Tuple` from
typing is redundant.

---

## Suggestions

### S-01: Add `__init__.py` to tool subdirectories

Each tool directory (`fleet-context-inference/`, `bottle-hygiene/`,
`git-archaeology/`) should have an `__init__.py` to enable package imports
and proper Python packaging. Without this, relative imports and package
installation won't work.

### S-02: The `_extract_headers` title extraction logic exits too early

**File:** `tools/bottle-hygiene/hygiene_checker.py`, lines 519-526

```python
for line in lines:
    stripped = line.strip()
    if stripped.startswith("# ") and not bottle.title:
        bottle.title = stripped[2:].strip()
    elif stripped.startswith("## ") and not bottle.title:
        bottle.title = stripped[3:].strip()
    else:
        break  # Stops after first non-heading line
```

The `else: break` exits after the very first non-heading line. If there's a
blank line between `# Title` and `## Subtitle`, the loop breaks before
checking `## Subtitle`. In practice, most bottles have the title on the first
line, so this is unlikely to trigger, but it's fragile.

### S-03: `infer_context.py` `_parse_numstat_line` rename detection is approximate

**File:** `tools/fleet-context-inference/infer_context.py`, line 646

```python
is_new = filepath.endswith("}")  # approximate detection
```

This marks files ending with `}` as new files. Git's numstat format for renames
uses `{old => new}` syntax, so `}` appears at the end, but this heuristic would
also match files that legitimately end with `}` in their name.

### S-04: `bottle_tracker.py` `_resolve_bottle_id` uses ambiguous fallback

**File:** `tools/bottle-hygiene/bottle_tracker.py`, lines 416-421

```python
filename = os.path.basename(path)
row = self._conn.execute(
    "SELECT bottle_id FROM bottles WHERE filename = ? LIMIT 1",
    (filename,),
).fetchone()
```

If multiple vessels have a bottle with the same filename (e.g., `DIRECTIVE.md`),
this returns the first match, which may not be the correct one. Consider adding
a `vessel_name` filter to the fallback query.

### S-05: `fleet_matcher.py` scoring weights are not validated at runtime

**File:** `tools/fleet-context-inference/fleet_matcher.py`, lines 461-466

The constructor prints a warning if weights don't sum to 1.0 but doesn't
normalize them. If custom weights are provided that sum to 1.5 or 0.3, the
overall score could exceed 1.0 or be unexpectedly low. Consider normalizing.

### S-06: Consider adding `__all__` exports to each module

None of the 7 files define `__all__`, which means `from module import *`
would export everything including private helpers and CLI functions.
Defining `__all__` would clarify the public API.

---

## Per-File Review

### 1. `tools/git-archaeology/craftsman_reader.py` (1,951 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | PASS (all stdlib) |
| Security | PASS — git commands use list args (no shell injection); subprocess has timeouts |
| Error handling | PASS — GitCommandError properly raised; numstat errors gracefully handled |
| Hardcoded paths | None |
| Logic bugs | **C-01** (missing f-string) |
| Unused code | W-05 (4 constants), W-06 (2 imports) |

**Summary:** Well-structured file with good separation of concerns.
The one critical bug (C-01) is a simple missing `f` prefix.
Git command execution is properly sandboxed with list arguments and timeouts.

### 2. `tools/fleet-context-inference/infer_context.py` (1,020 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | PASS (all stdlib) |
| Security | PASS — git commands use list args; subprocess has timeout |
| Error handling | PASS — TimeoutExpired and CalledProcessError caught; validation done |
| Hardcoded paths | None |
| Logic bugs | None found |
| Unused code | None significant |

**Summary:** Clean implementation of the Context Inferrer protocol.
The `GitScanner` class properly handles errors and timeouts.
The `parse_numstat_line` rename detection is approximate (S-03) but acceptable.

### 3. `tools/fleet-context-inference/capability_parser.py` (864 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | W-03 — `from infer_context import ...` requires CWD to be the directory |
| Security | PASS — TOML parsing is safe |
| Error handling | PASS — validation issues collected, not thrown |
| Hardcoded paths | None |
| Logic bugs | None found |
| Unused code | None |

**Summary:** Solid TOML parser with comprehensive validation.
The `ProfileMerger` weighted merge algorithm is well-documented.
The relative import issue (W-03) needs resolution for proper packaging.

### 4. `tools/fleet-context-inference/fleet_matcher.py` (872 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | W-03 — `from capability_parser import ...` requires CWD to be the directory |
| Security | PASS |
| Error handling | PASS |
| Hardcoded paths | None |
| Logic bugs | None found |
| Unused code | None |

**Summary:** Well-implemented scoring engine with clear algorithm documentation.
The `HistoricalSuccessTracker` with neutral priors is a good design choice.
The `TaskDescription.from_string()` parser handles free-text input robustly.

### 5. `tools/bottle-hygiene/hygiene_checker.py` (1,219 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | PASS (all stdlib) |
| Security | PASS — only reads files, no writes except report output |
| Error handling | PASS — IOError/OSError caught on file reads |
| Hardcoded paths | None |
| Logic bugs | **W-01** (wrong variable in ack-rate calc), **W-02** (rstrip misuse) |
| Unused code | W-07 (`import time`) |

**Summary:** Comprehensive hygiene checking with good 4-phase architecture.
The cross-reference algorithm (`_bottle_references`) is thorough with 4 methods.
The `_calculate_vessel_metrics` bug (W-01) will cause incorrect ack-rate reporting.

### 6. `tools/bottle-hygiene/bottle_tracker.py` (1,012 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | PASS (all stdlib) |
| Security | S-02 (f-string SQL clause construction — safe but fragile pattern) |
| Error handling | PASS — SQLite errors handled; `__enter__`/`__exit__` for cleanup |
| Hardcoded paths | None |
| Logic bugs | None found |
| Unused code | None |

**Summary:** Clean SQLite-backed persistence layer. Schema design is good
with proper indexes and foreign keys. The status upgrade hierarchy
(`_upgrade_status`) is well-designed to prevent accidental status downgrades.
The `_resolve_bottle_id` ambiguous fallback (S-04) is a minor concern.

### 7. `tools/bottle-hygiene/auto_respond.py` (777 lines)

| Check | Result |
|-------|--------|
| Syntax | PASS |
| Imports | PASS (all stdlib) |
| Security | **S-01** (bare `except Exception: pass`) |
| Error handling | PASS except S-01 |
| Hardcoded paths | None |
| Logic bugs | None found |
| Unused code | None |

**Summary:** Good template-based response system. The `_is_already_acknowledged`
check is thorough. The `suggest_response_type` heuristic provides reasonable
defaults. The bare except (S-01) is the only real issue.

---

## Conformance Status

**Test:** Load FLUX bytecode VM interpreter and verify basic functionality.

```python
import sys
sys.path.insert(0, 'src')
from flux.vm.interpreter import Interpreter
```

**Result:** PASS (with caveat)

| Check | Result |
|-------|--------|
| Module import | PASS — `flux.vm.interpreter.Interpreter` loads successfully |
| Interpreter construction | PASS — `Interpreter(bytecode=b'\x00')` creates instance |
| Register access | NOTE — Public API uses `vm.regs` (RegisterFile), not `vm.registers` |
| Execution method | NOTE — Public API is `vm.execute()`, not `vm.run()` |
| Available methods | `execute`, `dump_state`, `reset`, `on_a2a`, `on_io_read`, `on_io_write` |

**API Note:** The conformance test in the audit spec used `vm.registers[0] = 10`
and `vm.run()`, which don't match the actual interpreter API (`vm.regs`,
`vm.execute()`). The interpreter module itself loads and instantiates correctly.
This is a documentation/test mismatch, not a runtime bug.

---

## Summary of Required Actions

| Priority | ID | Description | File | Effort |
|----------|----|-------------|------|--------|
| Critical | C-01 | Add `f` prefix to f-string on line 565 | craftsman_reader.py | 1 min |
| Security | S-01 | Replace bare `except: pass` with logged warning | auto_respond.py | 2 min |
| Warning | W-01 | Fix `bottles_orphan` → `bottles_sent` in ack-rate calc | hygiene_checker.py | 1 min |
| Warning | W-02 | Replace `rstrip` with `re.sub` for parenthetical removal | hygiene_checker.py | 5 min |
| Warning | W-03 | Add `sys.path` manipulation or `__init__.py` for cross-imports | 3 files | 10 min |
| Warning | W-05-W-08 | Remove unused constants/imports | 2 files | 5 min |

**Estimated total fix time:** ~25 minutes

---

*Audited by Super Z — Fleet Auditor*
*Protocol: SUPERZ-AUDIT-2026-04-12*
*"Trust the code. Audit the code. The code remembers everything."*
