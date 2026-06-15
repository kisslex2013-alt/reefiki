# OpenViking Ideas for REEFIKI

## Purpose

This document captures reusable architectural ideas from OpenViking that could strengthen REEFIKI without copying OpenViking's implementation. The goal is to position REEFIKI as a stricter, agent-agnostic memory and context control plane for multi-agent coding workflows.

OpenViking describes itself as a context database for AI agents. The useful lesson for REEFIKI is not the exact product shape, but the framing: memory should not be treated as a loose pile of vector chunks. It should be governed, typed, observable, layered, and exportable to agents.

A concise positioning sentence for REEFIKI:

> REEFIKI is an agent-agnostic memory and context control plane: it stores, governs, retrieves, audits, and exports the context that coding agents need.

## High-Level Takeaway

OpenViking's strongest idea is the filesystem paradigm for context. It organizes memories, resources, and skills in a structure that agents can navigate. REEFIKI can adapt this idea into a virtual project context tree focused on coding agents, governance, and portable agent contracts.

Example REEFIKI namespace:

```text
reefiki://project/reefiki/memories/
reefiki://project/reefiki/decisions/
reefiki://project/reefiki/constraints/
reefiki://project/reefiki/agent-contracts/
reefiki://project/reefiki/sessions/
reefiki://project/reefiki/artifacts/
reefiki://project/reefiki/skills/
```

This gives agents a stable mental model: retrieve by scope and path, not only by embedding similarity.

## Idea 1: Context Filesystem

OpenViking treats context like a filesystem. REEFIKI can use the same conceptual model while keeping its own identity: a governed context filesystem for project memory.

Suggested top-level context areas:

```text
memory       Durable facts, preferences, project knowledge
Decision     Architecture and product decisions
constraint   Rules, prohibitions, safety boundaries, compatibility limits
artifact     Reports, plans, PR summaries, audit outputs, generated docs
skill        Reusable workflows and procedures
session      Archived agent/user sessions
contract     Agent-agnostic instructions and export formats
```

Value for REEFIKI:

- Makes memory easier for agents to inspect and explain.
- Separates different kinds of context instead of flattening everything into generic memory.
- Supports scoped retrieval: project, user, agent, task, or artifact.
- Creates a clear foundation for CLI commands, MCP tools, and future UI views.

## Idea 2: L0/L1/L2 Layered Context

OpenViking uses three context layers:

```text
L0: Abstract, about 100 tokens, used for discovery and filtering
L1: Overview, about 1k-2k tokens, used for navigation and rerank
L2: Full detail, loaded only when needed
```

REEFIKI adaptation:

```text
L0: Memory capsule
A short statement of what the item is and when to use it.

L1: Agent-facing context card
A compact working summary with scope, constraints, source, freshness, and links to details.

L2: Source artifact
The full session, file, report, transcript, decision record, or raw source.
```

Example:

```text
L0:
User prefers generated reports in docs/, but original README/AGENTS/CHANGELOG stay at root.

L1:
# Docs Folder Convention
Scope: REEFIKI generated reports
Rule: docs/ contains audit, strategy, and recommendation files generated during analysis. Do not copy original project markdown files into docs/ unless explicitly requested.
Source: user correction
Freshness: current
Use when: organizing generated markdown outputs.

L2:
Full conversation excerpt or correction record that introduced the rule.
```

Value for REEFIKI:

- Reduces context load while preserving traceability.
- Lets small models use L0/L1 without reading full artifacts.
- Gives larger agents a path to request L2 only when needed.
- Fits REEFIKI's governance angle: every compact memory can link back to its source.

## Idea 3: Typed Context Instead Of Generic Memory

OpenViking distinguishes memory, resources, and skills. REEFIKI should go further for coding workflows.

Recommended context types:

```text
user_memory       User preferences, identity, communication style
project_memory    Stable facts about the repository and architecture
agent_memory      Lessons about how agents should operate in this project
Decision          Architecture/product decisions and their rationale
constraint        Rules, compatibility limits, safety requirements
artifact          Generated reports, plans, reviews, strategy docs
skill             Reusable procedures and workflows
session           Archived interaction summaries
contract          Vendor-neutral agent instruction packages
```

Why this matters:

- Different types need different retention rules.
- A stale decision should be superseded differently from a stale preference.
- Agent execution lessons should not be mixed with user identity.
- Artifacts should remain source-linked rather than silently becoming memory.

## Idea 4: Retrieval Trajectory And `reefiki why`

OpenViking emphasizes observable retrieval. REEFIKI can turn this into a signature feature.

Proposed command:

```bash
reefiki why "provider fallback support"
```

Example output:

```text
Query intent: architecture change
Loaded:
- L0 decision/provider-abstraction
- L1 artifact/agent-contract-v2
- L1 memory/user-prefers-vendor-agnostic-prompts
Skipped:
- session/old-codex-auth-debug because it is stale
Reason:
- newer correction exists
- current task targets provider fallback behavior
```

Value for REEFIKI:

- Makes memory debuggable.
- Helps users understand why an agent saw a piece of context.
- Exposes stale or conflicting memory instead of hiding it behind retrieval magic.
- Creates a concrete differentiator from ordinary vector search memory tools.

## Idea 5: Session Commit With Memory Diff

OpenViking's `session.commit()` lifecycle is useful: archive messages, summarize, extract memories, and write a memory diff. REEFIKI can adapt this as a stricter, governance-first workflow.

Proposed command:

```bash
reefiki session commit
```

Example result:

```text
Archive created: reefiki://project/reefiki/sessions/2026-06-07-001
Summary generated: yes
Candidate memories: 4
Created: 1
Merged: 2
Skipped: 1
Memory diff: reefiki://project/reefiki/sessions/2026-06-07-001/memory_diff.json
```

The important principle: memory updates should be explicit, reviewable, and reversible.

Example memory diff:

```json
{
  "operation": "merge",
  "target": "preferences/generated-docs-location",
  "reason": "User corrected docs/ convention",
  "source_session": "2026-06-07-001",
  "before": "Generated docs may be collected in docs/.",
  "after": "Generated reports go in docs/. Original project markdown files stay at root unless explicitly requested."
}
```

Value for REEFIKI:

- Prevents silent memory drift.
- Provides auditability and rollback.
- Makes memory extraction safer across multiple agents.
- Supports governance gates before durable memory changes.

## Idea 6: Intent-Based Context Preparation

OpenViking distinguishes simple retrieval from LLM-planned retrieval. REEFIKI can use a similar split.

Simple search:

```bash
reefiki find "codex auth"
```

Agent context preparation:

```bash
reefiki prepare-context "Fix Codex provider fallback in this repo"
```

Possible plan:

```text
Intent: implementation task
Needed context:
- project constraints
- relevant architecture decisions
- provider authentication cases
- agent contract
- recent generated docs
Excluded context:
- unrelated UX strategy docs
- stale auth checks superseded by newer smoke-test rule
```

Value for REEFIKI:

- Aligns retrieval with task intent, not just keywords.
- Produces better context bundles for Codex, Claude Code, Hermes, and other agents.
- Lets REEFIKI become a preflight context compiler for coding agents.

## Idea 7: Agent Memory Vs User Memory

OpenViking separates user-related memory from agent/task memory. REEFIKI should make this explicit.

Suggested scopes:

```text
user memory
Who the user is, how they prefer to work, communication conventions.

project memory
Stable repository facts, architecture, dependencies, workflows.

agent memory
Lessons about how agents should execute tasks in this project.

artifact memory
Generated documents and reports, always source-linked.

case memory
Problem/solution records from past debugging or implementation sessions.
```

This helps avoid mixing unrelated facts, such as a user's language preference and a repository's SQLite FTS5 dependency.

## Idea 8: REEFIKI URI Scheme

A `reefiki://` URI scheme would give memory and artifacts stable references.

Examples:

```text
reefiki://user/preferences/language
reefiki://project/reefiki/decisions/context-filesystem
reefiki://project/reefiki/artifacts/STRATEGY.md
reefiki://project/reefiki/sessions/2026-06-07-001
reefiki://project/reefiki/contracts/codex
reefiki://project/reefiki/contracts/claude-code
reefiki://project/reefiki/contracts/vendor-neutral
```

Value:

- Makes context references portable across agents.
- Gives MCP tools and CLI commands a common addressing model.
- Allows memory diffs to point to exact sources and targets.
- Creates a natural bridge to future UI or web workspace integrations.

## What Not To Copy Blindly

OpenViking is useful inspiration, but REEFIKI should avoid becoming a clone.

Avoid:

- Copying implementation code, especially because OpenViking is AGPL-3.0.
- Adding heavy infrastructure too early, such as Rust/C++ components or a complex server requirement, unless there is a clear need.
- Framing REEFIKI as only a context database. Its stronger identity is governance, multi-agent portability, and agent-neutral memory contracts.
- Over-indexing on token optimization. Layered context is useful, but REEFIKI's core value should be correctness, control, auditability, and reliable agent handoff.

## Recommended REEFIKI Positioning

A strong positioning paragraph:

> REEFIKI treats memory as a governed context filesystem for AI agents. Every memory has a type, scope, source, freshness, confidence, and retrieval trace. Agents receive layered context: L0 capsules for discovery, L1 cards for working context, and L2 artifacts only when needed. Unlike ordinary vector memory, REEFIKI focuses on auditability, conflict handling, multi-agent portability, and vendor-neutral context export.

## Candidate Features

### 1. Virtual Context Tree

Priority: HIGH
Complexity: M

Create a virtual tree over existing REEFIKI storage:

```text
reefiki://project/{project}/memories/
reefiki://project/{project}/decisions/
reefiki://project/{project}/constraints/
reefiki://project/{project}/artifacts/
reefiki://project/{project}/sessions/
reefiki://project/{project}/contracts/
```

This can start as a logical addressing layer without changing all storage internals.

### 2. L0/L1/L2 Memory Cards

Priority: HIGH
Complexity: M

Add layered representations to memory records:

```text
l0_summary
l1_context_card
l2_source_uri
```

Start with generated reports and user-corrected preferences, then expand to sessions and decisions.

### 3. `reefiki why`

Priority: HIGH
Complexity: M

Expose retrieval trace for any query or context bundle. This is a strong trust and debugging feature.

### 4. Session Commit And Memory Diff

Priority: HIGH
Complexity: L

Introduce explicit commit lifecycle for session-to-memory extraction:

```bash
reefiki session commit --review
reefiki memory diff show
reefiki memory diff revert <id>
```

This aligns strongly with REEFIKI's governance identity.

### 5. Intent-Based `prepare-context`

Priority: MEDIUM
Complexity: M

Create a command that compiles agent-ready context based on task intent:

```bash
reefiki prepare-context --for codex "implement provider fallback"
reefiki prepare-context --for claude-code "review auth architecture"
reefiki prepare-context --for hermes "schedule weekly repo audit"
```

### 6. Agent-Neutral Context Export

Priority: HIGH
Complexity: S-M

Use the same underlying memory, but export it differently for agents:

```text
AGENTS.md style
CLAUDE.md style
Codex prompt style
Hermes task prompt style
MCP response format
```

The source should stay vendor-neutral; only the final rendering changes.

## Suggested Implementation Order

Sprint 1: Foundation

1. Define context types and `reefiki://` URI scheme.
2. Add L0/L1/L2 fields or derived views for memory records.
3. Implement a read-only context tree listing command.
4. Add generated docs/artifacts to the tree.

Sprint 2: Observability

1. Add retrieval trace capture.
2. Implement `reefiki why`.
3. Show skipped stale/conflicting memories.
4. Add tests for conflict explanation.

Sprint 3: Governance

1. Add `session commit` workflow.
2. Generate memory diffs.
3. Add review/revert mechanics.
4. Connect quality gate to durable memory writes.

Sprint 4: Agent Exports

1. Implement `prepare-context`.
2. Add `--for codex`, `--for claude-code`, `--for hermes`, and `--for vendor-neutral` modes.
3. Test the same scenario across multiple agents.

## Dogfood With Odysseus

Odysseus can be used as an external workspace to test whether REEFIKI works as a memory control plane outside its own CLI.

Possible bridge tools:

```text
reefiki.search_memory(project, query)
reefiki.get_project_context(project)
reefiki.add_memory(project, content, source)
reefiki.audit_memory(project)
reefiki.resolve_conflicts(project)
reefiki.export_agent_context(project, agent)
```

This would let an Odysseus agent call REEFIKI as a real external context provider. If that works reliably, it becomes strong proof that REEFIKI is not just an internal memory helper, but a portable context control plane.

## Final Recommendation

Use OpenViking as architectural inspiration for naming, layering, retrieval observability, and session lifecycle. Keep REEFIKI distinct by emphasizing stricter governance, auditability, memory diffs, multi-agent coding workflows, and vendor-neutral context export.

The most valuable near-term feature set is:

1. `reefiki://` URI namespace.
2. L0/L1/L2 context cards.
3. Typed context: memory, decision, constraint, artifact, skill, session, contract.
4. `reefiki why` retrieval trace.
5. `reefiki session commit` with memory diff.
6. `reefiki prepare-context --for <agent>`.

Together these would make REEFIKI feel less like another memory store and more like a governed context operating layer for AI agents.
