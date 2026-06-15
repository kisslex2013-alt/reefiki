# REEFIKI LeadOps

LeadOps is a local coordination method for running several agent tasks in parallel without turning REEFIKI into a new agent runtime.

It keeps the current rules:

- REEFIKI remains the durable knowledge and governance layer.
- `memoir` remains short working memory and preferences.
- `graphify` remains structure maps.
- `codegraph` remains disposable code navigation.
- No background writer, auto-promotion, auto-capture, cron, daemon, MCP server, or global config change is introduced by this document.

## Roles

| Role | Responsibility | Writes |
|---|---|---|
| Lead | Reads project context, creates tasks, assigns workers, verifies results, integrates final changes, updates docs/wiki/log/index, decides the next loop. | Coordination files and final integration only. |
| Worker | Executes one bounded task in one dedicated worktree/branch. | Only the assigned write surface. |
| Explorer | Answers a read-only question about code/docs/wiki. | None. |
| Verifier | Reviews a diff, tests, scope, security, publish safety, and missing evidence. | None unless explicitly assigned. |

The lead is the integration owner. Workers and explorers may run in parallel, but shared coordination writes are serialized through the lead.

## Task Board

For a longer batch, the lead may create a local board in `plans/leadops/<date>-<topic>.md`.

For cross-thread worktree ownership, use the machine-readable ledger:

```text
plans/leadops/worktree-ledger.json
```

This file is intentionally small and empty by default. It becomes active when a lead opens a batch or parallel worktree set. Because it coordinates ownership, it is itself a coordination file: one integration owner edits it during a batch.

Use these states:

| State | Meaning |
|---|---|
| `ready` | Task has scope, non-goals, expected evidence, owner, and write surface. |
| `assigned` | Worker/explorer/verifier is running. |
| `blocked` | Missing input, failing gate, conflict, or unclear ownership. |
| `review` | Worker returned a result; lead or verifier must inspect it. |
| `integrated` | Lead accepted and integrated the useful result. |
| `published` | Publish/merge flow completed, if requested. |
| `superseded` | Useful intent was replaced elsewhere with evidence. |

Minimal task card:

```text
id:
state:
owner:
worktree:
branch:
scope:
forbidden_paths:
expected_evidence:
result:
lead_decision:
```

Minimal ledger entry:

```json
{
  "branch": "codex/example-task",
  "worktree": "S:/Coding/01_PROJECTS/_worktrees/REEFIKI-example-task",
  "owner": "thread-or-agent-id",
  "scope": "projects/reefiki/wiki/**",
  "coordination_files": ["projects/reefiki/wiki/log.md"],
  "integration_owner": "lead-thread-or-agent-id",
  "milestone": "nearest natural milestone",
  "created_at": "2026-06-13",
  "status": "active",
  "next_action": "finish targeted tests and publish dry-run",
  "cleanup_reason": ""
}
```

Ledger rules:

- `owner`, `scope`, `milestone`, and `created_at` are required for active task branches.
- `coordination_files` must list shared files such as `ROADMAP.md`, `TASKS.md`, `AGENTS.md`, `projects/*/wiki/log.md`, `projects/*/wiki/index.md`, and `plans/leadops/worktree-ledger.json` when touched.
- If two entries touch the same coordination file, they need the same non-empty `integration_owner`.
- Roadmap/batch worktree leases should close at the nearest milestone and default to review after 14 days.
- Remote `origin/codex/*` branches should be deleted after they are reachable from `origin/main`.

## Loop

1. Lead preflight:
   - read `AGENTS.md`, `ROADMAP.md`, `TASKS.md`, relevant wiki pages and current worktree status;
   - check shared checkout status, but do not use it if dirty or behind;
   - choose one coherent batch or stop on a real blocker.
2. Lead slices work:
   - create independent tasks with disjoint write surfaces;
   - assign one integration owner for shared files like `ROADMAP.md`, `TASKS.md`, `wiki/log.md`, `wiki/index.md`, `AGENTS.md`.
3. Workers run:
   - one task = one `git worktree` = one `codex/*` branch;
   - no push;
   - no cleanup;
   - no unrelated refactor;
   - no shared coordination writes unless assigned.
4. Workers report:
   - changed paths;
   - tests/checks run;
   - evidence found;
   - blockers and residual risks;
   - exact next action if incomplete.
5. Lead integrates:
   - inspect diffs;
   - keep only useful intent;
   - update wiki/log/index when durable knowledge changed;
   - run targeted tests and broader gates when scope requires.
6. Lead closes the loop:
   - commit scoped paths;
   - publish only when requested and only through REEFIKI publish flow;
   - keep or cleanup worktrees according to `docs/WORKTREE_LIFECYCLE.md`;
   - repeat until the batch is complete or blocked.

## Boundaries

Do:

- use parallel reads for large audits, link triage, queue review, source inspection, and independent code slices;
- serialize writes to coordination files through the lead;
- prefer small worktrees from fresh `origin/main`;
- ask workers for proof, not confidence;
- let the lead do final review and publish decisions.

Do not:

- install Paperclip, Agent Team AI, LangGraph, or any other orchestration runtime from this document alone;
- let workers push, publish, clean up worktrees, or mutate global config;
- let multiple agents edit `wiki/log.md`, `wiki/index.md`, `ROADMAP.md`, `TASKS.md`, or `AGENTS.md` without an assigned integration owner;
- merge stale worktree final trees wholesale;
- turn reflection or task reports into auto-writes.

## Closeout Gates

Before the lead calls a LeadOps batch complete:

- `git status --short --branch`
- `git diff --name-only origin/main...HEAD`
- targeted tests for changed behavior
- `python scripts/validate_frontmatter.py projects/reefiki/wiki`
- `python scripts/reefiki.py --project projects/reefiki doctor`
- `python scripts/reefiki.py --project projects/reefiki index`
- `python scripts/reefiki.py --project projects/reefiki dashboard --format json --limit 5` for governance/dashboard batches
- `python scripts/reefiki.py memory golden --project reefiki --format json` for memory/routing/query batches
- `python -m pytest` when code or shared CLI behavior changed
- `python scripts/reefiki.py worktree-status --format json`
- `python scripts/reefiki.py worktree-status --ledger plans/leadops/worktree-ledger.json --format json` for parallel/batch work
- `python scripts/reefiki.py orchestration-check --ledger plans/leadops/worktree-ledger.json --include-global-config --format json` before publishing a LeadOps batch
- `python scripts/reefiki.py publish-task --dry-run --cleanup --format json` when publish/merge is requested

Stage only explicit paths. Do not use `git add -A`.

## External References

These are references for patterns only, not adopted runtimes:

- Paperclip: agent-company style orchestration; watchlist/sandbox only.
- Agent Team AI: possible UI/runner candidate if a concrete sandbox smoke is needed.
- LangGraph supervisor: useful supervisor pattern, overkill for REEFIKI unless building a real runtime.
- Code Agent Orchestra / multi-agent workspace guides: useful wording for lead/worker/verifier discipline.
