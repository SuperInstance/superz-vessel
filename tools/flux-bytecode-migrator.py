#!/usr/bin/env python3
"""
flux-bytecode-migrator — Translate FLUX bytecode between opcode numbering systems.

The FLUX ecosystem has two incompatible ISA numbering systems:
  1. Runtime (opcodes.py): ~80 opcodes, the actual executing VM
  2. Unified Spec (isa_unified.py): ~200 opcodes, the convergence target

Usage:
    python migrate.py --from runtime --to unified --input program.bin --output out.bin
    python migrate.py --validate program.bin
    python migrate.py --mnemonic-map
"""

import sys
import argparse
from enum import IntEnum
from typing import Dict, Tuple, List


class RuntimeOp(IntEnum):
    NOP = 0x00; MOV = 0x01; LOAD = 0x02; STORE = 0x03
    JMP = 0x04; JZ = 0x05; JNZ = 0x06; CALL = 0x07
    IADD = 0x08; ISUB = 0x09; IMUL = 0x0A; IDIV = 0x0B
    IMOD = 0x0C; INEG = 0x0D; INC = 0x0E; DEC = 0x0F
    IAND = 0x10; IOR = 0x11; IXOR = 0x12; INOT = 0x13
    ISHL = 0x14; ISHR = 0x15; ROTL = 0x16; ROTR = 0x17
    ICMP = 0x18; IEQ = 0x19; ILT = 0x1A; ILE = 0x1B
    IGT = 0x1C; IGE = 0x1D; TEST = 0x1E; SETCC = 0x1F
    PUSH = 0x20; POP = 0x21; DUP = 0x22; SWAP = 0x23
    ROT = 0x24; ENTER = 0x25; LEAVE = 0x26; ALLOCA = 0x27
    RET = 0x28; CALL_IND = 0x29; TAILCALL = 0x2A; MOVI = 0x2B
    IREM = 0x2C; CMP = 0x2D; JE = 0x2E; JNE = 0x2F
    REGION_CREATE = 0x30; REGION_DESTROY = 0x31; REGION_TRANSFER = 0x32
    MEMCOPY = 0x33; MEMSET = 0x34; MEMCMP = 0x35
    JL = 0x36; JGE = 0x37
    CAST = 0x38; BOX = 0x39; UNBOX = 0x3A; CHECK_TYPE = 0x3B; CHECK_BOUNDS = 0x3C
    FADD = 0x40; FSUB = 0x41; FMUL = 0x42; FDIV = 0x43
    FNEG = 0x44; FABS = 0x45; FMIN = 0x46; FMAX = 0x47
    FEQ = 0x48; FLT = 0x49; FLE = 0x4A; FGT = 0x4B; FGE = 0x4C
    JG = 0x4D; JLE = 0x4E; LOAD8 = 0x4F
    VLOAD = 0x50; VSTORE = 0x51; VADD = 0x52; VSUB = 0x53
    VMUL = 0x54; VDIV = 0x55; VFMA = 0x56; STORE8 = 0x57
    TELL = 0x60; ASK = 0x61; DELEGATE = 0x62; DELEGATE_RESULT = 0x63
    REPORT_STATUS = 0x64; REQUEST_OVERRIDE = 0x65; BROADCAST = 0x66
    REDUCE = 0x67; DECLARE_INTENT = 0x68; ASSERT_GOAL = 0x69
    VERIFY_OUTCOME = 0x6A; EXPLAIN_FAILURE = 0x6B; SET_PRIORITY = 0x6C
    TRUST_CHECK = 0x70; TRUST_UPDATE = 0x71; TRUST_QUERY = 0x72; REVOKE_TRUST = 0x73
    CAP_REQUIRE = 0x74; CAP_REQUEST = 0x75; CAP_GRANT = 0x76; CAP_REVOKE = 0x77
    BARRIER = 0x78; SYNC_CLOCK = 0x79; FORMATION_UPDATE = 0x7A; EMERGENCY_STOP = 0x7B
    HALT = 0x80; YIELD = 0x81; RESOURCE_ACQUIRE = 0x82; RESOURCE_RELEASE = 0x83
    DEBUG_BREAK = 0x84


class UnifiedOp(IntEnum):
    HALT = 0x00; NOP = 0x01; RET = 0x02; IRET = 0x03
    BRK = 0x04; WFI = 0x05; RESET = 0x06; SYN = 0x07
    INC = 0x08; DEC = 0x09; NOT = 0x0A; NEG = 0x0B
    PUSH = 0x0C; POP = 0x0D; CONF_LD = 0x0E; CONF_ST = 0x0F
    SYS = 0x10; TRAP = 0x11; DBG = 0x12; CLF = 0x13
    SEMA = 0x14; YIELD_U = 0x15; CACHE = 0x16; STRIPCF = 0x17
    MOVI = 0x18; ADDI = 0x19; SUBI = 0x1A; ANDI = 0x1B
    ORI = 0x1C; XORI = 0x1D; SHLI = 0x1E; SHRI = 0x1F
    ADD = 0x20; SUB = 0x21; MUL = 0x22; DIV = 0x23; MOD = 0x24
    AND = 0x25; OR = 0x26; XOR = 0x27; SHL = 0x28; SHR = 0x29
    MIN = 0x2A; MAX = 0x2B; CMP_EQ = 0x2C; CMP_LT = 0x2D
    CMP_GT = 0x2E; CMP_NE = 0x2F
    FADD = 0x30; FSUB = 0x31; FMUL = 0x32; FDIV = 0x33
    FMIN = 0x34; FMAX = 0x35; FTOI = 0x36; ITOF = 0x37
    LOAD = 0x38; STORE = 0x39; MOV = 0x3A; SWP = 0x3B
    JZ = 0x3C; JNZ = 0x3D; JLT = 0x3E; JGT = 0x3F
    MOVI16 = 0x40; ADDI16 = 0x41; SUBI16 = 0x42; JMP = 0x43
    JAL = 0x44; CALL = 0x45; LOOP = 0x46; SELECT = 0x47
    LOADOFF = 0x48; STOREOF = 0x49; LOADI = 0x4A; STOREI = 0x4B
    ENTER = 0x4C; LEAVE = 0x4D; COPY = 0x4E; FILL = 0x4F
    TELL = 0x50; ASK = 0x51; DELEG = 0x52; BCAST = 0x53
    ACCEPT = 0x54; DECLINE = 0x55; REPORT = 0x56; MERGE = 0x57
    FORK = 0x58; JOIN = 0x59; SIGNAL = 0x5A; AWAIT = 0x5B
    TRUST = 0x5C; DISCOV = 0x5D; STATUS = 0x5E; HEARTBT = 0x5F
    C_ADD = 0x60; C_SUB = 0x61; C_MUL = 0x62; C_DIV = 0x63
    C_FADD = 0x64; C_FSUB = 0x65; C_FMUL = 0x66; C_FDIV = 0x67
    C_MERGE = 0x68; C_THRESH = 0x69; C_BOOST = 0x6A; C_DECAY = 0x6B
    C_SOURCE = 0x6C; C_CALIB = 0x6D; C_EXPLY = 0x6E; C_VOTE = 0x6F
    ABS = 0x90; SIGN = 0x91; SQRT = 0x92; POW = 0x93; LOG2 = 0x94
    FSQRT = 0x9D; FSIN = 0x9E; FCOS = 0x9F
    JMPL = 0xE0; JALL = 0xE1; CALLL = 0xE2; TAIL = 0xE3; TRACE = 0xE9
    HALT_ERR = 0xF0; DUMP = 0xF2; ASSERT = 0xF3; ID = 0xF4; VER = 0xF5
    ILLEGAL = 0xFF


SEMANTIC_MAP = {
    "NOP": "NOP", "HALT": "HALT", "RET": "RET", "YIELD": "YIELD_U",
    "DEBUG_BREAK": "BRK", "EMERGENCY_STOP": "HALT_ERR",
    "IADD": "ADD", "ISUB": "SUB", "IMUL": "MUL", "IDIV": "DIV",
    "IMOD": "MOD", "IREM": "MOD", "INC": "INC", "DEC": "DEC",
    "INEG": "NEG", "INOT": "NOT", "IAND": "AND", "IOR": "OR",
    "IXOR": "XOR", "ISHL": "SHL", "ISHR": "SHR",
    "IEQ": "CMP_EQ", "ILT": "CMP_LT", "IGT": "CMP_GT",
    "PUSH": "PUSH", "POP": "POP", "ENTER": "ENTER", "LEAVE": "LEAVE",
    "LOAD": "LOAD", "STORE": "STORE", "MEMCOPY": "COPY", "MEMSET": "FILL",
    "FADD": "FADD", "FSUB": "FSUB", "FMUL": "FMUL", "FDIV": "FDIV",
    "FNEG": "NEG", "FABS": "ABS", "FMIN": "FMIN", "FMAX": "FMAX",
    "JMP": "JMP", "JZ": "JZ", "JNZ": "JNZ", "JL": "JLT", "JG": "JGT",
    "CALL": "CALL", "MOVI": "MOVI",
    "TELL": "TELL", "ASK": "ASK", "DELEGATE": "DELEG", "BROADCAST": "BCAST",
}

FMT_A = {RuntimeOp.NOP, RuntimeOp.HALT, RuntimeOp.YIELD, RuntimeOp.DUP, RuntimeOp.SWAP, RuntimeOp.DEBUG_BREAK, RuntimeOp.EMERGENCY_STOP}
FMT_B = {RuntimeOp.INC, RuntimeOp.DEC, RuntimeOp.ENTER, RuntimeOp.LEAVE, RuntimeOp.PUSH, RuntimeOp.POP, RuntimeOp.INEG, RuntimeOp.FNEG, RuntimeOp.INOT}
FMT_D = {RuntimeOp.JMP, RuntimeOp.JZ, RuntimeOp.JNZ, RuntimeOp.JE, RuntimeOp.JNE, RuntimeOp.JG, RuntimeOp.JL, RuntimeOp.JGE, RuntimeOp.JLE, RuntimeOp.MOVI, RuntimeOp.CALL}
FMT_E = {RuntimeOp.VFMA, RuntimeOp.IADD, RuntimeOp.ISUB, RuntimeOp.IMUL, RuntimeOp.IDIV, RuntimeOp.IMOD, RuntimeOp.IREM, RuntimeOp.IAND, RuntimeOp.IOR, RuntimeOp.IXOR, RuntimeOp.ISHL, RuntimeOp.ISHR, RuntimeOp.FADD, RuntimeOp.FSUB, RuntimeOp.FMUL, RuntimeOp.FDIV, RuntimeOp.FMIN, RuntimeOp.FMAX}


def get_fmt(op_byte: int) -> str:
    if op_byte in FMT_A: return "A"
    if op_byte in FMT_B: return "B"
    if op_byte in FMT_D: return "D"
    if op_byte in FMT_E: return "E"
    if op_byte >= 0x60: return "G"
    return "C"


class MigrationResult:
    def __init__(self):
        self.output_bytes: List[int] = []
        self.translated = 0
        self.failed = 0
        self.no_equivalent: List[Tuple[int, str]] = []
        self.warnings: List[str] = []
        self.format_changes: List[str] = []

    @property
    def output(self) -> bytes:
        return bytes(self.output_bytes)

    def __repr__(self):
        return f"MigrationResult(OK: {self.translated} translated, {self.failed} failed, {len(self.warnings)} warnings)"


def migrate_runtime_to_unified(bytecode: bytes) -> MigrationResult:
    result = MigrationResult()
    pc = 0
    while pc < len(bytecode):
        op_byte = bytecode[pc]
        fmt = get_fmt(op_byte)
        try:
            rt_name = RuntimeOp(op_byte).name
        except ValueError:
            result.warnings.append(f"Unknown 0x{op_byte:02X} at pc={pc}")
            result.output_bytes.append(op_byte)
            pc += 1
            result.failed += 1
            continue

        uni_name = SEMANTIC_MAP.get(rt_name)
        if uni_name is None:
            result.no_equivalent.append((op_byte, rt_name))
            sizes = {"A":1,"B":2,"C":3,"D":4,"E":4,"G":4}
            result.output_bytes.extend(bytecode[pc:pc+sizes.get(fmt,1)])
            pc += sizes.get(fmt, 1)
            result.failed += 1
            continue

        try:
            uni_op = UnifiedOp[uni_name]
        except KeyError:
            result.warnings.append(f"{uni_name} not in UnifiedOp")
            result.output_bytes.append(op_byte)
            pc += 1
            result.failed += 1
            continue

        if fmt == "A":
            result.output_bytes.append(uni_op)
            pc += 1
        elif fmt == "B":
            result.output_bytes.extend([uni_op, bytecode[pc+1]])
            pc += 2
        elif fmt == "C":
            if pc + 2 < len(bytecode):
                result.output_bytes.extend([uni_op, bytecode[pc+1], bytecode[pc+2], 0x00])
                result.format_changes.append(f"{rt_name}: C(3B)->E(4B)")
                pc += 3
            else:
                result.warnings.append(f"Truncated C-format {rt_name} at pc={pc}")
                result.output_bytes.append(uni_op)
                pc += 1
                result.failed += 1
                continue
        elif fmt == "D":
            if pc + 3 < len(bytecode):
                result.output_bytes.extend([uni_op] + list(bytecode[pc+1:pc+4]))
                pc += 4
            else:
                result.warnings.append(f"Truncated D-format {rt_name} at pc={pc}")
                result.output_bytes.append(uni_op)
                pc += 1
                result.failed += 1
                continue
        elif fmt == "E":
            if pc + 3 < len(bytecode):
                result.output_bytes.extend([uni_op] + list(bytecode[pc+1:pc+4]))
                pc += 4
            else:
                result.warnings.append(f"Truncated E-format {rt_name} at pc={pc}")
                result.output_bytes.append(uni_op)
                pc += 1
                result.failed += 1
                continue
        else:
            result.output_bytes.extend(bytecode[pc:pc+4])
            pc += 4
            result.failed += 1
            continue
        result.translated += 1
    return result


def validate_bytecode(bytecode: bytes) -> Dict:
    if not bytecode:
        return {"system": "unknown", "confidence": 0, "reason": "empty"}
    rt_set = set(o.value for o in RuntimeOp)
    un_set = set(o.value for o in UnifiedOp)
    rt_hits = sum(1 for b in bytecode if b in rt_set)
    un_hits = sum(1 for b in bytecode if b in un_set)
    rs, us = 0, 0
    if bytecode[-1] == 0x80: rs += 3
    if bytecode[-1] == 0x00: us += 3
    if bytecode[0] == 0x00: rs += 2
    if bytecode[0] == 0x01: us += 2
    if rt_hits > un_hits: rs += 2
    elif un_hits > rt_hits: us += 2
    if rs > us:
        return {"system": "runtime", "confidence": min(rs/7*100,100), "score": f"{rs}:{us}", "size": len(bytecode), "rt_hits": rt_hits, "un_hits": un_hits}
    elif us > rs:
        return {"system": "unified", "confidence": min(us/7*100,100), "score": f"{us}:{rs}", "size": len(bytecode), "rt_hits": rt_hits, "un_hits": un_hits}
    return {"system": "ambiguous", "confidence": 50, "score": f"{rs}:{rs}", "size": len(bytecode)}


def print_mnemonic_map():
    print("=" * 85)
    print("FLUX BYTECODE MIGRATION MAP: Runtime <-> Unified")
    print("=" * 85)
    print(f"{'RT':<6} {'Runtime':<22} {'':>4} {'Unified':<22} {'UN':<6} {'Status'}")
    print("-" * 85)
    ok, fail = 0, 0
    for rt_op in RuntimeOp:
        nm = SEMANTIC_MAP.get(rt_op.name)
        st = "OK" if nm else "NO_EQUIV"
        uh = ""
        if nm:
            try:
                uh = f"0x{UnifiedOp[nm].value:02X}"
                ok += 1
            except KeyError:
                st = "MISS"; nm += "*"
        else:
            fail += 1; nm = "---"
        print(f"0x{rt_op.value:02X}   {rt_op.name:<22} {'->':>4} {nm:<22} {uh:<6} {st}")
    print(f"\nTotal: {len(RuntimeOp)} | Translatable: {ok} | No equivalent: {fail}")
    print("=" * 85)
    print("FORMAT DIFFERENCES:")
    print(f"  A: 1B=1B OK | B: 2B=2B OK | C: 3B!=2B CONFLICT | D: 4B!=3B CONFLICT | E: 4B=4B OK | G: var!=5B CONFLICT")


def main():
    p = argparse.ArgumentParser(description="FLUX Bytecode Migrator")
    p.add_argument("--from", dest="fr", choices=["runtime","unified"])
    p.add_argument("--to", dest="to", choices=["runtime","unified"])
    p.add_argument("--input","-i")
    p.add_argument("--output","-o")
    p.add_argument("--validate","-v", action="store_true")
    p.add_argument("--mnemonic-map","-m", action="store_true")
    p.add_argument("--hex")
    a = p.parse_args()

    if a.mnemonic_map:
        print_mnemonic_map()
        return

    if a.validate:
        bc = bytes.fromhex(a.hex) if a.hex else (open(a.input,"rb").read() if a.input else None)
        if not bc: print("Error: need --input or --hex"); sys.exit(1)
        r = validate_bytecode(bc)
        for k,v in r.items(): print(f"  {k}: {v}")
        return

    if a.fr and a.to:
        bc = bytes.fromhex(a.hex) if a.hex else (open(a.input,"rb").read() if a.input else None)
        if not bc: print("Error: need --input or --hex"); sys.exit(1)
        if a.fr == "runtime" and a.to == "unified":
            result = migrate_runtime_to_unified(bc)
        else:
            print("Error: unified->runtime not yet implemented"); sys.exit(1)
        print(result)
        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for w in result.warnings[:20]: print(f"  - {w}")
        if result.no_equivalent:
            print(f"\nNo equivalent ({len(result.no_equivalent)}):")
            for op,name in result.no_equivalent: print(f"  0x{op:02X} {name}")
        if a.output:
            open(a.output,"wb").write(result.output)
            print(f"\nWritten: {a.output} ({len(result.output)} bytes)")
        else:
            print(f"\nHex: {result.output.hex()}")
        return

    p.print_help()


if __name__ == "__main__":
    main()
