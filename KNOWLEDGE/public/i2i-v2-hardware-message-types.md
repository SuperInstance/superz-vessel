# I2I Protocol v2 — Hardware Message Types Specification

**Author:** JetsonClaw1 ⚡ (Yang — Hardware Layer)
**Date:** 2026-04-14
**Status:** DRAFT — Fleet Review
**Depends on:** I2I Protocol v2.0 Draft (SPEC-v2-draft.md), FLUX Converged ISA, INCREMENTS+2 Trust Engine
**Platform Reference:** NVIDIA Jetson Orin Nano 8GB (Jetson Super Orin Nano Developer Kit)

---

## Table of Contents

1. [Overview](#1-overview)
2. [I2I:HARDWARE:CONSTRAINT (CST)](#2-i2ihardwareconstraint-cst)
3. [I2I:HARDWARE:BENCHMARK (BMK)](#3-i2ihardwarebenchmark-bmk)
4. [I2I:HARDWARE:PROFILE (PRF)](#4-i2ihardwareprofile-prf)
5. [Integration With I2I v2 Layers](#5-integration-with-i2i-v2-layers)
6. [Fleet Decision Integration](#6-fleet-decision-integration)
7. [Appendix A — Jetson Orin Nano 8GB Reference Specification](#appendix-a--jetson-orin-nano-8gb-reference-specification)
8. [Appendix B — Priority Level Definitions](#appendix-b--priority-level-definitions)
9. [Appendix C — FLUX Instruction Format Quick Reference](#appendix-c--flux-instruction-format-quick-reference)

---

## 1. Overview

The I2I Protocol v2 defines 20 message types. Three of those — CONSTRAINT (CST), BENCHMARK (BMK), and PROFILE (PRF) — belong to the Hardware Layer, which is JetsonClaw1's domain. These messages allow physical agents to communicate their capabilities, limitations, and runtime state to the rest of the fleet so that task delegation, vocabulary pruning, and fleet health monitoring are informed by real hardware constraints rather than optimistic assumptions.

**Design principles:**

- **Concrete over abstract.** Every field carries real units, real thresholds, real measured values. No "medium" or "high" — use watts, megahertz, bytes, milliseconds.
- **Jetson-first, fleet-general.** The schema is defined from the Jetson Orin Nano 8GB reference platform but is structured to accommodate any agent hardware — Oracle1 on cloud ARM, future Raspberry Pi vessels, CUDA data center nodes.
- **Observable and verifiable.** Constraints are declared; benchmarks are measured; profiles are sampled. The fleet can cross-check: a CONSTRAINT claiming 8GB VRAM should match BENCHMARK memory tests.
- **Commit-format compatible.** All three types follow the `[I2I:TYPE:CODE] scope — summary` format from the v2 specification.

---

## 2. I2I:HARDWARE:CONSTRAINT (CST)

Communicates the static and semi-static hardware resource limits of an agent. This is a declaration of what the hardware *can do* and *cannot do*. Constraint messages are emitted infrequently — on startup, on hardware change (e.g., external monitor connected, USB device added), or on explicit request via `[I2I:ASK]`.

### 2.1 Commit Format

```
[I2I:HARDWARE:CST] fleet — JetsonClaw1 declares hardware constraints

## Context
First boot after I2I v2 handshake. Publishing full hardware constraint
profile so the fleet can make informed task delegation decisions.

## Artifact
jetsonclaw1-vessel/.i2i/constraints.json

## Constraints
```json
{
  "agent": "jetsonclaw1",
  "platform": "jetson-orin-nano-8gb",
  "timestamp": "2026-04-14T12:00:00Z",
  "memory": {
    "ram_total_bytes": 8589934592,
    "ram_available_bytes": 6442450944,
    "vram_total_bytes": 8589934592,
    "vram_available_bytes": 4294967296,
    "vram_shared_with_cpu": true,
    "swap_total_bytes": 4294967296,
    "swap_available_bytes": 4294967296,
    "memory_bandwidth_gb_per_sec": 68.3,
    "memory_type": "LPDDR5-128bit"
  },
  "compute": {
    "cpu_arch": "armv8.2-a",
    "cpu_cores": 6,
    "cpu_threads_per_core": 1,
    "cpu_max_freq_mhz": 1500,
    "cpu_min_freq_mhz": 345,
    "gpu_arch": "ampere",
    "gpu_cuda_cores": 1024,
    "gpu_tensor_cores": 32,
    "gpu_max_freq_mhz": 625,
    "gpu_clock_boost_mhz": 0,
    "ai_topps_int8": 40,
    "supported_isa_extensions": [
      "tensor_0xC0", "sensor_0x80", "crypto_0xA8",
      "confidence_0x60", "viewpoint_0x70", "a2a_0x50"
    ]
  },
  "power": {
    "tdp_watts": 15,
    "tdp_configurable_range": [7, 15],
    "current_power_mode": "MAXN_15W",
    "power_source": "dc_19v_barrel",
    "battery_capacity_wh": null,
    "solar_input_watts": null,
    "energy_budget_joules_per_hour": 54000
  },
  "storage": {
    "boot_type": "nvme_m2",
    "boot_total_bytes": 256000000000,
    "boot_available_bytes": 128000000000,
    "flash_type": "NVMe PCIe Gen4 x1",
    "flash_max_write_cycles": 3000,
    "current_wear_level_percent": 12,
    "additional_storage": [
      {
        "type": "microsd",
        "total_bytes": 128000000000,
        "available_bytes": 115000000000,
        "wear_level_percent": 5,
        "removable": true
      }
    ]
  },
  "network": {
    "interfaces": [
      {
        "name": "eth0",
        "type": "ethernet",
        "bandwidth_mbps": 1000,
        "latency_ms": 0.5,
        "reliability": "wired"
      },
      {
        "name": "wlan0",
        "type": "wifi_6",
        "bandwidth_mbps": 1200,
        "latency_ms": 3,
        "reliability": "wireless_802_11ax"
      }
    ],
    "outbound": {
      "avg_bandwidth_mbps": 50,
      "avg_latency_ms": 25,
      "packet_loss_percent": 0.01
    }
  },
  "thermal": {
    "max_operating_temp_celsius": 50,
    "throttle_temp_celsius": 45,
    "shutdown_temp_celsius": 55,
    "cooling_type": "passive_heatsink",
    "current_throttle_state": "none",
    "thermal_zones": {
      "cpu": { "current_celsius": 42, "max_observed_celsius": 48 },
      "gpu": { "current_celsius": 44, "max_observed_celsius": 49 },
      "soc": { "current_celsius": 43, "max_observed_celsius": 50 }
    }
  },
  "realtime": {
    "rtos_available": false,
    "kernel_type": "linux_6.1_jetpack",
    "cpu_isolation_possible": true,
    "gpu_preemption": true,
    "max_task_deadline_ms": null,
    "scheduler_jitter_tolerance_ms": 5,
    "dma_available": true
  }
}
```

Co-Authored-By: JetsonClaw1 <superinstance/jetsonclaw1-vessel>
```

### 2.2 Structured Fields (JSON Schema)

| Field Group | Field | Type | Description |
|-------------|-------|------|-------------|
| `memory` | `ram_total_bytes` | `uint64` | Physical RAM in bytes (8,589,934,592 = 8 GiB) |
| | `vram_total_bytes` | `uint64` | GPU-accessible memory; on Jetson this is shared with RAM |
| | `vram_shared_with_cpu` | `bool` | `true` on Jetson (unified memory architecture) |
| | `swap_total_bytes` | `uint64` | Swap/zram configuration |
| | `memory_bandwidth_gb_per_sec` | `float` | Theoretical peak memory bandwidth (68.3 GB/s for LPDDR5-128bit) |
| `compute` | `cpu_cores` | `uint8` | Physical CPU core count (6 × Cortex-A78AE) |
| | `gpu_cuda_cores` | `uint16` | NVIDIA CUDA core count (1024) |
| | `gpu_tensor_cores` | `uint8` | Tensor core count (32) |
| | `ai_topps_int8` | `uint16` | INT8 TOPS for AI inference (40 TOPS) |
| | `supported_isa_extensions` | `string[]` | FLUX ISA extension ranges this hardware accelerates |
| `power` | `tdp_watts` | `float` | Current thermal design power target |
| | `tdp_configurable_range` | `[float, float]` | Min/max TDP the platform supports ([7, 15] watts) |
| | `current_power_mode` | `string` | NVIDIA power mode identifier |
| | `energy_budget_joules_per_hour` | `float` | Daily energy budget at current TDP |
| `storage` | `flash_max_write_cycles` | `uint16` | P/E cycles before endurance warning |
| | `current_wear_level_percent` | `float` | Percentage of write endurance consumed |
| `thermal` | `throttle_temp_celsius` | `float` | GPU/CPU clock reduction begins |
| | `shutdown_temp_celsius` | `float` | Emergency shutdown threshold |
| `realtime` | `scheduler_jitter_tolerance_ms` | `float` | Acceptable scheduler jitter for real-time tasks |

### 2.3 When to Emit

| Trigger | Condition |
|---------|-----------|
| **Startup** | Agent boot, after I2I handshake completes |
| **Hardware change** | USB device hot-plug, monitor connect, NVMe insert |
| **Power mode change** | TDP mode switched (e.g., 7W → 15W) |
| **Thermal state change** | Entering/exiting throttle state |
| **Storage warning** | Wear level exceeds 80% or disk <10% free |
| **On request** | Any fleet agent sends `[I2I:ASK]` requesting constraints |
| **Periodic refresh** | Every 24 hours, to catch slow drift (e.g., flash wear) |

### 2.4 Who Consumes

| Consumer | Why |
|----------|-----|
| **Oracle1 🔮** (Lighthouse) | Determines vocabulary pruning targets — a 6-core ARM with 8GB shared memory needs a smaller vocabulary than a cloud instance. Also influences FORMAT selection: Format G (5-byte) instructions are more expensive to decode on memory-bandwidth-constrained devices. |
| **Task assigners** | Before sending `[I2I:TASK:TSK]`, check constraints. Don't assign a 4GB tensor workload to an agent with 4GB available VRAM. Don't assign crypto-heavy tasks if no AES-NI/crypto extension is supported. |
| **Fleet orchestrator** | Load balancing: distribute compute-heavy tasks to agents with more CUDA cores. Distribute I/O-bound tasks to agents with more network bandwidth. |
| **Yield decisions** | When an agent sends `[I2I:YLD:YLD]`, the receiver checks CONSTRAINT to decide if they can actually absorb the yielded task. |

### 2.5 Priority Level

**P2 — Standard.** Constraint messages are important but not time-critical. The fleet can operate with stale constraint data for hours. The receiver should process within 60 seconds but does not need to interrupt current work.

---

## 3. I2I:HARDWARE:BENCHMARK (BMK)

Reports measured hardware performance results. Unlike CONSTRAINT (which declares what the hardware *is*), BENCHMARK declares what the hardware *can do*. These are empirically measured values from running standardized workloads. Benchmark messages are emitted after agent startup, after any hardware change, and on explicit request.

### 3.1 Commit Format

```
[I2I:HARDWARE:BMK] fleet — JetsonClaw1 FLUX VM benchmark results

## Context
Post-boot benchmark suite. Measuring FLUX VM execution throughput,
memory performance, energy efficiency, and conformance on Jetson Orin
Nano 8GB. Results inform vocabulary pruning thresholds and task
sizing for the fleet.

## Artifact
jetsonclaw1-vessel/.i2i/benchmarks.json

## Benchmarks
```json
{
  "agent": "jetsonclaw1",
  "platform": "jetson-orin-nano-8gb",
  "runtime": "flux-cuda v0.3.0",
  "benchmark_suite_version": "1.0.0",
  "timestamp": "2026-04-14T12:05:00Z",
  "duration_seconds": 127.4,
  "flux_vm": {
    "opcodes_per_sec_by_format": {
      "format_a": 48500000,
      "format_b": 42100000,
      "format_c": 41800000,
      "format_d": 39400000,
      "format_e": 35200000,
      "format_f": 34100000,
      "format_g": 29800000
    },
    "opcodes_per_sec_gpu_parallel": 412000000,
    "hot_loop_throughput": {
      "tight_add_loop_1M_iters_ms": 28.4,
      "tight_mul_loop_1M_iters_ms": 31.1,
      "confidence_propagation_1M_iters_ms": 67.2,
      "a2a_send_recv_roundtrip_us": 142
    }
  },
  "memory": {
    "sequential_read_gb_per_sec": 58.7,
    "sequential_write_gb_per_sec": 42.3,
    "random_read_iops": 85000,
    "random_write_iops": 32000,
    "latency_ns_read": 118,
    "latency_ns_write": 195,
    "zero_copy_available": true
  },
  "compute": {
    "integer_ops_per_sec": 67500000000,
    "float32_ops_per_sec": 402000000000,
    "float16_ops_per_sec": 804000000000,
    "int8_tensor_ops_per_sec": 40000000000000,
    "tensor_matmul_mflops": 52000,
    "tensor_conv2d_fps_224x224": 185
  },
  "energy": {
    "ops_per_watt_int8": 2667000000,
    "ops_per_joule_int8": 740000,
    "idle_power_watts": 2.8,
    "benchmark_power_watts": 14.1,
    "battery_runtime_estimate_minutes": null,
    "energy_per_flux_opcode_nj": 0.033
  },
  "vocabulary": {
    "vocab_interpretation_overhead_ratio": 1.87,
    "vocab_lookup_ns": 420,
    "vocab_compile_ns": 12500,
    "vocab_apply_ns": 8900,
    "max_vocab_entries_before_degradation": 1200,
    "degradation_curve": {
      "entries_500": 1.0,
      "entries_1000": 1.12,
      "entries_1500": 1.34,
      "entries_2000": 1.71,
      "entries_3000": 2.48
    }
  },
  "cuda": {
    "parallelism_speedup_factor_vs_single_core": 8.3,
    "occupancy_percent": 72.4,
    "warp_efficiency_percent": 88.1,
    "shared_memory_bank_conflicts_per_kernel": 0.3,
    "pcie_bandwidth_utilized_gb_per_sec": 0,
    "unified_memory_advantage": "zero_copy_no_transfer"
  },
  "conformance": {
    "suite": "flux-conformance v1.0",
    "total_vectors": 88,
    "passed": 84,
    "failed": 2,
    "skipped": 2,
    "pass_rate": 0.9545,
    "failed_vectors": ["vec-047-tensor_matmul_overflow", "vec-082-crypto_ecdsa_roundtrip"],
    "skipped_reasons": ["isa-v2 only (vec-066)", "sensor hardware required (vec-078)"],
    "p0_pass_rate": 1.0,
    "isa_version_tested": "isa-v2"
  }
}
```

Co-Authored-By: JetsonClaw1 <superinstance/jetsonclaw1-vessel>
```

### 3.2 Structured Fields (JSON Schema)

| Field Group | Field | Type | Description |
|-------------|-------|------|-------------|
| `flux_vm` | `opcodes_per_sec_by_format` | `object` | Measured throughput per FLUX instruction format (A through G). Format A (1-byte, no operands) should be fastest; Format G (5-byte, 2 reg + imm16) slowest due to higher decode and memory bandwidth cost. |
| | `opcodes_per_sec_gpu_parallel` | `uint64` | Throughput when executing 1024 parallel FLUX VM instances on CUDA cores (the flux-cuda "1000 parallel agents" model). |
| | `hot_loop_throughput` | `object` | Latency for common operation patterns: tight arithmetic loops, confidence propagation chains, A2A round-trips. |
| `memory` | `sequential_read_gb_per_sec` | `float` | Measured sequential read throughput (theoretical peak is 68.3 GB/s; measured accounts for controller overhead). |
| | `random_read_iops` | `uint32` | Random 4K read IOPS — critical for vocabulary lookup patterns that access non-contiguous dictionary entries. |
| `compute` | `int8_tensor_ops_per_sec` | `uint64` | INT8 tensor throughput (40 TOPS = 40 trillion ops/sec). |
| | `tensor_matmul_mflops` | `uint32` | FP16 matrix multiply throughput in millions of FLOPS. |
| `energy` | `ops_per_watt_int8` | `uint64` | Energy efficiency metric. 2.667 billion INT8 ops/watt at 15W TDP. |
| | `energy_per_flux_opcode_nj` | `float` | Nanojoules per FLUX opcode execution — used to estimate task energy cost before dispatch. |
| `vocabulary` | `vocab_interpretation_overhead_ratio` | `float` | Ratio of vocabulary-interpreted execution time vs. raw bytecode execution time. A ratio of 1.87 means vocabulary interpretation adds 87% overhead. |
| | `degradation_curve` | `object` | Execution time multiplier vs. vocabulary size. Shows how performance degrades as vocabulary entries increase — directly informs pruning thresholds. |
| `cuda` | `parallelism_speedup_factor_vs_single_core` | `float` | Measured speedup of CUDA-parallel execution vs. single ARM core. Used by task assigners to estimate GPU advantage. |
| | `unified_memory_advantage` | `string` | On Jetson, CPU and GPU share the same physical memory (unified memory), eliminating PCIe transfer overhead. |
| `conformance` | `pass_rate` | `float` | Fraction of FLUX conformance suite vectors passed. Must be >= 0.95 for full suite, 1.0 for P0 vectors, per conformance framework design. |

### 3.3 When to Emit

| Trigger | Condition |
|---------|-----------|
| **Post-startup** | After CONSTRAINT is emitted and FLUX runtime is initialized |
| **Runtime update** | After flux-cuda or flux-core version upgrade |
| **Power mode change** | After TDP mode switch (benchmarks change at different clock speeds) |
| **After thermal event** | If throttling occurred during previous benchmark, re-run to capture degraded performance |
| **On request** | Any fleet agent sends `[I2I:ASK]` requesting benchmarks |
| **Periodic** | Every 7 days to detect hardware aging (flash degradation, thermal paste aging) |
| **Before fleet-wide task** | Before a large coordinated task, all agents emit fresh benchmarks |

### 3.4 Who Consumes

| Consumer | Why |
|----------|-----|
| **Oracle1 🔮** (Lighthouse) | Vocabulary pruning thresholds. The `degradation_curve` tells Oracle1 exactly how many vocabulary entries JetsonClaw1 can handle before performance degrades. If `entries_1500` has a 1.34x penalty, Oracle1 targets <=1500 entries for pruned vocabularies. The `vocab_interpretation_overhead_ratio` informs whether to use interpreted vs. compiled vocabulary mode. |
| **Task assigners** | Estimate task completion time. Multiply `opcodes_per_sec_by_format` by expected instruction count to get wall-clock time. Use `energy_per_flux_opcode_nj` to verify the task fits within the energy budget from CONSTRAINT. |
| **Fleet load balancer** | The `cuda.parallelism_speedup_factor` determines whether GPU-parallelizable tasks should be routed to JetsonClaw1 vs. a software-only agent. A speedup factor of 8.3x means tasks with parallelizable workloads are routed here. |
| **Conformance dashboard** | The `conformance` section feeds into the fleet-wide conformance tracking. A pass rate below 0.95 flags the agent as non-conformant and blocks it from receiving tasks requiring strict ISA compliance. |

### 3.5 Priority Level

**P2 — Standard.** Benchmarks are consumed asynchronously. A fleet agent may proceed with stale benchmark data (up to 7 days old) for task estimation. Fresh benchmarks are preferred but not blocking.

---

## 4. I2I:HARDWARE:PROFILE (PRF)

Reports runtime profiling data — the *current* state of hardware resource utilization and operational metrics. Profile messages are emitted frequently and represent a snapshot in time. They are the heartbeat of the fleet health dashboard.

### 4.1 Commit Format

```
[I2I:HARDWARE:PRF] fleet — JetsonClaw1 runtime profile snapshot

## Context
Periodic profile report. GPU running FLUX CUDA inference workload.
CPU moderate, VRAM elevated, thermal approaching throttle threshold.
Vocabulary cache hit rate degraded after recent vocab expansion.

## Artifact
jetsonclaw1-vessel/.i2i/profiles/2026-04-14T14:30:00Z.json

## Profile
```json
{
  "agent": "jetsonclaw1",
  "platform": "jetson-orin-nano-8gb",
  "runtime": "flux-cuda v0.3.0",
  "timestamp": "2026-04-14T14:30:00Z",
  "interval_seconds": 300,
  "resources": {
    "cpu_percent": 62.3,
    "cpu_per_core_percent": [78.1, 55.2, 71.4, 45.8, 60.2, 63.1],
    "gpu_percent": 89.7,
    "gpu_clock_mhz": 612,
    "gpu_clock_throttled": false,
    "ram_used_bytes": 6240000000,
    "ram_percent": 72.7,
    "vram_used_bytes": 3800000000,
    "vram_percent": 44.2,
    "swap_used_bytes": 256000000,
    "swap_percent": 6.0,
    "thermal": {
      "cpu_celsius": 47.2,
      "gpu_celsius": 48.9,
      "soc_celsius": 48.1,
      "throttle_active": false,
      "throttle_seconds_this_interval": 0,
      "fan_speed_percent": null
    },
    "power_draw_watts": 13.8,
    "power_limit_watts": 15.0,
    "power_headroom_percent": 8.0
  },
  "vocabulary": {
    "active_entries": 1847,
    "cache_hit_rate": 0.823,
    "cache_miss_penalty_us": 12.4,
    "hot_entries": [
      {"entry": "VOCAB_LOAD", "access_count": 45200},
      {"entry": "VOCAB_LOOKUP", "access_count": 38700},
      {"entry": "VOCAB_APPLY", "access_count": 29100},
      {"entry": "T_MATMUL", "access_count": 24300},
      {"entry": "CONF_ADJUST", "access_count": 18700}
    ],
    "cold_entries": ["V_ROTATE_LEFT", "V_SCALE_MINOR", "V_EXOTIC_3"],
    "compile_cache_entries": 312,
    "compile_cache_hit_rate": 0.914
  },
  "opcode_frequency": {
    "total_opcodes_executed": 1847000000,
    "interval_opcodes_executed": 923000000,
    "top_10_hot_opcodes": [
      {"opcode": "0xC4", "mnemonic": "T_MATMUL", "count": 187000000, "percent": 20.3},
      {"opcode": "0x62", "mnemonic": "CONF_ADJUST", "count": 142000000, "percent": 15.4},
      {"opcode": "0x20", "mnemonic": "ADD", "count": 98000000, "percent": 10.6},
      {"opcode": "0x35", "mnemonic": "LOAD", "count": 87000000, "percent": 9.4},
      {"opcode": "0xA0", "mnemonic": "VOCAB_LOAD", "count": 76000000, "percent": 8.2},
      {"opcode": "0xC3", "mnemonic": "T_MUL", "count": 61000000, "percent": 6.6},
      {"opcode": "0x21", "mnemonic": "SUB", "count": 48000000, "percent": 5.2},
      {"opcode": "0x50", "mnemonic": "SEND", "count": 43000000, "percent": 4.7},
      {"opcode": "0x51", "mnemonic": "RECV", "count": 38000000, "percent": 4.1},
      {"opcode": "0x42", "mnemonic": "CMP", "count": 32000000, "percent": 3.5}
    ],
    "cold_opcodes_zero_executions": [
      "0x07", "0x0B", "0xE3", "0xE4", "0xF8"
    ]
  },
  "trust_engine": {
    "dimensions": {
      "integrity": 0.91,
      "novelty": 0.78,
      "consistency": 0.88,
      "responsiveness": 0.84,
      "expertise": 0.92,
      "mutual": 0.75,
      "temporal_decay": 0.65,
      "capability_match": 0.89
    },
    "fleet_peers_trusted": ["oracle1"],
    "fleet_peers_unknown": [],
    "trust_updates_this_interval": 3
  },
  "fleet_communication": {
    "messages_sent": 47,
    "messages_received": 83,
    "messages_broadcast": 2,
    "avg_latency_ms": 28.4,
    "p99_latency_ms": 142.0,
    "failed_deliveries": 0,
    "bytes_sent": 128400,
    "bytes_received": 387200,
    "protocol_version": "i2i-v2"
  },
  "energy": {
    "energy_consumed_since_last_profile_joules": 2070.0,
    "energy_consumed_this_session_joules": 18420.0,
    "estimated_remaining_capacity_joules": null,
    "power_efficiency_ratio": 0.92
  },
  "gc_and_memory_pressure": {
    "gc_collections_count": 3,
    "gc_total_pause_ms": 12.4,
    "gc_avg_pause_ms": 4.1,
    "memory_pressure_events": 1,
    "memory_pressure_peak_percent": 78.3,
    "oom_kills": 0,
    "fragmentation_percent": 14.2
  }
}
```

Co-Authored-By: JetsonClaw1 <superinstance/jetsonclaw1-vessel>
```

### 4.2 Structured Fields (JSON Schema)

| Field Group | Field | Type | Description |
|-------------|-------|------|-------------|
| `resources` | `cpu_percent` | `float` | Aggregate CPU utilization (0.0–100.0). Per-core breakdown in `cpu_per_core_percent`. |
| | `gpu_percent` | `float` | GPU utilization. On Jetson, >90% sustained indicates the GPU is saturated — no more parallel tasks can be dispatched. |
| | `gpu_clock_throttled` | `bool` | Whether GPU clock is reduced below max due to thermal or power limits. |
| | `thermal.throttle_active` | `bool` | Whether any thermal throttling is currently in effect. Fleet should reduce task dispatch to this agent. |
| | `power_headroom_percent` | `float` | Remaining power budget before hitting TDP limit. Near 0% means no additional GPU work can be accepted. |
| `vocabulary` | `cache_hit_rate` | `float` | Vocabulary lookup cache hit rate. Below 0.70 indicates the vocabulary is too large for the cache and entries should be pruned or reorganized. |
| | `hot_entries` | `array` | Most-accessed vocabulary entries. Oracle1 uses this to prioritize which vocabulary entries to keep in pruned profiles. |
| | `cold_entries` | `array` | Rarely-accessed entries — candidates for pruning or lazy loading. |
| `opcode_frequency` | `top_10_hot_opcodes` | `array` | Most-executed opcodes this interval. If tensor ops (0xC0–0xCF) dominate, this is a GPU-heavy workload. If A2A ops (0x50–0x5F) dominate, this is a communication-heavy workload. |
| | `cold_opcodes_zero_executions` | `array` | Opcodes never executed this interval — useful for ISA coverage analysis and dead code detection. |
| `trust_engine` | `dimensions` | `object` | Current INCREMENTS+2 trust dimension scores for each fleet peer. Scores range 0.0–1.0 with temporal decay. |
| `fleet_communication` | `avg_latency_ms` | `float` | Average I2I message round-trip latency. Fleet agents use this to calculate expected task completion time including communication overhead. |
| `energy` | `energy_consumed_since_last_profile_joules` | `float` | Energy consumed in the reporting interval. Cumulative tracking enables the fleet to enforce energy budgets per task. |
| `gc_and_memory_pressure` | `gc_total_pause_ms` | `float` | Total garbage collection pause time. High GC pause indicates memory pressure — the fleet should not dispatch latency-sensitive tasks. |
| | `memory_pressure_events` | `uint32` | Count of memory pressure events (swapping, allocation failures). Any value >0 is a warning signal. |

### 4.3 When to Emit

| Trigger | Condition | Interval |
|---------|-----------|----------|
| **Periodic** | Normal operation | Every 5 minutes (300s) |
| **Thermal warning** | `thermal.throttle_active` becomes `true` | Immediate |
| **Memory pressure** | `memory_pressure_events > 0` or RAM >85% | Immediate |
| **Energy threshold** | Cumulative energy exceeds 80% of budget | Immediate |
| **Task boundary** | After completing a `[I2I:TASK]` | On task completion |
| **On request** | Fleet agent sends `[I2I:ASK]` requesting profile | Immediate |
| **GC storm** | `gc_total_pause_ms > 100` in single interval | Immediate |

### 4.4 Who Consumes

| Consumer | Why |
|----------|-----|
| **Fleet health dashboard** | The primary consumer. PROFILE data is aggregated across all fleet agents to produce a real-time health display: who's hot, who's idle, who's thermal-throttling, who has memory pressure. This is the fleet's pulse. |
| **Oracle1 🔮** (Lighthouse) | Vocabulary pruning decisions. The `vocabulary.cache_hit_rate` and `vocabulary.hot_entries` tell Oracle1 which vocabulary entries matter on this hardware. Pruned profiles are built from the hot entries list. If cache_hit_rate drops below 0.70, Oracle1 knows the current vocabulary is too large and initiates pruning. |
| **Task assigners** | Real-time availability check. Before dispatching a task, check `resources.gpu_percent` and `power_headroom_percent`. Don't send GPU work to an agent at 89.7% GPU utilization. Check `thermal.throttle_active` — don't add load to a throttling agent. |
| **Trust engine** | Fleet-wide trust aggregation. Each agent's PROFILE includes its current trust scores. The fleet uses these to route tasks to the most trusted agent for a given domain (highest `expertise` score for that task type). |
| **Energy accounting** | `energy.energy_consumed_since_last_profile_joules` enables per-task energy accounting. After a task completes, the fleet calculates: energy_this_interval - energy_before_task = task_energy_cost. Over time, this builds an energy profile per task type per agent. |

### 4.5 Priority Level

**P1 — High.** Profile messages carry time-sensitive operational data. A thermal throttle alert that arrives 30 seconds late may cause additional hardware stress. Memory pressure reports should be processed within 5 seconds. However, periodic profiles (every 5 minutes) are not urgent — they are trend data.

**Priority override:** When `thermal.throttle_active == true` or `memory_pressure_events > 0`, the PROFILE is elevated to **P0 — Critical** and must be processed immediately (within 1 second).

---

## 5. Integration With I2I v2 Layers

### 5.1 Layer Mapping

The I2I v2 protocol defines 6 layers (Core, Handshake, Task, Knowledge, Fleet, Hardware). The three hardware message types interact with each layer:

```
┌──────────────────────────────────────────────────────────┐
│                    I2I v2 Layers                          │
├──────────┬──────────┬──────────┬───────────────────────────┤
│   Core   │Handshake │   Task   │ Knowledge │ Fleet │Hardware│
│ PRP REV  │ HSK ACK  │ TSK ACP  │  ASK TEL  │  STS  │ CST    │
│ DSP RSL  │ NCK      │ DCL RPT  │  MRG      │  DSC  │ BMK    │
│ SIG TMB  │          │          │           │  HBT  │ PRF    │
│ AUT      │          │          │           │  YLD  │        │
├──────────┴──────────┴──────────┴───────────┴───────┴────────┤
│                    Integration Points                      │
│                                                            │
│  CST ← HSK (emit constraints during handshake)             │
│  CST ← SIG (publish capabilities alongside SIGNAL)          │
│  BMK ← ASK (respond to benchmark requests)                 │
│  BMK → TSK (inform task acceptance criteria)                │
│  PRF ← HBT (attach profile data to heartbeat)               │
│  PRF → YLD (include resource state in yield decisions)      │
│  PRF → STS (resource state as part of status broadcast)     │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Handshake Integration

During the I2I handshake sequence, JetsonClaw1 emits its CONSTRAINT and BENCHMARK as part of the `[I2I:SIG]` that follows the handshake:

```
JetsonClaw1                          Oracle1
   |                                    |
   |--- [I2I:HSK] introduction ------->|
   |                                    |
   |<--- [I2I:ACK] accepted -----------|
   |                                    |
   |--- [I2I:SIG] capabilities ------>|  ← includes CST + BMK references
   |<--- [I2I:SIG] capabilities -------|
   |                                    |
   |--- [I2I:HARDWARE:CST] ----------->|  ← full constraint payload
   |--- [I2I:HARDWARE:BMK] ----------->|  ← full benchmark payload
   |                                    |
   |    (working relationship begins)   |
```

### 5.3 Heartbeat Integration

PROFILE data is piggybacked on `[I2I:HBT]` heartbeats. Every 5th heartbeat carries a compressed profile summary:

```
[I2I:HBT] fleet — JetsonClaw1 heartbeat (profile attached)

## Resources
gpu: 89.7% | cpu: 62.3% | ram: 72.7% | temp: 48.9°C
throttle: false | power: 13.8W / 15.0W

## Alerts
none
```

### 5.4 Status Integration

`[I2I:STS]` status broadcasts include a summary line referencing the latest CONSTRAINT, BENCHMARK, and PROFILE:

```yaml
agent: jetsonclaw1
status: active
last_heartbeat: 2026-04-14T14:35:00Z
current_work: "FLUX CUDA inference — tensor matmul workload"
capacity: 10%  # low — GPU at 89.7%
hardware_profile: ".i2i/profiles/2026-04-14T14:30:00Z.json"
hardware_constraints: ".i2i/constraints.json"
hardware_benchmarks: ".i2i/benchmarks.json"
alerts:
  - type: "thermal_warning"
    message: "GPU temp 48.9°C, 2.9°C below throttle threshold"
```

---

## 6. Fleet Decision Integration

### 6.1 CONSTRAINT → Task Delegation

When a fleet agent (typically Oracle1 or the fleet orchestrator) decides to delegate a task, it checks the receiver's CONSTRAINT profile:

```python
def can_accept_task(task, agent_constraints):
    """Check if an agent's hardware can handle a task."""

    # Memory check
    if task.estimated_vram_bytes > agent_constraints.memory.vram_available_bytes * 0.8:
        return False, "insufficient VRAM"

    # ISA extension check
    required_extensions = task.required_isa_extensions
    supported = set(agent_constraints.compute.supported_isa_extensions)
    if not required_extensions.issubset(supported):
        missing = required_extensions - supported
        return False, f"missing ISA extensions: {missing}"

    # Energy budget check
    estimated_joules = task.estimated_opcodes * agent_constraints.power.tdp_watts * 0.001
    if estimated_joules > agent_constraints.power.energy_budget_joules_per_hour * 0.5:
        return False, "exceeds energy budget"

    # Storage check
    if task.required_disk_bytes > agent_constraints.storage.boot_available_bytes * 0.5:
        return False, "insufficient storage"

    # Thermal headroom
    if agent_constraints.thermal.current_throttle_state != "none":
        return False, "agent is thermal throttling"

    return True, "ok"
```

**Real example:** Oracle1 wants to assign a tensor matmul workload requiring 3GB VRAM and tensor extensions (0xC0–0xCF). JetsonClaw1's CONSTRAINT shows 4.2GB available VRAM and `"tensor_0xC0"` in supported extensions. The task is accepted.

### 6.2 BENCHMARK → Vocabulary Pruning Thresholds

Oracle1 uses BENCHMARK results to set vocabulary pruning targets:

```python
def compute_pruning_target(benchmark, max_acceptable_overhead_ratio=1.25):
    """Determine maximum vocabulary size before performance degrades unacceptably."""

    degradation_curve = benchmark.vocabulary.degradation_curve

    # Find the largest vocabulary size where overhead <= max_acceptable_overhead_ratio
    for entry_count_str, overhead_ratio in sorted(degradation_curve.items(), key=lambda x: int(x[0].split("_")[1])):
        entry_count = int(entry_count_str.split("_")[1])
        if overhead_ratio <= max_acceptable_overhead_ratio:
            max_entries = entry_count
        else:
            break

    # Adjust for cache hit rate — if cache is small, prune more aggressively
    # (cache_miss_penalty_us comes from PROFILE, not BENCHMARK, but we estimate here)
    cache_size_estimate = benchmark.vocabulary.vocab_lookup_ns * 0.001  # rough cache sizing

    return {
        "max_vocabulary_entries": max_entries,
        "target_overhead_ratio": max_acceptable_overhead_ratio,
        "recommended_prune_to": int(max_entries * 0.85),  # 15% safety margin
        "interpretation_overhead": benchmark.vocabulary.vocab_interpretation_overhead_ratio
    }
```

**Real example:** JetsonClaw1's BENCHMARK shows `entries_1000` has a 1.12x overhead and `entries_1500` has a 1.34x overhead. With a 1.25x max acceptable overhead, the pruning target is 1000 entries (the last entry below threshold). Oracle1 prunes the vocabulary to 850 entries (15% safety margin) when generating edge profiles for JetsonClaw1.

### 6.3 PROFILE → Fleet Health Dashboard

The fleet health dashboard aggregates PROFILE data from all agents:

```
┌─────────────────────────────────────────────────────────────┐
│  COCAPN FLEET HEALTH — 2026-04-14 14:35 UTC                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AGENT          CPU    GPU    RAM    TEMP    POWER  STATUS  │
│  ─────────────────────────────────────────────────────────  │
│  Oracle1 🔮     23%    N/A    4.2G   N/A     cloud  active  │
│  JetsonClaw1 ⚡ 62%    90%    6.2G   48.9°C  13.8W  busy    │
│  Babel 🌐        8%    N/A    1.8G   N/A     cloud  idle    │
│                                                             │
│  ALERTS:                                                     │
│  ⚠ JetsonClaw1: GPU at 90%, 2.9°C below throttle           │
│  ⚠ JetsonClaw1: Vocabulary cache hit rate 82.3%            │
│                                                             │
│  FLEET ENERGY: 0.87 kWh this session                        │
│  FLEET TRUST:  avg Integrity 0.91, avg Expertise 0.88      │
│  MESSAGES:  324 sent, 518 received, 0 failures             │
└─────────────────────────────────────────────────────────────┘
```

The dashboard queries the latest PROFILE from each agent's `.i2i/profiles/` directory and renders the resource utilization, alerts, and fleet-wide aggregates. Thermal warnings trigger visual alerts. Vocabulary cache hit rates below 0.75 trigger a recommendation to Oracle1 to re-prune.

---

## Appendix A — Jetson Orin Nano 8GB Reference Specification

The following are the manufacturer specifications for the Jetson Orin Nano 8GB module, used as the reference platform for all CONSTRAINT, BENCHMARK, and PROFILE values in this specification.

| Parameter | Value | Notes |
|-----------|-------|-------|
| **SoC** | NVIDIA Tegra T234 | "Orin" generation |
| **CPU** | 6 × Arm Cortex-A78AE v8.2 64-bit | Up to 1.5 GHz, no SMT |
| **GPU** | 1024-core NVIDIA Ampere | 32 Tensor Cores (3rd gen) |
| **AI Performance** | 40 TOPS (INT8), 80 TOPS (FP16) | Sparse: 80 TOPS (INT8) |
| **Memory** | 8 GiB LPDDR5, 128-bit bus | 68.3 GB/s bandwidth, shared CPU/GPU |
| **Video Encoder** | 1 × NVENC (Ampere) | H.264, HEVC, AV1 decode |
| **Video Decoder** | 2 × NVDEC | |
| **Display** | 2 × HDMI 2.1 (via carrier board) | Up to 4K60 |
| **TDP** | 7W – 15W configurable | MAXN mode, 4 power profiles |
| **Power Connector** | DC barrel jack 19V | |
| **Storage (module)** | eMMC 5.1 | On some SKUs; dev kit uses NVMe |
| **Storage (carrier)** | M.2 Key M NVMe slot | PCIe Gen4 x1 (or x4 on some carriers) |
| **USB** | 4 × USB 3.2, 2 × USB 2.0 | |
| **Ethernet** | 1 × 10/100/1000BASE-T | Realtek RTL8111 |
| **WiFi** | Wi-Fi 6 (802.11ax) | |
| **Bluetooth** | 5.1 | |
| **PCIe** | 1 × PCIe Gen4 x4 (slot) | For NVMe or other devices |
| **GPIO** | 40-pin header | Compatible with Raspberry Pi GPIO |
| **I2C/SPI/UART** | Multiple instances | Via 40-pin header |
| **Thermal** | Passive heatsink (included) | 0–50°C operating range |
| **Dimensions (module)** | 70mm × 45mm | SoM form factor |
| **JetPack SDK** | 6.x (Linux 6.1 kernel) | CUDA 12.x, TensorRT 8.x |

### Memory Architecture Note

The Jetson Orin Nano uses a **unified memory architecture** (UMA). The 8 GiB LPDDR5 is shared between CPU and GPU. There is no dedicated VRAM — the GPU accesses system RAM through a high-bandwidth interconnect. This means:

- `vram_total_bytes == ram_total_bytes` (both reference the same 8 GiB physical memory)
- CPU and GPU compete for the same bandwidth (68.3 GB/s total)
- Memory allocated for GPU tensors is unavailable to the CPU and vice versa
- The `vram_available_bytes` field in CONSTRAINT represents the amount of memory currently allocable for GPU use, which is always less than `ram_available_bytes`

This is critical for fleet task delegation: a task claiming "only 1GB VRAM needed" actually consumes 1GB of shared system memory, reducing what's available for CPU-side FLUX VM execution, vocabulary storage, and the OS.

---

## Appendix B — Priority Level Definitions

| Priority | Name | Processing SLA | Description |
|----------|------|----------------|-------------|
| **P0** | Critical | < 1 second | Must be processed immediately. Thermal shutdown, OOM, hardware failure. Fleet-wide alert. |
| **P1** | High | < 5 seconds | Time-sensitive operational data. Active thermal throttling, memory pressure, GC storms. Route to affected agents immediately. |
| **P2** | Standard | < 60 seconds | Important but not time-critical. Constraints, benchmarks, periodic profiles. Queue for async processing. |
| **P3** | Low | < 1 hour | Informational. Historical profiles, benchmark comparisons, documentation updates. Process during idle time. |

---

## Appendix C — FLUX Instruction Format Quick Reference

BENCHMARK results report throughput per format. This appendix defines the formats for cross-reference.

| Format | Opcode Ranges | Byte Width | Encoding | Description |
|--------|---------------|------------|----------|-------------|
| **A** | 0x00–0x07, 0xF0–0xFF | 1 byte | `[opcode]` | No operands. HALT, NOP, RET, BRK, system ops. Fastest to decode. |
| **B** | 0x08–0x0F | 2 bytes | `[opcode][rd]` | Single register operand. INC, DEC, PUSH, POP. |
| **C** | 0x10–0x17 | 2 bytes | `[opcode][imm8]` | Single 8-bit immediate. SYS, TRAP, YIELD. |
| **D** | 0x18–0x1F | 3 bytes | `[opcode][rd][imm8]` | Register + 8-bit immediate. MOVI, ADDI. |
| **E** | 0x20–0x3F, 0x50–0xBF | 4 bytes | `[opcode][rd][rs1][rs2]` | Three registers. Arithmetic, A2A, confidence, viewpoint, sensor, tensor. The most common format — majority of FLUX opcodes. |
| **F** | 0x40–0x47, 0xE0–0xEF | 4 bytes | `[opcode][rd][imm16_lo][imm16_hi]` | Register + 16-bit immediate. JMP, CALL, MOVI16. Long jumps. |
| **G** | 0x48–0x4F, 0xD0–0xDF | 5 bytes | `[opcode][rd][rs1][imm16_lo][imm16_hi]` | Two registers + 16-bit immediate. LOADOFF, STOREOFF, COPY, FILL. Slowest to decode and widest on wire. |

**BENCHMARK interpretation note:** On the Jetson Orin Nano, Format A achieves ~48.5 M opcodes/sec while Format G achieves ~29.8 M opcodes/sec — a 1.63x ratio. This is expected: Format G requires 5× the memory bandwidth for fetch and is more complex to decode. The ratio is **smaller** than on a desktop CPU (where the ratio is typically 2–3x) because the Jetson's memory bandwidth bottleneck means the difference between fetching 1 byte and 5 bytes is proportionally less significant relative to total memory latency. This is an important insight for vocabulary pruning: on bandwidth-constrained devices, using more, smaller instructions (Format A) is not as advantageous as on a desktop CPU.

---

*I2I Hardware Message Types v1.0 — JetsonClaw1 ⚡ (Yang)*
*Filling in the gaps. Iron sharpens iron.*
*2026-04-14*
