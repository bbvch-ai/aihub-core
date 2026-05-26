# License Overview

Swiss AI Hub uses a **mixed-license model**. Each published artifact (Docker image, npm package, PyPI package) carries
its own license — the per-package `LICENSE` file is authoritative for everything in that subtree, overriding the root
`LICENSE` for that package.

## Per-package license matrix

| Package                   | License                  | SPDX Identifier            | Rationale                                                                                                                  |
| ------------------------- | ------------------------ | -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| _root, unsorted code_     | Apache License 2.0       | `Apache-2.0`               | Default permissive license for the platform runtime and shared utilities.                                                  |
| `packages/core`           | Apache License 2.0       | `Apache-2.0`               | Shared library — must stay maximally permissive so every other package (incl. AGPL and proprietary ones) can depend on it. |
| `packages/agent`          | Apache License 2.0       | `Apache-2.0`               | Agent runtime + reference agents — extension surface for SDK users.                                                        |
| `packages/api`            | Apache License 2.0       | `Apache-2.0`               | REST + WebSocket gateway. Tenant-admin endpoints live in `packages/sysadmin-api` (proprietary).                            |
| `packages/bot`            | Apache License 2.0       | `Apache-2.0`               | Collaboration-platform integrations (Teams/Slack).                                                                         |
| `packages/pipeline`       | Apache License 2.0       | `Apache-2.0`               | Dagster ingestion/processing pipelines.                                                                                    |
| `packages/process`        | Apache License 2.0       | `Apache-2.0`               | Process orchestration engine.                                                                                              |
| `packages/web`            | GNU AGPL v3.0 (or later) | `AGPL-3.0-or-later`        | Admin/Process UI. Network-copyleft: hosted modifications must publish source. Blocks hostile SaaS rehosts of the UI.       |
| `packages/backup`         | GNU AGPL v3.0 (or later) | `AGPL-3.0-or-later`        | Backup/restore orchestration + Postgres maintenance. Same SaaS-rehost protection as the frontend.                          |
| `packages/sysadmin-api`\* | Proprietary              | `LicenseRef-Proprietary`\* | Multi-tenant administration API. All rights reserved — no use granted; commercial license required for any use.            |
| `packages/sysadmin-web`\* | Proprietary              | `LicenseRef-Proprietary`\* | Multi-tenant administration UI. All rights reserved — no use granted; commercial license required for any use.             |

\* The per-package proprietary `LICENSE` files at `packages/sysadmin-api/LICENSE` and `packages/sysadmin-web/LICENSE`
are the authoritative source for terms. Public visibility in this repository does not constitute a license; see those
files for the full notice.

## Third-party software

The platform orchestrates third-party Docker images, Python packages and Node.js packages, each carrying its own license
terms set by its respective upstream. Operators and downstream consumers are responsible for reviewing those terms
directly with the upstream sources before use. The matrix below points to the canonical references; nothing in this
repository purports to summarise or amend any third-party license.

- `LICENSE_REPORT.md` — generated inventory of third-party Python and Node.js dependencies and their declared licenses.
  Refreshed via `generate-license.sh`.
- `licenses.config.json#docker_licenses` — per-image base SPDX identifier as declared by the upstream image's
  repository.

## Reference

- Root `LICENSE` — Apache License 2.0 (canonical text).
