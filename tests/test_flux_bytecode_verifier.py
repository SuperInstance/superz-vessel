"""
Comprehensive tests for flux-bytecode-verifier.py — FLUX ISA bytecode verifier.

Tests cover:
- instruction_format_and_size() — opcode→format dispatch
- opcode_name() — opcode→mnemonic lookup
- BytecodeVerifier.verify() — all verification checks:
  1. Format validity / truncation
  2. Register bounds (0-31)
  3. Control flow (jump targets, alignment)
  4. Stack depth (PUSH/POP balance)
  5. Frame balance (ENTER/LEAVE)
  6. HALT reachability
- Error and warning generation
- VerificationResult stats
- Output formatters (human-readable, JSON)
- Hex parsing utility
- Built-in test suite consistency
"""

import json
import os
import sys
import importlib.util
import pytest

TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")


def _load_module(filename, name=None):
    """Load a module from a file with a hyphenated name."""
    name = name or filename.replace("-", "_")
    path = os.path.join(TOOLS_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # Register before exec so dataclasses work
    spec.loader.exec_module(mod)
    return mod


fbv = _load_module("flux-bytecode-verifier.py", "flux_bytecode_verifier")
fbm = _load_module("flux-bytecode-migrator.py", "flux_bytecode_migrator")


# ── instruction_format_and_size() tests ────────────────────────

class TestInstructionFormat:
    def test_format_a_range(self):
        """Opcodes 0x00-0x07 should be Format A (1 byte)."""
        for op in range(0x00, 0x08):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "A"
            assert size == 1

    def test_format_b_range(self):
        """Opcodes 0x08-0x0F should be Format B (2 bytes)."""
        for op in range(0x08, 0x10):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "B"
            assert size == 2

    def test_format_c_range(self):
        """Opcodes 0x10-0x17 should be Format C (2 bytes)."""
        for op in range(0x10, 0x18):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "C"
            assert size == 2

    def test_format_d_range(self):
        """Opcodes 0x18-0x1F should be Format D (3 bytes)."""
        for op in range(0x18, 0x20):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "D"
            assert size == 3

    def test_format_e_range(self):
        """Opcodes 0x20-0x3F should be Format E (4 bytes)."""
        for op in range(0x20, 0x40):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "E"
            assert size == 4

    def test_format_f_range(self):
        """Opcodes 0x40-0x47 should be Format F (4 bytes)."""
        for op in range(0x40, 0x48):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "F"
            assert size == 4

    def test_format_g_range(self):
        """Opcodes 0x48-0x4F should be Format G (5 bytes)."""
        for op in range(0x48, 0x50):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "G"
            assert size == 5

    def test_len_opcode_special_case(self):
        """0xA0 (LEN) should be Format D (3 bytes)."""
        fmt, size = fbv.instruction_format_and_size(0xA0)
        assert fmt == "D"
        assert size == 3

    def test_slice_opcode_special_case(self):
        """0xA4 (SLICE) should be Format G (5 bytes)."""
        fmt, size = fbv.instruction_format_and_size(0xA4)
        assert fmt == "G"
        assert size == 5

    def test_system_opcode_format_a(self):
        """Opcodes 0xF0-0xFF should be Format A (1 byte)."""
        for op in range(0xF0, 0x100):
            fmt, size = fbv.instruction_format_and_size(op)
            assert fmt == "A"
            assert size == 1

    def test_halt_is_format_a(self):
        """HALT (0x00) should be Format A."""
        fmt, size = fbv.instruction_format_and_size(0x00)
        assert (fmt, size) == ("A", 1)

    def test_add_is_format_e(self):
        """ADD (0x20) should be Format E."""
        fmt, size = fbv.instruction_format_and_size(0x20)
        assert (fmt, size) == ("E", 4)


# ── opcode_name() tests ────────────────────────────────────────

class TestOpcodeName:
    def test_known_opcode(self):
        """Should return name for known opcodes."""
        assert fbv.opcode_name(0x00) == "HALT"
        assert fbv.opcode_name(0x01) == "NOP"
        assert fbv.opcode_name(0x20) == "ADD"

    def test_unknown_opcode(self):
        """Should return hex string for unknown opcodes."""
        name = fbv.opcode_name(0xFC)
        assert "0xFC" in name or name == "RSVD1"


# ── BytecodeVerifier — valid programs ──────────────────────────

class TestValidPrograms:
    def setup_method(self):
        self.verifier = fbv.BytecodeVerifier()

    def test_halt_only(self):
        """Single HALT instruction should pass."""
        result = self.verifier.verify(bytes([0x00]))
        assert result.passed
        assert len(result.errors) == 0

    def test_nop_halt(self):
        """NOP + HALT should pass."""
        result = self.verifier.verify(bytes([0x01, 0x00]))
        assert result.passed

    def test_empty_bytecode(self):
        """Empty bytecode should pass (vacuously)."""
        result = self.verifier.verify(b"")
        assert result.passed

    def test_valid_multi_instruction(self):
        """MOVI r1,5 + ADD r1,r2,r3 + HALT should pass."""
        prog = bytes([0x18, 0x01, 0x05,   # MOVI r1, 5 (Format D)
                      0x20, 0x01, 0x02, 0x03,  # ADD r1, r2, r3 (Format E)
                      0x00])  # HALT
        result = self.verifier.verify(prog)
        assert result.passed

    def test_push_pop_balanced(self):
        """Balanced PUSH/POP should not warn about stack imbalance."""
        prog = bytes([0x0C, 0x01,  # PUSH r1 (Format B)
                      0x0D, 0x01,  # POP r1 (Format B)
                      0x00])  # HALT
        result = self.verifier.verify(prog)
        # Should not have stack imbalance warning
        stack_warnings = [w for w in result.warnings if "imbalance" in w.message.lower()]
        assert len(stack_warnings) == 0

    def test_enter_leave_balanced(self):
        """Balanced ENTER/LEAVE should pass."""
        prog = bytes([0x4C, 0x01, 0x00, 0x00, 0x08,  # ENTER r1, r0, 8 (Format G)
                      0x4D, 0x01, 0x00, 0x00, 0x08,  # LEAVE r1, r0, 8 (Format G)
                      0x00])  # HALT
        result = self.verifier.verify(prog)
        assert result.passed

    def test_stats_populated(self):
        """Stats should be populated after verification."""
        result = self.verifier.verify(bytes([0x01, 0x00]))
        assert result.stats["bytecode_size"] == 2
        assert result.stats["instruction_count"] == 2
        assert result.stats["halt_reachable"] is True


# ── BytecodeVerifier — error detection ─────────────────────────

class TestErrorDetection:
    def setup_method(self):
        self.verifier = fbv.BytecodeVerifier()

    def test_truncated_instruction(self):
        """Truncated Format E instruction should error."""
        # ADD = 0x20 (Format E, needs 4 bytes) but only 3 provided + no HALT
        prog = bytes([0x20, 0x01, 0x02])
        result = self.verifier.verify(prog)
        assert not result.passed
        assert any(e.kind == "INSTRUCTION_TRUNCATED" for e in result.errors)

    def test_register_out_of_range(self):
        """Register > 31 should error."""
        # INC = 0x08 (Format B), rd=0x25=37
        prog = bytes([0x08, 0x25, 0x00])
        result = self.verifier.verify(prog)
        assert not result.passed
        assert any(e.kind == "REGISTER_OUT_OF_RANGE" for e in result.errors)

    def test_multiple_registers_out_of_range(self):
        """Multiple bad registers in one instruction."""
        # MUL = 0x22 (Format E), r32, r33, r34
        prog = bytes([0x22, 0x20, 0x21, 0x22, 0x00])
        result = self.verifier.verify(prog)
        reg_errors = [e for e in result.errors if e.kind == "REGISTER_OUT_OF_RANGE"]
        assert len(reg_errors) == 3

    def test_leave_without_enter(self):
        """LEAVE without ENTER should error."""
        # LEAVE = 0x4D (Format G, 5 bytes)
        prog = bytes([0x4D, 0x01, 0x00, 0x00, 0x00, 0x00])
        result = self.verifier.verify(prog)
        assert not result.passed
        assert any(e.kind == "STACK_IMBALANCE" for e in result.errors)

    def test_jump_misaligned_target(self):
        """Jump to middle of instruction should error."""
        # JMP = 0x43 (Format F), target = 0x0001 (inside JMP itself)
        prog = bytes([0x43, 0x00, 0x00, 0x01, 0x00])
        result = self.verifier.verify(prog)
        assert not result.passed
        assert any(e.kind == "JUMP_MISALIGNED" for e in result.errors)

    def test_frame_imbalance_at_end(self):
        """ENTER without matching LEAVE should error."""
        # ENTER = 0x4C (Format G, 5 bytes), then HALT
        prog = bytes([0x4C, 0x01, 0x00, 0x00, 0x08, 0x00])
        result = self.verifier.verify(prog)
        assert not result.passed
        assert any("Frame imbalance" in e.message for e in result.errors)


# ── BytecodeVerifier — warnings ────────────────────────────────

class TestWarningDetection:
    def setup_method(self):
        self.verifier = fbv.BytecodeVerifier()

    def test_no_halt_warning(self):
        """Program without HALT should warn."""
        prog = bytes([0x01, 0x01])  # NOP, NOP
        result = self.verifier.verify(prog)
        assert any(w.kind == "NO_HALT" for w in result.warnings)

    def test_code_after_halt_warning(self):
        """Code after HALT (at non-zero PC) should warn about unreachable code."""
        # NOP (PC=0, 1 byte) + HALT (PC=1, 1 byte) + NOP (PC=2)
        prog = bytes([0x01, 0x00, 0x01])
        result = self.verifier.verify(prog)
        assert any(w.kind == "UNREACHABLE_CODE" for w in result.warnings)

    def test_push_without_pop_warning(self):
        """PUSH without POP should warn about stack imbalance."""
        prog = bytes([0x0C, 0x01, 0x00])  # PUSH r1, HALT
        result = self.verifier.verify(prog)
        stack_warnings = [w for w in result.warnings if "PUSH" in w.message and "POP" in w.message]
        assert len(stack_warnings) >= 1

    def test_pop_empty_stack_warning(self):
        """POP on empty stack should warn."""
        prog = bytes([0x0D, 0x01, 0x00])  # POP r1, HALT
        result = self.verifier.verify(prog)
        assert any(w.kind == "STACK_UNDERFLOW_WARNING" for w in result.warnings)


# ── VerificationResult tests ───────────────────────────────────

class TestVerificationResult:
    def test_initial_state_passes(self):
        """Fresh VerificationResult should pass."""
        result = fbv.VerificationResult()
        assert result.passed is True
        assert len(result.errors) == 0

    def test_add_error_sets_passed_false(self):
        """Adding an error should set passed to False."""
        result = fbv.VerificationResult()
        result.add_error(fbv.ErrorKind.UNKNOWN_OPCODE, 0, "test error")
        assert result.passed is False
        assert len(result.errors) == 1

    def test_add_warning_keeps_passed_true(self):
        """Adding a warning should not change passed."""
        result = fbv.VerificationResult()
        result.add_warning(fbv.WarningKind.NO_HALT, 0, "test warning")
        assert result.passed is True
        assert len(result.warnings) == 1

    def test_error_has_correct_fields(self):
        """VerifierMessage should have all fields."""
        result = fbv.VerificationResult()
        result.add_error(fbv.ErrorKind.REGISTER_OUT_OF_RANGE, 42, "bad reg", 0x08)
        err = result.errors[0]
        assert err.kind == "REGISTER_OUT_OF_RANGE"
        assert err.pc == 42
        assert err.message == "bad reg"
        assert err.opcode == 0x08


# ── Output formatters tests ────────────────────────────────────

class TestFormatters:
    def test_format_human_shows_verdict(self):
        """Human output should show pass/fail verdict."""
        result = fbv.VerificationResult()
        result.stats = {"bytecode_size": 1, "instruction_count": 1}
        text = fbv.format_result_human(result)
        assert "PASSED" in text

    def test_format_human_shows_errors(self):
        """Human output should list errors."""
        result = fbv.VerificationResult()
        result.add_error(fbv.ErrorKind.UNKNOWN_OPCODE, 0, "bad opcode", 0xFF)
        result.stats = {"bytecode_size": 0, "instruction_count": 0}
        text = fbv.format_result_human(result)
        assert "FAILED" in text
        assert "bad opcode" in text

    def test_format_json_is_valid_json(self):
        """JSON output should be valid JSON."""
        result = fbv.VerificationResult()
        result.stats = {"bytecode_size": 10, "instruction_count": 5}
        text = fbv.format_result_json(result)
        parsed = json.loads(text)
        assert parsed["passed"] is True
        assert parsed["stats"]["bytecode_size"] == 10

    def test_format_json_includes_errors(self):
        """JSON output should include error details."""
        result = fbv.VerificationResult()
        result.add_error(fbv.ErrorKind.REGISTER_OUT_OF_RANGE, 5, "r32 out of range", 0x22)
        result.stats = {}
        text = fbv.format_result_json(result)
        parsed = json.loads(text)
        assert len(parsed["errors"]) == 1
        assert parsed["errors"][0]["kind"] == "REGISTER_OUT_OF_RANGE"
        assert parsed["errors"][0]["pc"] == 5


# ── Hex parsing tests ──────────────────────────────────────────

class TestHexParsing:
    def test_simple_hex(self):
        """Should parse simple hex string."""
        assert fbv.parse_hex_input("00ff") == bytes([0x00, 0xFF])

    def test_hex_with_spaces(self):
        """Should parse hex with spaces."""
        assert fbv.parse_hex_input("00 ff") == bytes([0x00, 0xFF])

    def test_hex_with_commas(self):
        """Should parse hex with commas."""
        assert fbv.parse_hex_input("00,ff") == bytes([0x00, 0xFF])

    def test_hex_with_0x_prefix(self):
        """Should parse hex with 0x prefix."""
        assert fbv.parse_hex_input("0x00ff") == bytes([0x00, 0xFF])

    def test_hex_odd_length_raises(self):
        """Odd-length hex should raise ValueError."""
        with pytest.raises(ValueError, match="odd length"):
            fbv.parse_hex_input("0ff")

    def test_hex_uppercase(self):
        """Should handle uppercase hex."""
        assert fbv.parse_hex_input("00FF") == bytes([0x00, 0xFF])


# ── Built-in test suite tests ──────────────────────────────────

class TestBuiltInSuite:
    def test_run_tests_returns_true(self):
        """Built-in test suite should pass."""
        assert fbv.run_tests() is True


# ── Migrator tests (flux-bytecode-migrator.py) ─────────────────

class TestMigrator:
    def test_validate_empty_bytecode(self):
        """Empty bytecode should be 'unknown' system."""
        fbm
        result = fbm.validate_bytecode(b"")
        assert result["system"] == "unknown"

    def test_validate_runtime_halt(self):
        """Bytecode ending with 0x80 (runtime HALT) should detect runtime."""
        fbm
        prog = bytes([0x00, 0x01, 0x80])
        result = fbm.validate_bytecode(prog)
        assert result["system"] in ("runtime", "ambiguous")

    def test_validate_unified_halt(self):
        """Bytecode ending with 0x00 (unified HALT) should detect unified."""
        fbm
        prog = bytes([0x01, 0x01, 0x00])
        result = fbm.validate_bytecode(prog)
        assert result["system"] in ("unified", "ambiguous")

    def test_migrate_preserves_halt(self):
        """Migration should translate HALT correctly."""
        fbm
        # Runtime HALT = 0x80, should become Unified HALT = 0x00
        prog = bytes([0x80])
        result = fbm.migrate_runtime_to_unified(prog)
        assert result.output[0] == fbm.UnifiedOp.HALT

    def test_migrate_handles_unknown_opcode(self):
        """Migration should warn on unknown opcodes."""
        fbm
        # Use a byte that's not a valid RuntimeOp
        prog = bytes([0xFE, 0x80])
        result = fbm.migrate_runtime_to_unified(prog)
        assert result.failed >= 1

    def test_migrate_nop(self):
        """NOP should translate correctly."""
        fbm
        prog = bytes([fbm.RuntimeOp.NOP])
        result = fbm.migrate_runtime_to_unified(prog)
        assert result.translated == 1
        assert result.output[0] == fbm.UnifiedOp.NOP

    def test_get_fmt_a(self):
        """Format A for known format-A opcodes."""
        fbm
        assert fbm.get_fmt(fbm.RuntimeOp.NOP) == "A"
        assert fbm.get_fmt(fbm.RuntimeOp.HALT) == "A"

    def test_get_fmt_b(self):
        """Format B for known format-B opcodes."""
        fbm
        assert fbv and fbm.get_fmt(fbm.RuntimeOp.INC) == "B"
        assert fbm.get_fmt(fbm.RuntimeOp.PUSH) == "B"

    def test_semantic_map_covers_basic_ops(self):
        """Semantic map should cover basic arithmetic ops."""
        fbm
        assert "IADD" in fbm.SEMANTIC_MAP
        assert "ISUB" in fbm.SEMANTIC_MAP
        assert fbm.SEMANTIC_MAP["IADD"] == "ADD"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
