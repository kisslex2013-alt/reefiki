# REEFIKI — Full Repository Audit & Development Plan

> Audited: June 1, 2026. Commit snapshot at `kisslex2013-alt/reefiki` (main).
> Phase at time of audit: **Phase 0i** (memory governance layer base complete).
> Live wiki baseline: `projects/reefiki` 13/13 golden queries passing, `misses: []`.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture & Code Quality](#2-architecture--code-quality)
3. [Governance & Data Integrity](#3-governance--data-integrity)
4. [Test Coverage](#4-test-coverage)
5. [Multi-Agent & IDE Coverage](#5-multi-agent--ide-coverage)
6. [Developer Experience & Onboarding](#6-developer-experience--onboarding)
7. [Automation & UX — What to Automate](#7-automation--ux--what-to-automate)
8. [Positioning](#8-positioning)
9. [Proposals (P0→P3)](#9-proposals)
10. [Dependency Roadmap](#10-dependency-roadmap)

---

## 1. Executive Summary

REEFIKI is a well-conceived, philosophically consistent personal knowledge control plane. The core insight — distillation over archiving, `useful_when` as the gating field, layered routing across memoir/wiki/graphify — is sound and the Phase 0 integrity work is thorough. The project is at a **healthy inflection point**: the foundation is solid, the golden tests pass, and the governance layer is in place. The main risks going forward are:

1. **Monolithic code** — 3,950 LOC and 124 functions in a single file will make the codebase progressively harder to maintain and test.
2. **Agent-coverage gaps** — five minimal stubs cover fewer than half of the actively-used AI coding tools in 2026; several major tools are completely absent.
3. **Documentation mass** — 60 KB+ of doc files creates real onboarding friction; the architecture is good, but the surface area is high.
4. **Automation gaps** — many "human remember to run X" steps could be pre-commit hooks, session starters, or cron tasks.
5. **No CI** — the golden baseline and frontmatter validator are only as good as the last manual run.

---

## 2. Architecture & Code Quality

### 2.1 `scripts/reefiki.py` — The Monolith Question

**Measured stats:**
- 3,950 lines, 124 top-level `def` functions, zero classes in production code
- 218 `print()` calls (correct pattern for a CLI: stdout is the API)
- 2 `type: ignore` annotations, 0 `noqa`, 0 `assert` in production paths
- 0 hardcoded cloud API references — genuinely offline-first ✅
- 7 `subprocess` calls (git operations) — all necessary, no shell injection risk seen

**Does the monolith need refactoring?** Yes — but not urgently. At 3,950 lines the file is beyond comfortable single-file size, but its internal structure is disciplined: functions are pure (no global state), naming is consistent, and there is zero dead code (confirmed: no `TODO/FIXME/HACK`). The risk is future growth, not current bugs.

**Recommended split (target modules):**

```
scripts/
  reefiki.py              # thin CLI entry: main() + arg parsing only
  reefiki_core/
    __init__.py
    index.py              # build_index, search, search_existing, FTS5 queries
    frontmatter.py        # parse_frontmatter, as_text, parse_value  (move from validate_frontmatter.py too)
    graph.py              # build_backlink_index, extract_wiki_links, extract_heading_chunks
    dedup.py              # dedup_check, privacy_scan, file_sha256
    git_ops.py            # harvest_commit_payload, guard_staged, push_public_snapshot, publish_task_payload
    promotion.py          # promotion_dry_run, write_promotion_draft, apply_promotion_draft, review_queue_scan
    memory.py             # memory_route, memory_pack, memory_preflight, memory_explain, memory_status
    project.py            # project_root, repo_root, list_projects, find_project, iter_pages
```

The split boundary is clean: each proposed module has cohesive responsibility and minimal cross-module coupling. `git_ops.py` and `memory.py` are the most complex and highest-value isolation targets.

**Type annotation quality:** Good. Functions use `Path`, `dict[str, object]`, `list[str]`, `str | None` consistently. Two `type: ignore` annotations is low. The `object` return types in many `dict[str, object]` returns could be narrowed with `TypedDict` definitions — valuable but not urgent.

**Error handling:** No bare `raise Exception()` calls. Errors are communicated via exit codes and structured JSON output. This is the right pattern for a CLI tool consumed by agents.

### 2.2 SQLite FTS5 — Performance & Scalability

**Current approach:** FTS5 index at `.reefiki/index.sqlite`, markdown as source of truth, index is a read-through cache. This is the correct architecture for this scale.

**Scale ceiling:** FTS5 handles ~1M rows comfortably. At current Phase 0i scale (~100–150 pages) there is zero pressure. The ceiling becomes relevant somewhere around 10,000 pages — well into Phase 2+.

**Observed gap:** `build_index` (line 257) fully rebuilds the index every time. At current scale this is fast, but at 1,000+ pages the full rebuild becomes noticeable (~100ms+). **Incremental indexing** (index only changed files using `mtime` or git diff) should be added before Phase 1.

**Schema observation:** The FTS5 index stores `heading_chunks` for `search --chunks`. This is a good optimization for agent context retrieval. No issues found.

### 2.3 `scripts/reefiki_memory/__init__.py` — Memory Module

**Well-structured.** Uses `@dataclass(frozen=True)` throughout, `StrEnum` for capabilities, clean `to_dict()` serialization. This is the best-factored part of the codebase.

**Observation:** `PolicySafetyLayer.SECRET_PATTERNS` contains three hardcoded regex patterns (generic `api_key`/token/password, `tvly-dev-*`, `sk-*`). The `tvly-dev-` prefix (Tavily API key) is very specific — likely came from a real incident. Consider externalizing to a config file so patterns can be updated without code changes.

**`build_default_registry`** registers three providers (memoir, reefiki, graphify) but `graphify`'s `root` is determined by `project_code_path()` at runtime, which returns `None` if no code project is connected. This is handled correctly but is a silent no-op for disconnected projects — worth surfacing in `memory status` output.

### 2.4 `scripts/validate_frontmatter.py`

Solid implementation at 397 lines. Key observations:

- **`SKIP_FILENAMES`** set: `{"_schema.md", "log.md", "_dashboard.md", "_domain.md"}` — correct. But `status.md` is not in the skip list; if it gains frontmatter this will cause unexpected validation.
- **`BODY_WARN` vs `BODY_REQUIRED`** split is smart — `decision` pages get a non-blocking warning for missing ADR sections. This avoids breaking existing pages while encouraging good format.
- **`--format json`** mode returns structured errors with `code`, `line`, `column`, `expected`, `actual` — excellent for agent/CI diagnostics.
- **Gap:** no check for `id` field matching the filename (`id` should equal `filename_without_extension`). This is stated in `_schema.md` as a rule but not enforced in the validator.
- **Gap:** `use_count` and `last_used` are listed as required in `_schema.md` but their validation in the code requires checking — they appear in `REQUIRED_FIELDS` which is good.

---

## 3. Governance & Data Integrity

### 3.1 Frontmatter Schema — Completeness

The schema is well-designed. The `useful_when` gate is the best single design decision in the project — it forces articulation of value before storage. 

**Edge cases not covered:**

| Gap | Impact | Suggested fix |
|---|---|---|
| `id` not validated against filename | Silent id/filename drift | Add `FILENAME_ID_MISMATCH` check in validator |
| `tags` list can be empty (`tags: []`) — schema says min 1 | Passes validation currently | Add non-empty check |
| `date_added` format not validated (only presence) | Future dates, wrong format | Add ISO date regex check |
| `verified` field for `skill` type accepts any string, not just `YYYY-MM-DD \| null` | Inconsistent data | Add date-or-null check |
| Cross-page `id` uniqueness not enforced | Duplicate IDs possible | Add global uniqueness scan in `/lint` |

### 3.2 Conflict Resolution (30-day Quarantine)

The quarantine mechanism is conceptually sound. Observations:

- **No auto-expiry review.** When `quarantine_until` passes, the item appears in `/status` output as expired — but no action is forced. This is by design (manual review) but creates a growing backlog of "expired quarantine" items that users ignore. Consider adding a `/status` warning count and a dedicated `/resolve-quarantine` command.
- **30 days is long** for fast-moving technical knowledge (e.g., framework version decisions). Consider making quarantine duration a per-project config in `_domain.md` (default 30, range 7–90).

### 3.3 Dual-Remote Publishing — Security Assessment

**Current mechanism:** `push-public.ps1` + `publish_task_payload()` + `public-snapshot.private-projects.txt`. The `publish-task --dry-run` gate before any push is the right safety net.

**Security risks identified:**

1. **`public-snapshot.private-projects.txt` is a flat list of private project names.** If this file is misconfigured (a name is missing or misspelled), private wiki content can leak to the public remote without any error. Mitigation: add a hash/checksum of private project dirs to detect config/reality divergence before push.

2. **`classify_publish_diff`** (line 1329) classifies paths as `private-only` / `public-safe` / `mixed` based on path matching. If a private project's content appears in a shared file (e.g., `AGENTS.md` contains a project name), it won't be caught. This is low-risk given current structure but worth documenting.

3. **The PowerShell `push-public.ps1` script** is Windows-only. Linux/macOS users have no equivalent shell script. They must use the Python CLI, which has the safety gate, but the asymmetry is a DX gap.

4. **Worktree cleanup** is manual-with-confirmation. If the cleanup command is skipped after a failed publish, orphaned worktrees accumulate. `cleanup-worktree` should be idempotent and run automatically on the next `publish-task`.

### 3.4 Template Drift Prevention

Phase 0e closed the most obvious drift vectors. Current mechanism: `/sync-template` command + `_dashboard.md` scope. This is a manual, agent-executed operation.

**Gap:** there is no machine-verifiable "template version" field. If `_template/AGENTS.md` is updated but `/sync-template` is not run, projects drift silently. Suggested: add `template_version: "0i"` to `_domain.md` frontmatter and validate in `/lint` that all projects' versions match the template.

---

## 4. Test Coverage

### 4.1 What Exists

| File | Size | Framework | Tests | Coverage area |
|---|---|---|---|---|
| `test_reefiki_memory_contracts.py` | 69.5 KB | unittest | ~60 methods | Memory layer contracts: registry, route, preflight, status, lookup, promote, golden, pack, diff, publish, promotion-inbox |
| `test_reefiki_memory_governance.py` | 16.7 KB | unittest | ~15 methods | Governance: review queues, backlinks, orphan detection, conflict review, link health |
| `test_validate_frontmatter.py` | 2.1 KB | unittest | ~8 methods | Frontmatter validation basics |
| `test_reefiki_dedup.py` | 4.9 KB | unittest | ~10 methods | URL dedup, content hash, inbox dedup |
| `test_public_snapshot_guard.py` | 0.8 KB | unittest | ~3 methods | Guard-staged payload, private project filtering |

**Coverage quality:** `test_reefiki_memory_contracts.py` at 69.5 KB is the largest file in the entire repo — bigger than `reefiki.py` itself. It is comprehensive but has become a maintenance challenge: a single failing test requires scrolling through a huge file.

### 4.2 What Is Missing

| Missing area | Risk | Priority |
|---|---|---|
| CLI end-to-end tests for `/save`, `/process`, `/harvest` | High — these are user-facing command paths | P1 |
| FTS5 search correctness (query returns expected pages) | Medium — golden tests cover this indirectly | P2 |
| `promote-dry-run --apply-draft` (the only durable write path) | High — untested mutation | P0 |
| `push_public_snapshot` with real git fixture | High — security-sensitive | P1 |
| Windows path handling (junction, `_wiki/` symlink) | Medium — main user platform | P2 |
| `memory_pack --strict` size/quality thresholds | Medium | P2 |
| Incremental index rebuild (mtime-based) — once added | Medium | P2 |

### 4.3 Test Architecture Issue

`test_reefiki_memory_contracts.py` imports `reefiki.py` via `importlib.util.spec_from_file_location`. This ties tests to the monolithic file structure. After the refactoring split (§2.1), tests should import from `reefiki_core.*` modules directly.

**Recommendation:** split `test_reefiki_memory_contracts.py` into per-module test files mirroring the `reefiki_core/` structure. Target: no single test file over 500 lines.

---

## 5. Multi-Agent & IDE Coverage

### 5.1 Existing Stubs — Quality Assessment

| File | Agent | Quality | Issues |
|---|---|---|---|
| `CLAUDE.md` | Claude Code | ✅ Good | Has Claude-specific slash-command paths, session startup sequence |
| `.clinerules` | Cline / Roo Cline | ⚠️ Minimal | Lists operation names but no Cline-specific patterns (auto-approve, tool confirmation) |
| `.cursorrules` | Cursor | ⚠️ Minimal | Just a pointer + 2-line project description. No Cursor Composer/Agent mode guidance |
| `.codex/instructions.md` | Codex CLI | ⚠️ Minimal | Identical structure to `.cursorrules`. No Codex-specific flag guidance |
| `.windsurf/rules/main.md` | Cascade/Windsurf | ⚠️ Minimal | Identical structure to `.cursorrules`. No Cascade-specific workflow (flows, rules) |
| `.serena/project.yml` | Serena | ❌ Missing | Listed in `AGENTS.md` but returns 404 — file doesn't exist in the repo |

**Template drift in stubs:** `.cursorrules`, `.codex/instructions.md`, and `.windsurf/rules/main.md` are carbon copies of each other. If `AGENTS.md` changes its structure (e.g., adds a new command or operation), stubs don't auto-update — they just say "read AGENTS.md", which is the right fallback, but vendor-specific hints remain stale.

### 5.2 Missing Agent Coverage

#### Tier 1 — High-priority additions (widely used in 2026)

**GitHub Copilot — `.github/copilot-instructions.md`**
GitHub Copilot (Chat, Workspace, Agent mode) reads `.github/copilot-instructions.md` as the custom instructions file. Currently absent. This is the largest gap given Copilot's market share.

```markdown
<!-- .github/copilot-instructions.md -->
# GitHub Copilot — REEFIKI

This is a multi-project personal knowledge distillation wiki.
Full contract: **AGENTS.md** (repository root).

When working inside `projects/<name>/`:
- Read `projects/<name>/AGENTS.md` — full operation contract.
- Operations: save, process, query, harvest, status, lint, resolve, reindex, help.
- Operation specs live in `.claude/commands/<op>.md` (folder name is historical; content is vendor-neutral).

Key rules:
- Never write to `raw/` (immutable archive).
- Never rewrite `wiki/log.md` entries — append only.
- `useful_when` is mandatory on every wiki page. If you can't articulate it, reject to `seen/`.
```

Complexity: **S**

---

**Aider — `.aider.conf.yml` + `CONVENTIONS.md`**
Aider supports two mechanisms: `.aider.conf.yml` for CLI config and a conventions/instructions file (typically `CONVENTIONS.md` or pointed to via `--read`).

```yaml
# .aider.conf.yml
read:
  - AGENTS.md
model: claude-3-5-sonnet-20241022
```

Aider does not have a slash-command system; operations need to be triggered via natural language. The conventions file should include the natural-language triggers:

```markdown
# CONVENTIONS.md — REEFIKI (Aider)
Full contract: AGENTS.md

Natural language triggers for Aider sessions:
- "save this link" → /save operation (put in inbox/, no analysis)
- "process inbox" → /process operation
- "query wiki about X" → /query operation  
- "harvest session" → /harvest at session end
- "check wiki health" → /lint operation
```

Complexity: **S**

---

**Continue.dev — `.continue/config.json`**
Continue.dev supports custom context providers and system prompts via `.continue/config.json`.

```json
{
  "customCommands": [
    {
      "name": "reefiki-query",
      "description": "Query REEFIKI wiki",
      "prompt": "Using only knowledge in the wiki/ directory of the current REEFIKI project, answer: {input}"
    }
  ],
  "systemMessage": "You are working inside a REEFIKI knowledge control plane. Read AGENTS.md before any operation. For project-level work, read projects/<name>/AGENTS.md."
}
```

Complexity: **S**

---

**Gemini CLI — `GEMINI.md`**
Google's Gemini CLI (2025) reads `GEMINI.md` in the project root, analogous to `CLAUDE.md`.

```markdown
# GEMINI.md — REEFIKI
Full contract: AGENTS.md (repository root). Read it first.
Project-level work: projects/<name>/AGENTS.md.
```

Complexity: **S** (literally copy CLAUDE.md structure)

---

#### Tier 2 — Medium priority

| Agent | Config file | Notes |
|---|---|---|
| **Zed AI** | `.zed/settings.json` (`assistant.default_context`) | System prompt injection; read AGENTS.md content via file reference |
| **Amazon Q Developer** | `.amazonq/` or `.aws/amazonq/` | Emerging format; customization still limited |
| **Sourcegraph Cody** | `cody.json` / VS Code settings | Context fetcher config; can point to AGENTS.md |
| **JetBrains AI Assistant** | Custom prompt in IDE settings | No file-based config yet; document workaround in README |

#### Tier 3 — Community contribution or document-only

| Agent | Notes |
|---|---|
| **OpenHands / SWE-agent** | Autonomous agents; read `AGENTS.md` directly via shell. Document in README as "place REEFIKI root in working dir". |
| **Local models (Ollama, LM Studio)** | No file-based routing; users must manually inject AGENTS.md into context. Document context injection snippet. |
| **OpenAI Codex (cloud)** | Different from Codex CLI; web-based, no file config. Document: "paste AGENTS.md as system context". |
| **VS Code GitHub Copilot Chat** | Uses `.github/copilot-instructions.md` (same as Copilot above — one file covers both). |

### 5.3 Slash Commands — Cross-Agent Compatibility

Slash commands (`.claude/commands/*.md`) are natively supported only by Claude Code (and partially Cline). For other agents:

| Mechanism | Agents | Recommendation |
|---|---|---|
| Native slash commands | Claude Code, Cline | Already works |
| Tool/function calls | Codex CLI (has `--functions`) | Define reefiki ops as function schemas |
| Natural language | All agents | Always list NL triggers alongside slash commands |
| MCP server (future) | Any MCP-compatible agent | Add per T-40; exposes `/save`, `/query` etc. as MCP tools |

**Current gap:** `.claude/commands/` files are the canonical operation specs, but agents without slash-command support must read them as plain markdown (they can, but it's friction). Adding a `## Natural language trigger` section to each command spec file costs nothing and improves cross-agent usability.

### 5.4 Context Window Considerations

| Model tier | Context | Impact on `memory pack` |
|---|---|---|
| Small local (7B-13B) | 4K–8K tokens | `pack --strict` token limit must be ≤4K; test with `--limit` flag |
| Mid-tier (GPT-4o, Gemini Pro) | 128K tokens | Current defaults are appropriate |
| Large (Claude 3.5+, Gemini 1.5/2.0) | 200K–1M tokens | Could pack entire wiki; but quality gate is more important than size |

**Recommendation:** add `--context-budget <tokens>` to `memory pack` so agents can declare their window size and the pack respects it. This is a Phase 1 feature.

### 5.5 Provider Independence

**Confirmed offline-first:** zero hardcoded cloud API references in `reefiki.py` or `reefiki_memory/__init__.py`. The entire memory layer (FTS5 search, frontmatter validation, promotion, review queues) works without any network connection. ✅

**One exception:** Phase 0c mobile capture uses Telegram bot + Pipedream + GitHub Actions — these are cloud dependencies, but they're in `inbox/` capture, not in the memory layer itself. They are correctly isolated. ✅

**Local model governance quality:** AGENTS.md's contract is explicit and well-structured, but strict adherence depends on model instruction-following quality. 7B–13B local models follow about 60–70% of a complex contract like AGENTS.md. Mitigation: the `memory preflight` gate is a safety net that doesn't require model compliance — it's a CLI check. This is the right architecture. ✅

---

## 6. Developer Experience & Onboarding

### 6.1 Documentation Volume

| File | Size | Purpose |
|---|---|---|
| `COMMANDS.md` | 21.3 KB | User-facing command reference |
| `AGENTS.md` | 15.7 KB | Root agent contract |
| `ROADMAP.md` | 22.7 KB | Phase planning |
| `TASKS.md` | 23.6 KB | Sprint tracking |
| `projects/_template/AGENTS.md` | 9.3 KB | Per-project agent contract |

**Total:** ~92 KB of documentation to read before understanding the full system.

**Is this too much?** For a human onboarding: yes. For an agent reading the relevant subset: no — AGENTS.md is structured to load progressively ("read this first → then read project AGENTS.md → then read command specs"). The problem is the human README experience.

**The 4-question filter** (referenced in `process.md` and template AGENTS.md as "internal 4 questions") is never explicitly enumerated in any user-facing file. From context they appear to be:
1. Is this genuinely new vs. already in wiki?
2. When would this be useful again? (useful_when)
3. What type is this? (source/concept/decision/skill/synthesis)
4. Is there a conflict with existing knowledge?

These questions are the intellectual core of the system and should be made explicit somewhere visible.

### 6.2 Onboarding Path (Clone → First `/save`)

Estimated time for a non-technical user: **45–90 minutes**
Estimated time for a developer: **15–30 minutes**

Bottlenecks:
1. Understanding which project to open (`REEFIKI/` vs `projects/<name>/`) — the two-mode distinction is non-obvious
2. Pre-commit hook setup (`pip install pre-commit; pre-commit install`) — not mentioned in README quick start
3. `scripts/reefiki.py` requires Python in PATH — no mention of version requirement (confirmed Python 3.10+ from type hints)
4. Windows junction creation for `/connect` — requires admin rights or developer mode

**Missing:** a `QUICKSTART.md` (5-minute path) separate from the full README.

### 6.3 The `.claude/commands/` Naming Issue

The command specs live in `.claude/commands/` — a Claude Code convention. The codebase correctly notes "folder name is historical, content is vendor-neutral" in multiple places. But new users (and agents not familiar with this history) will assume these files are Claude-only. Consider:
- Add a `README.md` to `.claude/commands/` explaining the vendor-neutral nature
- Or rename to `.reefiki/commands/` and symlink `.claude/commands/` → `.reefiki/commands/`

---

## 7. Automation & UX — What to Automate

### 7.1 Pipeline Candidates (manual sequences that should be single commands)

| Current manual sequence | Proposed pipeline command | Level | Trigger | Safety concern |
|---|---|---|---|---|
| `/process` → `reindex` → `build_index` → `validate_frontmatter` | `/process` already triggers reindex; but index rebuild after batch process is manual | **Full auto** | Post-`/process` hook | None — all read/write within project scope |
| `memory pack --strict` → `memory golden` → `memory status` | `memory handoff` | **Full auto** | User says "continue session" or "new thread" | None — read-only |
| `validate_frontmatter.py` → `review-queues` → `backlinks --write` | `reefiki lint-full` | **Full auto** | Pre-push hook, weekly cron | None — read-only scan |
| `publish-task --dry-run` → review output → `push-public` | Already gated; UX issue is the two-step | **Semi-auto** | User says "push" | Publishing: require dry-run output review |
| `promote-dry-run --write-draft` → user review → `--apply-draft --yes` | Good as-is (explicit confirm required) | **Semi-auto** | Agent proposes; user confirms | Durable write: explicit confirmation is correct |

### 7.2 Session Bootstrap Checklist (what agent should do automatically at session start)

Currently in `projects/<name>/AGENTS.md` under "Авто-триггеры" — this is good. But:

- ✅ Inbox count check  
- ✅ Expired quarantine check
- ✅ Lint interval check (every 10 `/process`)
- ✅ Stale pages check
- ❌ **Missing:** `memory status --summary` to surface open promotion inbox items and provider health
- ❌ **Missing:** Check if SQLite index is older than most recent wiki file (trigger rebuild)
- ❌ **Missing:** Check if `_template` version > project version (template drift)
- ❌ **Missing:** Backup age warning if last commit > N days

### 7.3 Periodic Checks (cron/CI candidates)

| Check | Frequency | Level | Risk of full automation |
|---|---|---|---|
| `validate_frontmatter.py` on all wiki files | On every git commit | **Full auto** (pre-commit — already done ✅) | None |
| `reefiki.py review-queues` lint scan | Weekly | **Full auto** (cron + write report) | Low — read-only |
| `memory golden` baseline | Weekly or after batch `/process` | **Full auto** (CI job) | None — read-only; alerts on miss |
| `reefiki.py backlinks --write` | After every `/harvest` or `/process` | **Full auto** (post-hook) | None — generated artifact |
| `reefiki.py status --format json` | On demand (CI health check) | **Full auto** | None |
| Quarantine expiry sweep | Weekly | **Semi-auto** (report only, no auto-promote) | Auto-promotion of quarantined content is risky |

### 7.4 What Users Forget

Based on command structure analysis:

1. **`reindex` after batch Obsidian edits** — Obsidian edits bypass the CLI entirely; FTS5 index goes stale. Fix: add a file watcher or make `search` detect stale index via mtime comparison.
2. **`harvest` before closing IDE** — No session-end reminder mechanism. Fix: document as auto-trigger in AGENTS.md (partially there) and add to bootstrap checklist check ("last harvest was N turns ago").
3. **`backlinks --write` after `/process`** — backlink cache is a generated artifact; it goes stale after new pages are added. Fix: add to `/process` exit hook.
4. **`memory golden` after large batch** — golden baseline drift is silent. Fix: CI job or post-`/harvest` hook.
5. **`sync-template` after REEFIKI updates** — projects drift from template silently. Fix: template version field in `_domain.md` + lint check.

### 7.5 Safe Full-Automation Opportunities

| Operation | Implementation |
|---|---|
| CI: `validate_frontmatter.py` on PR | GitHub Actions `.github/workflows/ci.yml` — runs on push/PR to `projects/*/wiki/**` |
| CI: `memory golden` baseline | Same workflow — run and compare against stored baseline; fail on regression |
| Post-commit hook: `backlinks --write` | `.git/hooks/post-commit` — safe, fast, idempotent |
| Cron: weekly `review-queues --write-report` | GitHub Actions scheduled workflow — writes report artifact, no durable changes |
| mtime-based index rebuild | In `search()` — check `max(wiki_file.mtime)` vs `index.sqlite mtime`; rebuild if stale |

---

## 8. Positioning

### 8.1 Unique Value Proposition

REEFIKI's clearest differentiator: **local-first governance layer that works identically across any LLM agent or IDE, with explicit knowledge routing, quarantine, and typed knowledge taxonomy** — without requiring a server, subscription, or API key.

Nearest analogues and how REEFIKI differs:

| Analogue | What they do | REEFIKI difference |
|---|---|---|
| **Mem0 / Zep** | Cloud memory service; stores and retrieves facts | REEFIKI is local, markdown-native, agent-agnostic; no API required |
| **Karpathy LLM Wiki** | Simple markdown wiki gist | REEFIKI adds governance (quarantine, types, validation, FTS5) |
| **Obsidian + AI plugin** | Graph knowledge base with AI features | REEFIKI uses Obsidian as viewer only; the control plane is CLI-native |
| **Honcho** | User-level personalization for agents | REEFIKI is project/domain-scoped, not user-profile-scoped |
| **LangChain Memory** | Session memory within a chain | REEFIKI is durable cross-session, not in-chain |

**What strengthens the project:**
- The `useful_when` gate is intellectually honest and creates genuine friction against knowledge hoarding
- The layered architecture (memoir / REEFIKI / graphify) maps cleanly to cognitive memory tiers
- The typed page taxonomy (`source/entity/concept/synthesis/decision/skill`) gives structure without over-engineering
- Local-first + markdown = works offline, inspectable, Git-backed, no lock-in

**What weakens the project:**
- High onboarding cost (92 KB of docs before first `/save`)
- Windows-centric assumptions (junction symlinks, PowerShell scripts) with no Linux/macOS equivalents for some operations
- The "agent does it autonomously" UX is aspirational; without session-start hooks enforced in the IDE, users must remember to trigger operations
- No CI — the golden baseline only proves quality at the last manual run

### 8.2 Open-Source Adoption Risk

The project is currently structured for personal use by a sophisticated technical user. For community adoption:
- Russian-language primary README (EN and ZH versions exist but are less complete)
- No `CONTRIBUTING.md`
- No `QUICKSTART.md` (15-minute path)
- Agent stubs cover ~40% of the actively-used tools

---

## 9. Proposals

### Core (P0)

---

**CORE-01 — CI pipeline: validate_frontmatter + golden baseline**
- **Problem:** The pre-commit hook protects committed files, but there is no CI job to catch regressions across all projects, especially after template updates or batch Obsidian edits. The golden baseline (`13/13` in `projects/reefiki`) exists but is only verified manually.
- **Solution:**
```yaml
# .github/workflows/ci.yml
name: REEFIKI CI
on:
  push:
    paths: ['projects/*/wiki/**', 'scripts/**', 'tests/**']
  pull_request:
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pre-commit
      - run: python scripts/validate_frontmatter.py $(find projects -path "*/wiki/*.md" -not -name "_*" -not -name "log.md")
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python -m pytest tests/ -v
  golden:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: python scripts/reefiki.py memory golden --project reefiki --format json | python -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if not d.get('misses') else 1)"
```
- **Value:** Regressions are caught automatically; new contributors can trust the baseline.
- **Complexity:** S (1–2 days)
- **Priority:** P0

---

**CORE-02 — Fix missing `.serena/project.yml`**
- **Problem:** `AGENTS.md` lists `.serena/project.yml` as a stub file, but the file returns 404 — it does not exist in the repository. This is a broken promise in the agent-agnostic claim.
- **Solution:** Create the file:
```yaml
# .serena/project.yml
initial_prompt: |
  Read AGENTS.md in the repository root. It contains the full operating contract for REEFIKI.
  When working inside a project folder (projects/<name>/), read projects/<name>/AGENTS.md instead.
  Slash commands are defined in .claude/commands/ (vendor-neutral despite the folder name).
```
- **Value:** Serena users get a working integration.
- **Complexity:** S (< 1 hour)
- **Priority:** P0

---

**CORE-03 — Add `id`/filename consistency check to validator**
- **Problem:** `_schema.md` states "`id` == filename without `.md`" but `validate_frontmatter.py` doesn't enforce this. A file `wiki/decisions/use-sqlite.md` with `id: use-postgres` passes validation silently.
- **Solution:**
```python
# in validate_file_report()
if "id" in fm and fm["id"] != path.stem:
    errors.append(error(
        path, "ID_FILENAME_MISMATCH",
        f"id field '{fm['id']}' does not match filename '{path.stem}'",
        expected=path.stem, actual=fm["id"]
    ))
```
- **Value:** Prevents broken wiki links (`[[slug]]` links depend on `id == filename`).
- **Complexity:** S
- **Priority:** P0

---

### Core (P1)

---

**CORE-04 — Incremental FTS5 index rebuild (mtime-based)**
- **Problem:** `build_index()` performs a full table drop + rebuild every call. At 100 pages this is ~20ms. At 1,000 pages (Phase 1) it becomes a noticeable pause on every `search`.
- **Solution:** Compare `max(page.stat().st_mtime)` across wiki files against `index.sqlite` mtime. Rebuild only if wiki is newer. For selective updates, use INSERT OR REPLACE by `path`:
```python
def build_index(project: Path) -> int:
    db = db_path(project)
    pages = iter_pages(project)
    if db.exists():
        db_mtime = db.stat().st_mtime
        if all(p.stat().st_mtime <= db_mtime for p in pages):
            return 0  # index is current
    # ... existing rebuild logic
```
- **Value:** `/query` and `search` become near-instant after the first build.
- **Complexity:** M
- **Priority:** P1

---

**CORE-05 — `reefiki lint-full` composite command**
- **Problem:** A full wiki health check requires running four separate commands: `validate_frontmatter.py`, `review-queues`, `backlinks --write`, and `memory golden`. Users run them in sequence manually; often only one is run.
- **Solution:** Add `reefiki.py lint-full` that runs all four in sequence, exits 0 only if all pass, and emits a structured JSON summary:
```
python scripts/reefiki.py lint-full --project reefiki --format json
```
Output: `{ "frontmatter": {...}, "review_queues": {...}, "golden": {...}, "backlinks": {...}, "overall": "pass|warn|fail" }`
- **Value:** Single command for CI, pre-push hooks, and session health checks.
- **Complexity:** M
- **Priority:** P1

---

**CORE-06 — `--apply-draft` test coverage**
- **Problem:** `promote-dry-run --apply-draft <path> --yes` is the only durable write path in `reefiki.py` outside of the slash commands. It has no test coverage (confirmed — `test_reefiki_memory_contracts.py` has no test for `apply_promotion_draft`).
- **Solution:** Add integration test with a temp project fixture:
```python
class ApplyDraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # create minimal project structure
        # create promotion draft
    
    def test_apply_draft_creates_wiki_page(self):
        # call apply_promotion_draft(project, draft_path, yes=True)
        # assert wiki page created with correct frontmatter
    
    def test_apply_draft_updates_log(self):
        # assert wiki/log.md has append entry
    
    def test_apply_draft_requires_explicit_yes(self):
        # assert no write without yes=True
```
- **Value:** Prevents silent regressions in the only durable write path.
- **Complexity:** M
- **Priority:** P0 (security-adjacent)

---

### Code Quality (P1)

---

**CQ-01 — Split `reefiki.py` into `reefiki_core/` package**
- **Problem:** 3,950 LOC, 124 functions in one file. Logical groups exist (FTS5 queries, git ops, promotion, memory layer) but are interleaved.
- **Solution:** Extract to `scripts/reefiki_core/` as outlined in §2.1. Keep `reefiki.py` as a thin CLI shim (arg parsing + dispatch). Estimated: ~600 LOC for the shim, ~3,350 LOC distributed across 7 modules.
- **Value:** Faster test runs (import only the module under test), clearer ownership per domain, easier to add new contributors.
- **Complexity:** L (1–2 weeks, careful not to break imports)
- **Priority:** P1

---

**CQ-02 — Split `test_reefiki_memory_contracts.py`**
- **Problem:** 69.5 KB test file — bigger than the production code. A test failure message shows a line number in a 2,200-line file.
- **Solution:** Split into `test_memory_route.py`, `test_memory_status.py`, `test_memory_pack.py`, `test_memory_promote.py`, `test_memory_golden.py`. Each <300 lines.
- **Complexity:** M
- **Priority:** P1

---

**CQ-03 — Add `QUICKSTART.md`**
- **Problem:** A new user faces 15.7 KB AGENTS.md before they understand what to type. The README has the right information but is interspersed with architecture diagrams and philosophy.
- **Solution:** Create `QUICKSTART.md` with a strict 5-minute path:
  1. Requirements (Python 3.10+, pre-commit)
  2. `pre-commit install`
  3. Open `REEFIKI/` in Claude Code / Cursor / Windsurf
  4. Say: "Create a new project called `test` about Python"
  5. Say: "Save https://peps.python.org/pep-0008/"
  6. Say: "Process inbox"
  7. Say: "What do we know about code style?"
- **Complexity:** S
- **Priority:** P1

---

**CQ-04 — Enumerate the 4-question filter publicly**
- **Problem:** The "internal 4 questions" for `/process` are referenced but never shown to the user. New agents implementing the protocol have to reverse-engineer them.
- **Solution:** Add a `## The Distillation Filter` section to `_schema.md` and `COMMANDS.md`:
  1. **Delta:** Is this genuinely new relative to existing wiki pages?
  2. **Scenario:** Can I write a concrete `useful_when`? (if not → `seen/`)
  3. **Type:** What knowledge type is this? (source/concept/decision/skill/synthesis)
  4. **Conflict:** Does this contradict an existing page? (→ `## Conflicting claims`)
- **Complexity:** S
- **Priority:** P1

---

### Integrations (P1)

---

**INT-01 — GitHub Copilot stub**
- **Problem:** No `.github/copilot-instructions.md`. Copilot (Chat, Workspace, Agent mode) has no REEFIKI awareness.
- **Solution:** See §5.2 Tier 1 above. One concise file, 20 lines.
- **Complexity:** S
- **Priority:** P1

---

**INT-02 — Aider `.aider.conf.yml` + `CONVENTIONS.md`**
- **Solution:** See §5.2 Tier 1 above.
- **Complexity:** S
- **Priority:** P1

---

**INT-03 — Gemini CLI `GEMINI.md`**
- **Solution:** Mirror `CLAUDE.md` structure for Gemini CLI.
- **Complexity:** S
- **Priority:** P1

---

**INT-04 — Continue.dev `.continue/config.json`**
- **Solution:** See §5.2 Tier 1 above.
- **Complexity:** S
- **Priority:** P2

---

**INT-05 — MCP server for memory operations**
This is already tracked as T-40. Expanding on the design:
- **Problem:** As MCP becomes the standard for agent tool calls, agents that support MCP (Claude Desktop, Cline with MCP, etc.) can call REEFIKI operations as structured tools rather than parsing natural language.
- **Solution:** A minimal MCP server exposing:
  - `reefiki_save(source: str, project: str) → SaveResult`
  - `reefiki_query(question: str, project: str) → QueryResult`
  - `reefiki_status(project: str) → StatusResult`
  - `reefiki_memory_pack(task: str, project: str, strict: bool) → PackResult`
- **Implementation:** Python MCP SDK (`mcp` package). Thin wrapper over existing `reefiki.py` functions.
- **Complexity:** L
- **Priority:** P2 (after Phase 0j stabilizes)

---

### Developer Experience (P2)

---

**DX-01 — Template version field to detect drift**
- **Problem:** After `/sync-template`, existing projects update, but there's no machine-readable way to confirm they're in sync.
- **Solution:** Add `template_version: "0i"` to `_template/_domain.md`. Add to `/lint` check: compare project `_domain.md` template_version against current template. Warn if mismatched.
- **Complexity:** S
- **Priority:** P2

---

**DX-02 — `--context-budget <tokens>` for `memory pack`**
- **Problem:** Memory pack size is controlled by `--limit` (page count) but agents have different context window sizes. A 7B local model with 4K tokens needs a radically different pack than Claude with 200K tokens.
- **Solution:** Add `--context-budget 4000` flag. Estimate token count of assembled pack (rough: `len(text) / 4`) and truncate/prioritize to fit budget.
- **Complexity:** M
- **Priority:** P2

---

**DX-03 — `reefiki session-start` composite command**
Consolidates the auto-triggers from AGENTS.md into a single CLI command that agents can call mechanically:
```
python scripts/reefiki.py session-start --project reefiki --format json
```
Returns: inbox count, expired quarantines, stale pages, lint overdue, promotion inbox open count, index freshness, template version match.
- **Complexity:** M
- **Priority:** P2

---

**DX-04 — Linux/macOS `push-public.sh`**
- **Problem:** `push-public.ps1` is PowerShell-only. Users on Linux/macOS must use the Python CLI (`publish-task`) which is correct but the PowerShell script implies a "simple" path that doesn't exist for them.
- **Solution:** Create `scripts/push-public.sh` with identical logic (bash), add to README alongside the PowerShell version.
- **Complexity:** S
- **Priority:** P2

---

### Ecosystem (P3)

---

**ECO-01 — `CONTRIBUTING.md`**
- Brief guide for external contributors: project philosophy, how to add a wiki project, how to run tests, how to add a new agent stub.
- **Complexity:** S
- **Priority:** P3

---

**ECO-02 — English-first README**
- `README.md` is Russian-first. `README.en.md` exists but is a secondary citizen. For open-source adoption, either make EN the primary file or generate it from the RU version with a clear note.
- **Complexity:** M (content, not code)
- **Priority:** P3

---

**ECO-03 — Zed AI `.zed/settings.json` stub**
- **Complexity:** S
- **Priority:** P3

---

## 10. Dependency Roadmap

```
Phase 0i (now)
     │
     ├─── CORE-02 [S, P0] Fix .serena/project.yml  ──────────── unblocks: Serena users
     ├─── CORE-03 [S, P0] id/filename validator     ──────────── unblocks: CORE-01 CI
     ├─── CORE-06 [M, P0] apply-draft test          ──────────── no dependencies
     │
     ├─── CORE-01 [S, P0] CI pipeline               ──── needs: CORE-03
     │         depends on tests passing ────────────────── needs: existing tests OK
     │
     ├─── INT-01..03 [S, P1] Agent stubs            ──────────── independent, parallelize
     ├─── CQ-03 [S, P1] QUICKSTART.md               ──────────── independent
     ├─── CQ-04 [S, P1] Enumerate 4-question filter ──────────── independent
     │
     ├─── CORE-05 [M, P1] lint-full command         ──────────── needs: CORE-01 (for CI integration)
     ├─── CORE-04 [M, P1] Incremental index         ──────────── independent
     │
     ▼
Phase 0j (stabilization)
     │
     ├─── CQ-01 [L, P1] Split reefiki_core/         ──────────── needs: CORE-01 (CI catches regressions)
     ├─── CQ-02 [M, P1] Split test file             ──── before: CQ-01 (migrate tests alongside split)
     ├─── DX-01 [S, P2] Template version field      ──────────── needs: CORE-05 (lint-full integration)
     ├─── DX-03 [M, P2] session-start command       ──────────── needs: CORE-05
     ├─── DX-04 [S, P2] push-public.sh              ──────────── independent
     │
     ▼
Phase 1 (growth trigger: >200 pages or >3 query misses/month)
     │
     ├─── DX-02 [M, P2] --context-budget for pack   ──────────── needs: CQ-01 (refactor)
     ├─── INT-04 [S, P2] Continue.dev stub          ──────────── independent
     ├─── INT-05 [L, P2] MCP server                 ──── needs: CQ-01, stable CLI API
     │
     ├─── T-21 [?] Confidence tagging               ──────────── as per existing TASKS.md
     ├─── T-20 [?] Static site export               ──────────── as per existing TASKS.md
     │
     ▼
Phase 2+ (trigger: multi-user or >1000 pages)
     ├─── T-40 MCP/REST API (expands INT-05)
     ├─── T-41 Vector/graph search layer
```

### Parallelizable sprint (immediate, no dependencies between items):

| Item | Owner | Time |
|---|---|---|
| CORE-02 — create `.serena/project.yml` | 30 min |
| CORE-03 — add id/filename validator check | 2 hours |
| INT-01 — `.github/copilot-instructions.md` | 30 min |
| INT-02 — `.aider.conf.yml` + `CONVENTIONS.md` | 1 hour |
| INT-03 — `GEMINI.md` | 30 min |
| CQ-03 — `QUICKSTART.md` | 2 hours |
| CQ-04 — enumerate 4-question filter in docs | 1 hour |

**Total for immediate sprint: ~8 hours, fully parallelizable.**

---

## Summary Scorecard

| Category | Current state | Target |
|---|---|---|
| Architecture | Monolith, well-structured | Modular `reefiki_core/` package |
| Type safety | Good (`dict[str, object]`) | TypedDict narrowing for key return types |
| Test coverage | Comprehensive for memory layer; gaps in durable write, CLI flows | All durable write paths tested; CI green |
| Agent coverage | 5 stubs (~40% of tools) | 9 stubs + community doc for others |
| CI/CD | None | GitHub Actions: validate + tests + golden |
| Onboarding | 45–90 min; complex | 15 min with QUICKSTART.md |
| Automation | Many manual sequences | `lint-full`, `session-start`, post-commit hooks |
| Documentation | Comprehensive but overwhelming | Tiered: QUICKSTART → COMMANDS → AGENTS |
| Positioning | Clear and defensible | Strengthen with EN-first README + CONTRIBUTING |
