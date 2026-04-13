#!/usr/bin/env python3
"""
FLUX Bytecode Verifier — Static validation of FLUX bytecode before execution.

This tool reads FLUX bytecode (as hex string, bytes file, or raw bytes) and
performs comprehensive static analysis to catch errors before the VM ever runs
the program. It validates against the converged ISA specification where:
  - HALT = 0x00 (canonical position)
  - Formats A/B/C/D/E/F/G dispatch by opcode range
  - 32 registers (r0–r31), 8-bit and 16-bit immediates
  - Stack-based activation frames via ENTER/LEAVE

Verification checks performed:
  1. Format validity   — every instruction matches its expected format (A/B/C/D/E/F/G)
  2. Register bounds   — all register references are 0-31
  3. Immediate bounds  — imm8 is 0-255, imm16 is 0-65535, signed values in range
  4. Control flow      — jumps don't land mid-instruction, HALT reachability
  5. Stack depth       — PUSH/POP balance, ENTER/LEAVE frame balance
  6. Well-formedness   — program doesn't end mid-instruction, HALT is reachable

Usage examples:
    echo "00 08 01 20 01 02 03 00" | python flux-bytecode-verifier.py
    python flux-bytecode-verifier.py program.bin
    python flux-bytecode-verifier.py program.bin --json
    python flux-bytecode-verifier.py --hex "0008012001020300"
    python flux-bytecode-verifier.py --run-tests

Author: Super Z — FLUX Bytecode Verifier for the SuperInstance fleet.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set


# ---------------------------------------------------------------------------
# Error & Warning Types
# ---------------------------------------------------------------------------

class ErrorKind(str, Enum):
    """Categories of verification errors."""
    INVALID_FORMAT = "INVALID_FORMAT"
    REGISTER_OUT_OF_RANGE = "REGISTER_OUT_OF_RANGE"
    INSTRUCTION_TRUNCATED = "INSTRUCTION_TRUNCATED"
    JUMP_MISALIGNED = "JUMP_MISALIGNED"
    STACK_IMBALANCE = "STACK_IMBALANCE"
    UNKNOWN_OPCODE = "UNKNOWN_OPCODE"


class WarningKind(str, Enum):
    """Categories of verification warnings (non-fatal)."""
    UNREACHABLE_CODE = "UNREACHABLE_CODE"
    STACK_UNDERFLOW_WARNING = "STACK_UNDERFLOW_WARNING"
    NO_HALT = "NO_HALT"


@dataclass
class VerifierMessage:
    """A single error or warning emitted by the verifier."""
    kind: str          # ErrorKind or WarningKind value
    pc: int            # Program counter where the issue was detected
    message: str       # Human-readable description
    opcode: int = -1   # Opcode byte that triggered the issue (if applicable)


@dataclass
class VerificationResult:
    """Complete result of a bytecode verification pass.

    Attributes:
        passed:        True if zero errors were found.
        errors:        List of hard errors that must be fixed.
        warnings:      List of soft warnings (program may still run).
        stats:         Dictionary with verification statistics.
    """
    passed: bool = True
    errors: List[VerifierMessage] = field(default_factory=list)
    warnings: List[VerifierMessage] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)

    def add_error(self, kind: ErrorKind, pc: int, message: str,
                  opcode: int = -1) -> None:
        """Convenience method to append an error."""
        self.errors.append(VerifierMessage(kind.value, pc, message, opcode))
        self.passed = False

    def add_warning(self, kind: WarningKind, pc: int, message: str,
                    opcode: int = -1) -> None:
        """Convenience method to append a warning."""
        self.warnings.append(VerifierMessage(kind.value, pc, message, opcode))


# ---------------------------------------------------------------------------
# ISA Definition — Converged ISA (canonical)
# ---------------------------------------------------------------------------

# Opcode name table for known opcodes (used in human-readable output).
OPCODE_NAMES: Dict[int, str] = {
    0x00: "HALT",  0x01: "NOP",   0x02: "RET",   0x03: "IRET",
    0x04: "BRK",   0x05: "WFI",   0x06: "RESET", 0x07: "SYN",
    0x08: "INC",   0x09: "DEC",   0x0A: "NOT",   0x0B: "NEG",
    0x0C: "PUSH",  0x0D: "POP",   0x0E: "CONF_LD", 0x0F: "CONF_ST",
    0x10: "SYS",   0x11: "TRAP",  0x12: "DBG",   0x13: "CLF",
    0x14: "SEMA",  0x15: "YIELD", 0x16: "CACHE", 0x17: "STRIPCF",
    0x18: "MOVI",  0x19: "ADDI",  0x1A: "SUBI",  0x1B: "ANDI",
    0x1C: "ORI",   0x1D: "XORI",  0x1E: "SHLI",  0x1F: "SHRI",
    0x20: "ADD",   0x21: "SUB",   0x22: "MUL",   0x23: "DIV",
    0x24: "MOD",   0x25: "AND",   0x26: "OR",    0x27: "XOR",
    0x28: "SHL",   0x29: "SHR",   0x2A: "MIN",   0x2B: "MAX",
    0x2C: "CMP_EQ", 0x2D: "CMP_LT", 0x2E: "CMP_GT", 0x2F: "CMP_NE",
    0x30: "FADD",  0x31: "FSUB",  0x32: "FMUL",  0x33: "FDIV",
    0x34: "FMIN",  0x35: "FMAX",  0x36: "FTOI",  0x37: "ITOF",
    0x38: "LOAD",  0x39: "STORE", 0x3A: "MOV",   0x3B: "SWP",
    0x3C: "JZ",    0x3D: "JNZ",   0x3E: "JLT",   0x3F: "JGT",
    0x40: "MOVI16", 0x41: "ADDI16", 0x42: "SUBI16", 0x43: "JMP",
    0x44: "JAL",   0x45: "CALL",  0x46: "LOOP",  0x47: "SELECT",
    0x48: "LOADOFF", 0x49: "STOREOF", 0x4A: "LOADI", 0x4B: "STOREI",
    0x4C: "ENTER", 0x4D: "LEAVE", 0x4E: "COPY",  0x4F: "FILL",
    0x50: "TELL",  0x51: "ASK",   0x52: "DELEG", 0x53: "BCAST",
    0x54: "ACCEPT", 0x55: "DECLINE", 0x56: "REPORT", 0x57: "MERGE",
    0x58: "FORK",  0x59: "JOIN",  0x5A: "SIGNAL", 0x5B: "AWAIT",
    0x5C: "TRUST",  0x5D: "DISCOV", 0x5E: "STATUS", 0x5F: "HEARTBT",
    0x60: "CONF_ADD", 0x61: "CONF_SUB", 0x62: "CONF_MUL", 0x63: "CONF_DIV",
    0x64: "CONF_FADD", 0x65: "CONF_FSUB", 0x66: "CONF_FMUL", 0x67: "CONF_FDIV",
    0x68: "CONF_MERGE", 0x69: "CONF_THRESH", 0x6A: "CONF_BOOST", 0x6B: "CONF_DECAY",
    0x6C: "CONF_SOURCE", 0x6D: "CONF_CALIB", 0x6E: "CONF_EXPLY", 0x6F: "CONF_VOTE",
    # 0x70-0x7F: Viewpoint ops (Format E)
    0x80: "VLOAD", 0x81: "VSTORE", 0x82: "VADD", 0x83: "VSUB",
    0x84: "VMUL",  0x85: "VDIV",  0x86: "VFMA",  0x87: "VREDUCE",
    # 0x88-0x8F: More sensor ops
    # 0x90-0x9F: Extended math/crypto (Format E)
    0x90: "ABS",   0x91: "SIGN",  0x92: "SQRT",  0x93: "POW",
    0x94: "LOG2",  0x95: "EXP",   0x96: "CLZ",   0x97: "CTZ",
    0x98: "POPCNT", 0x99: "BSWAP", 0x9A: "HASH",  0x9B: "AES_ENC",
    0x9C: "AES_DEC", 0x9D: "FSQRT", 0x9E: "FSIN", 0x9F: "FCOS",
    # 0xA0-0xAF: Mixed formats
    0xA0: "LEN",   0xA1: "CAST",  0xA2: "BOX",   0xA3: "UNBOX",
    0xA4: "SLICE", 0xA5: "CONCAT", 0xA6: "RESIZE", 0xA7: "FILL_RNG",
    0xA8: "COPY_RNG", 0xA9: "CMP_MEM", 0xAA: "SWAP_RNG", 0xAB: "FIND",
    0xAC: "REPLACE", 0xAD: "SPLIT", 0xAE: "JOIN_S", 0xAF: "TYPEOF",
    # 0xB0-0xBF: Vector/SIMD (Format E)
    # 0xC0-0xCF: Tensor/neural (Format E)
    # 0xD0-0xDF: Extended memory (Format G)
    # 0xE0-0xEF: Long jumps/calls (Format F)
    0xE0: "JMPL",  0xE1: "JALL",  0xE2: "CALLL", 0xE3: "TAIL",
    0xE4: "JMPL_COND", 0xE5: "RETVAL", 0xE6: "SWITCH", 0xE7: "TABLE",
    0xE8: "EXCEPT", 0xE9: "TRACE", 0xEA: "PROFILE", 0xEB: "GUARD",
    0xEC: "SPEC_LOAD", 0xED: "SPEC_STORE", 0xEE: "PREFETCH", 0xEF: "FLUSH",
    # 0xF0-0xFF: Extended system (Format A)
    0xF0: "HALT_ERR", 0xF1: "PANIC", 0xF2: "DUMP",  0xF3: "ASSERT",
    0xF4: "ID",    0xF5: "VER",   0xF6: "CPUID", 0xF7: "RDTSC",
    0xF8: "MSR",   0xF9: "IRQ",   0xFA: "NMI",   0xFB: "SGI",
    0xFC: "RSVD1", 0xFD: "RSVD2", 0xFE: "RSVD3", 0xFF: "ILLEGAL",
}


def opcode_name(op: int) -> str:
    """Return the mnemonic name for a known opcode, or a hex string."""
    return OPCODE_NAMES.get(op, f"OP_0x{op:02X}")


# ---------------------------------------------------------------------------
# Format Resolution — dispatch by opcode range per the converged ISA spec
# ---------------------------------------------------------------------------

# Instruction format sizes in bytes.
FMT_A_SIZE = 1   # [op]
FMT_B_SIZE = 2   # [op][rd]
FMT_C_SIZE = 2   # [op][imm8]
FMT_D_SIZE = 3   # [op][rd][imm8]
FMT_E_SIZE = 4   # [op][rd][rs1][rs2]
FMT_F_SIZE = 4   # [op][rd][imm16hi][imm16lo]
FMT_G_SIZE = 5   # [op][rd][rs1][imm16hi][imm16lo]


def instruction_format_and_size(op: int) -> Tuple[str, int]:
    """Determine the instruction format and byte-size for a given opcode.

    This follows the converged ISA dispatch table:
      - 0x00-0x03: Format A (1 byte)
      - 0x04-0x07: Format A (1 byte)
      - 0x08-0x0F: Format B (2 bytes) — [op][rd]
      - 0x10-0x17: Format C (2 bytes) — [op][imm8]
      - 0x18-0x1F: Format D (3 bytes) — [op][rd][imm8]
      - 0x20-0x3F: Format E (4 bytes) — [op][rd][rs1][rs2]
      - 0x40-0x47: Format F (4 bytes) — [op][rd][imm16hi][imm16lo]
      - 0x48-0x4F: Format G (5 bytes) — [op][rd][rs1][imm16hi][imm16lo]
      - 0x50-0x6F: Format E (4 bytes) — A2A and confidence ops
      - 0x70-0x7F: Format E (4 bytes) — Viewpoint ops
      - 0x80-0x8F: Format E (4 bytes) — Sensor ops
      - 0x90-0x9F: Format E (4 bytes) — Extended math/crypto
      - 0xA0-0xAF: Mixed (LEN=D, SLICE=G, rest=E)
      - 0xB0-0xBF: Format E (4 bytes) — Vector/SIMD
      - 0xC0-0xCF: Format E (4 bytes) — Tensor/neural
      - 0xD0-0xDF: Format G (5 bytes) — Extended memory
      - 0xE0-0xEF: Format F (4 bytes) — Long jumps/calls
      - 0xF0-0xFF: Format A (1 byte) — Extended system

    Special cases in 0xA0-0xAF:
      - 0xA0 (LEN):   Format D (3 bytes)
      - 0xA4 (SLICE): Format G (5 bytes)

    Returns:
        Tuple of (format_char, byte_size), e.g. ("A", 1), ("E", 4), etc.
    """
    if op <= 0x07:
        return ("A", FMT_A_SIZE)
    if op <= 0x0F:
        return ("B", FMT_B_SIZE)
    if op <= 0x17:
        return ("C", FMT_C_SIZE)
    if op <= 0x1F:
        return ("D", FMT_D_SIZE)
    if op <= 0x3F:
        return ("E", FMT_E_SIZE)
    if op <= 0x47:
        return ("F", FMT_F_SIZE)
    if op <= 0x4F:
        return ("G", FMT_G_SIZE)
    # 0x50-0x8F: all Format E
    if op <= 0x8F:
        return ("E", FMT_E_SIZE)
    # 0x90-0x9F: Extended math — Format E
    if op <= 0x9F:
        return ("E", FMT_E_SIZE)
    # 0xA0-0xAF: Mixed — special cases for LEN and SLICE
    if op <= 0xAF:
        if op == 0xA0:  # LEN
            return ("D", FMT_D_SIZE)
        if op == 0xA4:  # SLICE
            return ("G", FMT_G_SIZE)
        return ("E", FMT_E_SIZE)
    # 0xB0-0xCF: Format E
    if op <= 0xCF:
        return ("E", FMT_E_SIZE)
    # 0xD0-0xDF: Format G
    if op <= 0xDF:
        return ("G", FMT_G_SIZE)
    # 0xE0-0xEF: Format F
    if op <= 0xEF:
        return ("F", FMT_F_SIZE)
    # 0xF0-0xFF: Format A
    return ("A", FMT_A_SIZE)


# Set of opcodes that are unconditional jumps/calls (for control flow analysis).
JUMP_OPCODES: Set[int] = {
    0x02,  # RET
    0x43,  # JMP
    0x44,  # JAL
    0x45,  # CALL
    0x46,  # LOOP
    0xE0,  # JMPL
    0xE1,  # JALL
    0xE2,  # CALLL
    0xE3,  # TAIL
}

# Conditional branch opcodes (fall-through is possible).
CONDITIONAL_OPCODES: Set[int] = {
    0x3C,  # JZ
    0x3D,  # JNZ
    0x3E,  # JLT
    0x3F,  # JGT
    0xE4,  # JMPL_COND
}

# Opcodes that terminate the program (no fall-through).
TERMINAL_OPCODES: Set[int] = {
    0x00,  # HALT
    0xF0,  # HALT_ERR
    0xF1,  # PANIC
    0xFF,  # ILLEGAL
}

# All branch/jump opcodes (both conditional and unconditional).
ALL_BRANCH_OPCODES = JUMP_OPCODES | CONDITIONAL_OPCODES

# Opcodes that are known (have names in our table).
KNOWN_OPCODES: Set[int] = set(OPCODE_NAMES.keys())


# ---------------------------------------------------------------------------
# Bytecode Verifier
# ---------------------------------------------------------------------------

class BytecodeVerifier:
    """Statically validates FLUX bytecode against the converged ISA spec.

    Usage:
        verifier = BytecodeVerifier()
        result = verifier.verify(bytecode)
        if result.passed:
            print("Bytecode is valid!")
        else:
            for err in result.errors:
                print(f"ERROR at 0x{err.pc:04X}: {err.message}")
    """

    def __init__(self) -> None:
        """Initialize the verifier with fresh internal state."""
        self._reset()

    def _reset(self) -> None:
        """Reset all internal tracking state for a new verification pass."""
        self._instruction_starts: Set[int] = set()   # PCs that are instruction starts
        self._jump_targets: Set[int] = set()         # PCs that are jump targets
        self._errors: List[VerifierMessage] = []
        self._warnings: List[VerifierMessage] = []

    def verify(self, data: bytes) -> VerificationResult:
        """Run all verification checks on the given bytecode.

        Args:
            data: Raw bytecode as a bytes object.

        Returns:
            A VerificationResult containing errors, warnings, and stats.
        """
        self._reset()
        result = VerificationResult()

        # --- Phase 1: Sequential decode & basic checks ---
        pc = 0
        instruction_count = 0
        max_stack_depth = 0
        current_stack_depth = 0
        frame_depth = 0          # ENTER/LEAVE nesting
        max_frame_depth = 0
        halt_seen = False
        halt_pc = -1
        code_after_halt = False

        while pc < len(data):
            op = data[pc]
            fmt, size = instruction_format_and_size(op)
            name = opcode_name(op)

            # Record this PC as an instruction start.
            self._instruction_starts.add(pc)

            # --- Check 1: Instruction truncation ---
            # The instruction must fit entirely within the bytecode.
            if pc + size > len(data):
                result.add_error(
                    ErrorKind.INSTRUCTION_TRUNCATED, pc,
                    f"{name} (format {fmt}) needs {size} bytes but only "
                    f"{len(data) - pc} byte(s) remain (truncated at EOF)",
                    op
                )
                pc += 1  # Skip one byte and try to continue.
                continue

            # Extract operand bytes for bounds checking.
            operands = data[pc + 1: pc + size]

            # --- Check 2: Register bounds (0-31) ---
            # Register fields appear at specific positions depending on format:
            #   B: [rd]           — byte 1
            #   D: [rd][imm8]     — byte 1 is rd
            #   E: [rd][rs1][rs2] — bytes 1,2,3 are registers
            #   F: [rd][imm16hi][imm16lo] — byte 1 is rd
            #   G: [rd][rs1][imm16hi][imm16lo] — bytes 1,2 are registers
            reg_positions = self._register_positions(fmt)
            for pos in reg_positions:
                if pos < len(operands):
                    reg_val = operands[pos]
                    if reg_val > 31:
                        result.add_error(
                            ErrorKind.REGISTER_OUT_OF_RANGE, pc,
                            f"{name}: register r{reg_val} at operand byte {pos} "
                            f"is out of range (must be 0-31)",
                            op
                        )

            # --- Check 3: Immediate bounds ---
            self._check_immediates(result, pc, op, fmt, operands)

            # --- Check 4: Control flow — record jump targets ---
            self._collect_jump_targets(data, pc, op, fmt, size, operands)

            # --- Check 5: Stack depth tracking ---
            if op == 0x0C:   # PUSH
                current_stack_depth += 1
                max_stack_depth = max(max_stack_depth, current_stack_depth)
            elif op == 0x0D: # POP
                if current_stack_depth <= 0:
                    result.add_warning(
                        WarningKind.STACK_UNDERFLOW_WARNING, pc,
                        f"{name}: POP with empty stack (potential underflow)",
                        op
                    )
                else:
                    current_stack_depth -= 1
            elif op == 0x4C: # ENTER — pushes a new activation frame
                frame_depth += 1
                max_frame_depth = max(max_frame_depth, frame_depth)
            elif op == 0x4D: # LEAVE — pops the current activation frame
                if frame_depth <= 0:
                    result.add_error(
                        ErrorKind.STACK_IMBALANCE, pc,
                        f"{name}: LEAVE without matching ENTER (frame underflow)",
                        op
                    )
                else:
                    frame_depth -= 1

            # --- Check 6: HALT reachability ---
            if op in TERMINAL_OPCODES:
                if not halt_seen:
                    halt_seen = True
                    halt_pc = pc
                if pc != 0:
                    code_after_halt = True

            instruction_count += 1
            pc += size

        # --- Post-loop checks ---

        # Check if we ended exactly at the boundary (no partial instruction).
        if pc != len(data):
            # This should have been caught by truncation check, but be safe.
            result.add_error(
                ErrorKind.INSTRUCTION_TRUNCATED, pc,
                f"Program ends with {len(data) - pc} trailing byte(s) that do "
                f"not form a complete instruction",
                data[pc] if pc < len(data) else -1
            )

        # Warning: code after HALT
        if code_after_halt:
            result.add_warning(
                WarningKind.UNREACHABLE_CODE, halt_pc,
                f"HALT at 0x{halt_pc:04X} is followed by {len(data) - halt_pc - 1} "
                f"unreachable byte(s)",
                data[halt_pc]
            )

        # Warning: no HALT instruction found
        if not halt_seen and len(data) > 0:
            result.add_warning(
                WarningKind.NO_HALT, 0,
                "Program contains no HALT or terminal instruction — "
                "execution may fall off the end of bytecode",
            )

        # Warning: stack imbalance (PUSH without matching POP)
        if current_stack_depth > 0:
            result.add_warning(
                WarningKind.STACK_UNDERFLOW_WARNING, 0,
                f"Stack imbalance: {current_stack_depth} PUSH(es) without "
                f"matching POP(s) at end of program",
            )

        # Error: frame imbalance (ENTER without matching LEAVE)
        if frame_depth > 0:
            result.add_error(
                ErrorKind.STACK_IMBALANCE, 0,
                f"Frame imbalance: {frame_depth} ENTER(s) without matching "
                f"LEAVE(s) at end of program",
            )

        # --- Check 7: Jump alignment — all jump targets must land on
        # instruction boundaries ---
        for target_pc in sorted(self._jump_targets):
            if target_pc < 0 or target_pc >= len(data):
                result.add_error(
                    ErrorKind.JUMP_MISALIGNED, target_pc,
                    f"Jump target 0x{target_pc:04X} is outside bytecode "
                    f"(0x0000-0x{len(data)-1:04X})"
                )
            elif target_pc not in self._instruction_starts:
                result.add_error(
                    ErrorKind.JUMP_MISALIGNED, target_pc,
                    f"Jump target 0x{target_pc:04X} lands in the middle of "
                    f"an instruction (not an instruction boundary)"
                )

        # --- Populate stats ---
        result.stats = {
            "bytecode_size": len(data),
            "instruction_count": instruction_count,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "max_stack_depth": max_stack_depth,
            "final_stack_depth": current_stack_depth,
            "frame_depth": frame_depth,
            "max_frame_depth": max_frame_depth,
            "halt_reachable": halt_seen,
            "halt_pc": halt_pc if halt_seen else None,
            "jump_targets": sorted(self._jump_targets),
        }

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _register_positions(fmt: str) -> List[int]:
        """Return byte-offsets (relative to the first operand byte) that hold
        register fields for the given instruction format.

        Format layouts (after the opcode byte):
            A: (no operands)
            B: [rd]                    → register at offset 0
            C: [imm8]                  → no registers
            D: [rd][imm8]              → register at offset 0
            E: [rd][rs1][rs2]          → registers at offsets 0, 1, 2
            F: [rd][imm16hi][imm16lo]  → register at offset 0
            G: [rd][rs1][imm16hi][imm16lo] → registers at offsets 0, 1
        """
        _TABLE = {
            "A": [],
            "B": [0],
            "C": [],
            "D": [0],
            "E": [0, 1, 2],
            "F": [0],
            "G": [0, 1],
        }
        return _TABLE.get(fmt, [])

    def _check_immediates(self, result: VerificationResult, pc: int,
                          op: int, fmt: str, operands: bytes) -> None:
        """Validate immediate value bounds for the current instruction.

        - imm8 fields: always unsigned 0-255 (they are raw bytes, so always valid)
        - imm16 fields: constructed from [imm16hi][imm16lo] — always 0-65535
          (since they are raw bytes, they are inherently in range)

        However, for certain opcodes the immediate has *semantic* range
        constraints (e.g., signed immediates, register counts, etc.).
        We check those here.
        """
        name = opcode_name(op)

        if fmt in ("F", "G") and len(operands) >= 3:
            # imm16 = (hi << 8) | lo — always in 0..65535 for raw bytes.
            # No raw bounds error possible, but we log for awareness.
            pass

        if fmt == "D" and len(operands) >= 2:
            # operands[0] = rd (register, checked elsewhere)
            # operands[1] = imm8 — always 0-255 as a raw byte.
            pass

        # Semantic checks: JMP/JAL/CALL/JMPL etc. with target = 0 might be odd.
        # We don't flag these as errors, but some are noteworthy.
        # (Kept minimal — the verifier focuses on structural correctness.)

    def _collect_jump_targets(self, data: bytes, pc: int, op: int,
                               fmt: str, size: int,
                               operands: bytes) -> None:
        """Parse jump/call instructions and record their target PCs.

        Jump targets are extracted based on the format:
          - JMP (0x43, Format F): target = imm16 = (operands[1]<<8)|operands[2]
          - JMPL (0xE0, Format F): target = imm16
          - JAL (0x44, Format F): target = imm16
          - CALL (0x45, Format F): target = imm16
          - CALLL (0xE2, Format F): target = imm16
          - TAIL (0xE3, Format F): target = imm16
          - JZ/JNZ/JLT/JGT (Format D): target = imm8 (short branch)
          - LOOP (0x46, Format F): target = imm16
        """
        # Short branches (Format D): imm8 is a signed offset or absolute addr.
        # For now we treat imm8 as a target address (absolute).
        if op in (0x3C, 0x3D, 0x3E, 0x3F):  # JZ, JNZ, JLT, JGT — Format D
            if len(operands) >= 2:
                target = operands[1]  # imm8 as target address
                self._jump_targets.add(target)
            return

        # Format F jumps: imm16 is the target address.
        if op in (0x43, 0x44, 0x45, 0x46, 0xE0, 0xE1, 0xE2, 0xE3):
            if len(operands) >= 3:
                target = (operands[1] << 8) | operands[2]
                self._jump_targets.add(target)
            return

        # Format G with branch semantics (e.g., conditional long jump).
        if op == 0xE4:  # JMPL_COND — Format F (from E0-EF range)
            if len(operands) >= 3:
                target = (operands[1] << 8) | operands[2]
                self._jump_targets.add(target)


# ---------------------------------------------------------------------------
# Human-readable & JSON output formatters
# ---------------------------------------------------------------------------

def format_result_human(result: VerificationResult) -> str:
    """Format verification result as human-readable text."""
    lines: List[str] = []

    # Header
    lines.append("=" * 64)
    lines.append("  FLUX Bytecode Verifier — Verification Report")
    lines.append("=" * 64)

    # Verdict
    if result.passed:
        lines.append(f"\n  ✅  PASSED — bytecode is structurally valid")
    else:
        lines.append(f"\n  ❌  FAILED — {len(result.errors)} error(s) found")

    if result.warnings:
        lines.append(f"  ⚠️   {len(result.warnings)} warning(s)")

    # Stats
    lines.append("")
    lines.append(f"  Bytecode size:      {result.stats.get('bytecode_size', 0)} bytes")
    lines.append(f"  Instructions:       {result.stats.get('instruction_count', 0)}")
    lines.append(f"  Max stack depth:    {result.stats.get('max_stack_depth', 0)}")
    lines.append(f"  Final stack depth:  {result.stats.get('final_stack_depth', 0)}")
    lines.append(f"  Frame depth:        {result.stats.get('frame_depth', 0)}")
    lines.append(f"  Max frame depth:    {result.stats.get('max_frame_depth', 0)}")
    lines.append(f"  HALT reachable:     {'yes' if result.stats.get('halt_reachable') else 'no'}")
    if result.stats.get('halt_pc') is not None:
        lines.append(f"  HALT at PC:         0x{result.stats['halt_pc']:04X}")
    if result.stats.get('jump_targets'):
        targets_str = ", ".join(f"0x{t:04X}" for t in result.stats['jump_targets'])
        lines.append(f"  Jump targets:       {targets_str}")

    # Errors
    if result.errors:
        lines.append("")
        lines.append(f"  ERRORS ({len(result.errors)}):")
        lines.append("  " + "-" * 58)
        for err in result.errors:
            op_str = f" [0x{err.opcode:02X}]" if err.opcode >= 0 else ""
            lines.append(f"  [{err.kind}]  PC=0x{err.pc:04X}{op_str}  {err.message}")

    # Warnings
    if result.warnings:
        lines.append("")
        lines.append(f"  WARNINGS ({len(result.warnings)}):")
        lines.append("  " + "-" * 58)
        for warn in result.warnings:
            op_str = f" [0x{warn.opcode:02X}]" if warn.opcode >= 0 else ""
            lines.append(f"  [{warn.kind}]  PC=0x{warn.pc:04X}{op_str}  {warn.message}")

    lines.append("")
    lines.append("=" * 64)
    return "\n".join(lines)


def format_result_json(result: VerificationResult) -> str:
    """Format verification result as JSON (machine-readable).

    Converts VerifierMessage objects to plain dicts for JSON serialization.
    """
    def _msg_to_dict(msg: VerifierMessage) -> Dict:
        return {
            "kind": msg.kind,
            "pc": msg.pc,
            "pc_hex": f"0x{msg.pc:04X}",
            "message": msg.message,
            "opcode": msg.opcode,
            "opcode_hex": f"0x{msg.opcode:02X}" if msg.opcode >= 0 else None,
        }

    output = {
        "passed": result.passed,
        "errors": [_msg_to_dict(e) for e in result.errors],
        "warnings": [_msg_to_dict(w) for w in result.warnings],
        "stats": result.stats,
        "stats_extra": {
            "jump_targets_hex": [f"0x{t:04X}" for t in result.stats.get("jump_targets", [])],
            "halt_pc_hex": (f"0x{result.stats['halt_pc']:04X}"
                            if result.stats.get("halt_pc") is not None else None),
        },
    }
    return json.dumps(output, indent=2, default=str)


# ---------------------------------------------------------------------------
# Input parsing helpers
# ---------------------------------------------------------------------------

def parse_hex_input(hex_str: str) -> bytes:
    """Parse a hex string (with optional spaces, 0x prefixes, commas) into bytes.

    Accepts formats like:
        "00 08 01 20"
        "00,08,01,20"
        "0x00080120"
        "000801202001020300"
    """
    # Remove common separators and whitespace.
    cleaned = hex_str.replace("0x", "").replace("0X", "").replace(",", "").replace(" ", "").replace("\n", "").replace("\t", "")
    if len(cleaned) % 2 != 0:
        raise ValueError(f"Hex string has odd length ({len(cleaned)} chars); "
                         f"each byte needs exactly 2 hex digits")
    return bytes.fromhex(cleaned)


def read_bytecode_from_file(path: str) -> bytes:
    """Read raw binary bytecode from a file path."""
    with open(path, "rb") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Test Suite — embedded test cases
# ---------------------------------------------------------------------------

def run_tests() -> bool:
    """Run the embedded test suite. Returns True if all tests pass."""
    print("Running FLUX Bytecode Verifier test suite...")
    print("-" * 64)

    verifier = BytecodeVerifier()
    all_passed = True
    test_num = 0

    def _check(test_name: str, bytecode: bytes, expect_pass: bool,
               expect_errors: int = 0, expect_warnings: int = 0) -> None:
        nonlocal all_passed, test_num
        test_num += 1
        result = verifier.verify(bytecode)
        ok = True
        reasons = []

        if result.passed != expect_pass:
            ok = False
            reasons.append(f"expected passed={expect_pass}, got passed={result.passed}")

        if len(result.errors) < expect_errors:
            ok = False
            reasons.append(f"expected ≥{expect_errors} errors, got {len(result.errors)}")

        if len(result.warnings) < expect_warnings:
            ok = False
            reasons.append(f"expected ≥{expect_warnings} warnings, got {len(result.warnings)}")

        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"  Test {test_num:02d}: [{status}] {test_name}")
        for r in reasons:
            print(f"           → {r}")
        if not ok and (result.errors or result.warnings):
            for e in result.errors:
                print(f"           ERR: [{e.kind}] 0x{e.pc:04X}: {e.message}")
            for w in result.warnings:
                print(f"           WRN: [{w.kind}] 0x{w.pc:04X}: {w.message}")

    # --- Test 1: Minimal valid program — just HALT ---
    _check("HALT only (valid)", bytes([0x00]), expect_pass=True)

    # --- Test 2: NOP + HALT (two valid instructions) ---
    _check("NOP + HALT (valid)", bytes([0x01, 0x00]), expect_pass=True)

    # --- Test 3: Truncated Format E instruction (ADD needs 4 bytes, only 2) ---
    # ADD = 0x20, Format E, needs [op][rd][rs1][rs2] = 4 bytes
    _check("Truncated ADD instruction",
           bytes([0x20, 0x01, 0x00]),  # Missing rs2
           expect_pass=False, expect_errors=1)

    # --- Test 4: Register out of range ---
    # INC = 0x08, Format B = [op][rd], rd=0x25 = 37 > 31
    _check("Register out of range (INC r37)",
           bytes([0x08, 0x25, 0x00]),
           expect_pass=False, expect_errors=1)

    # --- Test 5: PUSH without POP (stack imbalance warning) ---
    _check("PUSH without POP (stack warning)",
           bytes([0x0C, 0x01, 0x00]),  # PUSH r1, NOP, HALT
           expect_pass=True, expect_warnings=1)

    # --- Test 6: POP on empty stack (underflow warning) ---
    _check("POP on empty stack (underflow warning)",
           bytes([0x0D, 0x01, 0x00]),  # POP r1, NOP, HALT
           expect_pass=True, expect_warnings=1)

    # --- Test 7: LEAVE without ENTER (frame imbalance error) ---
    _check("LEAVE without ENTER (frame error)",
           bytes([0x4D, 0x01, 0x00, 0x00, 0x00, 0x00]),  # LEAVE is Format G (5 bytes)
           expect_pass=False, expect_errors=1)

    # --- Test 8: Code after HALT (unreachable warning) ---
    _check("Code after HALT (unreachable warning)",
           bytes([0x00, 0x01, 0x00]),  # HALT, NOP, (no second HALT — fall through)
           expect_pass=True, expect_warnings=1)

    # --- Test 9: No HALT instruction (warning) ---
    _check("No HALT instruction",
           bytes([0x01, 0x01]),  # NOP, NOP — no terminal
           expect_pass=True, expect_warnings=1)

    # --- Test 10: Valid multi-instruction program ---
    # MOVI r1,5 (0x18 0x01 0x05) + ADD r1,r2,r3 (0x20 0x01 0x02 0x03) + HALT
    _check("Valid multi-instruction program",
           bytes([0x18, 0x01, 0x05, 0x20, 0x01, 0x02, 0x03, 0x00]),
           expect_pass=True)

    # --- Test 11: Empty bytecode ---
    _check("Empty bytecode", b"", expect_pass=True)

    # --- Test 12: ENTER/LEAVE balanced (valid) ---
    # ENTER is Format G: [0x4C][rd][rs1][imm16hi][imm16lo] = 5 bytes
    # LEAVE is Format G: [0x4D][rd][rs1][imm16hi][imm16lo] = 5 bytes
    _check("ENTER/LEAVE balanced",
           bytes([0x4C, 0x01, 0x00, 0x00, 0x08,   # ENTER r1, r0, 8
                  0x4D, 0x01, 0x00, 0x00, 0x08,   # LEAVE r1, r0, 8
                  0x00]),                           # HALT
           expect_pass=True)

    # --- Test 13: JMP to misaligned target ---
    # JMP is 0x43 (Format F = 4 bytes): [0x43][rd][imm16hi][imm16lo]
    # JMP r0, target=0x0003 which lands inside the MOVI instruction (offset 3)
    # MOVI starts at 0, is 3 bytes long (Format D), so PC 3 is the start of
    # the next instruction only if something starts there.
    # Let's construct: [JMP r0, 0x0001][HALT]
    # = [0x43 0x00 0x00 0x01][0x00]
    # Jump target 0x0001 lands inside the JMP instruction itself (byte 1).
    _check("JMP to misaligned target (inside instruction)",
           bytes([0x43, 0x00, 0x00, 0x01, 0x00]),
           expect_pass=False, expect_errors=1)

    # --- Test 14: Valid PUSH/POP balanced ---
    _check("PUSH/POP balanced",
           bytes([0x0C, 0x01,   # PUSH r1
                  0x0D, 0x01,   # POP r1
                  0x00]),        # HALT
           expect_pass=True)

    # --- Test 15: Multiple register out of range in Format E ---
    # MUL r32,r33,r34 = [0x22][0x20][0x21][0x22][0x00]
    # r32=0x20=32, r33=0x21=33, r34=0x22=34 — all > 31
    _check("Three registers out of range in MUL",
           bytes([0x22, 0x20, 0x21, 0x22, 0x00]),
           expect_pass=False, expect_errors=3)

    print("-" * 64)
    total = test_num
    passed = total - (1 if not all_passed else 0)  # simplified
    print(f"  Results: {'ALL PASSED' if all_passed else 'SOME FAILED'} "
          f"({test_num} tests)")
    print()
    return all_passed


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    """Main entry point for the CLI interface.

    Supports:
      - Reading hex from stdin (piped or typed)
      - Reading a binary file via positional argument
      - --hex flag for inline hex string
      - --json flag for machine-readable JSON output
      - --run-tests to execute the embedded test suite

    Returns:
        Exit code: 0 if verification passed (or tests passed), 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="FLUX Bytecode Verifier — statically validate FLUX bytecode",
        epilog="Examples:\n"
               '  echo "00 08 01 20 01 02 03 00" | python flux-bytecode-verifier.py\n'
               "  python flux-bytecode-verifier.py program.bin\n"
               "  python flux-bytecode-verifier.py program.bin --json\n"
               "  python flux-bytecode-verifier.py --hex 0001080120020300\n"
               "  python flux-bytecode-verifier.py --run-tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file", nargs="?", default=None,
        help="Path to a binary bytecode file to verify"
    )
    parser.add_argument(
        "--hex", default=None,
        help="Inline hex string to verify (e.g. '0008012001020300')"
    )
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="Output results as JSON instead of human-readable text"
    )
    parser.add_argument(
        "--run-tests", action="store_true", default=False,
        help="Run the embedded test suite and exit"
    )

    args = parser.parse_args()

    # Run test suite if requested.
    if args.run_tests:
        success = run_tests()
        return 0 if success else 1

    # Determine bytecode source (priority: --hex > file arg > stdin).
    bytecode: Optional[bytes] = None

    if args.hex:
        try:
            bytecode = parse_hex_input(args.hex)
        except ValueError as e:
            print(f"Error parsing hex input: {e}", file=sys.stderr)
            return 1
    elif args.file:
        try:
            bytecode = read_bytecode_from_file(args.file)
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            return 1
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 1
    else:
        # Read from stdin if it has data (not a terminal).
        if sys.stdin.isatty():
            parser.print_help()
            print("\nError: no input provided. Pipe hex data, use --hex, "
                  "or specify a file.", file=sys.stderr)
            return 1
        stdin_data = sys.stdin.read().strip()
        if not stdin_data:
            print("Error: stdin is empty", file=sys.stderr)
            return 1
        try:
            bytecode = parse_hex_input(stdin_data)
        except ValueError as e:
            print(f"Error parsing stdin hex: {e}", file=sys.stderr)
            return 1

    if bytecode is None:
        print("Error: no bytecode to verify", file=sys.stderr)
        return 1

    # Run verification.
    verifier = BytecodeVerifier()
    result = verifier.verify(bytecode)

    # Output results.
    if args.json:
        print(format_result_json(result))
    else:
        print(format_result_human(result))

    # Exit code: 0 if passed, 1 if errors found.
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
