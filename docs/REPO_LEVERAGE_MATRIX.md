# Repository Leverage Matrix

This document records external projects that can strengthen Cross-Harness Scaffolder. It separates design references from dependencies so attribution stays clean.

## Discovery Pattern

`chriscarrollsmith/github_repo_classifier` is useful as a discovery intake workflow:

- multi-strategy GitHub search,
- low-star hidden-gem discovery,
- LLM-based classification,
- enriched JSON output,
- HTML reports for underrated repositories.

Recommended search tracks:

- `ai coding agent ide extension`
- `agent sandbox firecracker`
- `postgres cockroachdb event store`
- `code review agent harness`
- `mcp coding agent`
- `terminal ai pair programming`

## Applicable Repo Categories

| Category | Candidate Repos | How To Leverage |
|---|---|---|
| Repo discovery | `https://github.com/chriscarrollsmith/github_repo_classifier` | Use as a separate research pipeline to identify underrated harness/runtime/database projects. |
| Terminal pair programming | `https://github.com/Aider-AI/aider` | Keep Aider as a harness profile and study git-aware patch workflows. |
| Open IDE assistants | `https://github.com/continuedev/continue`, `https://github.com/cline/cline`, `https://github.com/RooVetGit/Roo-Code` | Use profile ideas for extension-hosted harnesses and MCP/tool gates. |
| Agentic coding workspaces | `https://github.com/All-Hands-AI/OpenHands`, `https://github.com/block/goose` | Evaluate future live adapters for browser, shell, and multi-step coding work. |
| Local/open model IDEs | `https://github.com/TabbyML/tabby` and Tabnine-style projects | Study privacy-oriented completion and team policy controls. |
| Sandbox execution | SuperServe / Firecracker sandbox patterns, `https://github.com/e2b-dev/E2B`, `https://github.com/daytonaio/daytona` | Add isolated execution adapters and sandbox IDs in audit events. |
| Database portability | SQLAlchemy/Alembic patterns | Keep SQL dialects explicit and backend-specific retry logic separate. |
| Distributed SQL | CockroachDB examples | Use serializable retry loops and avoid advisory lock assumptions. |

## Attribution Policy

For every project:

- record URL and license in `ATTRIBUTIONS.md`,
- record commit SHA if code is copied,
- label the use as `design reference`, `optional dependency`, or `vendored code`,
- do not vendor code unless the license is compatible,
- prefer adapter interfaces over hard dependencies.

## Current State

Current implementation uses external projects as design references only. No external source code is copied or vendored.
