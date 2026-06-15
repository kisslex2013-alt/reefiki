# REEFIKI Audit Synthesis and Action Plan

Date: 2026-06-07
Scope: full pass over `docs/Audit_07.06.26/` plus spot-checks in `scripts/reefiki.py`, `scripts/validate_frontmatter.py`, `.pre-commit-config.yaml`, `.github/workflows/`, `.gitignore`, `README.md`, `ROADMAP.md`.

This file is the working synthesis for the June 2026 audit pack: 46 original audit inputs plus normalization/coverage artifacts. It is not another parallel audit. It normalizes priorities, notes where the raw audits disagree, and turns the useful parts into one execution order.

## What to treat as canonical

Read in this order if you need the shortest path:

1. `REEFIKI_AUDIT_ERRATA.md` — factual corrections and priority fixes.
2. This file — normalized execution plan.
3. `AUDIT_RECOMMENDATION_COVERAGE.md` — coverage checkpoint for named recommendations from audit/report inputs.
4. `ROADMAP.md` — live project roadmap after synthesis.
5. Source audits only for detail and code examples.

Important note:
- `19_claude_openviking-for-reefiki-1.md` and `19_claude_2_openviking-for-reefiki-v2.md` are duplicates.
- OpenViking reports should be read as an argument for a lightweight markdown-native context layer, not for early server/MCP/vector infrastructure.
- Named recommendations from sibling reports must get a durable destination or explicit rejection in `AUDIT_RECOMMENDATION_COVERAGE.md`.

## What changed after synthesis

These corrections override stronger claims in the raw reports:

1. Python baseline stays `3.11+`, not `3.9`.
Sources:
- [REEFIKI_AUDIT_ERRATA.md](REEFIKI_AUDIT_ERRATA.md)
- [REEFIKI_CROSSPLATFORM_AUDIT.md](REEFIKI_CROSSPLATFORM_AUDIT.md)
- [REEFIKI_DEPS_AUDIT.md](REEFIKI_DEPS_AUDIT.md)

2. The frontmatter CRLF bug exists in both parsers, not only in the validator.
Code:
- [scripts/reefiki.py](../../scripts/reefiki.py)
- [scripts/validate_frontmatter.py](../../scripts/validate_frontmatter.py)
Sources:
- [REEFIKI_AUDIT_ERRATA.md](REEFIKI_AUDIT_ERRATA.md)
- [REEFIKI_SECURITY_AUDIT.md](REEFIKI_SECURITY_AUDIT.md)

3. The real immediate risk is not "missing fancy search". It is path safety, publish safety, CI absence, and SQLite/git concurrency.
Sources:
- [REEFIKI_SECURITY_AUDIT.md](REEFIKI_SECURITY_AUDIT.md)
- [CONCURRENCY-AUDIT.md](CONCURRENCY-AUDIT.md)
- [SECURITY-AUDIT.md](SECURITY-AUDIT.md)
- [MEGA-AUDIT.md](MEGA-AUDIT.md)

4. Early vector search, MCP server, cloud memory, and full dashboard are not Phase 0/P1 work.
Sources:
- [STRATEGY.md](STRATEGY.md)
- [OPENVIKING_IDEAS_FOR_REEFIKI.md](OPENVIKING_IDEAS_FOR_REEFIKI.md)
- [19_claude_openviking-for-reefiki-1.md](19_claude_openviking-for-reefiki-1.md)
- [19_gemini_openviking-for-reefiki.md](19_gemini_openviking-for-reefiki.md)

5. Full wizard/dashboard/mobile productization is useful, but must follow safety and packaging.
Sources:
- [11_Onboarding Wizard.md](11_Onboarding%20Wizard.md)
- [12_DASHBOARD.md](12_DASHBOARD.md)
- [13_ARCHITECTURE_DECISIONS.md](13_ARCHITECTURE_DECISIONS.md)

## Execution order

The right order is:

1. Safety foundation
2. CI and verification gates
3. Packaging, installability, and legal baseline
4. Integrity and health tooling
5. Context/query improvements that stay markdown-native
6. UX layers such as dashboard and wizard
7. Advanced search, MCP, external ecosystem

## Step 1 - Safety foundation

Why now:
- Real data leak and corruption risks are still open in current code.

Code touchpoints:
- [scripts/reefiki.py](../../scripts/reefiki.py)
- [scripts/reefiki_memory/__init__.py](../../scripts/reefiki_memory/__init__.py)
- [.pre-commit-config.yaml](../../.pre-commit-config.yaml)

Do now:
- Add one shared containment helper for all local paths used by `save_source()`, `dedup_check()`, and `plan_check()`.
- Fix `escape_fts()` so empty-token queries return empty string, not raw FTS syntax.
- Add content-based secret scanning before publish flows and `harvest-commit`.
- Add secret scanning hook to pre-commit.
- Add subprocess timeouts.
- Replace the hardcoded `GLOBAL_MEMOIR_STORE` default path with a portable home-relative default.

Primary sources:
- [REEFIKI_SECURITY_AUDIT.md](REEFIKI_SECURITY_AUDIT.md)
- [SECURITY-AUDIT.md](SECURITY-AUDIT.md)
- [REEFIKI_AUDIT_ERRATA.md](REEFIKI_AUDIT_ERRATA.md)

Useful code examples already exist in:
- `SEC-003`, `SEC-005`, `SEC-007`, `SEC-010`, `SEC-012`, `SEC-017` inside [REEFIKI_SECURITY_AUDIT.md](REEFIKI_SECURITY_AUDIT.md)

## Step 2 - CI and verification gates

Why now:
- The repo has only `inbox-capture.yml`. Core checks are still manual.

Code touchpoints:
- [.github/workflows](../../.github/workflows)
- [tests](../../tests)

Do now:
- Add GitHub Actions for frontmatter validation, pytest, and memory golden baseline.
- Add tests for `escape_fts()`, path containment, publish safety, and `promote-dry-run --apply-draft`.
- Add git fixture tests for publish and harvest flows before any larger refactor.

Primary sources:
- [REEFIKI_AUDIT.md](REEFIKI_AUDIT.md)
- [REEFIKI_AUDIT_RU.md](REEFIKI_AUDIT_RU.md)
- [REEFIKI_EXTENDED_AUDITS.md](REEFIKI_EXTENDED_AUDITS.md)
- [CODE_QUALITY_AUDIT.md](CODE_QUALITY_AUDIT.md)

Useful code examples already exist in:
- `CORE-01`, `CORE-03`, `Q3`, `Q4` inside [REEFIKI_AUDIT.md](REEFIKI_AUDIT.md)

## Step 3 - Packaging, installability, legal baseline

Why now:
- `LICENSE` and `pyproject.toml` are still missing. Without these, open-source posture and install story are incomplete.

Code touchpoints:
- [README.md](../../README.md)
- [ROADMAP.md](../../ROADMAP.md)
- repo root packaging files

Do now:
- Add `LICENSE`.
- Add `pyproject.toml` with `requires-python >= 3.11`.
- Add minimal install guidance that matches the actual runtime.
- Separate "code license" from "wiki content ownership".

Primary sources:
- [01_LICENSING.md](01_LICENSING.md)
- [ADDITIONAL-AUDIT.md](ADDITIONAL-AUDIT.md)
- [reefiki-audit.md](reefiki-audit.md)

Useful code and file examples already exist in:
- `L-01` to `L-05` inside [01_LICENSING.md](01_LICENSING.md)
- `D3` inside [reefiki-audit.md](reefiki-audit.md)

## Step 4 - Concurrency and integrity

Why now:
- Multi-agent use is a core positioning claim, but the current write paths are still race-prone.

Code touchpoints:
- [scripts/reefiki.py](../../scripts/reefiki.py)

Do now:
- Add `busy_timeout` to all SQLite connections.
- Wrap SQLite usage in context managers.
- Add advisory lock for `build_index()`.
- Make inbox/plan/promotion page creation atomic.
- Bound `search_existing()` rebuild retries.
- Add integrity checks and a lightweight health/doctor command.

Primary sources:
- [CONCURRENCY-AUDIT.md](CONCURRENCY-AUDIT.md)
- [BACKUP-RECOVERY-AUDIT.md](BACKUP-RECOVERY-AUDIT.md)
- [04_DISASTER_RECOVERY.md](04_DISASTER_RECOVERY.md)
- [10_KNOWLEDGE_HEALTH_METRICS.md](10_KNOWLEDGE_HEALTH_METRICS.md)

Useful code examples already exist in:
- findings 1-12 inside [CONCURRENCY-AUDIT.md](CONCURRENCY-AUDIT.md)
- `check_index_integrity()` example inside [04_DISASTER_RECOVERY.md](04_DISASTER_RECOVERY.md)
- `knowledge_health()` example inside [10_KNOWLEDGE_HEALTH_METRICS.md](10_KNOWLEDGE_HEALTH_METRICS.md)

## Step 5 - Markdown-native context improvements

Why now:
- These give real retrieval gains without introducing vector infrastructure.
- The two Claude OpenViking files reinforce this conservative path: take the page/context patterns, leave the infrastructure.

Code touchpoints:
- [projects/_template/wiki/_schema.md](../../projects/_template/wiki/_schema.md)
- [projects/_template/.claude/commands/query.md](../../projects/_template/.claude/commands/query.md)
- [scripts/reefiki.py](../../scripts/reefiki.py)

Do now:
- Add `abstract` as an L0 summary field.
- Add typed page metadata only where it improves filtering, validation, or answer provenance.
- Add `_overview.md` per `wiki/<subdir>/`.
- Update `/query` to use abstract-first loading.
- Add compact `context-pack` bundles only after L0/L1 summaries are reliable.
- Add `why` / retrieval trace after `context-pack`, so answers can explain which pages were loaded and why.

Do not do now:
- `reefiki://` URI scheme.
- MCP or hosted server layer.
- embeddings/vector infrastructure.
- importing AGPL code or copying implementation from OpenViking.

Primary sources:
- [19_claude_openviking-for-reefiki-1.md](19_claude_openviking-for-reefiki-1.md)
- [OPENVIKING_IDEAS_FOR_REEFIKI.md](OPENVIKING_IDEAS_FOR_REEFIKI.md)
- [15_reefiki-user-context-revised.md](15_reefiki-user-context-revised.md)
- [16_reefiki-token-analysis.md](16_reefiki-token-analysis.md)
- [16_2_reefiki-token-final.md](16_2_reefiki-token-final.md)

Useful code examples already exist in:
- `abstract`, `_overview.md`, and query-step examples in [19_claude_openviking-for-reefiki-1.md](19_claude_openviking-for-reefiki-1.md)
- `context-pack` and token-budget examples in [16_1_reefiki-headroom-adaptation.md](16_1_reefiki-headroom-adaptation.md)

## Step 6 - Governance UX and knowledge quality

Why now:
- REEFIKI's differentiator is governance, not raw storage. Quality tooling should reinforce that before product UI grows.

Code touchpoints:
- [projects/_template/wiki/_schema.md](../../projects/_template/wiki/_schema.md)
- [scripts/validate_frontmatter.py](../../scripts/validate_frontmatter.py)
- [scripts/reefiki.py](../../scripts/reefiki.py)

Do now:
- Add `schema_version`.
- Add `id == filename` validation.
- Add health metrics that are operational, not decorative.
- Add `antipattern` or equivalent negative-knowledge representation only after schema/versioning groundwork is in place.

Primary sources:
- [08_SCHEMA_MIGRATIONS.md](08_SCHEMA_MIGRATIONS.md)
- [10_KNOWLEDGE_HEALTH_METRICS.md](10_KNOWLEDGE_HEALTH_METRICS.md)
- [14_UNIQUE_FEATURES.md](14_UNIQUE_FEATURES.md)
- [REEFIKI_AUDIT_RU.md](REEFIKI_AUDIT_RU.md)

## Step 7 - UX layers

Why later:
- Wizard, dashboard, mobile capture, and Obsidian docs are good multipliers, but they do not fix current safety gaps.

Code touchpoints:
- future `scripts/wizard.py`
- future dashboard entrypoint
- docs and template files

Do after steps 1-6 are green:
- Minimal `QUICKSTART.md`
- `docs/obsidian-setup.md`
- `docs/mobile-capture.md`
- minimal read-only dashboard
- wizard only after packaging and install flow are real

Primary sources:
- [05_UX_ACCESSIBILITY.md](05_UX_ACCESSIBILITY.md)
- [06_MOBILE_CAPTURE.md](06_MOBILE_CAPTURE.md)
- [07_OBSIDIAN.md](07_OBSIDIAN.md)
- [11_Onboarding Wizard.md](11_Onboarding%20Wizard.md)
- [12_DASHBOARD.md](12_DASHBOARD.md)
- [13_ARCHITECTURE_DECISIONS.md](13_ARCHITECTURE_DECISIONS.md)

## Step 8 - Advanced search and ecosystem

Why last:
- This is where cost and architecture sprawl start. The trigger must stay evidence-based.

Do only if the simpler stack demonstrably misses:
- qmd or another local search layer
- MCP server
- cloud sync / managed publish / templates marketplace
- vector search

Primary sources:
- [STRATEGY.md](STRATEGY.md)
- [09_COMPETITIVE_ANALYSIS.md](09_COMPETITIVE_ANALYSIS.md)
- [REEFIKI_AUDIT.md](REEFIKI_AUDIT.md)
- [OPENVIKING_IDEAS_FOR_REEFIKI.md](OPENVIKING_IDEAS_FOR_REEFIKI.md)

## Short backlog by priority

### P0

- `LICENSE` and `pyproject.toml`
- common path containment helper
- secret scanning in pre-commit and publish pipeline
- CI workflow for validator, tests, and golden baseline
- tests for `escape_fts`, path containment, and durable apply/publish paths
- SQLite `busy_timeout`, context managers, atomic file create

### P1

- `doctor`/health command
- `schema_version` and validator consistency checks
- `abstract` field and `_overview.md`
- `QUICKSTART.md`, recovery doc, Obsidian setup doc
- portable memoir store default and runtime checks

### P2

- minimal read-only dashboard
- wizard
- `_user/` formalization
- `context-pack` and `why`
- negative knowledge / `antipattern`

### P3

- MCP server
- vector/hybrid search
- managed cloud features
- marketplace and GTM work

## Practical rule

If an item depends on fixing current code risk, do not let strategy/UI work jump ahead of it.

The project should become:
- safe first
- testable second
- installable third
- easier to use fourth
- more ambitious only after that
