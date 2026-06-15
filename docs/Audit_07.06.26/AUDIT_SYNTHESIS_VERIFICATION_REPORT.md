# Audit Synthesis Verification Report

Date: 2026-06-07
Scope: spot-check of `AUDIT_SYNTHESIS_ACTION_PLAN.md`, `ROADMAP.md`, publish documentation, and current implementation in `scripts/reefiki.py`.

## Verdict

`AUDIT_SYNTHESIS_ACTION_PLAN.md` and `ROADMAP.md` are mostly consistent with the current repository state. Phase 0j is correctly marked as active, not complete.

The remaining problem is publish safety wording: some user-facing docs describe the current dual-remote publish path as safer than it is. Two high-risk edge cases are still open and should stay P0.

## Findings

### 1. High: renamed private project is not excluded from public snapshot

Current exclusion list still contains the old path:

- `scripts/public-snapshot.private-projects.txt:5` — `security-guidance-lite`

But the actual project now exists as:

- `projects/Security Guidance/_domain.md:40` — title/domain for `Security Guidance`

The snapshot implementation removes only projects listed in `scripts/public-snapshot.private-projects.txt`:

- `scripts/reefiki.py:1435` — iterates `private_projects`
- `scripts/reefiki.py:1436` — removes `projects/<name>` from the staged public snapshot

Impact: a public snapshot may include `projects/Security Guidance/` unless the exclusion list is updated. This conflicts with the intended invariant:

- `README.md:103` — public repo should contain no personal wiki projects
- `projects/reefiki/wiki/decisions/dual-remote-public-snapshot.md:63` — new private project must be added to the exclusion list before public snapshot

### 2. High: publish flow has no content-based secret scan

The current publish classifier is path-based:

- `scripts/reefiki.py:1407` — computes private/public changed paths
- `scripts/reefiki.py:1408` — classifies by path prefixes
- `scripts/reefiki.py:1421` — reports private/public paths

The public snapshot guard also checks paths, not file contents:

- `scripts/reefiki.py:1442` — blocks only staged paths under private project prefixes

But the synthesis plan explicitly keeps secret/content scanning as P0:

- `docs/Audit_07.06.26/AUDIT_SYNTHESIS_ACTION_PLAN.md:84` — add secret/content scan before commit/publish
- `ROADMAP.md:267` — add secret/content scan before commit/publish/harvest

Impact: a secret or private text added to a public file would not be caught by current `publish-task`. Therefore the wording in user-facing publish docs is too strong:

- `COMMANDS.md:213` — says direct public leak risk is blocked
- `.agents/skills/reefiki-dual-remote-publish/SKILL.md:41` — says public publication must be filtered snapshot, but does not mention content-scan limitation

## Confirmed Correct

- `ROADMAP.md:258` keeps Phase 0j active.
- `ROADMAP.md:262` lists the same remaining P0 themes as the synthesis: safety, CI, packaging, concurrency, and memory hardening.
- `docs/Audit_07.06.26/AUDIT_SYNTHESIS_ACTION_PLAN.md:81` treats Phase 0 as trust foundation, not finished work.
- `projects/reefiki/wiki/decisions/dual-remote-public-snapshot.md:64` correctly requires every push/merge/PR request to start with `publish-task --dry-run`.

## Git State At Check Time

- Branch: `main`
- Relation to remote: ahead of `origin/main` by 5 commits
- Latest commit: `20be9cb docs: normalize june audit plan`
- Working tree before creating this report: clean according to `git status --short --branch`

## Recommended Fix Order

1. Update `scripts/public-snapshot.private-projects.txt` so `projects/Security Guidance/` is excluded.
2. Add a content/secret scan to `publish-task` and public snapshot flow.
3. Soften `COMMANDS.md` and skill wording until content scanning exists.
4. Add tests for renamed private project exclusion and secret-in-public-file blocking.

## Addendum: Documentation Drift Review

Date: 2026-06-07
Scope: spot-check of CLI/skill/docs consistency around global memory orchestration and publish workflow guidance.

### Additional Findings

#### 3. Medium: deprecated commands still presented as active in orchestration skill

The skill doc still exposes removed commands as part of the apparent live CLI surface:

- `projects/reefiki/wiki/skills/global-memory-orchestration-cli.md:4` — title still includes `dream-review` and `ops-refresh`
- `projects/reefiki/wiki/skills/global-memory-orchestration-cli.md:33` — validation block still marks `dream-review` as runnable
- `projects/reefiki/wiki/skills/global-memory-orchestration-cli.md:34` — validation block still marks `ops-refresh` as runnable

But the same doc later says both commands were removed:

- `projects/reefiki/wiki/skills/global-memory-orchestration-cli.md:99` — pilot commands removed
- `projects/reefiki/wiki/skills/global-memory-orchestration-cli.md:115` — removed commands should not be returned

Impact: an agent or user skimming the header or validation examples can attempt commands that no longer exist.

#### 4. Low: publish docs still foreground legacy manual path over guarded workflow

User-facing documentation still teaches the old publication path as primary:

- `README.md:266` — tells users to publish via `scripts/push-public.ps1`
- `projects/reefiki/wiki/skills/readme-visuals-localization-and-public-snapshot.md:37` — teaches `git push origin main`
- `projects/reefiki/wiki/skills/readme-visuals-localization-and-public-snapshot.md:38` — teaches `scripts/push-public.ps1`

But the current command contract defines the guarded flow here:

- `COMMANDS.md:208` — `reefiki.py publish-task`
- `COMMANDS.md:209` — `cleanup-worktree`

The same skill also documents sharp edges in the legacy path:

- `projects/reefiki/wiki/skills/readme-visuals-localization-and-public-snapshot.md:55` — local branch can diverge from public-main
- `projects/reefiki/wiki/skills/readme-visuals-localization-and-public-snapshot.md:57` — path-sensitive command can error if run from wrong location

Impact: docs can steer users around newer safety rails even though the repo now has a safer guarded publish workflow.

### Additional Confirmed Correct

- `docs/Audit_07.06.26/INDEX.md:47` correctly reports 47 current files in the folder.
- `docs/Audit_07.06.26/INDEX.md:48` correctly explains that the total is 46 original inputs plus `AUDIT_SYNTHESIS_ACTION_PLAN.md` as the added normalization artifact.

### Addendum Recommendation

1. Remove deprecated command names from the orchestration skill title and runnable validation examples.
2. Make `reefiki.py publish-task` the primary documented publish contract in `README.md` and related skills.
3. Keep `scripts/push-public.ps1` only as an explicit fallback/manual path, with limitations called out inline.
