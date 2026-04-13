#!/usr/bin/env python3
"""FLUX Conformance Test Generator — ISA conformance test vector production tool.

Generates conformance test vectors from the FLUX converged ISA specification.
Pure Python stdlib — no external dependencies.

Encoding Reference (Converged ISA — Canonical):
  All little-endian. 32 registers (R0 = zero, R1–R31 general).

  Format dispatch by opcode range:
    0x00–0x07  Format A (1B) — [opcode]
    0x08–0x0F  Format B (2B) — [opcode][rd]
    0x10–0x17  Format C (2B) — [opcode][imm8]
    0x18–0x1F  Format D (3B) — [opcode][rd][imm8]
    0x20–0x3F  Format E (4B) — [opcode][rd][rs1][rs2]
    0x40–0x47  Format F (4B) — [opcode][rd][imm16_lo][imm16_hi]
    0x48–0x4F  Format G (5B) — [opcode][rd][rs1][imm16_lo][imm16_hi]
    0x50–0x6F  Format E (4B) — A2A + confidence
    0x70–0x7F  Format E (4B) — viewpoint
    0x80–0x8F  Format E (4B) — sensor
    0x90–0x9F  Format E (4B) — math/crypto
    0xA0–0xAF  Mixed (0xA0 = D, 0xA4 = G, rest = E)
    0xB0–0xBF  Format E (4B) — vector
    0xC0–0xCF  Format E (4B) — tensor
    0xD0–0xDF  Format G (5B) — extended memory
    0xE0–0xEF  Format F (4B) — long jumps
    0xF0–0xFF  Format A (1B) — system

Usage:
    python flux-conformance-generator.py                 # demo + coverage
    python flux-conformance-generator.py --json <path>   # export JSON
    python flux-conformance-generator.py --pytest <path>  # export pytest file
"""

from __future__ import annotations

import json
import os
import struct
import sys
import textwrap
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

ISA_VERSION = "2.0"
NUM_REGISTERS = 32

# ── Opcodes ────────────────────────────────────────────────────────────────────

# Format A  (1-byte)
HALT = 0x00
NOP  = 0x01
RET  = 0x02

# Format B  (2-byte)
INC  = 0x08
DEC  = 0x09
NOT  = 0x0A
NEG  = 0x0B
PUSH = 0x0C
POP  = 0x0D

# Format D  (3-byte)
MOVI = 0x18
ADDI = 0x19
SUBI = 0x1A

# Format E  — arithmetic / ALU  (4-byte)
ADD = 0x20
SUB = 0x21
MUL = 0x22
DIV = 0x23
MOD = 0x24
AND = 0x25
OR  = 0x26
XOR = 0x27

# Format E  — comparison
CMP_EQ = 0x2C
CMP_LT = 0x2D
CMP_GT = 0x2E
CMP_NE = 0x2F

# Format E  — float
FADD = 0x30
FSUB = 0x31
FMUL = 0x32
FDIV = 0x33

# Format E  — memory
LOAD  = 0x38
STORE = 0x39
MOV   = 0x3A
SWP   = 0x3B

# Format E  — conditional control
JZ  = 0x3C
JNZ = 0x3D
JLT = 0x3E
JGT = 0x3F

# Format F  (4-byte)
MOVI16 = 0x40
JMP    = 0x43
JAL    = 0x44

# Format G  (5-byte)
LOADOFF  = 0x48
STOREOFF = 0x49

# ── Opcode metadata database ──────────────────────────────────────────────────

OPCODE_DB: Dict[int, Dict[str, str]] = {
    # Format A — system
    0x00: {"mnemonic": "HALT", "format": "A", "category": "system"},
    0x01: {"mnemonic": "NOP",  "format": "A", "category": "system"},
    0x02: {"mnemonic": "RET",  "format": "A", "category": "control"},
    # Format B
    0x08: {"mnemonic": "INC",  "format": "B", "category": "arithmetic"},
    0x09: {"mnemonic": "DEC",  "format": "B", "category": "arithmetic"},
    0x0A: {"mnemonic": "NOT",  "format": "B", "category": "logic"},
    0x0B: {"mnemonic": "NEG",  "format": "B", "category": "arithmetic"},
    0x0C: {"mnemonic": "PUSH", "format": "B", "category": "stack"},
    0x0D: {"mnemonic": "POP",  "format": "B", "category": "stack"},
    # Format D
    0x18: {"mnemonic": "MOVI",  "format": "D", "category": "data"},
    0x19: {"mnemonic": "ADDI",  "format": "D", "category": "arithmetic"},
    0x1A: {"mnemonic": "SUBI",  "format": "D", "category": "arithmetic"},
    # Format E — arithmetic
    0x20: {"mnemonic": "ADD", "format": "E", "category": "arithmetic"},
    0x21: {"mnemonic": "SUB", "format": "E", "category": "arithmetic"},
    0x22: {"mnemonic": "MUL", "format": "E", "category": "arithmetic"},
    0x23: {"mnemonic": "DIV", "format": "E", "category": "arithmetic"},
    0x24: {"mnemonic": "MOD", "format": "E", "category": "arithmetic"},
    # Format E — logic
    0x25: {"mnemonic": "AND", "format": "E", "category": "logic"},
    0x26: {"mnemonic": "OR",  "format": "E", "category": "logic"},
    0x27: {"mnemonic": "XOR", "format": "E", "category": "logic"},
    # Format E — comparison
    0x2C: {"mnemonic": "CMP_EQ", "format": "E", "category": "comparison"},
    0x2D: {"mnemonic": "CMP_LT", "format": "E", "category": "comparison"},
    0x2E: {"mnemonic": "CMP_GT", "format": "E", "category": "comparison"},
    0x2F: {"mnemonic": "CMP_NE", "format": "E", "category": "comparison"},
    # Format E — float
    0x30: {"mnemonic": "FADD", "format": "E", "category": "float"},
    0x31: {"mnemonic": "FSUB", "format": "E", "category": "float"},
    0x32: {"mnemonic": "FMUL", "format": "E", "category": "float"},
    0x33: {"mnemonic": "FDIV", "format": "E", "category": "float"},
    # Format E — memory
    0x38: {"mnemonic": "LOAD",  "format": "E", "category": "memory"},
    0x39: {"mnemonic": "STORE", "format": "E", "category": "memory"},
    0x3A: {"mnemonic": "MOV",   "format": "E", "category": "data"},
    0x3B: {"mnemonic": "SWP",   "format": "E", "category": "data"},
    # Format E — control
    0x3C: {"mnemonic": "JZ",  "format": "E", "category": "control"},
    0x3D: {"mnemonic": "JNZ", "format": "E", "category": "control"},
    0x3E: {"mnemonic": "JLT", "format": "E", "category": "control"},
    0x3F: {"mnemonic": "JGT", "format": "E", "category": "control"},
    # Format F
    0x40: {"mnemonic": "MOVI16", "format": "F", "category": "data"},
    0x43: {"mnemonic": "JMP",    "format": "F", "category": "control"},
    0x44: {"mnemonic": "JAL",    "format": "F", "category": "control"},
    # Format G
    0x48: {"mnemonic": "LOADOFF",  "format": "G", "category": "memory"},
    0x49: {"mnemonic": "STOREOFF", "format": "G", "category": "memory"},
}

# Opcode ranges that require external hardware / are not testable in pure SW
EXTERNAL_RANGES: List[Tuple[int, int, str]] = [
    (0x50, 0x6F, "a2a"),
    (0x70, 0x7F, "viewpoint"),
    (0x80, 0x8F, "sensor"),
    (0xC0, 0xCF, "tensor"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Encoding helpers
# ═══════════════════════════════════════════════════════════════════════════════

def encode_a(opcode: int) -> bytes:
    """Format A: 1-byte instruction  [opcode]."""
    return bytes([opcode & 0xFF])


def encode_b(opcode: int, rd: int) -> bytes:
    """Format B: 2-byte instruction  [opcode][rd]."""
    return bytes([opcode & 0xFF, rd & 0x1F])


def encode_c(opcode: int, imm8: int) -> bytes:
    """Format C: 2-byte instruction  [opcode][imm8]."""
    return bytes([opcode & 0xFF, imm8 & 0xFF])


def encode_d(opcode: int, rd: int, imm8: int) -> bytes:
    """Format D: 3-byte instruction  [opcode][rd][imm8]."""
    return bytes([opcode & 0xFF, rd & 0x1F, imm8 & 0xFF])


def encode_e(opcode: int, rd: int, rs1: int, rs2: int) -> bytes:
    """Format E: 4-byte instruction  [opcode][rd][rs1][rs2]."""
    return bytes([opcode & 0xFF, rd & 0x1F, rs1 & 0x1F, rs2 & 0x1F])


def encode_f(opcode: int, rd: int, imm16: int) -> bytes:
    """Format F: 4-byte instruction  [opcode][rd][imm16_lo][imm16_hi]."""
    return bytes([opcode & 0xFF, rd & 0x1F,
                  imm16 & 0xFF, (imm16 >> 8) & 0xFF])


def encode_g(opcode: int, rd: int, rs1: int, imm16: int) -> bytes:
    """Format G: 5-byte instruction  [opcode][rd][rs1][imm16_lo][imm16_hi]."""
    return bytes([opcode & 0xFF, rd & 0x1F, rs1 & 0x1F,
                  imm16 & 0xFF, (imm16 >> 8) & 0xFF])


def to_hex(parts: Sequence[bytes]) -> str:
    """Concatenate byte sequences and return lowercase hex string."""
    return b''.join(parts).hex()


def float_to_bits(f: float) -> int:
    """Convert a Python float to an IEEE-754 single-precision bit pattern."""
    return struct.unpack('<I', struct.pack('<f', f))[0]


def bits_to_float(bits: int) -> float:
    """Convert an IEEE-754 single-precision bit pattern to a Python float."""
    return struct.unpack('<f', struct.pack('<I', bits & 0xFFFFFFFF))[0]


def _signed8(v: int) -> int:
    """Interpret an 8-bit unsigned value as signed (-128 … 127)."""
    v &= 0xFF
    return v - 256 if v >= 128 else v


# ═══════════════════════════════════════════════════════════════════════════════
# Test-vector builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_vector(
    name: str,
    opcode_val: int,
    category: str,
    mnemonic: str,
    fmt: str,
    prog_parts: Sequence[bytes],
    expected_regs: Dict[int, int],
    tags: List[str],
    *,
    halted: bool = True,
    initial_regs: Optional[Dict[int, int]] = None,
    initial_mem: Optional[Dict[int, int]] = None,
    expected_mem: Optional[Dict[int, int]] = None,
    desc: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a single conformance test-vector dictionary."""
    prog = b''.join(prog_parts)
    vector: Dict[str, Any] = {
        "name": name,
        "isa_version": ISA_VERSION,
        "category": category,
        "opcode_hex": f"0x{opcode_val:02X}",
        "mnemonic": mnemonic,
        "format": fmt,
        "program_hex": prog.hex(),
        "setup": {
            "description": desc or name,
        },
        "expected": {
            "registers": {f"R{k}": v for k, v in sorted(expected_regs.items())},
            "pc_after": len(prog),
            "halted": halted,
        },
        "tags": tags,
    }
    if initial_regs:
        vector["setup"]["initial_registers"] = {
            f"R{k}": v for k, v in sorted(initial_regs.items())
        }
    if initial_mem:
        vector["setup"]["initial_memory"] = {
            str(k): v for k, v in sorted(initial_mem.items())
        }
    if expected_mem:
        vector["expected"]["memory"] = {
            str(k): v for k, v in sorted(expected_mem.items())
        }
    return vector


# ═══════════════════════════════════════════════════════════════════════════════
# Conformance Test Generator
# ═══════════════════════════════════════════════════════════════════════════════

class ConformanceTestGenerator:
    """Generates ISA conformance test vectors for the FLUX converged ISA."""

    def __init__(self) -> None:
        self.opcode_db = OPCODE_DB
        self._all_vectors: List[Dict[str, Any]] = []

    # ── Public API ─────────────────────────────────────────────────────────

    def generate_all(self) -> List[Dict[str, Any]]:
        """Generate test vectors for every testable opcode."""
        self._all_vectors = []
        self._all_vectors.extend(self._gen_format_a())
        self._all_vectors.extend(self._gen_format_b())
        self._all_vectors.extend(self._gen_format_d())
        self._all_vectors.extend(self._gen_format_e_arithmetic())
        self._all_vectors.extend(self._gen_format_e_logic())
        self._all_vectors.extend(self._gen_format_e_comparison())
        self._all_vectors.extend(self._gen_format_e_float())
        self._all_vectors.extend(self._gen_format_e_memory())
        self._all_vectors.extend(self._gen_format_e_control())
        self._all_vectors.extend(self._gen_format_f())
        self._all_vectors.extend(self._gen_format_g())
        return list(self._all_vectors)

    def generate_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Generate only vectors belonging to *category*."""
        return [v for v in self.generate_all() if v["category"] == category]

    def export_json(self, vectors: List[Dict[str, Any]], path: str) -> None:
        """Write *vectors* to a JSON file at *path*."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as fh:
            json.dump(vectors, fh, indent=2)
            fh.write('\n')
        print(f"  [json]  wrote {len(vectors)} vectors -> {path}")

    def export_pytest(self, vectors: List[Dict[str, Any]], path: str) -> None:
        """Write *vectors* as a pytest parametrised test file at *path*."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        lines: List[str] = []
        lines.append('"""Auto-generated FLUX ISA conformance tests.')
        lines.append(f'ISA version: {ISA_VERSION}  |  Total vectors: {len(vectors)}')
        lines.append('Generated by flux-conformance-generator.py')
        lines.append('"""')
        lines.append('')
        lines.append('import json')
        lines.append('import pytest')
        lines.append('')
        lines.append('')
        lines.append('# ═══════════════════════════════════════════════════════════════════')
        lines.append('# Test Vectors (embedded)')
        lines.append('# ═══════════════════════════════════════════════════════════════════')
        lines.append('VECTORS = [')
        for v in vectors:
            lines.append(f'    # --- {v["name"]} ---')
            vec_data: Dict[str, Any] = {
                "name": v["name"],
                "mnemonic": v["mnemonic"],
                "format": v["format"],
                "opcode_hex": v["opcode_hex"],
                "program_hex": v["program_hex"],
                "expected": v["expected"],
                "tags": v["tags"],
            }
            setup = v.get("setup", {})
            if "initial_registers" in setup:
                vec_data["initial_registers"] = setup["initial_registers"]
            if "initial_memory" in setup:
                vec_data["initial_memory"] = setup["initial_memory"]
            lines.append('    ' + json.dumps(vec_data, indent=4).replace('\n', '\n    ') + ',')
        lines.append(']')
        lines.append('')
        lines.append('')
        lines.append('def _run_flux_program(program_hex: str,')
        lines.append('                       initial_regs: dict = None,')
        lines.append('                       initial_mem: dict = None) -> dict:')
        lines.append('    """Stub — replace with a real FLUX VM runner.')
        lines.append('')
        lines.append('    Must return:  {"pc": int, "halted": bool,')
        lines.append('                  "regs": list[int], "mem": dict[int, int]}')
        lines.append('    """')
        lines.append('    raise NotImplementedError(')
        lines.append('        "Conformance tests require a FLUX VM backend.  "')
        lines.append('        "Provide _run_flux_program or import from flux_vm."')
        lines.append('    )')
        lines.append('')
        lines.append('')
        lines.append('@pytest.mark.parametrize("vec", VECTORS, ids=lambda v: v["name"])')
        lines.append('def test_flux_conformance(vec):')
        lines.append('    """Verify a single FLUX ISA test vector."""')
        lines.append('    result = _run_flux_program(')
        lines.append('        vec["program_hex"],')
        lines.append('        vec.get("initial_registers"),')
        lines.append('        vec.get("initial_memory"),')
        lines.append('    )')
        lines.append('    exp = vec["expected"]')
        lines.append('    assert result["pc"] == exp["pc_after"], \\')
        lines.append('        f\'PC: expected {exp["pc_after"]}, got {result["pc"]}\'')
        lines.append('    if exp["halted"]:')
        lines.append('        assert result["halted"], "expected halted state"')
        lines.append('    for reg, val in exp.get("registers", {}).items():')
        lines.append('        idx = int(reg[1:])')
        lines.append('        assert result["regs"][idx] == val, \\')
        lines.append('            f\'R{idx}: expected {val}, got {result["regs"][idx]}\'')
        lines.append('    if "memory" in exp:')
        lines.append('        for addr, val in exp["memory"].items():')
        lines.append('            assert result["mem"][int(addr)] == val, \\')
        lines.append('                f\'MEM[{addr}]: expected {val}, got {result["mem"][int(addr)]}\'')
        lines.append('')
        lines.append('')
        lines.append('@pytest.mark.parametrize("vec", VECTORS, ids=lambda v: v["name"])')
        lines.append('def test_bytecode_decode_roundtrip(vec):')
        lines.append('    """Verify program_hex is valid hex and non-empty."""')
        lines.append('    raw = bytes.fromhex(vec["program_hex"])')
        lines.append('    assert len(raw) > 0, "empty program"')
        lines.append('    assert len(raw) == vec["expected"]["pc_after"], \\')
        lines.append('        f\'byte length {len(raw)} != pc_after {vec["expected"]["pc_after"]}\'')
        lines.append('')

        with open(path, 'w') as fh:
            fh.write('\n'.join(lines))
        print(f"  [pytest] wrote {len(vectors)} vectors -> {path}")

    # ── Coverage ───────────────────────────────────────────────────────────

    def coverage_report(self, vectors: Optional[List[Dict[str, Any]]] = None
                        ) -> Dict[str, Any]:
        """Return a coverage summary dict."""
        if vectors is None:
            vectors = self._all_vectors or self.generate_all()
        tested_opcodes: set = {int(v["opcode_hex"], 16) for v in vectors}
        total_defined = len(self.opcode_db)
        total_tested = len(tested_opcodes & set(self.opcode_db.keys()))
        external_count = sum(hi - lo + 1 for lo, hi, _ in EXTERNAL_RANGES)

        by_cat: Dict[str, Dict[str, int]] = {}
        for op, info in self.opcode_db.items():
            cat = info["category"]
            by_cat.setdefault(cat, {"total": 0, "tested": 0})
            by_cat[cat]["total"] += 1
            if op in tested_opcodes:
                by_cat[cat]["tested"] += 1

        by_fmt: Dict[str, Dict[str, int]] = {}
        for v in vectors:
            fmt = v["format"]
            by_fmt.setdefault(fmt, {"count": 0, "opcodes": set()})
            by_fmt[fmt]["count"] += 1
            by_fmt[fmt]["opcodes"].add(v["mnemonic"])

        return {
            "isa_version": ISA_VERSION,
            "total_defined_opcodes": total_defined,
            "total_tested_opcodes": total_tested,
            "total_vectors": len(vectors),
            "coverage_percent": round(total_tested / total_defined * 100, 1),
            "external_ranges": [
                {"range": f"0x{lo:02X}–0x{hi:02X}", "name": name}
                for lo, hi, name in EXTERNAL_RANGES
            ],
            "external_opcode_count": external_count,
            "by_category": by_cat,
            "by_format": {
                fmt: {"vectors": d["count"], "unique_opcodes": sorted(d["opcodes"])}
                for fmt, d in sorted(by_fmt.items())
            },
            "untested_opcodes": sorted(
                f"0x{op:02X} ({info['mnemonic']})"
                for op, info in self.opcode_db.items()
                if op not in tested_opcodes
            ),
        }

    # ── Demo / CLI ─────────────────────────────────────────────────────────

    def run_demo(self) -> None:
        """Print a human-readable summary to stdout."""
        vectors = self.generate_all()
        report = self.coverage_report(vectors)

        sep = "=" * 65
        print(sep)
        print(f"  FLUX Conformance Test Generator — ISA v{ISA_VERSION}")
        print(sep)
        print()
        print(f"  Generated {report['total_vectors']} test vectors "
              f"across {len(report['by_category'])} categories.")
        print()

        # Category breakdown
        print("  Category Breakdown:")
        for cat, info in sorted(report["by_category"].items()):
            ops_in_cat = sorted(
                info["mnemonic"] for op, info in self.opcode_db.items()
                if info["category"] == cat
            )
            print(f"    {cat:<14s}: {info['tested']:>2d} opcodes tested  "
                  f"({info['tested']}/{info['total']})  [{', '.join(ops_in_cat)}]")
        print()

        # Format distribution
        print("  Format Distribution:")
        for fmt, info in report["by_format"].items():
            print(f"    Format {fmt}: {info['vectors']:>3d} vectors  "
                  f"[{', '.join(info['unique_opcodes'])}]")
        print()

        # Coverage
        print("  Coverage:")
        print(f"    Defined opcodes : {report['total_defined_opcodes']}")
        print(f"    Tested opcodes  : {report['total_tested_opcodes']}")
        print(f"    Coverage        : {report['coverage_percent']}%")
        print()

        if report["untested_opcodes"]:
            print("  Untested opcodes:")
            for op in report["untested_opcodes"]:
                print(f"    {op}")
            print()

        # External ranges
        ext_names = [r["name"] for r in report["external_ranges"]]
        print(f"  External (skipped): {', '.join(ext_names)} "
              f"({report['external_opcode_count']} opcode slots)")
        print()

        # Sample vectors
        print("  Sample Test Vectors (first 5):")
        for v in vectors[:5]:
            exp_regs = v["expected"]["registers"]
            reg_str = ", ".join(f"{r}={val}" for r, val in exp_regs.items())
            print(f"    [{v['format']}] {v['mnemonic']:>7s}  "
                  f"{v['name']:<40s}  => {{{reg_str}}}")
        print()
        print(sep)

    # ═══════════════════════════════════════════════════════════════════════
    #  Generator methods  (one per logical group)
    # ═══════════════════════════════════════════════════════════════════════

    # ── Format A: system / control ─────────────────────────────────────────

    def _gen_format_a(self) -> List[Dict[str, Any]]:
        V = []

        # 1. HALT smoke
        V.append(build_vector(
            "HALT smoke: immediate halt",
            HALT, "system", "HALT", "A",
            [encode_a(HALT)],
            {},  # no register changes
            ["smoke", "system", "format-A", "pure"],
        ))

        # 2. NOP smoke
        V.append(build_vector(
            "NOP smoke: no operation then halt",
            NOP, "system", "NOP", "A",
            [encode_a(NOP), encode_a(HALT)],
            {},
            ["smoke", "system", "format-A", "pure"],
            desc="NOP; HALT — no side effects",
        ))

        # 3. NOP identity: R1=42 must survive NOP
        V.append(build_vector(
            "NOP identity: R1=42 unchanged",
            NOP, "system", "NOP", "A",
            [encode_d(MOVI, 1, 42), encode_a(NOP), encode_a(HALT)],
            {1: 42},
            ["identity", "system", "format-A", "pure"],
            desc="MOVI R1,42; NOP; HALT — R1 should still be 42",
        ))

        # 4. RET smoke (followed by HALT; RET itself does not halt)
        V.append(build_vector(
            "RET smoke: return instruction",
            RET, "control", "RET", "A",
            [encode_a(RET), encode_a(HALT)],
            {},
            ["smoke", "control", "format-A", "pure"],
            halted=False,
            desc="RET (stack empty — behaviour impl-defined); HALT",
        ))

        return V

    # ── Format B: INC / DEC / NOT / NEG / PUSH / POP ──────────────────────

    def _gen_format_b(self) -> List[Dict[str, Any]]:
        V = []

        # --- INC ---
        # 5. INC smoke
        V.append(build_vector(
            "INC smoke: R1=5 => R1=6",
            INC, "arithmetic", "INC", "B",
            [encode_d(MOVI, 1, 5), encode_b(INC, 1), encode_a(HALT)],
            {1: 6},
            ["smoke", "arithmetic", "format-B", "pure"],
        ))

        # 6. INC zero
        V.append(build_vector(
            "INC zero: R1=0 => R1=1",
            INC, "arithmetic", "INC", "B",
            [encode_d(MOVI, 1, 0), encode_b(INC, 1), encode_a(HALT)],
            {1: 1},
            ["zero", "arithmetic", "format-B", "pure"],
        ))

        # 7. INC boundary (255 -> 0 wrap)
        V.append(build_vector(
            "INC boundary: R1=255 => R1=0 (overflow)",
            INC, "arithmetic", "INC", "B",
            [encode_d(MOVI, 1, 255), encode_b(INC, 1), encode_a(HALT)],
            {1: 0},
            ["boundary", "arithmetic", "format-B", "pure"],
        ))

        # --- DEC ---
        # 8. DEC smoke
        V.append(build_vector(
            "DEC smoke: R1=5 => R1=4",
            DEC, "arithmetic", "DEC", "B",
            [encode_d(MOVI, 1, 5), encode_b(DEC, 1), encode_a(HALT)],
            {1: 4},
            ["smoke", "arithmetic", "format-B", "pure"],
        ))

        # 9. DEC zero (1 -> 0)
        V.append(build_vector(
            "DEC zero: R1=1 => R1=0",
            DEC, "arithmetic", "DEC", "B",
            [encode_d(MOVI, 1, 1), encode_b(DEC, 1), encode_a(HALT)],
            {1: 0},
            ["zero", "arithmetic", "format-B", "pure"],
        ))

        # 10. DEC boundary (0 -> 255 wrap)
        V.append(build_vector(
            "DEC boundary: R1=0 => R1=255 (underflow)",
            DEC, "arithmetic", "DEC", "B",
            [encode_d(MOVI, 1, 0), encode_b(DEC, 1), encode_a(HALT)],
            {1: 255},
            ["boundary", "arithmetic", "format-B", "pure"],
        ))

        # --- NOT ---
        # 11. NOT smoke
        V.append(build_vector(
            "NOT smoke: R1=0x0F => R1=0xF0",
            NOT, "logic", "NOT", "B",
            [encode_d(MOVI, 1, 0x0F), encode_b(NOT, 1), encode_a(HALT)],
            {1: 0xF0},
            ["smoke", "logic", "format-B", "pure"],
        ))

        # 12. NOT boundary
        V.append(build_vector(
            "NOT boundary: R1=0xFF => R1=0x00",
            NOT, "logic", "NOT", "B",
            [encode_d(MOVI, 1, 0xFF), encode_b(NOT, 1), encode_a(HALT)],
            {1: 0x00},
            ["boundary", "logic", "format-B", "pure"],
        ))

        # --- NEG ---
        # 13. NEG smoke (-5 in 2's complement)
        V.append(build_vector(
            "NEG smoke: R1=5 => R1=251 (two's complement -5)",
            NEG, "arithmetic", "NEG", "B",
            [encode_d(MOVI, 1, 5), encode_b(NEG, 1), encode_a(HALT)],
            {1: 251},
            ["smoke", "arithmetic", "format-B", "pure"],
        ))

        # 14. NEG zero
        V.append(build_vector(
            "NEG zero: R1=0 => R1=0",
            NEG, "arithmetic", "NEG", "B",
            [encode_d(MOVI, 1, 0), encode_b(NEG, 1), encode_a(HALT)],
            {1: 0},
            ["zero", "arithmetic", "format-B", "pure"],
        ))

        # --- PUSH / POP round-trip ---
        # 15. PUSH R1 then POP R2
        V.append(build_vector(
            "PUSH+POP round-trip: R1=42 push, R2 pop => R2=42",
            PUSH, "stack", "PUSH", "B",
            [encode_d(MOVI, 1, 42),
             encode_b(PUSH, 1),
             encode_d(MOVI, 2, 0),
             encode_b(POP, 2),
             encode_a(HALT)],
            {1: 42, 2: 42},
            ["smoke", "stack", "format-B", "pure"],
            desc="MOVI R1,42; PUSH R1; MOVI R2,0; POP R2; HALT",
        ))

        # 16. POP standalone smoke (pre-loaded stack)
        V.append(build_vector(
            "POP smoke: pre-loaded stack [99] => R1=99",
            POP, "stack", "POP", "B",
            [encode_d(MOVI, 1, 0),
             encode_b(POP, 1),
             encode_a(HALT)],
            {1: 99},
            ["smoke", "stack", "format-B", "requires-initial-stack"],
            initial_regs={},
            desc="POP R1; HALT — requires stack pre-loaded with [99]",
        ))

        return V

    # ── Format D: MOVI / ADDI / SUBI ──────────────────────────────────────

    def _gen_format_d(self) -> List[Dict[str, Any]]:
        V = []

        # --- MOVI ---
        # 16. MOVI smoke
        V.append(build_vector(
            "MOVI smoke: R1=42",
            MOVI, "data", "MOVI", "D",
            [encode_d(MOVI, 1, 42), encode_a(HALT)],
            {1: 42},
            ["smoke", "data", "format-D", "pure"],
        ))

        # 17. MOVI boundary (max imm8)
        V.append(build_vector(
            "MOVI boundary: R1=255",
            MOVI, "data", "MOVI", "D",
            [encode_d(MOVI, 1, 255), encode_a(HALT)],
            {1: 255},
            ["boundary", "data", "format-D", "pure"],
        ))

        # --- ADDI ---
        # 18. ADDI smoke
        V.append(build_vector(
            "ADDI smoke: R1=5 + 3 => R1=8",
            ADDI, "arithmetic", "ADDI", "D",
            [encode_d(MOVI, 1, 5), encode_d(ADDI, 1, 3), encode_a(HALT)],
            {1: 8},
            ["smoke", "arithmetic", "format-D", "pure"],
        ))

        # 19. ADDI zero
        V.append(build_vector(
            "ADDI zero: R1=5 + 0 => R1=5",
            ADDI, "arithmetic", "ADDI", "D",
            [encode_d(MOVI, 1, 5), encode_d(ADDI, 1, 0), encode_a(HALT)],
            {1: 5},
            ["zero", "arithmetic", "format-D", "pure"],
        ))

        # 20. ADDI boundary
        V.append(build_vector(
            "ADDI boundary: R1=255 + 1 => R1=0 (overflow)",
            ADDI, "arithmetic", "ADDI", "D",
            [encode_d(MOVI, 1, 255), encode_d(ADDI, 1, 1), encode_a(HALT)],
            {1: 0},
            ["boundary", "arithmetic", "format-D", "pure"],
        ))

        # --- SUBI ---
        # 21. SUBI smoke
        V.append(build_vector(
            "SUBI smoke: R1=8 - 3 => R1=5",
            SUBI, "arithmetic", "SUBI", "D",
            [encode_d(MOVI, 1, 8), encode_d(SUBI, 1, 3), encode_a(HALT)],
            {1: 5},
            ["smoke", "arithmetic", "format-D", "pure"],
        ))

        # 22. SUBI zero
        V.append(build_vector(
            "SUBI zero: R1=5 - 0 => R1=5",
            SUBI, "arithmetic", "SUBI", "D",
            [encode_d(MOVI, 1, 5), encode_d(SUBI, 1, 0), encode_a(HALT)],
            {1: 5},
            ["zero", "arithmetic", "format-D", "pure"],
        ))

        # 23. SUBI negative (3 - 5 wraps to 254)
        V.append(build_vector(
            "SUBI negative: R1=3 - 5 => R1=254 (wrap)",
            SUBI, "arithmetic", "SUBI", "D",
            [encode_d(MOVI, 1, 3), encode_d(SUBI, 1, 5), encode_a(HALT)],
            {1: 254},
            ["negative", "arithmetic", "format-D", "pure"],
        ))

        return V

    # ── Format E: arithmetic (ADD / SUB / MUL / DIV / MOD) ────────────────

    def _gen_format_e_arithmetic(self) -> List[Dict[str, Any]]:
        V = []

        # --- ADD ---
        # 24
        V.append(build_vector(
            "ADD smoke: R1=5, R2=3 => R1=8",
            ADD, "arithmetic", "ADD", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 3),
             encode_e(ADD, 1, 1, 2), encode_a(HALT)],
            {1: 8, 2: 3},
            ["smoke", "arithmetic", "format-E", "pure"],
        ))

        # 25
        V.append(build_vector(
            "ADD zero: R1=5, R2=0 => R1=5",
            ADD, "arithmetic", "ADD", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 0),
             encode_e(ADD, 1, 1, 2), encode_a(HALT)],
            {1: 5, 2: 0},
            ["zero", "arithmetic", "format-E", "pure"],
        ))

        # 26
        V.append(build_vector(
            "ADD boundary: R1=255, R2=1 => R1=0 (overflow)",
            ADD, "arithmetic", "ADD", "E",
            [encode_d(MOVI, 1, 255), encode_d(MOVI, 2, 1),
             encode_e(ADD, 1, 1, 2), encode_a(HALT)],
            {1: 0, 2: 1},
            ["boundary", "arithmetic", "format-E", "pure"],
        ))

        # --- SUB ---
        # 27
        V.append(build_vector(
            "SUB smoke: R1=10, R2=3 => R1=7",
            SUB, "arithmetic", "SUB", "E",
            [encode_d(MOVI, 1, 10), encode_d(MOVI, 2, 3),
             encode_e(SUB, 1, 1, 2), encode_a(HALT)],
            {1: 7, 2: 3},
            ["smoke", "arithmetic", "format-E", "pure"],
        ))

        # 28
        V.append(build_vector(
            "SUB negative: R1=3, R2=5 => R1=254 (wrap)",
            SUB, "arithmetic", "SUB", "E",
            [encode_d(MOVI, 1, 3), encode_d(MOVI, 2, 5),
             encode_e(SUB, 1, 1, 2), encode_a(HALT)],
            {1: 254, 2: 5},
            ["negative", "arithmetic", "format-E", "pure"],
        ))

        # 29
        V.append(build_vector(
            "SUB boundary: R1=0, R2=1 => R1=255 (underflow)",
            SUB, "arithmetic", "SUB", "E",
            [encode_d(MOVI, 1, 0), encode_d(MOVI, 2, 1),
             encode_e(SUB, 1, 1, 2), encode_a(HALT)],
            {1: 255, 2: 1},
            ["boundary", "arithmetic", "format-E", "pure"],
        ))

        # --- MUL ---
        # 30
        V.append(build_vector(
            "MUL smoke: R1=6, R2=7 => R1=42",
            MUL, "arithmetic", "MUL", "E",
            [encode_d(MOVI, 1, 6), encode_d(MOVI, 2, 7),
             encode_e(MUL, 1, 1, 2), encode_a(HALT)],
            {1: 42, 2: 7},
            ["smoke", "arithmetic", "format-E", "pure"],
        ))

        # 31
        V.append(build_vector(
            "MUL identity: R1=7, R2=1 => R1=7",
            MUL, "arithmetic", "MUL", "E",
            [encode_d(MOVI, 1, 7), encode_d(MOVI, 2, 1),
             encode_e(MUL, 1, 1, 2), encode_a(HALT)],
            {1: 7, 2: 1},
            ["identity", "arithmetic", "format-E", "pure"],
        ))

        # 32
        V.append(build_vector(
            "MUL zero: R1=7, R2=0 => R1=0",
            MUL, "arithmetic", "MUL", "E",
            [encode_d(MOVI, 1, 7), encode_d(MOVI, 2, 0),
             encode_e(MUL, 1, 1, 2), encode_a(HALT)],
            {1: 0, 2: 0},
            ["zero", "arithmetic", "format-E", "pure"],
        ))

        # --- DIV ---
        # 33
        V.append(build_vector(
            "DIV smoke: R1=15, R2=3 => R1=5",
            DIV, "arithmetic", "DIV", "E",
            [encode_d(MOVI, 1, 15), encode_d(MOVI, 2, 3),
             encode_e(DIV, 1, 1, 2), encode_a(HALT)],
            {1: 5, 2: 3},
            ["smoke", "arithmetic", "format-E", "pure"],
        ))

        # 34
        V.append(build_vector(
            "DIV identity: R1=7, R2=1 => R1=7",
            DIV, "arithmetic", "DIV", "E",
            [encode_d(MOVI, 1, 7), encode_d(MOVI, 2, 1),
             encode_e(DIV, 1, 1, 2), encode_a(HALT)],
            {1: 7, 2: 1},
            ["identity", "arithmetic", "format-E", "pure"],
        ))

        # --- MOD ---
        # 35
        V.append(build_vector(
            "MOD smoke: R1=10, R2=3 => R1=1",
            MOD, "arithmetic", "MOD", "E",
            [encode_d(MOVI, 1, 10), encode_d(MOVI, 2, 3),
             encode_e(MOD, 1, 1, 2), encode_a(HALT)],
            {1: 1, 2: 3},
            ["smoke", "arithmetic", "format-E", "pure"],
        ))

        return V

    # ── Format E: logic (AND / OR / XOR) ─────────────────────────────────

    def _gen_format_e_logic(self) -> List[Dict[str, Any]]:
        V = []

        # --- AND ---
        # 36
        V.append(build_vector(
            "AND smoke: R1=0xF0, R2=0x0F => R1=0x00",
            AND, "logic", "AND", "E",
            [encode_d(MOVI, 1, 0xF0), encode_d(MOVI, 2, 0x0F),
             encode_e(AND, 1, 1, 2), encode_a(HALT)],
            {1: 0x00, 2: 0x0F},
            ["smoke", "logic", "format-E", "pure"],
        ))

        # 37
        V.append(build_vector(
            "AND identity: R1=0xFF, R2=0xFF => R1=0xFF",
            AND, "logic", "AND", "E",
            [encode_d(MOVI, 1, 0xFF), encode_d(MOVI, 2, 0xFF),
             encode_e(AND, 1, 1, 2), encode_a(HALT)],
            {1: 0xFF, 2: 0xFF},
            ["identity", "logic", "format-E", "pure"],
        ))

        # --- OR ---
        # 38
        V.append(build_vector(
            "OR smoke: R1=0xF0, R2=0x0F => R1=0xFF",
            OR, "logic", "OR", "E",
            [encode_d(MOVI, 1, 0xF0), encode_d(MOVI, 2, 0x0F),
             encode_e(OR, 1, 1, 2), encode_a(HALT)],
            {1: 0xFF, 2: 0x0F},
            ["smoke", "logic", "format-E", "pure"],
        ))

        # 39
        V.append(build_vector(
            "OR identity: R1=0xAA, R2=0x00 => R1=0xAA",
            OR, "logic", "OR", "E",
            [encode_d(MOVI, 1, 0xAA), encode_d(MOVI, 2, 0x00),
             encode_e(OR, 1, 1, 2), encode_a(HALT)],
            {1: 0xAA, 2: 0x00},
            ["identity", "logic", "format-E", "pure"],
        ))

        # --- XOR ---
        # 40
        V.append(build_vector(
            "XOR smoke: R1=0xFF, R2=0x0F => R1=0xF0",
            XOR, "logic", "XOR", "E",
            [encode_d(MOVI, 1, 0xFF), encode_d(MOVI, 2, 0x0F),
             encode_e(XOR, 1, 1, 2), encode_a(HALT)],
            {1: 0xF0, 2: 0x0F},
            ["smoke", "logic", "format-E", "pure"],
        ))

        # 41
        V.append(build_vector(
            "XOR zero: R1=0xAA, R2=0xAA => R1=0x00",
            XOR, "logic", "XOR", "E",
            [encode_d(MOVI, 1, 0xAA), encode_d(MOVI, 2, 0xAA),
             encode_e(XOR, 1, 1, 2), encode_a(HALT)],
            {1: 0x00, 2: 0xAA},
            ["zero", "logic", "format-E", "pure"],
        ))

        return V

    # ── Format E: comparison (CMP_EQ / CMP_LT / CMP_GT / CMP_NE) ─────────

    def _gen_format_e_comparison(self) -> List[Dict[str, Any]]:
        V = []

        # CMP_EQ: rd = 1 if rs1 == rs2 else 0

        # 42
        V.append(build_vector(
            "CMP_EQ true: R1=5 == R2=5 => R3=1",
            CMP_EQ, "comparison", "CMP_EQ", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 5),
             encode_e(CMP_EQ, 3, 1, 2), encode_a(HALT)],
            {1: 5, 2: 5, 3: 1},
            ["smoke", "comparison", "format-E", "pure"],
        ))

        # 43
        V.append(build_vector(
            "CMP_EQ false: R1=5 != R2=3 => R3=0",
            CMP_EQ, "comparison", "CMP_EQ", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 3),
             encode_e(CMP_EQ, 3, 1, 2), encode_a(HALT)],
            {1: 5, 2: 3, 3: 0},
            ["smoke", "comparison", "format-E", "pure"],
        ))

        # CMP_LT: rd = 1 if signed(rs1) < signed(rs2) else 0

        # 44
        V.append(build_vector(
            "CMP_LT true: R1=3 < R2=5 => R3=1",
            CMP_LT, "comparison", "CMP_LT", "E",
            [encode_d(MOVI, 1, 3), encode_d(MOVI, 2, 5),
             encode_e(CMP_LT, 3, 1, 2), encode_a(HALT)],
            {1: 3, 2: 5, 3: 1},
            ["smoke", "comparison", "format-E", "pure"],
        ))

        # 45
        V.append(build_vector(
            "CMP_LT false: R1=5 >= R2=3 => R3=0",
            CMP_LT, "comparison", "CMP_LT", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 3),
             encode_e(CMP_LT, 3, 1, 2), encode_a(HALT)],
            {1: 5, 2: 3, 3: 0},
            ["smoke", "comparison", "format-E", "pure"],
        ))

        # CMP_GT: rd = 1 if signed(rs1) > signed(rs2) else 0

        # 46
        V.append(build_vector(
            "CMP_GT true: R1=5 > R2=3 => R3=1",
            CMP_GT, "comparison", "CMP_GT", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 3),
             encode_e(CMP_GT, 3, 1, 2), encode_a(HALT)],
            {1: 5, 2: 3, 3: 1},
            ["smoke", "comparison", "format-E", "pure"],
        ))

        # CMP_NE: rd = 1 if rs1 != rs2 else 0

        # 47
        V.append(build_vector(
            "CMP_NE true: R1=5 != R2=3 => R3=1",
            CMP_NE, "comparison", "CMP_NE", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 3),
             encode_e(CMP_NE, 3, 1, 2), encode_a(HALT)],
            {1: 5, 2: 3, 3: 1},
            ["smoke", "comparison", "format-E", "pure"],
        ))

        return V

    # ── Format E: float (FADD / FSUB / FMUL / FDIV) ──────────────────────

    def _gen_format_e_float(self) -> List[Dict[str, Any]]:
        V = []

        # Float ops require pre-loaded 32-bit registers (IEEE-754 single).
        # We use initial_registers since MOVI/MOVI16 cannot construct
        # arbitrary 32-bit float bit patterns in a single instruction.

        # 48  FADD: 1.5 + 2.5 = 4.0
        bits_1_5 = float_to_bits(1.5)
        bits_2_5 = float_to_bits(2.5)
        bits_4_0 = float_to_bits(4.0)
        V.append(build_vector(
            "FADD smoke: 1.5 + 2.5 = 4.0",
            FADD, "float", "FADD", "E",
            [encode_e(FADD, 1, 2, 3), encode_a(HALT)],
            {1: bits_4_0, 2: bits_1_5, 3: bits_2_5},
            ["smoke", "float", "format-E", "requires-initial-regs"],
            initial_regs={2: bits_1_5, 3: bits_2_5},
            desc="FADD R1,R2,R3 — registers pre-loaded with float bit patterns",
        ))

        # 49  FSUB: 5.0 - 3.0 = 2.0
        bits_5_0 = float_to_bits(5.0)
        bits_3_0 = float_to_bits(3.0)
        bits_2_0 = float_to_bits(2.0)
        V.append(build_vector(
            "FSUB smoke: 5.0 - 3.0 = 2.0",
            FSUB, "float", "FSUB", "E",
            [encode_e(FSUB, 1, 2, 3), encode_a(HALT)],
            {1: bits_2_0, 2: bits_5_0, 3: bits_3_0},
            ["smoke", "float", "format-E", "requires-initial-regs"],
            initial_regs={2: bits_5_0, 3: bits_3_0},
        ))

        # 50  FMUL: 2.0 * 3.0 = 6.0
        bits_6_0 = float_to_bits(6.0)
        V.append(build_vector(
            "FMUL smoke: 2.0 * 3.0 = 6.0",
            FMUL, "float", "FMUL", "E",
            [encode_e(FMUL, 1, 2, 3), encode_a(HALT)],
            {1: bits_6_0, 2: bits_2_0, 3: bits_3_0},
            ["smoke", "float", "format-E", "requires-initial-regs"],
            initial_regs={2: bits_2_0, 3: bits_3_0},
        ))

        # 51  FDIV: 10.0 / 2.0 = 5.0
        bits_10_0 = float_to_bits(10.0)
        V.append(build_vector(
            "FDIV smoke: 10.0 / 2.0 = 5.0",
            FDIV, "float", "FDIV", "E",
            [encode_e(FDIV, 1, 2, 3), encode_a(HALT)],
            {1: bits_5_0, 2: bits_10_0, 3: bits_2_0},
            ["smoke", "float", "format-E", "requires-initial-regs"],
            initial_regs={2: bits_10_0, 3: bits_2_0},
        ))

        return V

    # ── Format E: memory (LOAD / STORE / MOV / SWP) ──────────────────────

    def _gen_format_e_memory(self) -> List[Dict[str, Any]]:
        V = []

        # LOAD rd, rs1, rs2 → rd = memory[rs1]  (rs2 unused in simple model)

        # 52
        V.append(build_vector(
            "LOAD smoke: R1 = memory[R2=5] = 99",
            LOAD, "memory", "LOAD", "E",
            [encode_d(MOVI, 2, 5),
             encode_e(LOAD, 1, 2, 0),
             encode_a(HALT)],
            {1: 99, 2: 5},
            ["smoke", "memory", "format-E", "requires-initial-mem"],
            initial_mem={5: 99},
        ))

        # STORE rd, rs1, rs2 → memory[rs1] = rd

        # 53
        V.append(build_vector(
            "STORE smoke: memory[R2=5] = R1=42",
            STORE, "memory", "STORE", "E",
            [encode_d(MOVI, 1, 42), encode_d(MOVI, 2, 5),
             encode_e(STORE, 1, 2, 0),
             encode_a(HALT)],
            {1: 42, 2: 5},
            ["smoke", "memory", "format-E", "requires-mem-check"],
            expected_mem={5: 42},
        ))

        # MOV rd, rs1, rs2 → rd = rs1  (rs2 unused)

        # 54
        V.append(build_vector(
            "MOV smoke: R2 = R1 = 42",
            MOV, "data", "MOV", "E",
            [encode_d(MOVI, 1, 42),
             encode_e(MOV, 2, 1, 0),
             encode_a(HALT)],
            {1: 42, 2: 42},
            ["smoke", "data", "format-E", "pure"],
        ))

        # SWP rd, rs1, rs2 → swap rd and rs1  (rs2 unused)

        # 55
        V.append(build_vector(
            "SWP smoke: swap R1=5, R2=10 => R1=10, R2=5",
            SWP, "data", "SWP", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 10),
             encode_e(SWP, 1, 2, 0),
             encode_a(HALT)],
            {1: 10, 2: 5},
            ["smoke", "data", "format-E", "pure"],
        ))

        return V

    # ── Format E: control (JZ / JNZ / JLT / JGT) ─────────────────────────

    def _gen_format_e_control(self) -> List[Dict[str, Any]]:
        V = []
        # Conditional jumps: Format E [opcode][rd][rs1][rs2]
        # Model:  rd = 1 if condition true else 0
        #   JZ  → condition: rs1 == 0
        #   JNZ → condition: rs1 != 0
        #   JLT → condition: signed(rs1) < signed(rs2)
        #   JGT → condition: signed(rs1) > signed(rs2)
        # (Jump-target semantics tested separately; here we verify flag logic.)

        # --- JZ ---
        # 56  taken
        V.append(build_vector(
            "JZ taken: R1=0 => R3=1",
            JZ, "control", "JZ", "E",
            [encode_d(MOVI, 1, 0),
             encode_e(JZ, 3, 1, 2),
             encode_a(HALT)],
            {1: 0, 3: 1},
            ["smoke", "control", "format-E", "pure"],
        ))

        # 57  not taken
        V.append(build_vector(
            "JZ not-taken: R1=5 => R3=0",
            JZ, "control", "JZ", "E",
            [encode_d(MOVI, 1, 5),
             encode_e(JZ, 3, 1, 2),
             encode_a(HALT)],
            {1: 5, 3: 0},
            ["smoke", "control", "format-E", "pure"],
        ))

        # --- JNZ ---
        # 58
        V.append(build_vector(
            "JNZ taken: R1=5 => R3=1",
            JNZ, "control", "JNZ", "E",
            [encode_d(MOVI, 1, 5),
             encode_e(JNZ, 3, 1, 2),
             encode_a(HALT)],
            {1: 5, 3: 1},
            ["smoke", "control", "format-E", "pure"],
        ))

        # --- JLT ---
        # 59
        V.append(build_vector(
            "JLT taken: R1=3 < R2=5 => R3=1",
            JLT, "control", "JLT", "E",
            [encode_d(MOVI, 1, 3), encode_d(MOVI, 2, 5),
             encode_e(JLT, 3, 1, 2),
             encode_a(HALT)],
            {1: 3, 2: 5, 3: 1},
            ["smoke", "control", "format-E", "pure"],
        ))

        # --- JGT ---
        # 60
        V.append(build_vector(
            "JGT taken: R1=5 > R2=3 => R3=1",
            JGT, "control", "JGT", "E",
            [encode_d(MOVI, 1, 5), encode_d(MOVI, 2, 3),
             encode_e(JGT, 3, 1, 2),
             encode_a(HALT)],
            {1: 5, 2: 3, 3: 1},
            ["smoke", "control", "format-E", "pure"],
        ))

        return V

    # ── Format F: MOVI16 / JMP / JAL ──────────────────────────────────────

    def _gen_format_f(self) -> List[Dict[str, Any]]:
        V = []

        # --- MOVI16 ---
        # 61
        V.append(build_vector(
            "MOVI16 smoke: R1=1000",
            MOVI16, "data", "MOVI16", "F",
            [encode_f(MOVI16, 1, 1000), encode_a(HALT)],
            {1: 1000},
            ["smoke", "data", "format-F", "pure"],
        ))

        # 62
        V.append(build_vector(
            "MOVI16 boundary: R1=65535 (0xFFFF)",
            MOVI16, "data", "MOVI16", "F",
            [encode_f(MOVI16, 1, 0xFFFF), encode_a(HALT)],
            {1: 65535},
            ["boundary", "data", "format-F", "pure"],
        ))

        # --- JMP  (Format F: [opcode][rd][imm16_lo][imm16_hi] → pc = imm16) ---

        # 63  Jump over poison instruction
        # Layout: JMP R0, 7  |  MOVI R1, 0xFF  |  HALT
        #         offset 0-3 |  offset 4-6    |  offset 7
        jmp_target = 7  # absolute address of HALT
        V.append(build_vector(
            "JMP smoke: jump over poison, R1 stays 0",
            JMP, "control", "JMP", "F",
            [encode_f(JMP, 0, jmp_target),
             encode_d(MOVI, 1, 0xFF),   # poison — should be skipped
             encode_a(HALT)],
            {1: 0},  # MOVI skipped
            ["smoke", "control", "format-F", "pure"],
            desc=f"JMP R0,{jmp_target}; MOVI R1,0xFF (skipped); HALT @{jmp_target}",
        ))

        # --- JAL  (Format F: rd = pc+4, pc = imm16) ---

        # 64  Jump-and-link
        # Layout: JAL R1, 7  |  MOVI R2, 0xFF  |  HALT
        #         offset 0-3 |  offset 4-6    |  offset 7
        jal_target = 7
        V.append(build_vector(
            f"JAL smoke: R1=return_addr(4), jump to {jal_target}",
            JAL, "control", "JAL", "F",
            [encode_f(JAL, 1, jal_target),
             encode_d(MOVI, 2, 0xFF),   # poison — should be skipped
             encode_a(HALT)],
            {1: 4, 2: 0},  # R1 = return address (address after JAL)
            ["smoke", "control", "format-F", "pure"],
            desc=f"JAL R1,{jal_target}; R1 should be 4 (return addr); HALT @{jal_target}",
        ))

        return V

    # ── Format G: LOADOFF / STOREOFF ──────────────────────────────────────

    def _gen_format_g(self) -> List[Dict[str, Any]]:
        V = []

        # LOADOFF rd, rs1, imm16 → rd = memory[rs1 + imm16]

        # 65
        V.append(build_vector(
            "LOADOFF smoke: R1 = memory[R2=0 + 10] = 99",
            LOADOFF, "memory", "LOADOFF", "G",
            [encode_d(MOVI, 2, 0),
             encode_g(LOADOFF, 1, 2, 10),
             encode_a(HALT)],
            {1: 99, 2: 0},
            ["smoke", "memory", "format-G", "requires-initial-mem"],
            initial_mem={10: 99},
        ))

        # STOREOFF rd, rs1, imm16 → memory[rs1 + imm16] = rd

        # 66
        V.append(build_vector(
            "STOREOFF smoke: memory[R2=0 + 10] = R1=42",
            STOREOFF, "memory", "STOREOFF", "G",
            [encode_d(MOVI, 1, 42), encode_d(MOVI, 2, 0),
             encode_g(STOREOFF, 1, 2, 10),
             encode_a(HALT)],
            {1: 42, 2: 0},
            ["smoke", "memory", "format-G", "requires-mem-check"],
            expected_mem={10: 42},
        ))

        return V


# ═══════════════════════════════════════════════════════════════════════════════
# Bytecode self-check  (run on import to catch encoding bugs)
# ═══════════════════════════════════════════════════════════════════════════════

def _self_check() -> None:
    """Verify a handful of critical bytecode encodings."""
    assert encode_a(HALT) == b'\x00', "HALT encoding"
    assert encode_b(INC, 3) == b'\x08\x03', "INC R3 encoding"
    assert encode_d(MOVI, 1, 42) == b'\x18\x01\x2a', "MOVI R1,42 encoding"
    assert encode_e(ADD, 1, 1, 2) == b'\x20\x01\x01\x02', "ADD R1,R1,R2 encoding"
    assert encode_f(MOVI16, 1, 1000) == b'\x40\x01\xe8\x03', "MOVI16 R1,1000"
    assert encode_g(LOADOFF, 1, 2, 10) == b'\x48\x01\x02\x0a\x00', "LOADOFF encoding"

    # Verify the canonical ADD smoke test bytecode
    add_smoke = to_hex([
        encode_d(MOVI, 1, 5),
        encode_d(MOVI, 2, 3),
        encode_e(ADD, 1, 1, 2),
        encode_a(HALT),
    ])
    assert add_smoke == "1801051802032001010200", f"ADD smoke hex: {add_smoke}"


_self_check()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main(argv: Optional[List[str]] = None) -> int:
    """Parse CLI args and run the generator."""
    if argv is None:
        argv = sys.argv[1:]

    show_demo = True
    json_path: Optional[str] = None
    pytest_path: Optional[str] = None
    category_filter: Optional[str] = None

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ('--json', '-j') and i + 1 < len(argv):
            json_path = argv[i + 1]
            show_demo = False
            i += 2
        elif arg in ('--pytest', '-p') and i + 1 < len(argv):
            pytest_path = argv[i + 1]
            show_demo = False
            i += 2
        elif arg in ('--category', '-c') and i + 1 < len(argv):
            category_filter = argv[i + 1]
            i += 2
        elif arg in ('--help', '-h'):
            print(__doc__)
            return 0
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            return 1

    gen = ConformanceTestGenerator()

    if category_filter:
        vectors = gen.generate_for_category(category_filter)
    else:
        vectors = gen.generate_all()

    if json_path:
        gen.export_json(vectors, json_path)

    if pytest_path:
        gen.export_pytest(vectors, pytest_path)

    if show_demo or (not json_path and not pytest_path):
        gen.run_demo()
        # Also print coverage JSON for machine parsing
        report = gen.coverage_report(vectors)
        print()
        print("  Coverage JSON:")
        print("  " + json.dumps(report, indent=2).replace("\n", "\n  "))

    return 0


if __name__ == "__main__":
    sys.exit(main())
