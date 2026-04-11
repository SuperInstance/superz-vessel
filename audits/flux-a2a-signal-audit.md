# FLUX-A2A Signal Protocol — Fleet Audit Report

**Date**: 2025-07-11  
**Auditor**: automated fleet audit  
**Version**: 0.1.0 | **Tests**: 879 collected, 840 passed, 39 skipped, 1 warning  
**Test runtime**: ~2.1s  

---

## Architecture Overview

Signal is the inter-agent communication layer for the FLUX multilingual ecosystem. It treats JSON as the universal AST — no parse step needed. The architecture has five layers:

1. **Schema Layer** (`schema.py`): Dataclass definitions for all protocol types — `Expression`, `Program`, `Agent`, `Message`, `Result`, `ConfidenceScore`, merge/branch/co-iteration configs. All types have `to_dict()`/`from_dict()` serialization.

2. **Interpreter** (`interpreter.py`): Tree-walking evaluator dispatching ~35 opcodes across arithmetic, logic, string/collection, control flow, agent communication (tell/ask/delegate/broadcast), and agent operations (branch/fork/merge/co_iterate). Confidence propagation is woven through every evaluation path.

3. **Agent Operations** (`fork_manager.py`, `co_iteration.py`): `BranchManager` handles parallel branch execution with 7 merge strategies. `CoIterationEngine` orchestrates multi-agent shared program traversal with cursor-based conflict detection and resolution.

4. **Advanced Protocols** (`consensus.py`, `discussion.py`, `pipeline.py`): `ConsensusDetector` measures agent agreement via cosine similarity in multi-dimensional opinion space. `DiscussionProtocol` supports debate/brainstorm/review/negotiation formats. `AgentWorkflowPipeline` orchestrates branch→discuss→synthesize workflows.

5. **Type System & Cross-Language Layer** (`types.py`, `type_safe_bridge.py`, `cross_compiler.py`, `optimizer.py`, `partial_eval.py`, `evolution.py`): FUTS (Flux Universal Type System) maps 6 natural language paradigms (ZHO/DEU/KOR/SAN/WEN/LAT) to 8 universal base types via `FluxBaseType`. Includes quantum superposition types, bridge cost matrices, and cross-language optimization.

---

## Test Quality Assessment

**Strengths**: Tests are well-organized by class (`TestArithmetic`, `TestBranching`, `TestConsensusModel`, etc.). Core interpreter tests cover all opcode categories. Schema tests validate serialization round-trips. Discussion/pipeline tests exercise multi-agent workflows end-to-end. Vector similarity and consensus detection have good mathematical precision tests (`pytest.approx`).

**Weaknesses**:
- **39 skipped tests** (4.4%), concentrated in language-bridge modules (`test_kor_san_bridge`, `test_wen_lat_bridge`, `test_zho_deu_bridge`). These represent genuine coverage gaps.
- **Limited error/edge-case testing**: Few tests probe deeply nested expressions, concurrent modification, or malformed input robustness.
- **No coverage configuration**: No `pytest-cov` thresholds or CI badge setup. Actual line coverage is unknown.
- **Deprecated API usage**: `test_discussion.py` uses `asyncio.get_event_loop()` instead of `asyncio.run()`.
- **No property-based or fuzz testing** despite the system accepting arbitrary JSON input.

---

## Bugs & Issues Found

1. **`BranchDef.from_dict()` mutates input** (schema.py:237): Uses `data.pop("body", [])` which destroys the caller's dict. Should copy instead.

2. **`_scope_confidence` never resets** (interpreter.py:119): Once an expression lowers scope confidence, it stays lowered permanently. The interpreter should save/restore scope confidence around branch bodies and sub-expressions.

3. **Enum duplication**: `ConflictResolutionStrategy` and `MergeStrategy` are defined identically in both `schema.py` and `co_iteration.py`. Same for `MergePolicyType` in `schema.py` and `MergePolicyTypeExt` in `fork_manager.py`. This creates import confusion and drift risk.

4. **`BytecodeChunk.emit()` lang_tags bug** (compiler.py:121–122): Only appends a lang_tag for the first instruction. Subsequent instructions within the same compilation silently lose their language tags.

5. **`ask` opcode immediately queries for responses** (interpreter.py:590): `find_by_reply(msg.id)` checks the message bus for replies to a message that was just sent — there can be no response yet. This makes `ask` always return `pending` in the single-threaded interpreter.

6. **No thread safety**: `Interpreter.state`, `BranchManager._branches`, and `ForkManager._forks` use plain dicts. The "parallel" branch execution is simulated sequentially with no guards for real concurrency.

---

## Code Quality Grade: B+

**Positive**:
- Clean, consistent Python with modern type hints and `slots=True` dataclasses
- Thorough docstrings and architectural documentation
- Consistent `to_dict()`/`from_dict()` serialization across all types
- `__all__` exports are comprehensive in `__init__.py`
- Test suite passes in 2 seconds — fast feedback loop

**Negative**:
- No linting/formatting config (`pyproject.toml` lacks ruff, mypy, or black)
- No CI/CD configuration
- No `py.typed` marker for downstream type checking
- Several modules exceed 1000 LOC (`optimizer.py`, `types.py`, `protocol.py`, `consensus.py`)
- Enum duplication across modules (3 duplicate enum pairs)
- The `ask` and `await` opcodes are effectively no-ops in single-threaded mode but have complex signatures suggesting otherwise

---

## Recommendations (Priority Order)

1. **Fix `BranchDef.from_dict` mutation bug** — replace `data.pop()` with `{**data}.get()`.

2. **Add scope confidence save/restore** around branch evaluation in the interpreter to prevent confidence leak across unrelated expressions.

3. **Consolidate duplicate enums** — import from `schema.py` in `co_iteration.py` and `fork_manager.py` rather than redefining.

4. **Add linting and type checking** — add `ruff`, `mypy --strict`, and `black` to `pyproject.toml`.

5. **Add test coverage reporting** — integrate `pytest-cov` with a minimum threshold (suggest 80%).

6. **Fix the 39 skipped bridge tests** — these cover cross-paradigm type bridging which is a core differentiator.

7. **Make `ask` actually work** — either implement request-response in the interpreter or document that it's a placeholder.

8. **Add a `py.typed` marker** and consider adding `__init__.py` to the tests directory for proper test discovery.

---

*This repo is architecturally sound for a v0.1 — the type system, consensus detection, and multi-language bridge concepts are well-designed. The code quality issues are fixable in a single cleanup pass. The main risk is that the enum duplication and confidence leak bugs could cause subtle, hard-to-debug issues as the codebase scales.*
