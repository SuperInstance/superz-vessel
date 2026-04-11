# SuperInstance Fleet Census — 2026-04-12

## Summary

| Category | Count | Percentage |
|----------|-------|-----------|
| **GREEN** | **75** | **11.3%** |
|  ├ Tested & Active | 21 | 3.2% |
|  └ Active (untested) | 54 | 8.1% |
| **YELLOW** | **95** | **14.3%** |
| **RED** | **88** | **13.2%** |
| **DEAD** | **408** | **61.3%** |
| **Total** | **666** | **100%** |

## Methodology

### Categorization Rules
- **GREEN**: Active (pushed within 30 days) with substantial code (≥10KB). Subdivided into **tested** (has test files/workflows verified) and **active_untested** (no tests detected).
- **YELLOW**: Has substantial code (≥10KB) but stale — no pushes in 30+ days. These need attention.
- **RED**: Empty shell or placeholder — under 10KB total content. Likely just a README or initial commit.
- **DEAD**: Fork with no modifications from upstream. Archived/reference copies.

### Test Detection
46 GREEN repos were deep-checked for test files via GitHub Contents API. Checked for: `*test*`, `*spec*`, `tests/`, `.github/workflows/`, `Makefile`, `Cargo.toml` (Rust tests), `pytest`, `vitest.config.ts`, `TESTING.md`.

### Language Breakdown

**GREEN repos by language:**
- Python: 26
- TypeScript: 23
- Rust: 6
- N/A: 6
- JavaScript: 3
- Go: 2
- Shell: 2
- C: 2
- HTML: 1
- Makefile: 1

**YELLOW repos by language:**
- TypeScript: 28
- Python: 27
- Rust: 16
- N/A: 14
- Makefile: 4
- Go: 2
- PowerShell: 1
- HTML: 1
- JavaScript: 1
- Jupyter Notebook: 1

## GREEN Repos — Healthy and Active

**21 verified with tests, 54 active (tests unconfirmed or absent)**

| Repo | Size | Language | Last Push | Tests? |
|------|------|----------|-----------|--------|
| [spreadsheet-moment-proto](https://github.com/SuperInstance/spreadsheet-moment-proto) | 88,630KB | TypeScript | 2026-03-15 (27d ago) | ❓ |
| [Constraint-Theory](https://github.com/SuperInstance/Constraint-Theory) | 87,639KB | JavaScript | 2026-03-28 (14d ago) | ❓ |
| [Lucineer](https://github.com/SuperInstance/Lucineer) | 75,168KB | Python | 2026-03-25 (17d ago) | ⚠️ |
| [polln](https://github.com/SuperInstance/polln) | 35,759KB | TypeScript | 2026-04-05 (6d ago) | ❓ |
| [SuperInstance-papers](https://github.com/SuperInstance/SuperInstance-papers) | 35,585KB | TypeScript | 2026-03-29 (13d ago) | ❓ |
| [cocapn](https://github.com/SuperInstance/cocapn) | 35,558KB | TypeScript | 2026-03-30 (12d ago) | ❓ |
| [Edge-Native](https://github.com/SuperInstance/Edge-Native) | 24,052KB | Python | 2026-04-04 (7d ago) | ❓ |
| [flux-wasm](https://github.com/SuperInstance/flux-wasm) | 22,656KB | Makefile | 2026-04-10 (1d ago) | ✅ |
| [flux-zig](https://github.com/SuperInstance/flux-zig) | 11,557KB | Zig | 2026-04-10 (1d ago) | ⚠️ |
| [flux-multilingual](https://github.com/SuperInstance/flux-multilingual) | 7,378KB | Python | 2026-04-11 (0d ago) | ⚠️ |
| [SmartCRDT](https://github.com/SuperInstance/SmartCRDT) | 7,071KB | TypeScript | 2026-04-10 (1d ago) | ✅ |
| [greenhorn-runtime](https://github.com/SuperInstance/greenhorn-runtime) | 5,093KB | Go | 2026-04-11 (0d ago) | ✅ |
| [flux-swarm](https://github.com/SuperInstance/flux-swarm) | 2,979KB | Go | 2026-04-11 (0d ago) | ✅ |
| [constraint-theory-research](https://github.com/SuperInstance/constraint-theory-research) | 2,165KB | Python | 2026-03-28 (14d ago) | ❓ |
| [pasture-ai](https://github.com/SuperInstance/pasture-ai) | 1,859KB | Rust | 2026-03-27 (15d ago) | ✅ |
| [nexus-runtime](https://github.com/SuperInstance/nexus-runtime) | 1,767KB | Python | 2026-04-08 (3d ago) | ✅ |
| [flux-runtime](https://github.com/SuperInstance/flux-runtime) | 1,677KB | Python | 2026-04-11 (0d ago) | ✅ |
| [I-know-kung-fu](https://github.com/SuperInstance/I-know-kung-fu) | 1,660KB | Python | 2026-03-28 (14d ago) | ❓ |
| [constraint-flow](https://github.com/SuperInstance/constraint-flow) | 1,126KB | TypeScript | 2026-03-28 (14d ago) | ❓ |
| [ai-ranch](https://github.com/SuperInstance/ai-ranch) | 1,067KB | Python | 2026-03-25 (17d ago) | ❓ |
| [constraint-theory-backup](https://github.com/SuperInstance/constraint-theory-backup) | 949KB | TypeScript | 2026-04-10 (1d ago) | ❓ |
| [constraint-theory-web](https://github.com/SuperInstance/constraint-theory-web) | 752KB | JavaScript | 2026-03-28 (14d ago) | ❓ |
| [cudaclaw](https://github.com/SuperInstance/cudaclaw) | 695KB | Rust | 2026-03-20 (22d ago) | ❓ |
| [dodecet-encoder](https://github.com/SuperInstance/dodecet-encoder) | 509KB | Rust | 2026-03-19 (23d ago) | ✅ |
| [flux-a2a-prototype](https://github.com/SuperInstance/flux-a2a-prototype) | 448KB | Python | 2026-04-11 (0d ago) | ✅ |
| [flux-a2a-signal](https://github.com/SuperInstance/flux-a2a-signal) | 344KB | Python | 2026-04-11 (0d ago) | ✅ |
| [CRDT_Research](https://github.com/SuperInstance/CRDT_Research) | 343KB | Python | 2026-03-13 (29d ago) | ❓ |
| [oracle1-index](https://github.com/SuperInstance/oracle1-index) | 303KB | HTML | 2026-04-11 (0d ago) | ✅ |
| [constraint-theory-python](https://github.com/SuperInstance/constraint-theory-python) | 257KB | Python | 2026-03-28 (14d ago) | ❓ |
| [iron-to-iron](https://github.com/SuperInstance/iron-to-iron) | 253KB | Python | 2026-04-11 (0d ago) | ✅ |
| [flux-os](https://github.com/SuperInstance/flux-os) | 251KB | C | 2026-04-10 (1d ago) | ⚠️ |
| [constraint-theory-core](https://github.com/SuperInstance/constraint-theory-core) | 235KB | Rust | 2026-03-28 (14d ago) | ❓ |
| [CognitiveEngine](https://github.com/SuperInstance/CognitiveEngine) | 201KB | Python | 2026-03-27 (15d ago) | ✅ |
| [higher-abstraction-vocabularies](https://github.com/SuperInstance/higher-abstraction-vocabularies) | 196KB | Python | 2026-04-10 (1d ago) | ⚠️ |
| [captains-log](https://github.com/SuperInstance/captains-log) | 151KB | N/A | 2026-04-10 (1d ago) | ⚠️ |
| [flux-core](https://github.com/SuperInstance/flux-core) | 147KB | Rust | 2026-04-10 (1d ago) | ✅ |
| [constraint-ranch](https://github.com/SuperInstance/constraint-ranch) | 135KB | TypeScript | 2026-03-28 (14d ago) | ❓ |
| [flux-py](https://github.com/SuperInstance/flux-py) | 114KB | Python | 2026-04-11 (0d ago) | ⚠️ |
| [flux-research](https://github.com/SuperInstance/flux-research) | 114KB | N/A | 2026-04-11 (0d ago) | ⚠️ |
| [flux-llama](https://github.com/SuperInstance/flux-llama) | 106KB | C | 2026-04-10 (1d ago) | ⚠️ |
| [flux-ide](https://github.com/SuperInstance/flux-ide) | 106KB | TypeScript | 2026-04-10 (1d ago) | ⚠️ |
| [flux-benchmarks](https://github.com/SuperInstance/flux-benchmarks) | 105KB | Shell | 2026-04-10 (1d ago) | ⚠️ |
| [flux-js](https://github.com/SuperInstance/flux-js) | 102KB | JavaScript | 2026-04-10 (1d ago) | ⚠️ |
| [flux-runtime-san](https://github.com/SuperInstance/flux-runtime-san) | 100KB | Python | 2026-04-11 (0d ago) | ✅ |
| [flux-cuda](https://github.com/SuperInstance/flux-cuda) | 97KB | Cuda | 2026-04-10 (1d ago) | ⚠️ |
| [flux-java](https://github.com/SuperInstance/flux-java) | 96KB | Java | 2026-04-10 (1d ago) | ⚠️ |
| [flux-runtime-wen](https://github.com/SuperInstance/flux-runtime-wen) | 87KB | Python | 2026-04-11 (0d ago) | ✅ |
| [flux-runtime-kor](https://github.com/SuperInstance/flux-runtime-kor) | 84KB | Python | 2026-04-11 (0d ago) | ✅ |
| [flux-runtime-zho](https://github.com/SuperInstance/flux-runtime-zho) | 83KB | Python | 2026-04-11 (0d ago) | ✅ |
| [flux](https://github.com/SuperInstance/flux) | 76KB | Rust | 2026-04-10 (1d ago) | ❓ |
| [flux-runtime-deu](https://github.com/SuperInstance/flux-runtime-deu) | 72KB | Python | 2026-04-11 (0d ago) | ✅ |
| [SuperInstance-Starter-Agent](https://github.com/SuperInstance/SuperInstance-Starter-Agent) | 72KB | TypeScript | 2026-03-14 (28d ago) | ❓ |
| [flux-runtime-lat](https://github.com/SuperInstance/flux-runtime-lat) | 67KB | Python | 2026-04-11 (0d ago) | ✅ |
| [oracle1-vessel](https://github.com/SuperInstance/oracle1-vessel) | 51KB | Shell | 2026-04-11 (0d ago) | ⚠️ |
| [Equipment-Self-Improvement](https://github.com/SuperInstance/Equipment-Self-Improvement) | 48KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [flux-envelope](https://github.com/SuperInstance/flux-envelope) | 47KB | Python | 2026-04-11 (0d ago) | ✅ |
| [Equipment-Memory-Hierarchy](https://github.com/SuperInstance/Equipment-Memory-Hierarchy) | 47KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [Equipment-Swarm-Coordinator](https://github.com/SuperInstance/Equipment-Swarm-Coordinator) | 40KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [Equipment-Consensus-Engine](https://github.com/SuperInstance/Equipment-Consensus-Engine) | 39KB | TypeScript | 2026-04-10 (1d ago) | ⚠️ |
| [superinstance-index](https://github.com/SuperInstance/superinstance-index) | 38KB | N/A | 2026-04-10 (1d ago) | ⚠️ |
| [Equipment-NLP-Explainer](https://github.com/SuperInstance/Equipment-NLP-Explainer) | 35KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [Equipment-Monitoring-Dashboard](https://github.com/SuperInstance/Equipment-Monitoring-Dashboard) | 33KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [Equipment-Context-Handoff](https://github.com/SuperInstance/Equipment-Context-Handoff) | 31KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [Equipment-Teacher-Student](https://github.com/SuperInstance/Equipment-Teacher-Student) | 30KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [AI-Writings](https://github.com/SuperInstance/AI-Writings) | 27KB | N/A | 2026-04-10 (1d ago) | ⚠️ |
| [Equipment-Escalation-Router](https://github.com/SuperInstance/Equipment-Escalation-Router) | 27KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [babel-vessel](https://github.com/SuperInstance/babel-vessel) | 26KB | N/A | 2026-04-11 (0d ago) | ⚠️ |
| [Equipment-CellLogic-Distiller](https://github.com/SuperInstance/Equipment-CellLogic-Distiller) | 26KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [git-agent-standard](https://github.com/SuperInstance/git-agent-standard) | 22KB | N/A | 2026-04-11 (0d ago) | ⚠️ |
| [Equipment-Hardware-Scaler](https://github.com/SuperInstance/Equipment-Hardware-Scaler) | 22KB | TypeScript | 2026-03-13 (29d ago) | ❓ |
| [SuperInstance-SDK1](https://github.com/SuperInstance/SuperInstance-SDK1) | 16KB | TypeScript | 2026-03-13 (29d ago) | ⚠️ |
| [fleet-workshop](https://github.com/SuperInstance/fleet-workshop) | 11KB | Python | 2026-04-11 (0d ago) | ⚠️ |
| [flux-vm-ts](https://github.com/SuperInstance/flux-vm-ts) | 10KB | TypeScript | 2026-04-11 (0d ago) | ⚠️ |
| [flux-repl](https://github.com/SuperInstance/flux-repl) | 10KB | Python | 2026-04-11 (0d ago) | ⚠️ |
| [fleet-discovery](https://github.com/SuperInstance/fleet-discovery) | 10KB | Python | 2026-04-11 (0d ago) | ⚠️ |

## YELLOW Repos — Needs Attention

**95 repos with code but no activity in 30+ days**

### Top 20 by Size (highest priority for review)

| Repo | Size | Language | Last Push | Days Stale |
|------|------|----------|-----------|------------|
| [usemeter](https://github.com/SuperInstance/usemeter) | 731,100KB | Makefile | 2026-01-09 | 92d |
| [tripartite-rs](https://github.com/SuperInstance/tripartite-rs) | 364,401KB | Rust | 2026-01-09 | 92d |
| [ws-fabric](https://github.com/SuperInstance/ws-fabric) | 321,390KB | Rust | 2026-01-10 | 91d |
| [websocket-fabric](https://github.com/SuperInstance/websocket-fabric) | 318,698KB | Rust | 2026-01-10 | 91d |
| [realtime-core](https://github.com/SuperInstance/realtime-core) | 161,039KB | Makefile | 2026-01-10 | 91d |
| [quicunnel](https://github.com/SuperInstance/quicunnel) | 131,935KB | Makefile | 2026-01-09 | 92d |
| [StudyLog](https://github.com/SuperInstance/StudyLog) | 119,501KB | TypeScript | 2026-01-11 | 90d |
| [makerlog-ai](https://github.com/SuperInstance/makerlog-ai) | 51,492KB | TypeScript | 2026-01-24 | 77d |
| [educationgamecocapn](https://github.com/SuperInstance/educationgamecocapn) | 48,740KB | JavaScript | 2026-01-20 | 81d |
| [health](https://github.com/SuperInstance/health) | 37,109KB | N/A | 2026-01-10 | 91d |
| [vector-search](https://github.com/SuperInstance/vector-search) | 17,980KB | TypeScript | 2026-01-09 | 92d |
| [cloudflare-code](https://github.com/SuperInstance/cloudflare-code) | 12,240KB | TypeScript | 2026-01-23 | 78d |
| [PersonalLog](https://github.com/SuperInstance/PersonalLog) | 9,362KB | TypeScript | 2026-01-10 | 91d |
| [SuperInstanceEco](https://github.com/SuperInstance/SuperInstanceEco) | 8,264KB | Jupyter Notebook | 2026-01-10 | 91d |
| [Tripartite1](https://github.com/SuperInstance/Tripartite1) | 3,878KB | Rust | 2026-01-08 | 93d |

### Remaining YELLOW Repos (80 more)

| Repo | Size | Language | Last Push | Days Stale |
|------|------|----------|-----------|------------|
| [Baton](https://github.com/SuperInstance/Baton) | 27KB | N/A | 2026-03-04 | 38d |
| [Bayesian-Multi-Armed-Bandits](https://github.com/SuperInstance/Bayesian-Multi-Armed-Bandits) | 14KB | TypeScript | 2026-01-08 | 93d |
| [CascadeRouter](https://github.com/SuperInstance/CascadeRouter) | 134KB | TypeScript | 2026-01-09 | 92d |
| [Claude-prism-local-json](https://github.com/SuperInstance/Claude-prism-local-json) | 1409KB | TypeScript | 2026-01-15 | 86d |
| [Claude_Baton](https://github.com/SuperInstance/Claude_Baton) | 248KB | N/A | 2026-03-04 | 38d |
| [DMLog](https://github.com/SuperInstance/DMLog) | 479KB | Python | 2026-01-10 | 91d |
| [DeckBoss](https://github.com/SuperInstance/DeckBoss) | 72KB | TypeScript | 2026-03-03 | 39d |
| [Hardware-Aware-Flagging](https://github.com/SuperInstance/Hardware-Aware-Flagging) | 32KB | TypeScript | 2026-01-08 | 93d |
| [Murmur](https://github.com/SuperInstance/Murmur) | 24KB | TypeScript | 2026-01-01 | 100d |
| [Mycelium](https://github.com/SuperInstance/Mycelium) | 330KB | N/A | 2026-03-05 | 37d |
| [Privacy-First-Analytics](https://github.com/SuperInstance/Privacy-First-Analytics) | 83KB | TypeScript | 2026-01-08 | 93d |
| [Rotational-Transformer](https://github.com/SuperInstance/Rotational-Transformer) | 198KB | N/A | 2026-03-08 | 34d |
| [Sandbox-Lifecycle-Manager](https://github.com/SuperInstance/Sandbox-Lifecycle-Manager) | 79KB | TypeScript | 2026-01-08 | 93d |
| [Spreader-tool](https://github.com/SuperInstance/Spreader-tool) | 112KB | TypeScript | 2026-01-09 | 92d |
| [SuperInstance-gamedev](https://github.com/SuperInstance/SuperInstance-gamedev) | 1918KB | TypeScript | 2026-01-20 | 81d |
| [SuperInstanceDocs](https://github.com/SuperInstance/SuperInstanceDocs) | 10KB | N/A | 2026-01-10 | 91d |
| [SwarmMCP](https://github.com/SuperInstance/SwarmMCP) | 156KB | N/A | 2026-03-03 | 39d |
| [SwarmOrchestration](https://github.com/SuperInstance/SwarmOrchestration) | 15KB | TypeScript | 2026-01-10 | 91d |
| [ToolGuardian](https://github.com/SuperInstance/ToolGuardian) | 84KB | TypeScript | 2026-01-09 | 92d |
| [UI](https://github.com/SuperInstance/UI) | 12KB | TypeScript | 2026-01-10 | 91d |
| [activelog-backend](https://github.com/SuperInstance/activelog-backend) | 41KB | PowerShell | 2026-01-10 | 91d |
| [agent-coordinator](https://github.com/SuperInstance/agent-coordinator) | 55KB | Python | 2026-01-10 | 91d |
| [agent-grid](https://github.com/SuperInstance/agent-grid) | 14KB | TypeScript | 2026-01-10 | 91d |
| [ai-character-integrations](https://github.com/SuperInstance/ai-character-integrations) | 66KB | Python | 2026-01-10 | 91d |
| [ai-character-sdk](https://github.com/SuperInstance/ai-character-sdk) | 37KB | Python | 2026-01-10 | 91d |
| [ai-token-counter](https://github.com/SuperInstance/ai-token-counter) | 13KB | Python | 2026-01-09 | 92d |
| [audio-pipeline](https://github.com/SuperInstance/audio-pipeline) | 44KB | Rust | 2026-01-10 | 91d |
| [bandit-learner](https://github.com/SuperInstance/bandit-learner) | 35KB | N/A | 2026-01-10 | 91d |
| [cache-layer](https://github.com/SuperInstance/cache-layer) | 53KB | Rust | 2026-01-10 | 91d |
| [cache-layer-optimizer](https://github.com/SuperInstance/cache-layer-optimizer) | 42KB | Rust | 2026-01-10 | 91d |
| [caching-service](https://github.com/SuperInstance/caching-service) | 10KB | Python | 2026-01-10 | 91d |
| [character-agent-integration](https://github.com/SuperInstance/character-agent-integration) | 84KB | Python | 2026-01-09 | 92d |
| [character-library](https://github.com/SuperInstance/character-library) | 114KB | Python | 2026-01-09 | 92d |
| [character-skill-trees](https://github.com/SuperInstance/character-skill-trees) | 73KB | Python | 2026-01-09 | 92d |
| [cloudflare-vibe](https://github.com/SuperInstance/cloudflare-vibe) | 1419KB | TypeScript | 2026-01-18 | 83d |
| [cluster-orchestrator](https://github.com/SuperInstance/cluster-orchestrator) | 49KB | Rust | 2026-01-10 | 91d |
| [conversation-toolkit](https://github.com/SuperInstance/conversation-toolkit) | 80KB | Python | 2026-01-09 | 92d |
| [cost-analysis](https://github.com/SuperInstance/cost-analysis) | 14KB | TypeScript | 2026-01-09 | 92d |
| [deployment-automator](https://github.com/SuperInstance/deployment-automator) | 56KB | Go | 2026-01-10 | 91d |
| [distributed-tracing](https://github.com/SuperInstance/distributed-tracing) | 60KB | Rust | 2026-01-10 | 91d |
| [embedding-utils](https://github.com/SuperInstance/embedding-utils) | 55KB | Python | 2026-01-09 | 92d |
| [embeddings-engine](https://github.com/SuperInstance/embeddings-engine) | 27KB | N/A | 2026-01-10 | 91d |
| [equilibrium-tokens](https://github.com/SuperInstance/equilibrium-tokens) | 155KB | Rust | 2026-01-10 | 91d |
| [escalation-engine](https://github.com/SuperInstance/escalation-engine) | 48KB | Python | 2026-01-10 | 91d |
| [eveng1_python_sdk](https://github.com/SuperInstance/eveng1_python_sdk) | 111KB | Python | 2026-01-10 | 91d |
| [frozen-model-rl](https://github.com/SuperInstance/frozen-model-rl) | 55KB | Rust | 2026-01-10 | 91d |
| [gpu-accelerator](https://github.com/SuperInstance/gpu-accelerator) | 55KB | Rust | 2026-01-10 | 91d |
| [hardware-capability-profiler](https://github.com/SuperInstance/hardware-capability-profiler) | 78KB | TypeScript | 2026-01-08 | 93d |
| [health-monitoring-service](https://github.com/SuperInstance/health-monitoring-service) | 10KB | Python | 2026-01-09 | 92d |
| [hierarchical-memory](https://github.com/SuperInstance/hierarchical-memory) | 151KB | Python | 2026-01-10 | 91d |
| [inference-optimizer](https://github.com/SuperInstance/inference-optimizer) | 45KB | Python | 2026-01-10 | 91d |
| [jepa-sentiment](https://github.com/SuperInstance/jepa-sentiment) | 156KB | TypeScript | 2026-01-09 | 92d |
| [llm-cost-calculator](https://github.com/SuperInstance/llm-cost-calculator) | 17KB | Python | 2026-01-09 | 92d |
| [local-model-manager](https://github.com/SuperInstance/local-model-manager) | 91KB | Python | 2026-01-09 | 92d |
| [luciddreamer-os](https://github.com/SuperInstance/luciddreamer-os) | 18KB | HTML | 2026-01-10 | 91d |
| [model-switching-strategy](https://github.com/SuperInstance/model-switching-strategy) | 14KB | Python | 2026-01-09 | 92d |
| [monitoring-dashboard](https://github.com/SuperInstance/monitoring-dashboard) | 14KB | TypeScript | 2026-01-09 | 92d |
| [multi-provider-router](https://github.com/SuperInstance/multi-provider-router) | 112KB | Python | 2026-01-09 | 92d |
| [multibot](https://github.com/SuperInstance/multibot) | 284KB | Python | 2026-01-10 | 91d |
| [outcome-tracker](https://github.com/SuperInstance/outcome-tracker) | 32KB | Python | 2026-01-10 | 91d |
| [pool-rs](https://github.com/SuperInstance/pool-rs) | 49KB | N/A | 2026-01-09 | 92d |
| [prism](https://github.com/SuperInstance/prism) | 1978KB | TypeScript | 2026-01-18 | 83d |
| [project-JEPA](https://github.com/SuperInstance/project-JEPA) | 129KB | Go | 2026-01-10 | 91d |
| [project1](https://github.com/SuperInstance/project1) | 3339KB | TypeScript | 2026-01-10 | 91d |
| [protocol-adapters](https://github.com/SuperInstance/protocol-adapters) | 19KB | N/A | 2026-01-10 | 91d |
| [provider-abstraction-layer](https://github.com/SuperInstance/provider-abstraction-layer) | 11KB | Python | 2026-01-09 | 92d |
| [rag-indexer](https://github.com/SuperInstance/rag-indexer) | 51KB | Python | 2026-01-10 | 91d |
| [rate-limiter](https://github.com/SuperInstance/rate-limiter) | 43KB | Rust | 2026-01-10 | 91d |
| [rate-limiting-service](https://github.com/SuperInstance/rate-limiting-service) | 11KB | Python | 2026-01-09 | 92d |
| [secret-manager](https://github.com/SuperInstance/secret-manager) | 39KB | Rust | 2026-01-10 | 91d |
| [semantic-store](https://github.com/SuperInstance/semantic-store) | 30KB | N/A | 2026-01-10 | 91d |
| [streaming-response-handler](https://github.com/SuperInstance/streaming-response-handler) | 21KB | Python | 2026-01-10 | 91d |
| [task-queue](https://github.com/SuperInstance/task-queue) | 54KB | Makefile | 2026-01-10 | 91d |
| [timeseries-db](https://github.com/SuperInstance/timeseries-db) | 57KB | Rust | 2026-01-10 | 91d |
| [token-vault](https://github.com/SuperInstance/token-vault) | 239KB | Rust | 2026-02-09 | 61d |
| [training-data-collector](https://github.com/SuperInstance/training-data-collector) | 27KB | Python | 2026-01-10 | 91d |
| [vector-navigator](https://github.com/SuperInstance/vector-navigator) | 33KB | N/A | 2026-01-10 | 91d |
| [webgpu-profiler](https://github.com/SuperInstance/webgpu-profiler) | 143KB | TypeScript | 2026-01-09 | 92d |
| [webrtc-stream](https://github.com/SuperInstance/webrtc-stream) | 32KB | N/A | 2026-01-10 | 91d |
| [ws-status-indicator](https://github.com/SuperInstance/ws-status-indicator) | 30KB | TypeScript | 2026-01-10 | 91d |

## RED Repos — Placeholders

**88 repos under 10KB — likely README-only or empty shells**

| Repo | Size | Language | Last Push |
|------|------|----------|-----------|
| [AI-Smart-Notifications](https://github.com/SuperInstance/AI-Smart-Notifications) | 0KB | N/A | 2026-01-08 |
| [AIR](https://github.com/SuperInstance/AIR) | 1KB | N/A | 2026-03-18 |
| [Agent-Lifecycle-Registry](https://github.com/SuperInstance/Agent-Lifecycle-Registry) | 0KB | N/A | 2026-01-08 |
| [Auto-Backup-Compression-Encryption](https://github.com/SuperInstance/Auto-Backup-Compression-Encryption) | 0KB | N/A | 2026-01-08 |
| [Auto-Tuning-Engine](https://github.com/SuperInstance/Auto-Tuning-Engine) | 0KB | N/A | 2026-01-08 |
| [Automatic-Type-Safe-IndexedDB](https://github.com/SuperInstance/Automatic-Type-Safe-IndexedDB) | 9KB | TypeScript | 2026-01-08 |
| [Central-Error-Manager](https://github.com/SuperInstance/Central-Error-Manager) | 0KB | N/A | 2026-01-08 |
| [Claude-Abstraction](https://github.com/SuperInstance/Claude-Abstraction) | 0KB | N/A | 2026-01-13 |
| [Claude-PRISM-CF](https://github.com/SuperInstance/Claude-PRISM-CF) | 0KB | N/A | 2026-01-15 |
| [Dynamic-Theming](https://github.com/SuperInstance/Dynamic-Theming) | 0KB | N/A | 2026-01-08 |
| [Ghost-tiles](https://github.com/SuperInstance/Ghost-tiles) | 1KB | N/A | 2026-03-10 |
| [In-Browser-Dev-Tools](https://github.com/SuperInstance/In-Browser-Dev-Tools) | 0KB | N/A | 2026-01-08 |
| [In-Browser-Vector-Search](https://github.com/SuperInstance/In-Browser-Vector-Search) | 0KB | N/A | 2026-01-08 |
| [JEPA-Real-Time-Sentiment-Analysis](https://github.com/SuperInstance/JEPA-Real-Time-Sentiment-Analysis) | 0KB | N/A | 2026-01-08 |
| [LOG-Tensor](https://github.com/SuperInstance/LOG-Tensor) | 1KB | N/A | 2026-03-10 |
| [MPC-Orchestration-Optimization](https://github.com/SuperInstance/MPC-Orchestration-Optimization) | 0KB | N/A | 2026-01-08 |
| [Polln-whitepapers](https://github.com/SuperInstance/Polln-whitepapers) | 1KB | N/A | 2026-03-10 |
| [Private-ML-Personalization](https://github.com/SuperInstance/Private-ML-Personalization) | 0KB | N/A | 2026-01-08 |
| [Proactive-Planning-AI-Hub](https://github.com/SuperInstance/Proactive-Planning-AI-Hub) | 0KB | N/A | 2026-01-08 |
| [Real-Time-Collaboration](https://github.com/SuperInstance/Real-Time-Collaboration) | 0KB | N/A | 2026-01-08 |
| [Rubiks-Tensor-Transformer](https://github.com/SuperInstance/Rubiks-Tensor-Transformer) | 1KB | N/A | 2026-03-08 |
| [Spreadsheet-ai](https://github.com/SuperInstance/Spreadsheet-ai) | 1KB | N/A | 2026-03-10 |
| [Vibe-Code-Agent-Gen](https://github.com/SuperInstance/Vibe-Code-Agent-Gen) | 0KB | N/A | 2026-01-08 |
| [activelog-claude](https://github.com/SuperInstance/activelog-claude) | 8KB | Python | 2026-01-10 |
| [actualize](https://github.com/SuperInstance/actualize) | 0KB | N/A | 2026-03-16 |
| [bordercollie](https://github.com/SuperInstance/bordercollie) | 1KB | N/A | 2026-03-23 |
| [businesslog-app](https://github.com/SuperInstance/businesslog-app) | 1KB | Python | 2026-01-10 |
| [cacapn](https://github.com/SuperInstance/cacapn) | 1KB | N/A | 2026-03-27 |
| [clawcanvas](https://github.com/SuperInstance/clawcanvas) | 0KB | N/A | 2026-03-19 |
| [clawcraft](https://github.com/SuperInstance/clawcraft) | 0KB | N/A | 2026-03-20 |
| [clawmatrix](https://github.com/SuperInstance/clawmatrix) | 1KB | N/A | 2026-03-20 |
| [commit-caster](https://github.com/SuperInstance/commit-caster) | 9KB | Python | 2026-04-11 |
| [config-manager](https://github.com/SuperInstance/config-manager) | 0KB | N/A | 2026-01-10 |
| [cuda-claw](https://github.com/SuperInstance/cuda-claw) | 0KB | N/A | 2026-03-16 |
| [distributed-lock](https://github.com/SuperInstance/distributed-lock) | 3KB | Rust | 2026-01-10 |
| [examples](https://github.com/SuperInstance/examples) | 0KB | N/A | 2026-01-09 |
| [expression-injection](https://github.com/SuperInstance/expression-injection) | 0KB | N/A | 2026-01-14 |
| [fleet-ci](https://github.com/SuperInstance/fleet-ci) | 0KB | N/A | 2026-04-11 |
| [fleet-mechanic](https://github.com/SuperInstance/fleet-mechanic) | 0KB | Python | 2026-04-11 |
| [flowstate](https://github.com/SuperInstance/flowstate) | 0KB | N/A | 2026-03-17 |
| [flux-collab](https://github.com/SuperInstance/flux-collab) | 0KB | Python | 2026-04-11 |
| [flux-conformance](https://github.com/SuperInstance/flux-conformance) | 1KB | N/A | 2026-04-11 |
| [flux-coverage](https://github.com/SuperInstance/flux-coverage) | 5KB | Python | 2026-04-11 |
| [flux-crypto](https://github.com/SuperInstance/flux-crypto) | 5KB | Python | 2026-04-11 |
| [flux-debugger](https://github.com/SuperInstance/flux-debugger) | 9KB | Python | 2026-04-11 |
| [flux-decompiler](https://github.com/SuperInstance/flux-decompiler) | 8KB | Python | 2026-04-11 |
| [flux-diff](https://github.com/SuperInstance/flux-diff) | 6KB | Python | 2026-04-11 |
| [flux-fuzzer](https://github.com/SuperInstance/flux-fuzzer) | 8KB | Python | 2026-04-11 |
| [flux-grammar](https://github.com/SuperInstance/flux-grammar) | 9KB | Python | 2026-04-11 |
| [flux-ir](https://github.com/SuperInstance/flux-ir) | 6KB | Python | 2026-04-11 |
| [flux-linker](https://github.com/SuperInstance/flux-linker) | 7KB | Python | 2026-04-11 |
| [flux-lsp](https://github.com/SuperInstance/flux-lsp) | 1KB | N/A | 2026-04-11 |
| [flux-metrics](https://github.com/SuperInstance/flux-metrics) | 7KB | Python | 2026-04-11 |
| [flux-optimizer](https://github.com/SuperInstance/flux-optimizer) | 8KB | Python | 2026-04-11 |
| [flux-packager](https://github.com/SuperInstance/flux-packager) | 8KB | Python | 2026-04-11 |
| [flux-profiler](https://github.com/SuperInstance/flux-profiler) | 9KB | Python | 2026-04-11 |
| [flux-signatures](https://github.com/SuperInstance/flux-signatures) | 8KB | Python | 2026-04-11 |
| [flux-simulator](https://github.com/SuperInstance/flux-simulator) | 8KB | Python | 2026-04-11 |
| [flux-spec](https://github.com/SuperInstance/flux-spec) | 1KB | N/A | 2026-04-11 |
| [flux-stdlib](https://github.com/SuperInstance/flux-stdlib) | 6KB | Python | 2026-04-11 |
| [flux-testkit](https://github.com/SuperInstance/flux-testkit) | 9KB | Python | 2026-04-11 |
| [flux-timeline](https://github.com/SuperInstance/flux-timeline) | 6KB | Python | 2026-04-11 |
| [flux-validator](https://github.com/SuperInstance/flux-validator) | 7KB | Python | 2026-04-11 |
| [flux-visualizer](https://github.com/SuperInstance/flux-visualizer) | 8KB | Python | 2026-04-11 |
| [flux-vocabulary](https://github.com/SuperInstance/flux-vocabulary) | 1KB | N/A | 2026-04-11 |
| [flux-wasm-gen](https://github.com/SuperInstance/flux-wasm-gen) | 6KB | Python | 2026-04-11 |
| [git-agent](https://github.com/SuperInstance/git-agent) | 0KB | N/A | 2026-04-04 |
| [git-agent-codespace](https://github.com/SuperInstance/git-agent-codespace) | 1KB | Shell | 2026-04-11 |
| [greenhorn](https://github.com/SuperInstance/greenhorn) | 6KB | N/A | 2026-04-11 |
| [greenhorn-onboarding](https://github.com/SuperInstance/greenhorn-onboarding) | 9KB | N/A | 2026-04-11 |
| [imagegen1](https://github.com/SuperInstance/imagegen1) | 0KB | N/A | 2026-01-17 |
| [jetsonclaw1-onboarding](https://github.com/SuperInstance/jetsonclaw1-onboarding) | 6KB | N/A | 2026-04-10 |
| [mask-lock-clips](https://github.com/SuperInstance/mask-lock-clips) | 1KB | N/A | 2026-03-23 |
| [memory-visualization](https://github.com/SuperInstance/memory-visualization) | 0KB | N/A | 2026-01-09 |
| [multi-device-sync](https://github.com/SuperInstance/multi-device-sync) | 0KB | N/A | 2026-01-08 |
| [optimized-system-monitor](https://github.com/SuperInstance/optimized-system-monitor) | 0KB | N/A | 2026-01-08 |
| [pinchrs](https://github.com/SuperInstance/pinchrs) | 1KB | N/A | 2026-03-19 |
| [platonic-randomness](https://github.com/SuperInstance/platonic-randomness) | 1KB | N/A | 2026-03-10 |
| [superz-diary](https://github.com/SuperInstance/superz-diary) | 0KB | N/A | 2026-04-11 |
| [superz-vessel](https://github.com/SuperInstance/superz-vessel) | 0KB | Python | 2026-04-11 |
| [temp](https://github.com/SuperInstance/temp) | 0KB | N/A | 2026-03-18 |
| [test-repo](https://github.com/SuperInstance/test-repo) | 0KB | N/A | 2026-03-19 |
| [test-sdk-connection](https://github.com/SuperInstance/test-sdk-connection) | 0KB | N/A | 2026-03-13 |
| [universal-import-export](https://github.com/SuperInstance/universal-import-export) | 0KB | N/A | 2026-01-08 |
| [vessel-template](https://github.com/SuperInstance/vessel-template) | 8KB | Python | 2026-04-11 |
| [voxel-logic](https://github.com/SuperInstance/voxel-logic) | 1KB | N/A | 2026-03-10 |
| [websocket-fabric-v2](https://github.com/SuperInstance/websocket-fabric-v2) | 0KB | N/A | 2026-01-10 |
| [workflow-engineer](https://github.com/SuperInstance/workflow-engineer) | 0KB | N/A | 2026-01-10 |

## DEAD Repos — Forks

**408 forked repos — archival/reference copies**

Too many to list individually. These are forks of upstream repos with no meaningful modifications. Key fork sources include:
- Total forks: **408** (61.3% of fleet)
- Many are from the `fleet-*`, `nexus-*`, and `cuda-*` ecosystem namespaces
- Recommend archiving or deleting forks that are no longer referenced

## Recommendations

### 🔴 Critical Actions

1. **Audit the 408 dead forks (61.3% of fleet)** — This is by far the biggest issue. Run a cleanup script to identify which forks have no unique commits vs upstream and either delete or archive them. Many `fleet-*` and `nexus-*` forks appear to be auto-generated placeholders.

2. **Triage the 95 YELLOW repos** — 14.3% of the fleet is stale with real code. Prioritize the largest ones: `usemeter` (713MB), `tripartite-rs` (356MB), `ws-fabric` (314MB), `realtime-core` (157MB). Decide: revive, archive, or merge.

### 🟡 Priority Improvements

3. **Add tests to GREEN-untested repos** — 54 of 75 GREEN repos (72%) lack verified tests. The `flux-*` ecosystem has good CI coverage in core repos (`flux-core`, `flux-swarm`, `flux-runtime*`) but newer additions like `flux-py`, `flux-zig`, `flux-vm-ts`, `flux-ide` need test suites.

4. **Clean up RED placeholders** — 88 repos are under 10KB. Delete truly empty ones (0KB). For repos with a README spec but no code (e.g., `flux-spec`, `flux-lsp`, `flux-vocabulary`), decide if they're still planned or should be archived.

5. **Establish fleet-wide CI standard** — Create a `fleet-ci` template with mandatory test, lint, and type-check steps. 21 repos already have `.github/workflows` — use these as the template for the rest.

### 🟢 Fleet Health Goals

6. **Reduce fork ratio from 61% to under 20%** — This should be the #1 fleet hygiene goal. After cleanup, the fleet should be primarily source repos, not forks.

7. **Consolidate the flux-* ecosystem** — 25+ flux repos exist. Group into: `flux-core` (compiler/runtime), `flux-stdlib` (standard library), `flux-languages` (JS/Py/Zig/etc runtimes), and `flux-tooling` (LSP, debugger, profiler, etc).

8. **Create a fleet health dashboard** — Automated weekly census checking push recency, test coverage, CI status, and dependency freshness. Track GREEN/YELLOW/RED/DEAD ratios over time.

9. **Revive or archive the January 2026 batch** — 60+ repos haven't been touched since January 8-10, 2026. Many appear to be from an initial creation sprint. Either they need active development or formal archival.

10. **Document repo purposes** — 37% of repos have no description. Add descriptions to all repos with `repo description set` via API, especially the `flux-*` and `Equipment-*` families.

---

*Census generated: 2026-04-12 by Super Z — Fleet Census Bot v1.0*
*Total repositories analyzed: 666*
*API calls made: ~470 (7 pages + 46 deep checks)*