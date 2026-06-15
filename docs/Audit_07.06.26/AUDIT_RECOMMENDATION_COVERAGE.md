# Audit Recommendation Coverage

Date: 2026-06-07
Scope: June audit pack plus Codex App / REEFIKI external tooling reports.

Purpose: make sure useful ideas from audit/report inputs have a durable home in REEFIKI docs, roadmap, or wiki, so single recommendations do not disappear during synthesis.

## Coverage Table

| Recommendation / idea | Source | Durable location | Status |
|---|---|---|---|
| Safety foundation: path containment, FTS crash handling, secret scan, subprocess timeout, portable memoir store | June audit pack | `docs/Audit_07.06.26/AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md` Phase 0j | covered |
| CI and verification gates | June audit pack | `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md` Phase 0j | covered |
| Packaging/legal baseline: `LICENSE`, `pyproject.toml`, Python 3.11+ | June audit pack | `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md` Phase 0j | covered |
| Concurrency/integrity: SQLite timeout, locks, atomic writes, doctor/health | June audit pack | `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md` Phase 0j | covered |
| Markdown-native context layer: `abstract`, `_overview.md`, context-pack, `why` | OpenViking / token audits | `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md` Phase 0j/P2 | covered |
| Avoid early MCP/vector/server/cloud layers | OpenViking / strategy audits | `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md`, `external-tool-adoption-governance` | covered |
| External tooling governance: watchlist first, REEFIKI durable decisions | Codex App tooling watchlist report | `ROADMAP.md` Phase 0h, `external-tool-adoption-governance`, `external-tool-watchlist`, `triage-external-tool` | covered |
| Odysseus external dogfood workspace | OpenViking ideas, REEFIKI report | `docs/ODYSSEUS_DOGFOOD.md`, `ROADMAP.md` Phase 0h, `external-tool-watchlist` | covered after this pass |
| `crawl4ai` for web ingestion | REEFIKI report, Security Guidance report | `external-tool-watchlist`, `ROADMAP.md` Phase 0h | covered after this pass |
| `markitdown` for artifact ingestion | Codex App / REEFIKI / Security Guidance reports | `external-tool-watchlist`, `ROADMAP.md` Phase 0h | covered |
| `headroom` reversible context compression | Codex App / REEFIKI reports, token audits | `external-tool-watchlist`, `ROADMAP.md`, `AUDIT_SYNTHESIS_ACTION_PLAN.md` | covered |
| `vellum-assistant` governance/traceability ideas | REEFIKI report, audit docs | `external-tool-watchlist`, `ROADMAP.md` Phase 0h | covered after this pass |
| `spec-kit` as template source | Codex App / Metrica reports | `external-tool-watchlist`, `ROADMAP.md` Phase 0h | covered |
| `claude-code-harness`, Claude workflows, wshobson/agents as reference only | Codex App report | `external-tool-watchlist`, `ROADMAP.md` Phase 0h | covered |
| `telegram-agent` / `mcp-telegram` deferred/restricted | Codex App report | `external-tool-watchlist`, `ROADMAP.md` Phase 0h | covered |
| `ruflo`, jailbreak/restriction-bypass, broad agent megastacks rejected | Codex App / REEFIKI reports | `external-tool-watchlist`, `external-tool-adoption-governance`, `ROADMAP.md` Phase 0h | covered |
| Skill quality references: SkillOpt, taste-skill, mattpocock/skills | earlier link triage, Codex report | `skillopt-evaluation-gates-r-and-d`, `taste-skill-writing-reference`, `skill-quality-gate`, `ROADMAP.md` | covered |
| Security Guidance reference patterns | Security Guidance report | `projects/Security Guidance/wiki/concepts/authorized-agent-security-reference-patterns.md` | covered in target project |

## Missing Item Found

Odysseus was present in source material but missing from durable REEFIKI roadmap/registry docs. The cause was a synthesis/filtering error:

1. The first external-tool registry pass focused on the global Codex watchlist.
2. Odysseus appeared in `reefiki-report.md`, not in the global watchlist.
3. The registry prompt asked for a fixed initial list and did not require a coverage pass over sibling report recommendations.
4. Because Odysseus was a dogfood scenario rather than a tool to install, it fell between "external tool registry" and "roadmap feature" categories.

## Prevention Rule

Every future audit/report synthesis must include a coverage pass:

1. Extract all named recommendations/tools/patterns from every input report.
2. For each item, assign one durable destination: roadmap, registry, decision, skill, docs brief, seen/deferred, or explicit rejection.
3. If an item is intentionally not adopted, write the reason.
4. Only then mark the audit/report batch as covered.

This file is the first coverage checkpoint for the June 2026 audit/report batch.
