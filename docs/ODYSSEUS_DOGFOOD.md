# Odysseus Dogfood Plan

Date: 2026-06-07
Status: planned dogfood candidate, not an integration dependency

## Purpose

Odysseus is useful for REEFIKI as an external dogfood workspace: a separate agent/workspace that can test whether REEFIKI behaves like a portable context and memory control plane, not just as its own local CLI.

This is not a proposal to install Odysseus into REEFIKI core, add MCP servers, or change the memory stack. The test value is behavioral: can an external workspace consume REEFIKI context, respect governance, and expose retrieval/conflict quality?

## When To Use

Use Odysseus only after the current foundation gates are stable:

1. Phase 0j P0/P1 is green enough for safe publish, CI, packaging, and concurrency work.
2. Markdown-native context work exists: `abstract`, `_overview.md`, `context-pack`, and `why` / retrieval trace.
3. There is a concrete benchmark question, not a vague "try a new agent" task.

Before those gates, keep Odysseus as a dogfood candidate in roadmap/registry only.

## Scenarios

1. **Project onboarding** — given only a project name, Odysseus asks REEFIKI for the minimum context pack and produces a correct first action.
2. **Memory retrieval** — asks a question whose answer exists in wiki and checks whether REEFIKI returns the right pages, not just keyword matches.
3. **Stale memory conflict** — uses pages with old decisions or conflicting claims and checks whether REEFIKI surfaces the conflict.
4. **Agent-specific context export** — requests context for Codex, Claude Code, Hermes, and vendor-neutral modes; compares size and usefulness.
5. **Multi-agent handoff** — receives a handoff from one agent and uses REEFIKI to recover decisions and current constraints.
6. **Long-session summarization** — tests whether long work can be distilled into decisions/skills/synthesis without session dump.
7. **Governance gate** — proposes a new external tool and verifies REEFIKI routes it through watchlist -> registry/decision/skill.
8. **Memory deletion or update** — tests whether obsolete knowledge becomes review/resolve work instead of silent overwrite.
9. **Vendor-neutral prompt generation** — asks REEFIKI for a prompt that works outside one agent's conventions.
10. **Model comparison** — runs the same context pack through multiple agents/models and compares misses, hallucinations, and overreach.

## Success Criteria

- Odysseus can use REEFIKI without needing direct access to private project folders outside the chosen scope.
- REEFIKI can explain why each page was included or skipped.
- Stale/conflicting knowledge is visible in the output.
- Context packs stay small enough to be useful in a real agent session.
- The dogfood result creates durable REEFIKI artifacts only when there is a reusable decision, procedure, synthesis, or verified risk.

## Non-Goals

- No Odysseus install as part of REEFIKI core.
- No MCP/server layer just for this dogfood.
- No new memory runtime.
- No automatic capture of every Odysseus session.
- No public publish of private project data.

## Evidence Sources

- `docs/Audit_07.06.26/OPENVIKING_IDEAS_FOR_REEFIKI.md`
- `C:/Users/kissl/Documents/Codex/2026-06-07/codex-app-reefiki-metrica-security-guidance/reefiki-report.md`

## Next Action

Keep this as a ready dogfood brief. Activate it only when Phase 0j foundation work and the first markdown-native context/why layer are ready to measure.
