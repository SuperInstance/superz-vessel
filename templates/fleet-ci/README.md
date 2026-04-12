# 🚢 Fleet CI Pipeline Template

Standardized CI/CD workflows for every vessel in the SuperInstance fleet. Drop these files into your repo, add the config, and push.

![Fleet CI](https://img.shields.io/github/actions/workflow/status/superinstance/fleet-ci/fleet-ci.yml?branch=main&label=Fleet%20CI&style=for-the-badge)
![Quality Gates](https://img.shields.io/github/actions/workflow/status/superinstance/fleet-ci/fleet-quality-gates.yml?branch=main&label=Quality%20Gates&style=for-the-badge)
![Fleet Health](https://img.shields.io/badge/Fleet%20Health-100%25-brightgreen?style=for-the-badge)

---

## 📂 Files

| File | Purpose |
|------|---------|
| `fleet-ci.yml` | Main CI pipeline — loads config, dispatches language jobs, runs quality gates |
| `fleet-ci-python.yml` | Python workflow — ruff, pytest, mypy, Python 3.10–3.12 matrix |
| `fleet-ci-rust.yml` | Rust workflow — cargo fmt, clippy, test, release build, audit |
| `fleet-ci-typescript.yml` | TypeScript workflow — eslint, tsc, vitest/jest, build check |
| `fleet-quality-gates.yml` | Quality gate enforcement — coverage, lint, conformance, docs, security |
| `fleet-manifest-validator.yml` | Weekly fleet.json validation, repo accessibility, I2I peer checks |
| `fleet-bottle-monitor.yml` | Daily bottle scan — stale detection, critical alerts, dashboard |
| `.fleet-ci-config.json` | Per-repo configuration — language, thresholds, gate settings |
| `actions/` | Composite actions — load-config, lint, test, conformance, audit, quality-gates |

---

## 🚀 Quick Start

### 1. Copy the templates

```bash
# From your vessel repo root:
cp -r templates/fleet-ci/.github/workflows/*.yml .github/workflows/
cp templates/fleet-ci/.fleet-ci-config.json .
```

Or copy individual files as needed:
- **Python vessel** → `fleet-ci-python.yml`
- **Rust vessel** → `fleet-ci-rust.yml`
- **TypeScript vessel** → `fleet-ci-typescript.yml`
- **All vessels** → `fleet-ci.yml` (auto-detects language)

### 2. Configure your repo

Edit `.fleet-ci-config.json`:

```json
{
  "fleet_ci_version": "2.0",
  "language": "python",
  "test_command": "pytest -x -q",
  "coverage_threshold": 80,
  "conformance_tests": false,
  "quality_gates": {
    "block_merge_on_failure": true,
    "require_tests": true,
    "require_docs": false
  }
}
```

### 3. Set up secrets

In GitHub → Settings → Secrets and variables → Actions:

| Secret | Required | Description |
|--------|----------|-------------|
| `FLEET_TOKEN` | For fleet checks | PAT with `repo:read` access to fleet org |
| `CODECOV_TOKEN` | Optional | Codecov upload token |
| `SLACK_WEBHOOK_URL` | Optional | Slack webhook for failure notifications |

### 4. Enable branch protection

Settings → Branches → `main` → Add branch protection rule:
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- Add: `Fleet CI`, `Quality Gates`

---

## ⚙️ Configuration Reference

### `.fleet-ci-config.json`

```jsonc
{
  // Core settings
  "fleet_ci_version": "2.0",          // Config schema version
  "language": "python",               // python | rust | typescript
  "test_command": "pytest -x -q",     // Custom test command
  "lint_command": "",                 // Custom lint command (empty = auto-detect)
  "coverage_threshold": 80,           // Min coverage % to pass quality gate

  // FLUX ISA
  "conformance_tests": false,         // Enable FLUX ISA conformance tests
  "isa_version": "2.0",               // FLUX ISA version string

  // Quality gates
  "quality_gates": {
    "block_merge_on_failure": true,   // Fail CI on quality gate failure
    "require_tests": true,            // Tests must pass
    "require_docs": false,            // README + API docs required
    "require_conformance": false,     // Conformance tests must pass
    "require_security_audit": true,   // No critical vulnerabilities
    "coverage_threshold": 80,         // Per-gate coverage threshold
    "max_warnings": 0                 // Max lint warnings allowed
  },

  // Language-specific (optional — override defaults)
  "python": {
    "versions": ["3.10", "3.11", "3.12"],
    "run_mypy": false,
    "mypy_targets": "src tests"
  },
  "rust": {
    "versions": ["stable", "nightly"],
    "clippy_flags": "-D warnings",
    "release_build": true
  },
  "typescript": {
    "versions": ["18", "20"],
    "test_framework": "vitest"        // vitest | jest
  },

  // Fleet monitoring
  "fleet": {
    "validate_fleet_json": true,
    "check_i2i_messages": true,
    "verify_bottle_format": true,
    "bottle_max_age_days": 7
  }
}
```

---

## 🏗️ Architecture

### Pipeline Flow

```
Push / PR
    │
    ▼
┌──────────────┐
│  Load Config  │  ← .fleet-ci-config.json
└──────┬───────┘
       │
       ├──────────────────────────────┐
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│  🔍 Lint      │              │  🔒 Audit     │
└──────┬───────┘              └──────────────┘
       │
       ▼
┌──────────────┐
│  🧪 Test      │  ← matrix: versions
└──────┬───────┘
       │
       ▼ (if conformance_tests)
┌──────────────┐
│  ⚡ Conform.  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 🚦 Quality    │  ← block_merge check
│    Gates      │
└──────┬───────┘
       │
       ▼ (if failure)
┌──────────────┐
│ 📢 Notify     │  ← Slack webhook
└──────────────┘
```

### Composite Actions

Located in `actions/`, these are reusable building blocks:

| Action | Purpose |
|--------|---------|
| `load-config` | Parse `.fleet-ci-config.json`, output env vars |
| `lint` | Run language-appropriate linter |
| `test` | Run test suite with coverage |
| `conformance` | Run FLUX ISA conformance tests |
| `audit` | Run security audit (pip-audit, cargo-audit, npm audit) |
| `quality-gates` | Evaluate all gates, block merge if configured |

### Caching

All workflows cache dependencies automatically:
- **Python**: pip cache via `actions/setup-python` + ruff cache
- **Rust**: cargo registry, git, and build cache via `actions/cache`
- **TypeScript**: npm/pnpm/yarn cache via `actions/setup-node`

### Artifacts

| Artifact | Retention | Content |
|----------|-----------|---------|
| `test-results-*` | 14 days | JUnit XML, coverage reports |
| `conformance-results` | 30 days | Conformance test XML + JSON |
| `security-audit` | 30 days | Audit reports + summaries |
| `python-build` / `rust-release` / `ts-build` | 7 days | Build artifacts |

---

## 📊 Quality Gates

Quality gates are enforced in `fleet-quality-gates.yml`. Gates run as a **required status check** and can optionally **block merge**.

### Gate Details

| Gate | Default Threshold | Description |
|------|-------------------|-------------|
| Coverage | 80% | Line coverage for new code |
| Lint | 0 warnings | No critical lint errors |
| Conformance | 100% pass rate | FLUX ISA conformance (if configured) |
| Documentation | README required | README must exist (if `require_docs: true`) |
| Security | 0 critical | No critical/high vulnerabilities |

### Bypassing Gates

For urgent fixes, use workflow dispatch with `skip_quality_gates: true`:
```yaml
workflow_dispatch:
  inputs:
    skip_quality_gates: "true"
```

Or set `quality_gates.block_merge_on_failure: false` in config for non-blocking reporting.

---

## 🔍 Fleet Monitoring

### Manifest Validator (`fleet-manifest-validator.yml`)

Runs **every Monday at 06:00 UTC** or on-demand:
- ✅ Validates `fleet.json` schema
- 🔗 Checks all dependency vessel repos are accessible
- 🔗 Verifies I2I peer links (protocol, endpoint format)
- 📊 Generates health score (0–100)
- 🐛 Creates GitHub issue if health drops below 80%

### Bottle Monitor (`fleet-bottle-monitor.yml`)

Runs **daily at 08:00 UTC** or on-demand:
- 🍶 Scans all vessel repos for bottles
- ⚠️ Flags bottles unread > 7 days
- 🚨 Alerts on critical unread bottles
- 📊 Generates dashboard summary
- 📢 Creates/updates GitHub issue for alerts

---

## 🛠️ Extending

### Adding a new language

1. Create `fleet-ci-go.yml` (or your language)
2. Create `actions/lint/action.yml` — add your language branch
3. Create `actions/test/action.yml` — add your language branch
4. Update `actions/load-config/action.yml` — add version matrix output
5. Update this README

### Adding a new quality gate

1. Add job in `fleet-quality-gates.yml`
2. Add output in `actions/quality-gates/action.yml`
3. Update the quality report table

### Custom composite actions

Create a new directory under `actions/`:
```
actions/
  my-action/
    action.yml    # Composite action definition
    script.sh     # Helper scripts
```

Use in workflows:
```yaml
- uses: ./actions/my-action
  with:
    input: "value"
```

---

## 📋 Version History

| Version | Changes |
|---------|---------|
| 2.0 | Composite actions, quality gates as code, fleet monitoring |
| 1.0 | Initial monolithic CI workflow |

---

## 🤝 Contributing

1. Fork the `fleet-ci` template repo
2. Create a feature branch: `git checkout -b fleet/my-feature`
3. Commit changes with clear descriptions
4. Push and open a PR — Fleet CI runs automatically!
5. Ensure all quality gates pass before requesting review

---

_Built for the SuperInstance Fleet — standardized CI/CD across all vessels._
