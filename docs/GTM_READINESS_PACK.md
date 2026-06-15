# REEFIKI GTM Readiness Pack

Status: internal review pack, no submission.

This pack collects the public story and proof surfaces needed before any marketplace, launch or external listing work. It does not submit to a marketplace, add analytics, add paid gating or change runtime configuration.

## Product Narrative

REEFIKI is a local-first markdown memory control plane for AI agents.

The core promise:

- agents keep durable decisions, skills and synthesis in project-scoped markdown;
- low-value material is refused or quarantined instead of becoming permanent noise;
- retrieval quality is measurable through golden checks;
- handoff context is bounded and provenance-aware;
- publication is guarded by private/public workflow checks.

Short positioning:

> REEFIKI gives AI coding agents a local, auditable memory layer that survives threads without turning your repo into an unreviewed archive.

## Target User

Primary user:

- solo developer or technical operator using Codex, Claude Code, Cursor, Windsurf/Cascade or similar agents;
- works across multiple code projects;
- wants durable agent memory without giving private project data to a hosted memory backend;
- needs safe git/publish behavior in dirty or mixed private/public repositories.

Secondary user:

- small engineering team evaluating agent-safe repo workflows;
- consultant/operator who needs repeatable project onboarding and handoff packs.

## Supported Use Cases

| Use case | Current proof |
|---|---|
| Create or connect a project wiki | `QUICKSTART.md`, root/project `AGENTS.md`, `/new`, `/connect` docs |
| Save/process/query/harvest loop | `COMMANDS.md`, onboarding fixture |
| Agent handoff | `memory pack --strict`, `memory golden` |
| Public/private publication | `publish-task --dry-run --cleanup --format json` |
| Install story | `docs/INSTALL.md` |
| Public demo | `docs/PUBLIC_DEMO.md` |
| Dashboard demo | `docs/DASHBOARD_DEMO.md` |
| Sync direction | `docs/MANAGED_SYNC_DECISION.md` |

## Demo Links

- [Public demo](PUBLIC_DEMO.md)
- [Install landing](INSTALL.md)
- [Dashboard demo](DASHBOARD_DEMO.md)
- [Managed sync decision](MANAGED_SYNC_DECISION.md)
- [Quickstart](../QUICKSTART.md)
- [Command reference](../COMMANDS.md)
- [Agent flow conformance](AGENT_FLOW_CONFORMANCE.md)

## Install Instructions

Current public install path:

```powershell
pipx install git+https://github.com/kisslex2013-alt/reefiki-personal.git
reefiki --help
reefiki onboarding
```

Checkout install:

```powershell
git clone https://github.com/kisslex2013-alt/reefiki.git
cd reefiki
python -m pip install .
reefiki --help
```

See [Install](INSTALL.md) for clean temp environment smoke and uninstall notes.

## Security And Local-First Claims

Claims that are currently supported:

- markdown files remain the durable source of truth;
- local SQLite/search indexes are rebuildable;
- public snapshots remove configured private project folders;
- publish flow blocks dirty worktrees and runs secret/content scans for publication paths;
- Ops Board is localhost-only and read-only;
- onboarding dry-run writes nothing unless `--fixture-root` is supplied.

Claims not allowed yet:

- hosted cloud sync;
- managed account system;
- marketplace availability;
- vector/hybrid search runtime;
- MCP server;
- enterprise compliance;
- automatic background sync;
- paid plan or licensing gates.

## Review Checklist Before Any External Listing

- `docs/PUBLIC_DEMO.md` is current.
- `docs/INSTALL.md` install commands are smoke-tested.
- `docs/DASHBOARD_DEMO.md` browser/API smoke is current.
- `docs/MANAGED_SYNC_DECISION.md` still says no backend implementation.
- `python scripts\reefiki.py publish-task --dry-run --cleanup --format json` passes.
- Public docs do not claim cloud/vector/MCP/marketplace features.
- Public docs do not copy private wiki content.
- Screenshots, if added later, come only from synthetic fixture data.

## Submission Boundary

This pack is not a launch action.

Explicitly out of scope:

- marketplace submission;
- external analytics;
- paid gating;
- hosted landing service;
- new package registry release;
- global agent runtime config changes;
- cloud sync backend.

The next safe GTM step is review: compare this pack against the current README, command behavior and publish dry-run output before deciding whether any external listing is justified.
