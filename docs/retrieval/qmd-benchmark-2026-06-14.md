# qmd retrieval benchmark

- project: reefiki
- candidate: qmd
- outcome: benchmark-complete
- go_no_go: no-adoption-benefit
- qmd_status: results-loaded
- fixed_corpus_count: 9

## Summary

- FTS5 hits: 9
- qmd hits: 9
- improved: 0
- regressed: 0

## Method

- qmd command surface: `qmd search ... --format json -n 5 -c reefiki-benchmark`
- qmd collection: `projects/reefiki/wiki` only
- npm cache: local generated `.cache/qmd-benchmark/npm`
- runtime not used: no `qmd mcp`, no `qmd serve`, no `qmd embed`, no vector search, no rerank, no model downloads
- comparison id: wiki file slug from qmd `file` path, not qmd short `docid`

## Cases

### lookup-control-plane-spec

- query: REEFIKI 2 control plane
- expected: reefiki-2-control-plane-spec
- FTS5 actual: reefiki-2-mvp-status-after-pack, reefiki-2-control-plane-spec, reefiki-primary-brand-and-legacy-v2-alias, reefiki-2-control-plane-research-comparison, reefiki-2-external-agent-research-synthesis
- FTS5 missing: -
- qmd actual: reefiki-2-control-plane-spec, reefiki-primary-brand-and-legacy-v2-alias, reefiki-2-mvp-status-after-pack, reefiki-2-external-agent-research-synthesis, reefiki-2-control-plane-research-comparison
- qmd missing: -

### lookup-routing-promotion-contract

- query: routing promotion contract
- expected: reefiki-routing-and-promotion-contract
- FTS5 actual: reefiki-routing-and-promotion-contract, reefiki-memory-governance-first-automation-steps, memoir-to-reefiki-promotion-gate, we-decided-to-keep-memoir-for-short-working-memory-and-reefiki-for-durable-knowl, reefiki-2-mvp-status-after-pack
- FTS5 missing: -
- qmd actual: reefiki-routing-and-promotion-contract, reefiki-2-mvp-status-after-pack, memoir-to-reefiki-promotion-gate, reefiki-2-external-agent-research-synthesis, global-memory-orchestration-cli
- qmd missing: -

### lookup-global-memory-cli

- query: global memory orchestration CLI
- expected: global-memory-orchestration-cli
- FTS5 actual: global-memory-orchestration-cli, reefiki-leadops-orchestration, june-2026-t111-package-extraction-pattern, github-research-safe-adoption-slice, reefiki-routing-and-promotion-contract
- FTS5 missing: -
- qmd actual: reefiki-leadops-orchestration, github-research-safe-adoption-slice, global-memory-orchestration-cli, reefiki-2-external-agent-research-synthesis, reefiki-routing-and-promotion-contract
- qmd missing: -

### lookup-skill-quality-gate

- query: skill quality gate
- expected: skill-quality-gate
- FTS5 actual: skill-quality-gate, taste-skill-writing-reference, skillopt-evaluation-gates-r-and-d, agent-skills-workflow-patterns-candidate, agent-agnostic-contract-audit
- FTS5 missing: -
- qmd actual: skillopt-evaluation-gates-r-and-d, skill-quality-gate, taste-skill-writing-reference, adopt-skill-adoption-governance, agent-skills-workflow-patterns-candidate
- qmd missing: -

### lookup-codegraph-evaluation-runbook

- query: codegraph evaluation runbook
- expected: codegraph-evaluation-runbook
- FTS5 actual: codegraph-evaluation-runbook, adopt-skill-adoption-governance, understand-anything-sandbox-watch, codegraph-code-navigation-candidate, skill-quality-gate
- FTS5 missing: -
- qmd actual: codegraph-evaluation-runbook, skill-quality-gate, adopt-skill-adoption-governance, understand-anything-sandbox-watch, codegraph-code-navigation-candidate
- qmd missing: -

### lookup-external-tool-governance

- query: external tool governance codegraph codebase memory
- expected: codegraph-code-navigation-candidate, codebase-memory-mcp-watch
- FTS5 actual: understand-anything-sandbox-watch, codegraph-code-navigation-candidate, codegraph-evaluation-runbook, codebase-memory-mcp-watch, external-tool-watchlist
- FTS5 missing: -
- qmd actual: understand-anything-sandbox-watch, codegraph-code-navigation-candidate, codegraph-evaluation-runbook, codebase-memory-mcp-watch, external-tool-watchlist
- qmd missing: -

### lookup-public-snapshot-workflow

- query: public snapshot dual remote
- expected: dual-remote-public-snapshot
- FTS5 actual: dual-remote-public-snapshot, staged-scope-and-publish-guard, svg-visual-unification, agent-workflow-reference-patterns, agent-agnostic-contract-audit
- FTS5 missing: -
- qmd actual: dual-remote-public-snapshot, staged-scope-and-publish-guard, svg-visual-unification, agent-workflow-reference-patterns, agent-agnostic-contract-audit
- qmd missing: -

### lookup-review-queue-contract

- query: review queues stale orphan duplicate
- expected: reefiki-review-queue-contract
- FTS5 actual: reefiki-review-queue-contract, reefiki-memory-governance-first-automation-steps, reefiki-2-control-plane-spec, memory-reflection-boundary, reefiki-routing-and-promotion-contract
- FTS5 missing: -
- qmd actual: reefiki-review-queue-contract, reefiki-memory-governance-first-automation-steps, reefiki-2-control-plane-spec, memory-reflection-boundary, reefiki-routing-and-promotion-contract
- qmd missing: -

### lookup-wrapper-pilot-removal

- query: remove wrapper pilots
- expected: remove-wrapper-pilots
- FTS5 actual: remove-wrapper-pilots, agent-agnostic-contract-audit, june-2026-t111-package-extraction-pattern, global-memory-orchestration-cli, local-json-adapter-before-mcp-rest-server
- FTS5 missing: -
- qmd actual: remove-wrapper-pilots, agent-agnostic-contract-audit, log-2026-04-to-2026-05, global-memory-orchestration-cli, index
- qmd missing: -

## Generated Path Cleanup

- checked: projects/reefiki/.qmd, .cache/qmd-benchmark
- removed by CLI: -
- initial CLI cleanup failure: `.cache/qmd-benchmark` hit transient Windows directory-not-empty lock under the local npm cache after `npx`.
- manual follow-up cleanup: removed `.cache/qmd-benchmark` and `projects/reefiki/.qmd` after the qmd process exited.
- final remaining: -

## Decision

Keep qmd disabled by default unless a future fixed miss set shows repeatable improvement without regressions.
