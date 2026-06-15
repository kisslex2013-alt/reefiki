# REEFIKI Public Demo

Languages: [Русский](#русский) · [English](#english) · [中文](#中文)

## Русский

Это публичная demo-поверхность REEFIKI. Её можно публиковать, потому что она описывает продуктовый flow, CLI-доказательства и public docs без копирования приватных wiki-проектов.

Короткий сценарий demo:

1. Открыть чистый checkout и прочитать `AGENTS.md`.
2. Создать или подключить wiki-проект.
3. Сохранить источник в `inbox/`, затем обработать его в durable `wiki/` или `seen/`.
4. Спросить wiki с provenance вместо ответа из памяти модели.
5. Зафиксировать reusable decisions, skills и synthesis в markdown.

Подробная canonical-страница ниже на английском.

## English

This is the static public demo surface for REEFIKI. It is safe to publish because it describes the product flow, CLI proofs and public docs without copying private wiki projects.

## 中文

这是 REEFIKI 的公开 demo 页面。它可以安全发布，因为它只描述产品流程、CLI 证明和公开文档，不复制私有 wiki 项目。

简短 demo 流程：

1. 从干净 checkout 开始，并读取 `AGENTS.md`。
2. 创建或连接 wiki 项目。
3. 把来源保存到 `inbox/`，再处理成 durable `wiki/` 或 `seen/`。
4. 基于 wiki 和 provenance 查询，而不是依赖模型记忆。
5. 把 reusable decisions、skills 和 synthesis 固化到 markdown。

下面继续保留英文 canonical 页面。

## What REEFIKI Shows

REEFIKI is a local-first memory control plane for AI agents. It keeps useful knowledge in markdown, rejects low-value archive noise and gives the next agent a bounded context pack.

The demo story has five steps:

1. Start from a clean checkout and read `AGENTS.md`.
2. Create or connect a project wiki.
3. Save a source into `inbox/`, then process it into durable `wiki/` knowledge or `seen/`.
4. Query the wiki with provenance instead of relying on model memory.
5. Harvest reusable decisions, skills and synthesis into markdown with an append-only log.

## Try The Local Demo

The onboarding command has a dry-run mode and a deterministic fixture mode:

```powershell
reefiki onboarding
reefiki onboarding --fixture-root C:\Temp\reefiki-demo
reefiki --project C:\Temp\reefiki-demo\projects\reefiki-onboarding-demo status
```

For checkout development, the same flow works without a global install:

```powershell
python scripts\reefiki.py onboarding --format json
python scripts\reefiki.py onboarding --fixture-root C:\Temp\reefiki-demo --format json
python scripts\reefiki.py --project C:\Temp\reefiki-demo\projects\reefiki-onboarding-demo status
```

The fixture creates demo data under the supplied temp folder. It does not read or export private project folders from this repository.

## Public-Safe Capabilities

| Capability | Public demo proof | Boundary |
|---|---|---|
| Daily wiki cycle | `onboarding --fixture-root` creates a deterministic demo project | No private `projects/*` export |
| Retrieval quality | `memory golden --project reefiki` tracks stable lookup expectations | No vector or hybrid search runtime |
| Handoff context | `memory pack --project reefiki --strict` builds a bounded pack | No new storage layer |
| Read-only dashboard | `dashboard` and `ops-dashboard` summarize local state | No remote mutation or cloud dashboard |
| Public/private publish | `publish-task --dry-run --cleanup --format json` preflights publication | No manual push to `public` |

## Safe Links

- [Quickstart](../QUICKSTART.md)
- [Command reference](../COMMANDS.md)
- [Agent flow conformance](AGENT_FLOW_CONFORMANCE.md)
- [Agent Readiness spec](skill-products/AGENT_READINESS_SPEC.md)
- [Recovery guide](RECOVERY.md)
- [Roadmap](../ROADMAP.md)

## Private Boundary

The public snapshot removes private project folders listed in `scripts/public-snapshot.private-projects.txt`. This demo must not embed private wiki pages, raw sources, inbox items, seen records, local usernames, tokens or unpublished project notes.

Allowed public material:

- root docs and command references;
- generated screenshots or fixture outputs that contain only demo data;
- CLI examples using placeholder paths such as `C:\Temp\reefiki-demo`;
- product claims already backed by public docs and tests.

Not allowed:

- `projects/reefiki/wiki/**` content copied into public docs;
- private project names used as examples beyond the documented boundary list;
- managed sync backend, hosted dashboard, marketplace submission, MCP server or vector search claims;
- real local paths from the operator workspace as demo evidence.

## Verification Checklist

Before publishing changes to this demo surface:

```powershell
python scripts\reefiki.py secret-scan --format json docs\PUBLIC_DEMO.md README.md TASKS.md
python scripts\reefiki.py publish-task --dry-run --cleanup --format json
```

Also check links and claims manually:

- links resolve inside the public repository;
- no private wiki content is copied into the demo;
- feature claims match current `README.md`, `COMMANDS.md`, `TASKS.md` and `ROADMAP.md`;
- future items remain labelled as future work, not implemented features.
