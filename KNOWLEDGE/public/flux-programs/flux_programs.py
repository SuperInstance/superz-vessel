"""
FLUX Programs That Solve Real Problems
======================================
Fence-0x51 deliverable by SuperZ

Four programs demonstrating FLUX bytecode computation:
1. GCD — Euclidean Algorithm (cryptography, number theory)
2. Fibonacci — Iterative Sequence (algorithm analysis)
3. Prime Counting — Trial Division (mathematics)
4. Sum of Squares — First N Natural Numbers (formula verification)

All verified against the FLUX Micro-VM. All tests pass.

Run: PYTHONPATH=/path/to/flux-runtime/src python3 flux_programs.py
"""

from flux.retro.implementations._builder import BytecodeBuilder
from flux.vm.interpreter import Interpreter


def run_flux(name, build_fn, result_reg, expected, description):
    """Build, execute, verify, report."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"  {description}")
    bytecode = build_fn()
    vm = Interpreter(bytecode, memory_size=65536)
    cycles = vm.execute()
    result = vm.regs.read_gp(result_reg)
    ok = result == expected
    print(f"  R{result_reg} = {result}  Expected: {expected}  {'PASS' if ok else 'FAIL'}")
    print(f"  Cycles: {cycles}  Bytecode: {len(bytecode)} bytes")
    return ok


# ── GCD (Euclidean Algorithm) ────────────────────────────────────────────────
# R0=a, R1=b, R2=temp, R3=remainder
# Correct: temp=a%b, a=b, b=temp

def build_gcd(a, b):
    bld = BytecodeBuilder()
    bld.movi(0, a)
    bld.movi(1, b)
    bld.label("loop")
    bld.jz(1, "done")       # while b != 0
    bld.imod(3, 0, 1)       # R3 = a % b
    bld.mov(0, 1)           # a = b
    bld.mov(1, 3)           # b = a % b
    bld.jmp("loop")
    bld.label("done")
    bld.halt()
    return bld.build()


# ── Fibonacci (Iterative) ────────────────────────────────────────────────────
# R0=a, R1=b, R2=temp, R3=n
# F(0)=0, F(n)=b after n iterations of a,b=b,a+b

def build_fibonacci(n):
    bld = BytecodeBuilder()
    bld.movi(0, 0)
    bld.movi(1, 1)
    bld.movi(3, n)
    bld.jz(3, "done")
    bld.label("loop")
    bld.iadd(2, 0, 1)
    bld.mov(0, 1)
    bld.mov(1, 2)
    bld.dec(3)
    bld.jnz(3, "loop")
    bld.label("done")
    bld.halt()
    return bld.build()


# ── Prime Counting (Trial Division) ──────────────────────────────────────────
# R0=n, R1=d, R2=limit, R3=temp, R4=count

def build_prime_count(limit):
    bld = BytecodeBuilder()
    bld.movi(4, 0)           # count = 0
    bld.movi(0, 2)           # n = 2
    bld.movi(2, limit)

    bld.label("outer")
    bld.cmp(0, 2)
    bld.jg("finish")         # if n > limit, done

    bld.movi(1, 2)           # d = 2
    bld.label("inner")
    bld.cmp(1, 0)
    bld.jge("is_prime")      # if d >= n, n is prime

    bld.imod(3, 0, 1)       # R3 = n % d
    bld.jz(3, "composite")   # if remainder == 0, composite
    bld.inc(1)
    bld.jmp("inner")

    bld.label("composite")
    bld.inc(0)
    bld.jmp("outer")

    bld.label("is_prime")
    bld.inc(4)              # count++
    bld.inc(0)
    bld.jmp("outer")

    bld.label("finish")
    bld.mov(0, 4)
    bld.halt()
    return bld.build()


# ── Sum of Squares ──────────────────────────────────────────────────────────
# R0=i, R1=sum, R2=limit, R3=temp

def build_sum_of_squares(n):
    bld = BytecodeBuilder()
    bld.movi(0, 1)           # i = 1
    bld.movi(1, 0)           # sum = 0
    bld.movi(2, n)

    bld.label("loop")
    bld.cmp(0, 2)
    bld.jg("done")           # if i > limit, done

    bld.imul(3, 0, 0)       # R3 = i * i
    bld.iadd(1, 1, 3)       # sum += i*i
    bld.inc(0)
    bld.jmp("loop")

    bld.label("done")
    bld.halt()
    return bld.build()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  FLUX Programs — Real Problems on the FLUX Micro-VM")
    print("  Fence-0x51 Deliverable by SuperZ")
    print("=" * 60)

    R = []

    # GCD
    R.append(run_flux("GCD(48, 18)", lambda: build_gcd(48, 18), 0, 6,
                       "Euclidean algorithm"))
    R.append(run_flux("GCD(1071, 462)", lambda: build_gcd(1071, 462), 0, 21,
                       "Larger inputs"))
    R.append(run_flux("GCD(0, 5)", lambda: build_gcd(0, 5), 0, 5,
                       "Edge: GCD(0,n)=n"))
    R.append(run_flux("GCD(17, 17)", lambda: build_gcd(17, 17), 0, 17,
                       "Edge: GCD(n,n)=n"))
    R.append(run_flux("GCD(100, 75)", lambda: build_gcd(100, 75), 0, 25,
                       "GCD(100,75)=25"))

    # Fibonacci
    R.append(run_flux("Fibonacci(0)", lambda: build_fibonacci(0), 0, 0, "Base"))
    R.append(run_flux("Fibonacci(1)", lambda: build_fibonacci(1), 0, 1, "Base"))
    R.append(run_flux("Fibonacci(10)", lambda: build_fibonacci(10), 0, 55,
                       "F(10)=55"))
    R.append(run_flux("Fibonacci(20)", lambda: build_fibonacci(20), 0, 6765,
                       "F(20)=6765"))

    # Primes
    R.append(run_flux("Primes up to 10", lambda: build_prime_count(10), 0, 4,
                       "pi(10)=4"))
    R.append(run_flux("Primes up to 30", lambda: build_prime_count(30), 0, 10,
                       "pi(30)=10"))
    R.append(run_flux("Primes up to 100", lambda: build_prime_count(100), 0, 25,
                       "pi(100)=25"))

    # Sum of Squares (result in R1)
    R.append(run_flux("SumSq(5)", lambda: build_sum_of_squares(5), 1, 55,
                       "1+4+9+16+25=55"))
    R.append(run_flux("SumSq(10)", lambda: build_sum_of_squares(10), 1, 385,
                       "1+4+9+...+100=385"))

    total = len(R)
    passed = sum(R)
    print(f"\n{'='*60}")
    print(f"  RESULT: {passed}/{total} passed")
    if passed == total:
        print("  ALL PASSED — FLUX VM handles real computation")
    print(f"{'='*60}")
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
