# Link Confidence Report

Date: 2026-06-14
Project: reefiki
Read-only: true
Confidence tagging needed: yes
Reason: Repeated ambiguous wikilinks found: 8 >= threshold 3.

## Totals

- pages: 77
- wikilinks: 434
- review_queue_items: 10
- broken_links: 0
- orphans: 2

## Classes

### extracted-looking

Count: 408
- `agent-agnostic-contract-pattern` -> `agent-rules-stack-author-system` (wiki/concepts/agent-agnostic-contract-pattern.md:31, related_edge_with_note)
- `agent-agnostic-contract-pattern` -> `adopt-agent-agnostic-architecture` (wiki/concepts/agent-agnostic-contract-pattern.md:32, related_edge_with_note)
- `agent-agnostic-contract-pattern` -> `agent-agnostic-contract-audit` (wiki/concepts/agent-agnostic-contract-pattern.md:33, related_edge_with_note)
- `agent-agnostic-contract-pattern` -> `layered-memory-model` (wiki/concepts/agent-agnostic-contract-pattern.md:34, related_edge_with_note)
- `agent-agnostic-contract-pattern` -> `adopt-skill-adoption-governance` (wiki/concepts/agent-agnostic-contract-pattern.md:35, related_edge_with_note)
- `knowledge-capture-decision-tree` -> `procedure-over-fact` (wiki/concepts/knowledge-capture-decision-tree.md:42, related_edge_with_note)
- `knowledge-capture-decision-tree` -> `layered-memory-model` (wiki/concepts/knowledge-capture-decision-tree.md:43, related_edge_with_note)
- `knowledge-capture-decision-tree` -> `memoir-to-reefiki-promotion-gate` (wiki/concepts/knowledge-capture-decision-tree.md:44, related_edge_with_note)

### inferred-looking

Count: 18
- `agent-agnostic-contract-pattern` -> `agent-agnostic-contract-audit` (wiki/concepts/agent-agnostic-contract-pattern.md:27, implicit_or_unexplained_edge)
- `durable-harvest-closeout` -> `staged-scope-and-publish-guard` (wiki/skills/durable-harvest-closeout.md:18, implicit_or_unexplained_edge)
- `reefiki-experience-monitor` -> `durable-harvest-closeout` (wiki/skills/reefiki-experience-monitor.md:13, implicit_or_unexplained_edge)
- `agent-workflow-reference-patterns` -> `memory-reflection-boundary` (wiki/synthesis/agent-workflow-reference-patterns.md:13, implicit_or_unexplained_edge)
- `agent-workflow-reference-patterns` -> `external-tool-adoption-governance` (wiki/synthesis/agent-workflow-reference-patterns.md:14, implicit_or_unexplained_edge)
- `agent-workflow-reference-patterns` -> `dual-remote-public-snapshot` (wiki/synthesis/agent-workflow-reference-patterns.md:15, implicit_or_unexplained_edge)
- `ai-assistant-devex-backlog-2026-06` -> `source-of-truth-diagnostics` (wiki/synthesis/ai-assistant-devex-backlog-2026-06.md:56, implicit_or_unexplained_edge)
- `ai-assistant-devex-backlog-2026-06` -> `safe-task-worktree-bootstrap` (wiki/synthesis/ai-assistant-devex-backlog-2026-06.md:57, implicit_or_unexplained_edge)

### ambiguous-looking

Count: 8
- `shared-checkout-preserve-and-scoped-republish` -> `safe-task-worktree-bootstrap` (wiki/skills/shared-checkout-preserve-and-scoped-republish.md:40, missing_backlink)
- `shared-checkout-preserve-and-scoped-republish` -> `staged-scope-and-publish-guard` (wiki/skills/shared-checkout-preserve-and-scoped-republish.md:41, missing_backlink)
- `shared-checkout-preserve-and-scoped-republish` -> `dual-remote-public-snapshot` (wiki/skills/shared-checkout-preserve-and-scoped-republish.md:42, missing_backlink)
- `shared-checkout-preserve-and-scoped-republish` -> `durable-harvest-closeout` (wiki/skills/shared-checkout-preserve-and-scoped-republish.md:43, missing_backlink)
- `odysseus-wsl-test-matrix-2026-06-12` -> `triage-external-tool` (wiki/synthesis/odysseus-wsl-test-matrix-2026-06-12.md:60, missing_backlink)
- `post-sprint-21-trigger-gated-backlog` -> `product-positioning-2026-06-11` (wiki/synthesis/post-sprint-21-trigger-gated-backlog.md:35, missing_backlink)
- `post-sprint-21-trigger-gated-backlog` -> `local-json-adapter-before-mcp-rest-server` (wiki/synthesis/post-sprint-21-trigger-gated-backlog.md:36, missing_backlink)
- `post-sprint-21-trigger-gated-backlog` -> `staged-scope-and-publish-guard` (wiki/synthesis/post-sprint-21-trigger-gated-backlog.md:37, missing_backlink)

## Review Queue Counts

- orphan_review: 2
- missing_backlink: 8

## Smallest Next Slice

Add an optional confidence marker only for `## Related` edge lines in `_schema.md`, then triage the top ambiguous links before any auto-rewrite.
