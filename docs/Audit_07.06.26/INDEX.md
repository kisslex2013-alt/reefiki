# REEFIKI Audit Index

This folder contains the full June 2026 audit pack. It is not a single linear report. Some files overlap, some correct earlier findings, and several files contain experimental ideas rather than immediate roadmap work.

## Start here

1. [AUDIT_SYNTHESIS_ACTION_PLAN.md](AUDIT_SYNTHESIS_ACTION_PLAN.md) — normalized execution order, disagreements, and source links.
2. [REEFIKI_AUDIT_ERRATA.md](REEFIKI_AUDIT_ERRATA.md) — factual corrections to earlier reports.
3. [AUDIT_RECOMMENDATION_COVERAGE.md](AUDIT_RECOMMENDATION_COVERAGE.md) — coverage checkpoint for audit/report recommendations.
4. [../../ROADMAP.md](../../ROADMAP.md) — live roadmap after synthesis.

## Canonical evidence set

| File | Use |
|---|---|
| [REEFIKI_SECURITY_AUDIT.md](REEFIKI_SECURITY_AUDIT.md) | detailed security findings with code examples |
| [SECURITY-AUDIT-FOLLOWUP-2026-06.md](SECURITY-AUDIT-FOLLOWUP-2026-06.md) | current-state follow-up confirming remaining security gaps and invalidated older assumptions |
| [CONCURRENCY-AUDIT.md](CONCURRENCY-AUDIT.md) | inter-process race conditions and SQLite/git write hazards |
| [BACKUP-RECOVERY-AUDIT.md](BACKUP-RECOVERY-AUDIT.md) | recovery gaps and memoir backup risk |
| [CODE_QUALITY_AUDIT.md](CODE_QUALITY_AUDIT.md) | monolith, test gaps, duplication, packaging issues |
| [ADDITIONAL-AUDIT.md](ADDITIONAL-AUDIT.md) | licensing, localization, performance, DR, UX, migrations, metrics |
| [REEFIKI_AUDIT.md](REEFIKI_AUDIT.md) | broad repo audit with concrete P0-P3 proposals |
| [REEFIKI_AUDIT_RU.md](REEFIKI_AUDIT_RU.md) | Russian version with detailed examples and roadmap phrasing |
| [REEFIKI_EXTENDED_AUDITS.md](REEFIKI_EXTENDED_AUDITS.md) | contract, tests, concurrency and performance follow-ups |
| [MEGA-AUDIT.md](MEGA-AUDIT.md) | merged summary, useful as a catalog, not as the sole truth source |

## Strategy and idea docs

| File | Status |
|---|---|
| [STRATEGY.md](STRATEGY.md) | strategic idea bank; not execution order |
| [OPENVIKING_IDEAS_FOR_REEFIKI.md](OPENVIKING_IDEAS_FOR_REEFIKI.md) | useful patterns, but infrastructure-heavy parts are not near-term |
| [19_claude_openviking-for-reefiki-1.md](19_claude_openviking-for-reefiki-1.md) | practical markdown-native OpenViking adaptation |
| [19_claude_2_openviking-for-reefiki-v2.md](19_claude_2_openviking-for-reefiki-v2.md) | duplicate of the previous file |
| [19_gemini_openviking-for-reefiki.md](19_gemini_openviking-for-reefiki.md) | wider OpenViking idea sweep, more speculative |
| [19_gemini_2_openviking-for-reefiki.md](19_gemini_2_openviking-for-reefiki.md) | follow-up artifact, also strategic rather than binding |
| [18_vellum-insights-for-reefiki.md](18_vellum-insights-for-reefiki.md) | useful for `NOW.md`, TTL, and session discipline ideas |
| [18_2_reefiki-proactive-behaviors.md](18_2_reefiki-proactive-behaviors.md) | agent behavior ideas; needs selective adoption |
| [16_*.md](16_reefiki-token-analysis.md) | token-budget and context-loading work; use for optimization details, not product priority by itself |

## Topic audits

The numbered docs `01_` through `14_` cover focused themes such as licensing, localization, performance, disaster recovery, UX, mobile capture, Obsidian, migrations, competitive analysis, health metrics, wizard, dashboard, architecture decisions, and unique features.

Use them as source material for implementation details and example code. The normalized priority order lives in [AUDIT_SYNTHESIS_ACTION_PLAN.md](AUDIT_SYNTHESIS_ACTION_PLAN.md), not in the raw numbering.

## Folder status

- Current files in this folder: 49
- Original audit inputs: 46 files; `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `AUDIT_SYNTHESIS_VERIFICATION_REPORT.md`, and `AUDIT_RECOMMENDATION_COVERAGE.md` are added normalization/verification/governance artifacts.
- Two files are duplicates: `19_claude_openviking-for-reefiki-1.md` and `19_claude_2_openviking-for-reefiki-v2.md`
- The synthesis and errata should be treated as the safest starting point before acting on any individual recommendation
