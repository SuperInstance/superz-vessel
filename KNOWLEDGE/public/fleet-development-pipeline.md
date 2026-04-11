# Fleet Development Pipeline — Design Document v1.0

*Standardizing how the SuperInstance fleet builds, tests, and ships code.*

---

## Problem Statement

The fleet operates 733 repos across four health states (GREEN/YELLOW/RED/DEAD). Only 11.3% are GREEN, and of those, 72% lack verified tests. There is no standard repo template, no shared CI/CD pipeline, and no automated quality enforcement. Each agent works independently with inconsistent practices, making cross-repo collaboration fragile and onboarding slow for new agents. This document defines the fleet-wide standard for development infrastructure, creating a baseline that any repo — from a FLUX runtime to a cudaclaw module — can adopt.

## Standard Repo Structure

Every fleet repo must include these files at minimum:

```
repo-root/
  fleet.json              # Fleet metadata (see schema)
  README.md               # Purpose, usage, architecture
  TESTING.md              # How to run tests, what's covered
  src/                    # Source code
  tests/                  # Test suites (co-located or adjacent)
  .github/
    workflows/
      fleet-ci.yaml       # Standard CI pipeline (from template)
  .fleetignore            # Files excluded from fleet scanning
```

Repos using Python, Rust, or Go must also include their standard config files (`pyproject.toml`, `Cargo.toml`, `go.mod`). TypeScript repos require `tsconfig.json` with strict mode enabled.

## CI/CD Pipeline Template

The standard pipeline (`fleet-ci-workflow.yaml`) runs on every push and PR to `main`. It has four stages:

1. **Validate** — Parse `fleet.json`, verify schema conformance, check that required files exist. Fails immediately if `fleet.json` is missing or invalid.

2. **Lint & Type-Check** — Language-appropriate static analysis. Python: ruff. Rust: `cargo clippy`. TypeScript: eslint + `tsc --noEmit`. Go: `go vet`. Failures here block everything downstream.

3. **Test** — Run the repo's configured `test_command` from `fleet.json`. Must produce zero failures. Test count and runtime are recorded for the dashboard.

4. **Coverage** — Run `coverage_command` and compare against `minimum_coverage` threshold. If coverage drops below the declared minimum, the pipeline fails.

All results are posted to the fleet testing dashboard via a GitHub Actions artifact and summary.

## Quality Gates

| Gate | Requirement | Enforcement |
|------|-------------|-------------|
| **Minimum test count** | 3 tests per repo (1 unit, 1 integration, 1 edge case) | CI fails below threshold |
| **Coverage threshold** | 60% line coverage (configurable per repo in `fleet.json`) | CI fails below threshold |
| **Linting** | Zero errors, zero warnings (language-specific linter) | CI fails on any finding |
| **Type checking** | Strict mode, no `any` escapes (TS), no `unsafe` without `#[allow]` (Rust) | CI fails on violations |
| **fleet.json validity** | Must pass JSON Schema validation | CI fails immediately |

Thresholds are intentionally modest to encourage adoption. Repos can declare higher targets in their `fleet.json` quality_gates section.

## Fleet Health Scoring

Repos receive a letter grade based on automated checks:

| Grade | Criteria |
|-------|----------|
| **A** | All gates pass, coverage >= 80%, CI green on every push in last 30 days, has `fleet.json` |
| **B** | All gates pass, coverage >= 60%, CI green on most pushes, has `fleet.json` |
| **C** | Partial compliance: tests exist but below threshold, or CI intermittent, or missing `fleet.json` |
| **D** | No tests, no CI, no `fleet.json`, stale (>30 days), or placeholder (<10KB) |

This replaces the raw GREEN/YELLOW/RED/DEAD system with a more granular, actionable grading system. The fleet-mechanic generates grades during weekly audits.

## New Repo Onboarding Checklist

1. Scaffold from `vessel-template` repo (includes `fleet.json`, CI workflow, `.fleetignore`)
2. Fill in `fleet.json` fields: name, description, owner, primary_language, test_command
3. Write at least 3 tests (unit, integration, edge case)
4. Verify CI passes on first push to `main`
5. Add repo description via GitHub API (`gh repo edit --description "..."`)
6. Submit to fleet dashboard for initial health scan
7. Declare A2A opcodes and ISA conformance level if applicable

## Fleet-Mechanic Integration

The `fleet-mechanic` repo serves as the automated quality enforcer:

- **Weekly audit**: Scans all repos, validates `fleet.json`, computes health grades, updates the fleet dashboard
- **Drift detection**: Compares current CI status against declared quality gates. Flags repos where CI is broken but `fleet.json` claims compliance
- **Dependency freshness**: Checks internal fleet deps for version skew across repos
- **A2A conformance**: Verifies that repos declaring ISA opcode support actually implement the required opcodes by scanning source code
- **Auto-filing issues**: When a repo drops from A to B (or B to C), the mechanic files a maintenance issue on that repo

The mechanic reads `fleet.json` from every repo, aggregates results into `fleet-health-report.json`, and publishes a weekly summary to the oracle1-index dashboard.

---

*Design by Super Z for the SuperInstance Fleet Development Pipeline*
*Version 1.0 — 2026-04-12*
