# License Overview

Swiss AI Hub uses a **mixed-license model**. Each published artifact (Docker image, npm package, PyPI package) carries
its own license — the per-package `LICENSE` file is authoritative for everything in that subtree, overriding the root
`LICENSE` for that package.

## Per-package license matrix

| Package                   | License                  | SPDX Identifier         | Rationale                                                                                                                          |
| ------------------------- | ------------------------ | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| _root, unsorted code_     | Apache License 2.0       | `Apache-2.0`            | Default permissive license for the platform runtime and shared utilities.                                                          |
| `packages/core`           | Apache License 2.0       | `Apache-2.0`            | Shared library — must stay maximally permissive so every other package (incl. AGPL/BSL ones) can depend on it.                     |
| `packages/agent`          | Apache License 2.0       | `Apache-2.0`            | Agent runtime + reference agents — extension surface for SDK users.                                                                |
| `packages/api`            | Apache License 2.0       | `Apache-2.0`            | REST + WebSocket gateway. Tenant-admin endpoints live in `packages/sysadmin-api` (BSL).                                            |
| `packages/bot`            | Apache License 2.0       | `Apache-2.0`            | Collaboration-platform integrations (Teams/Slack).                                                                                 |
| `packages/pipeline`       | Apache License 2.0       | `Apache-2.0`            | Dagster ingestion/processing pipelines.                                                                                            |
| `packages/process`        | Apache License 2.0       | `Apache-2.0`            | Process orchestration engine.                                                                                                      |
| `packages/web`            | GNU AGPL v3.0 (or later) | `AGPL-3.0-or-later`     | Admin/Process UI. Network-copyleft: hosted modifications must publish source. Blocks hostile SaaS rehosts of the UI.               |
| `packages/backup`         | GNU AGPL v3.0 (or later) | `AGPL-3.0-or-later`     | Backup/restore orchestration + Postgres maintenance. Same SaaS-rehost protection as the frontend.                                  |
| `packages/sysadmin-api`\* | Business Source License  | `LicenseRef-BUSL-1.1`\* | Multi-tenant administration API. Production use requires a commercial license until the Change Date (then converts to Apache-2.0). |
| `packages/sysadmin-web`\* | Business Source License  | `LicenseRef-BUSL-1.1`\* | Multi-tenant administration UI. Production use requires a commercial license until the Change Date (then converts to Apache-2.0).  |

\* The per-package BSL `LICENSE` files at `packages/sysadmin-api/LICENSE` and `packages/sysadmin-web/LICENSE` are the
authoritative source for terms, including the Change Date (2030-05-13) on which they convert to Apache-2.0.

## BSL parameters (sysadmin-\* packages)

When the BSL packages land they will use the **BUSL-1.1** template with the following terms:

- **Licensor**: bbv Software Services AG
- **Change License**: Apache License, Version 2.0
- **Change Date**: 4 years after the file's commit date (the per-file `LICENSE` records the exact date at the time of
  release).
- **Additional Use Grant**: Non-production use only. You may copy, modify, redistribute, and use the Licensed Work for
  development, testing, evaluation, and other non-production purposes. Production use requires a separate commercial
  license from the Licensor.

## SPDX & per-file headers

Source files should carry an SPDX identifier comment at the top:

- Apache-2.0 files: `# SPDX-License-Identifier: Apache-2.0` (Python) / `// SPDX-License-Identifier: Apache-2.0`
  (TS/Vue/JS).
- AGPL files: `SPDX-License-Identifier: AGPL-3.0-or-later`.
- BSL files: `SPDX-License-Identifier: LicenseRef-BUSL-1.1`.

The SPDX-aware tooling ([REUSE](https://reuse.software/), `pip-licenses`, `pnpm licenses list`) reads the package-level
`license` metadata as the authoritative answer. The SPDX header on each source file is a defence in depth — it makes the
license unambiguous when a single file is copied out of the package.

## Compatibility notes

- Apache-2.0 → AGPL-3.0-or-later: one-way compatible. Apache code may be used inside AGPL packages.
- Apache-2.0 → BUSL-1.1: BSL is not OSI-approved and is not a free-software license during the BSL period. Apache code
  may be embedded into BSL packages, but the resulting binary is BSL-restricted until the Change Date.
- AGPL-3.0-or-later → BUSL-1.1: AGPL is **not** compatible with BSL. BSL packages must not import AGPL code directly.
  The sysadmin packages depend only on `packages/core` and `packages/api` (both Apache-2.0).

## Reference

- Root `LICENSE` — Apache License 2.0 (canonical text).
- `LICENSE_REPORT.md` — generated report of third-party dependency licenses. Refreshed via `generate-license.sh`.
- `licenses.config.json` — configures the report generator (allow-listed licenses, package paths).
