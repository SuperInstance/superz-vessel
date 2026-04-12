#!/usr/bin/env python3
"""
Fleet Capability Registry (FCR) — SuperInstance Fleet
======================================================

A Python tool and schema for registering, querying, and matching agent
capabilities across the SuperInstance fleet.  Enables dynamic task routing,
gap analysis, and fleet-wide synergy measurement.

Author:  Super Z <superz@superinstance.dev>
Repo:    SuperInstance/superz-vessel
Version: 1.0.0
License: MIT

Architecture
------------
- **Capability** — a single skill/expertise/permission an agent possesses,
  with proficiency level, evidence trail, and optional expiration.
- **AgentProfile** — a full profile for a fleet agent including capabilities,
  trust scores, work history, and claimed fences.
- **TaskRequirement** — specification of what a task needs so the registry
  can find the best-qualified agent(s).
- **FleetCapabilityRegistry** — the central class that stores, queries,
  matches, and exports fleet data.

Matching Algorithm
------------------
Score = 0.4 * capability_match
      + 0.3 * trust_composite
      + 0.2 * availability_bonus
      + 0.1 * evidence_factor

Where:
  capability_match = Σ min(agent_level, required_level) / num_required_caps
  availability     = {active: 1.0, idle: 0.7, offline: 0.0}
  evidence_factor  = min(evidence_count / 10, 1.0)
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Capability:
    """A single capability registered for an agent.

    Attributes:
        name:         Unique identifier, e.g. ``"isa-auditing"``.
        category:     One of ``"expertise"``, ``"tool"``, ``"permission"``,
                      or ``"language"``.
        level:        Proficiency in [0.0, 1.0].
        evidence:     List of opaque evidence references (commit hashes,
                      fence IDs, audit report IDs).
        last_updated: ISO-8601 timestamp of the most-recent update.
        expires:      Optional ISO-8601 expiry; ``None`` means permanent.
    """

    name: str
    category: str  # "expertise" | "tool" | "permission" | "language"
    level: float  # 0.0 – 1.0
    evidence: List[str] = field(default_factory=list)
    last_updated: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires: Optional[str] = None

    # -- validation ----------------------------------------------------------

    def __post_init__(self) -> None:
        if not 0.0 <= self.level <= 1.0:
            raise ValueError(f"Capability level must be in [0, 1]; got {self.level}")
        if self.category not in ("expertise", "tool", "permission", "language"):
            raise ValueError(f"Unknown category: {self.category}")

    # -- serialization helpers -----------------------------------------------

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Capability":
        return cls(**d)

    def is_expired(self, now: Optional[str] = None) -> bool:
        """Return ``True`` if the capability has passed its expiry."""
        if self.expires is None:
            return False
        ref = now or datetime.now(timezone.utc).isoformat()
        return self.expires <= ref


@dataclass
class AgentProfile:
    """Full profile for a fleet agent.

    Attributes:
        name:             Agent identifier, e.g. ``"Super Z"``.
        vessel:           Vessel / repo name, e.g. ``"superz-vessel"``.
        repo:             Full GitHub repo path.
        status:           ``"active"``, ``"idle"``, or ``"offline"``.
        capabilities:     List of :class:`Capability` objects.
        trust_composite:  Aggregate trust score in [0.0, 1.0].
        trust_dimensions: Per-dimension trust breakdown.
        worklog:          Session / commit / task counters.
        fences_claimed:   Fence IDs this agent has claimed.
    """

    name: str
    vessel: str
    repo: str
    status: str  # "active" | "idle" | "offline"
    capabilities: List[Capability] = field(default_factory=list)
    trust_composite: float = 0.0
    trust_dimensions: Dict[str, float] = field(default_factory=dict)
    worklog: Dict[str, int] = field(default_factory=dict)
    fences_claimed: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in ("active", "idle", "offline"):
            raise ValueError(f"Unknown status: {self.status}")
        if not 0.0 <= self.trust_composite <= 1.0:
            raise ValueError(
                f"Trust composite must be in [0, 1]; got {self.trust_composite}"
            )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "vessel": self.vessel,
            "repo": self.repo,
            "status": self.status,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "trust_composite": self.trust_composite,
            "trust_dimensions": self.trust_dimensions,
            "worklog": self.worklog,
            "fences_claimed": self.fences_claimed,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AgentProfile":
        caps = [Capability.from_dict(c) for c in d.get("capabilities", [])]
        return cls(
            name=d["name"],
            vessel=d["vessel"],
            repo=d["repo"],
            status=d["status"],
            capabilities=caps,
            trust_composite=d.get("trust_composite", 0.0),
            trust_dimensions=d.get("trust_dimensions", {}),
            worklog=d.get("worklog", {}),
            fences_claimed=d.get("fences_claimed", []),
        )

    def get_capability(self, name: str) -> Optional[Capability]:
        """Return a capability by *name*, or ``None`` if not found."""
        for cap in self.capabilities:
            if cap.name == name:
                return cap
        return None


@dataclass
class TaskRequirement:
    """Specification of what a task needs from an agent.

    Attributes:
        required_capabilities: Capability names that are mandatory.
        minimum_level:         Lowest acceptable proficiency per cap.
        minimum_trust:         Lowest acceptable composite trust score.
        preferred_agents:      Agent names given a small preference boost.
        excluded_agents:       Agent names that must never be matched.
    """

    required_capabilities: List[str] = field(default_factory=list)
    minimum_level: float = 0.5
    minimum_trust: float = 0.3
    preferred_agents: List[str] = field(default_factory=list)
    excluded_agents: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TaskRequirement":
        return cls(**d)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class FleetCapabilityRegistry:
    """Central capability registry for the SuperInstance fleet.

    Stores agent profiles, provides querying / matching, and can serialize
    to ``fleet.json`` or import from ``.i2i/peers.md`` files.

    Parameters:
        fleet_json_path: Optional path to a ``fleet.json`` file to load on
                         initialization.  If the file does not exist the
                         registry starts empty.
    """

    def __init__(self, fleet_json_path: Optional[str] = None) -> None:
        self._agents: Dict[str, AgentProfile] = {}
        if fleet_json_path and os.path.isfile(fleet_json_path):
            self._load_json(fleet_json_path)

    # -- persistence ---------------------------------------------------------

    def _load_json(self, path: str) -> None:
        """Load agent profiles from a JSON file."""
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for agent_data in data.get("agents", []):
            profile = AgentProfile.from_dict(agent_data)
            self._agents[profile.name] = profile

    def to_fleet_json(self, path: str) -> None:
        """Export the full registry as a ``fleet.json`` file.

        The file contains metadata (generated_at, version) and the list of
        all registered agent profiles.

        Parameters:
            path: Destination file path.
        """
        payload = {
            "schema": "fleet-capability-registry/v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agent_count": len(self._agents),
            "agents": [p.to_dict() for p in self._agents.values()],
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    # -- mutation ------------------------------------------------------------

    def register_agent(self, profile: AgentProfile) -> None:
        """Register or update an agent profile.

        If an agent with the same *name* already exists it is replaced in
        full.

        Parameters:
            profile: The :class:`AgentProfile` to register.
        """
        self._agents[profile.name] = profile

    def add_capability(self, agent_name: str, cap: Capability) -> None:
        """Add (or update) a single capability for an agent.

        Parameters:
            agent_name: Name of the target agent.
            cap:        The :class:`Capability` to add.

        Raises:
            KeyError: If *agent_name* is not in the registry.
        """
        agent = self._agents.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent not found: {agent_name}")
        # Replace if same name exists, otherwise append
        for i, existing in enumerate(agent.capabilities):
            if existing.name == cap.name:
                agent.capabilities[i] = cap
                return
        agent.capabilities.append(cap)

    def revoke_capability(self, agent_name: str, cap_name: str) -> None:
        """Remove a capability from an agent.

        Parameters:
            agent_name: Name of the target agent.
            cap_name:   Capability name to remove.

        Raises:
            KeyError: If *agent_name* is not in the registry.
            ValueError: If the capability is not present.
        """
        agent = self._agents.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent not found: {agent_name}")
        original_len = len(agent.capabilities)
        agent.capabilities = [c for c in agent.capabilities if c.name != cap_name]
        if len(agent.capabilities) == original_len:
            raise ValueError(
                f"Capability '{cap_name}' not found on agent '{agent_name}'"
            )

    # -- querying ------------------------------------------------------------

    def query(
        self,
        capability: str,
        min_level: float = 0.0,
        include_expired: bool = False,
    ) -> List[AgentProfile]:
        """Find all agents possessing a given capability above *min_level*.

        Parameters:
            capability:        Capability name to search for.
            min_level:         Minimum proficiency threshold.
            include_expired:   Whether to include expired capabilities.

        Returns:
            List of matching :class:`AgentProfile` objects sorted by
            capability level (descending).
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        results: List[Tuple[AgentProfile, float]] = []
        for agent in self._agents.values():
            cap = agent.get_capability(capability)
            if cap is None:
                continue
            if not include_expired and cap.is_expired(now_iso):
                continue
            if cap.level >= min_level:
                results.append((agent, cap.level))
        # Sort by capability level descending
        results.sort(key=lambda pair: pair[1], reverse=True)
        return [r[0] for r in results]

    # -- matching ------------------------------------------------------------

    def match_task(
        self, requirement: TaskRequirement
    ) -> List[Tuple[AgentProfile, float]]:
        """Match a :class:`TaskRequirement` to qualified agents.

        Returns a list of ``(agent, score)`` tuples sorted by score
        (descending).  The matching algorithm is:

        ``score = 0.4 * cap_match + 0.3 * trust + 0.2 * availability
                  + 0.1 * evidence``

        Parameters:
            requirement: The task specification to match against.

        Returns:
            Sorted list of ``(AgentProfile, score)`` pairs.
        """
        matches: List[Tuple[AgentProfile, float]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for agent in self._agents.values():
            # Exclusion filter
            if agent.name in requirement.excluded_agents:
                continue

            # Trust gate
            if agent.trust_composite < requirement.minimum_trust:
                continue

            # Capability gate — every required cap must be present
            cap_levels: List[float] = []
            all_evidence: List[str] = []
            for req_cap in requirement.required_capabilities:
                cap = agent.get_capability(req_cap)
                if cap is None:
                    break
                if cap.is_expired(now_iso):
                    break
                if cap.level < requirement.minimum_level:
                    break
                cap_levels.append(cap.level)
                all_evidence.extend(cap.evidence)
            else:
                # All required capabilities met
                score = self._compute_score(
                    agent, cap_levels, requirement, all_evidence
                )
                matches.append((agent, score))

        matches.sort(key=lambda pair: pair[1], reverse=True)
        return matches

    @staticmethod
    def _compute_score(
        agent: AgentProfile,
        cap_levels: List[float],
        requirement: TaskRequirement,
        all_evidence: List[str],
    ) -> float:
        """Internal scoring helper."""
        # Capability match: normalised sum of min(agent_level, required_level)
        n_caps = max(len(requirement.required_capabilities), 1)
        cap_match = sum(min(l, requirement.minimum_level) for l in cap_levels) / n_caps

        # Trust component
        trust = agent.trust_composite

        # Availability bonus
        avail_map = {"active": 1.0, "idle": 0.7, "offline": 0.0}
        availability = avail_map.get(agent.status, 0.0)

        # Evidence factor — caps at 10 items
        evidence_factor = min(len(all_evidence) / 10.0, 1.0)

        # Weighted combination
        score = (
            0.4 * cap_match
            + 0.3 * trust
            + 0.2 * availability
            + 0.1 * evidence_factor
        )

        # Small preference boost (0.02 per preferred agent match)
        if agent.name in requirement.preferred_agents:
            score += 0.02

        return round(score, 4)

    # -- analytics -----------------------------------------------------------

    def get_fleet_summary(self) -> dict:
        """Return fleet-wide capability statistics.

        Includes:
        - Total agent count by status.
        - Unique capability catalog with per-capability agent counts and
          average proficiency.
        - Aggregate trust statistics.
        """
        status_counts: Dict[str, int] = {}
        cap_catalog: Dict[str, dict] = {}
        total_trust = 0.0
        total_sessions = 0
        total_commits = 0

        for agent in self._agents.values():
            status_counts[agent.status] = status_counts.get(agent.status, 0) + 1
            total_trust += agent.trust_composite
            total_sessions += agent.worklog.get("total_sessions", 0)
            total_commits += agent.worklog.get("total_commits", 0)

            for cap in agent.capabilities:
                if cap.name not in cap_catalog:
                    cap_catalog[cap.name] = {
                        "category": cap.category,
                        "agent_count": 0,
                        "levels": [],
                    }
                entry = cap_catalog[cap.name]
                entry["agent_count"] += 1
                entry["levels"].append(cap.level)

        # Compute averages
        cap_summary = {}
        for name, data in cap_catalog.items():
            levels = data["levels"]
            cap_summary[name] = {
                "category": data["category"],
                "agent_count": data["agent_count"],
                "avg_level": round(sum(levels) / len(levels), 3) if levels else 0.0,
                "max_level": round(max(levels), 3) if levels else 0.0,
                "min_level": round(min(levels), 3) if levels else 0.0,
            }

        n = len(self._agents) or 1
        return {
            "total_agents": len(self._agents),
            "status_breakdown": status_counts,
            "unique_capabilities": len(cap_summary),
            "capabilities": cap_summary,
            "avg_trust_composite": round(total_trust / n, 3),
            "total_sessions": total_sessions,
            "total_commits": total_commits,
        }

    def detect_gaps(self, min_agents: int = 1) -> List[dict]:
        """Find capability gaps — areas with fewer than *min_agents* qualified.

        A "gap" is defined as a capability category (``expertise``, ``tool``,
        etc.) where fewer than *min_agents* agents hold *any* capability in
        that category, or the average proficiency is below 0.5.

        Returns:
            List of gap descriptors sorted by severity.
        """
        summary = self.get_fleet_summary()
        gaps: List[dict] = []

        # Build category-level aggregations
        cat_data: Dict[str, List[float]] = {}
        for cap_name, info in summary["capabilities"].items():
            cat = info["category"]
            if cat not in cat_data:
                cat_data[cat] = []
            cat_data[cat].append(info["avg_level"])

        for cat, levels in cat_data.items():
            avg = sum(levels) / len(levels) if levels else 0.0
            if len(levels) < min_agents:
                gaps.append({
                    "category": cat,
                    "severity": "critical",
                    "reason": (
                        f"Only {len(levels)} agent(s) have capabilities in "
                        f"'{cat}' (need ≥ {min_agents})"
                    ),
                    "avg_level": round(avg, 3),
                })
            elif avg < 0.5:
                gaps.append({
                    "category": cat,
                    "severity": "warning",
                    "reason": (
                        f"Average proficiency in '{cat}' is {avg:.2f} "
                        f"(threshold 0.50)"
                    ),
                    "avg_level": round(avg, 3),
                })

        # Also flag individual capabilities with very low coverage
        for cap_name, info in summary["capabilities"].items():
            if info["agent_count"] < min_agents:
                gaps.append({
                    "category": "individual",
                    "capability": cap_name,
                    "severity": "critical",
                    "reason": (
                        f"Capability '{cap_name}' held by only "
                        f"{info['agent_count']} agent(s)"
                    ),
                    "avg_level": info["avg_level"],
                })

        gaps.sort(key=lambda g: (0 if g["severity"] == "critical" else 1))
        return gaps

    def compute_fleet_synergy(self) -> dict:
        """Compute fleet synergy — how well the fleet covers capability areas.

        Synergy is measured on two axes:

        1. **Coverage** — ratio of capability categories that have at least
           one agent with proficiency ≥ 0.5.
        2. **Depth** — average number of agents per capability area, capped
           at 3 (redundancy sweet-spot).
        3. **Balance** — standard deviation of average proficiency across
           capability categories (lower = more balanced).

        Returns:
            A dict with ``coverage``, ``depth``, ``balance``, and an overall
            ``synergy_score`` in [0.0, 1.0].
        """
        summary = self.get_fleet_summary()
        caps = summary["capabilities"]

        if not caps:
            return {
                "coverage": 0.0,
                "depth": 0.0,
                "balance": 0.0,
                "synergy_score": 0.0,
                "categories": {},
            }

        # Coverage: fraction of capabilities with avg_level >= 0.5
        qualified = sum(1 for info in caps.values() if info["avg_level"] >= 0.5)
        coverage = qualified / len(caps)

        # Depth: average agent count per cap, capped at 3
        raw_depth = sum(info["agent_count"] for info in caps.values()) / len(caps)
        depth = min(raw_depth / 3.0, 1.0)

        # Balance: 1.0 - normalized stddev of avg_levels
        levels = [info["avg_level"] for info in caps.values()]
        mean = sum(levels) / len(levels)
        variance = sum((l - mean) ** 2 for l in levels) / len(levels)
        stddev = math.sqrt(variance)
        balance = max(1.0 - stddev, 0.0)  # stddev is typically < 1

        synergy = round(0.4 * coverage + 0.3 * depth + 0.3 * balance, 4)

        # Per-category breakdown
        categories: Dict[str, dict] = {}
        for cap_name, info in caps.items():
            cat = info["category"]
            if cat not in categories:
                categories[cat] = {"caps": 0, "total_agents": 0, "levels": []}
            categories[cat]["caps"] += 1
            categories[cat]["total_agents"] += info["agent_count"]
            categories[cat]["levels"].append(info["avg_level"])

        for cat, data in categories.items():
            data["avg_proficiency"] = round(
                sum(data["levels"]) / len(data["levels"]), 3
            )

        return {
            "coverage": round(coverage, 4),
            "depth": round(depth, 4),
            "balance": round(balance, 4),
            "synergy_score": synergy,
            "categories": categories,
        }

    # -- I2I import ----------------------------------------------------------

    def from_i2i_peers(self, peers_md_path: str) -> int:
        """Import agent profiles from a ``.i2i/peers.md`` markdown file.

        Parses a simple markdown format where each agent is a ``## <Name>``
        heading followed by key-value metadata lines like
        ``- vessel: superz-vessel`` or ``- capabilities: isa-auditing, ...``.

        Parameters:
            peers_md_path: Path to the peers markdown file.

        Returns:
            Number of agents imported.
        """
        if not os.path.isfile(peers_md_path):
            raise FileNotFoundError(f"peers.md not found: {peers_md_path}")

        with open(peers_md_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        imported = 0
        now_iso = datetime.now(timezone.utc).isoformat()

        # Split into agent blocks by ## headings
        blocks = re.split(r"^##\s+", content, flags=re.MULTILINE)
        for block in blocks[1:]:  # skip preamble before first heading
            lines = block.strip().splitlines()
            if not lines:
                continue
            agent_name = lines[0].strip()
            vessel = repo = status = ""
            capabilities_raw = ""

            for line in lines[1:]:
                line = line.strip()
                if line.startswith("- vessel:"):
                    vessel = line.split(":", 1)[1].strip()
                elif line.startswith("- repo:"):
                    repo = line.split(":", 1)[1].strip()
                elif line.startswith("- status:"):
                    status = line.split(":", 1)[1].strip()
                elif line.startswith("- capabilities:"):
                    capabilities_raw = line.split(":", 1)[1].strip()

            if not vessel:
                vessel = agent_name.lower().replace(" ", "-")
            if not repo:
                repo = f"SuperInstance/{vessel}"
            if not status:
                status = "active"

            caps: List[Capability] = []
            if capabilities_raw:
                for cap_name in capabilities_raw.split(","):
                    cap_name = cap_name.strip()
                    if cap_name:
                        caps.append(
                            Capability(
                                name=cap_name,
                                category="expertise",
                                level=0.5,
                                last_updated=now_iso,
                            )
                        )

            profile = AgentProfile(
                name=agent_name,
                vessel=vessel,
                repo=repo,
                status=status,
                capabilities=caps,
            )
            self._agents[agent_name] = profile
            imported += 1

        return imported

    # -- helpers -------------------------------------------------------------

    @property
    def agents(self) -> Dict[str, AgentProfile]:
        """Read-only access to the internal agent map."""
        return dict(self._agents)

    def get_agent(self, name: str) -> Optional[AgentProfile]:
        """Retrieve a single agent by name."""
        return self._agents.get(name)

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"FleetCapabilityRegistry(agents={len(self._agents)})"


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def _bar(value: float, width: int = 30) -> str:
    """Render a filled bar for *value* in [0, 1]."""
    filled = int(round(value * width))
    empty = width - filled
    return "█" * filled + "░" * empty


def print_synergy_chart(synergy: dict) -> None:
    """Print a text-based bar chart of fleet synergy metrics."""
    print("\n╔══════════════════════════════════════════════════╗")
    print("║          FLEET SYNERGY DASHBOARD                ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  Overall Synergy : {synergy['synergy_score']:.4f}                    ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  Coverage  {_bar(synergy['coverage'])} {synergy['coverage']:.1%}  ║")
    print(f"║  Depth     {_bar(synergy['depth'])} {synergy['depth']:.1%}  ║")
    print(f"║  Balance   {_bar(synergy['balance'])} {synergy['balance']:.1%}  ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Category Breakdown                             ║")
    print("╠══════════════════════════════════════════════════╣")
    for cat, data in synergy.get("categories", {}).items():
        avg = data.get("avg_proficiency", 0.0)
        n_caps = data["caps"]
        n_agents = data["total_agents"]
        print(
            f"║  {cat:<16s} {_bar(avg, 20)} {avg:.2f}  "
            f"({n_caps} caps, {n_agents} agents) ║"
        )
    print("╚══════════════════════════════════════════════════╝")


def print_gap_report(gaps: List[dict]) -> None:
    """Print a human-readable capability gap report."""
    if not gaps:
        print("\n✅ No capability gaps detected — fleet is well-covered.")
        return
    print(f"\n⚠️  {len(gaps)} capability gap(s) detected:")
    print("─" * 60)
    for i, gap in enumerate(gaps, 1):
        sev = gap["severity"].upper()
        marker = "🔴" if sev == "CRITICAL" else "🟡"
        cap_label = gap.get("capability", gap["category"])
        print(f"  {marker} [{sev}] {cap_label}")
        print(f"     {gap['reason']}")
        if gap.get("avg_level") is not None:
            print(f"     Average level: {gap['avg_level']:.3f}")
    print("─" * 60)


# ---------------------------------------------------------------------------
# Pre-populated fleet data
# ---------------------------------------------------------------------------

def build_sample_fleet() -> FleetCapabilityRegistry:
    """Build a registry pre-populated with the 5 known fleet agents.

    Returns:
        A :class:`FleetCapabilityRegistry` with realistic capability data.
    """
    now = datetime.now(timezone.utc).isoformat()

    oracle1 = AgentProfile(
        name="Oracle1",
        vessel="oracle1-vessel",
        repo="SuperInstance/oracle1-vessel",
        status="active",
        capabilities=[
            Capability(
                name="isa-design",
                category="expertise",
                level=0.95,
                evidence=["a1b2c3", "d4e5f6", "oracle-isa-v3"],
                last_updated=now,
            ),
            Capability(
                name="fleet-coordination",
                category="expertise",
                level=0.90,
                evidence=["coord-session-1", "coord-session-3"],
                last_updated=now,
            ),
            Capability(
                name="semantic-analysis",
                category="tool",
                level=0.85,
                evidence=["sem-review-01"],
                last_updated=now,
            ),
        ],
        trust_composite=0.92,
        trust_dimensions={"competence": 0.95, "reliability": 0.90, "transparency": 0.91},
        worklog={"total_sessions": 14, "total_commits": 62, "tasks_completed": 38},
        fences_claimed=["0x41", "0x43"],
    )

    super_z = AgentProfile(
        name="Super Z",
        vessel="superz-vessel",
        repo="SuperInstance/superz-vessel",
        status="active",
        capabilities=[
            Capability(
                name="isa-auditing",
                category="expertise",
                level=0.93,
                evidence=["audit-r1", "audit-r2", "audit-r3", "audit-r4", "fence-0x42"],
                last_updated=now,
            ),
            Capability(
                name="conformance-testing",
                category="expertise",
                level=0.90,
                evidence=["conf-v1", "conf-v2", "conf-v3", "bench-01"],
                last_updated=now,
            ),
            Capability(
                name="bytecode-analysis",
                category="tool",
                level=0.88,
                evidence=["bc-analysis-01", "bc-analysis-02"],
                last_updated=now,
            ),
            Capability(
                name="security-audit",
                category="expertise",
                level=0.87,
                evidence=["sec-audit-1", "sec-audit-2", "sec-audit-3"],
                last_updated=now,
            ),
        ],
        trust_composite=0.90,
        trust_dimensions={"competence": 0.92, "reliability": 0.88, "transparency": 0.90},
        worklog={"total_sessions": 11, "total_commits": 45, "tasks_completed": 29},
        fences_claimed=["0x42", "0x45", "0x46"],
    )

    quill = AgentProfile(
        name="Quill",
        vessel="quill-vessel",
        repo="SuperInstance/quill-vessel",
        status="idle",
        capabilities=[
            Capability(
                name="specification-writing",
                category="expertise",
                level=0.82,
                evidence=["spec-isa-v2", "spec-a2a-v1"],
                last_updated=now,
            ),
            Capability(
                name="isa-convergence",
                category="expertise",
                level=0.75,
                evidence=["convergence-draft-1"],
                last_updated=now,
            ),
            Capability(
                name="multilingual-ops",
                category="language",
                level=0.70,
                evidence=["ml-ops-test"],
                last_updated=now,
            ),
        ],
        trust_composite=0.68,
        trust_dimensions={"competence": 0.72, "reliability": 0.65, "transparency": 0.67},
        worklog={"total_sessions": 7, "total_commits": 22, "tasks_completed": 14},
        fences_claimed=["0x44"],
    )

    jetson = AgentProfile(
        name="JetsonClaw1",
        vessel="jetsonclaw1-vessel",
        repo="SuperInstance/jetsonclaw1-vessel",
        status="active",
        capabilities=[
            Capability(
                name="hardware-design",
                category="expertise",
                level=0.91,
                evidence=["hw-design-01", "hw-design-02", "hw-review-01"],
                last_updated=now,
            ),
            Capability(
                name="sensor-ops",
                category="tool",
                level=0.88,
                evidence=["sensor-int-1"],
                last_updated=now,
            ),
            Capability(
                name="rust-implementation",
                category="tool",
                level=0.85,
                evidence=["rust-module-1", "rust-module-2"],
                last_updated=now,
            ),
            Capability(
                name="energy-management",
                category="expertise",
                level=0.80,
                evidence=["energy-profile-01"],
                last_updated=now,
            ),
        ],
        trust_composite=0.88,
        trust_dimensions={"competence": 0.90, "reliability": 0.87, "transparency": 0.87},
        worklog={"total_sessions": 9, "total_commits": 38, "tasks_completed": 24},
        fences_claimed=["0x47"],
    )

    babel = AgentProfile(
        name="Babel",
        vessel="babel-vessel",
        repo="SuperInstance/babel-vessel",
        status="idle",
        capabilities=[
            Capability(
                name="vocabulary-design",
                category="expertise",
                level=0.78,
                evidence=["vocab-draft-1", "vocab-review-1"],
                last_updated=now,
            ),
            Capability(
                name="multilingual-ops",
                category="language",
                level=0.72,
                evidence=["ml-ops-babel-1"],
                last_updated=now,
            ),
            Capability(
                name="viewpoint-ops",
                category="expertise",
                level=0.70,
                evidence=["vp-ops-01"],
                last_updated=now,
            ),
        ],
        trust_composite=0.65,
        trust_dimensions={"competence": 0.68, "reliability": 0.63, "transparency": 0.64},
        worklog={"total_sessions": 5, "total_commits": 15, "tasks_completed": 9},
        fences_claimed=[],
    )

    registry = FleetCapabilityRegistry()
    for agent in [oracle1, super_z, quill, jetson, babel]:
        registry.register_agent(agent)

    return registry


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Fleet Capability Registry demo.

    Demonstrates:
    1. Register 5 agents with pre-populated data.
    2. Query for the ``"isa-auditing"`` capability.
    3. Match a task requiring ``["conformance-testing", "isa-auditing"]``.
    4. Detect capability gaps.
    5. Print fleet synergy score with text-based bar chart.
    """
    sep = "=" * 62

    # ── 1. Register agents ──────────────────────────────────────────────
    print(sep)
    print("  FLEET CAPABILITY REGISTRY — Demo Run")
    print(sep)
    registry = build_sample_fleet()
    print(f"\n✅ Registered {len(registry)} fleet agents:")
    for name, agent in registry.agents.items():
        cap_names = ", ".join(c.name for c in agent.capabilities)
        print(f"   • {name:<16s}  [{agent.status:<6s}]  caps: {cap_names}")

    # ── 2. Query for isa-auditing ───────────────────────────────────────
    print(f"\n{sep}")
    print("  QUERY: agents with 'isa-auditing' capability (min level 0.8)")
    print(sep)
    results = registry.query("isa-auditing", min_level=0.8)
    if results:
        for agent in results:
            cap = agent.get_capability("isa-auditing")
            assert cap is not None
            print(
                f"   → {agent.name:<16s}  level={cap.level:.2f}  "
                f"trust={agent.trust_composite:.2f}  "
                f"evidence={len(cap.evidence)} items"
            )
    else:
        print("   (no agents found)")

    # ── 3. Match a task ─────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  TASK MATCH: requires [conformance-testing, isa-auditing]")
    print(sep)
    requirement = TaskRequirement(
        required_capabilities=["conformance-testing", "isa-auditing"],
        minimum_level=0.5,
        minimum_trust=0.3,
        preferred_agents=["Super Z"],
        excluded_agents=[],
    )
    matches = registry.match_task(requirement)
    if matches:
        for agent, score in matches:
            print(f"   → {agent.name:<16s}  score={score:.4f}  trust={agent.trust_composite:.2f}")
    else:
        print("   (no matching agents)")

    # ── 4. Detect capability gaps ───────────────────────────────────────
    print(f"\n{sep}")
    print("  CAPABILITY GAP ANALYSIS")
    print(sep)
    gaps = registry.detect_gaps(min_agents=1)
    print_gap_report(gaps)

    # ── 5. Fleet synergy ────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  FLEET SYNERGY")
    print(sep)
    synergy = registry.compute_fleet_synergy()
    print_synergy_chart(synergy)

    # ── Fleet summary ───────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  FLEET SUMMARY")
    print(sep)
    summary = registry.get_fleet_summary()
    print(f"   Total agents      : {summary['total_agents']}")
    print(f"   Status breakdown  : {summary['status_breakdown']}")
    print(f"   Unique capabilities: {summary['unique_capabilities']}")
    print(f"   Avg trust         : {summary['avg_trust_composite']:.3f}")
    print(f"   Total sessions    : {summary['total_sessions']}")
    print(f"   Total commits     : {summary['total_commits']}")
    print(f"\n   Capability catalog:")
    for cap_name, info in sorted(summary["capabilities"].items()):
        print(
            f"     • {cap_name:<24s}  "
            f"avg={info['avg_level']:.2f}  "
            f"agents={info['agent_count']}  "
            f"category={info['category']}"
        )
    print(f"\n{sep}")
    print("  Demo complete.")
    print(sep)


if __name__ == "__main__":
    main()
