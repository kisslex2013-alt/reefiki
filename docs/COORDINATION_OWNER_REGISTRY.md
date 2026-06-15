# Coordination Owner Registry — deferred design

## Purpose

REEFIKI coordination files (`ROADMAP.md`, `TASKS.md`, `AGENTS.md`, project `wiki/log.md`, project `wiki/index.md`) are shared write surfaces. Sprint 21 intentionally does not add a lock or lease runtime. The registry below is a minimal future design if operation-aware staged guards still prove insufficient.

## Proposed Claim Shape

```json
{
  "owner": "codex/<task-or-thread>",
  "scope": ["TASKS.md", "projects/reefiki/wiki/log.md"],
  "intent": "close Sprint 21 T-119",
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "expires_at": "YYYY-MM-DDTHH:MM:SSZ",
  "base": "origin/main",
  "worktree": "S:/Coding/01_PROJECTS/_worktrees/<repo>-<task>"
}
```

## Guard Integration Point

If implemented, `guard-staged` would read active claims before commit:

- pass when every staged coordination file is claimed by the current owner;
- block when a staged coordination file is claimed by another active owner;
- warn, not block, when an expired claim exists and the staged diff is otherwise valid.

## Deferred Criteria

Do not implement this until there is real evidence after Sprint 21:

- repeated parallel conflicts on coordination files despite worktree isolation;
- operation profiles are too weak to explain ownership;
- manual integration-owner discipline causes actual lost work or blocked publish.

Until then, use the existing rule: one task branch owns coordination-file writes for its slice, stages explicit paths only and reports excluded dirty files.
