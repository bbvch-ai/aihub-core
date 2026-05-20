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

## Proprietary parameters (sysadmin-\* packages)

The `sysadmin-api` and `sysadmin-web` packages are licensed **"All Rights Reserved"** with the following terms:

- **Licensor**: bbv Software Services AG
- **Grant**: **None.** Public visibility in this repository, on container registries, or in any other distribution
  channel does not constitute a license to use, copy, modify, run, publish, distribute, sublicense, evaluate, or
  otherwise exploit the Licensed Work, in whole or in part, for any purpose — commercial or non-commercial.
- **Commercial license**: Required for any use. Contact bbv Software Services AG at <https://www.bbv.ch>.
- **Conversion**: None. The proprietary terms do not automatically convert to an open-source license.

## SPDX & per-file headers

Package-level `license` metadata (`pyproject.toml`, `package.json`) is the **authoritative answer** for SPDX tooling
(`pip-licenses`, `pnpm licenses list`, [REUSE](https://reuse.software/)) and for everyone who consumes a package as a
whole artifact. The per-package `LICENSE` file backs it up.

Per-file SPDX headers add defence-in-depth for snippet-level copying out of context — meaningful where IP risk is
concentrated, marginal where the license is well-known.

Policy:

- **Proprietary files MUST carry an SPDX header.** Every `.py` / `.ts` / `.vue` / `.js` / `.mjs` source file under
  `packages/sysadmin-api/` and `packages/sysadmin-web/` (excluding generated `sdk/client/**`) carries
  `SPDX-License-Identifier: LicenseRef-Proprietary` (`#` for Python, `//` for TS/JS, `<!--  -->` for Vue SFCs).
- **Apache-2.0 and AGPL files MAY carry an SPDX header but are not required to.** Adoption matches what comparable
  ecosystem projects do (FastAPI, Pydantic, Nuxt, Vue, etc. ship without per-file SPDX). The root `LICENSE` and the
  package-level `license` field are sufficient for these.

## Compatibility notes

- Apache-2.0 → AGPL-3.0-or-later: one-way compatible. Apache code may be used inside AGPL packages.
- Apache-2.0 → proprietary: one-way compatible. Apache code may be embedded into the proprietary packages, but the
  resulting binary remains proprietary and inherits the "All Rights Reserved" terms.
- AGPL-3.0-or-later → proprietary: AGPL is **not** compatible with proprietary distribution. Proprietary packages must
  not import AGPL code directly. The sysadmin packages depend only on `packages/core` and `packages/api` (both
  Apache-2.0).
- Proprietary → Apache / AGPL: **never.** Proprietary symbols must not leak into the open-source packages.

## Third-party services with special terms

Several Docker images the stack orchestrates carry non-standard or conditional licenses. The base SPDX identifier in
`licenses.config.json#docker_licenses` is the closest standard match, but the conditions below apply in addition:

- **MinerU** (`mineru-api`, `mineru-vlm`) — base Apache-2.0 **plus** a commercial-use threshold clause: above the
  upstream's stated revenue/usage threshold, a separate commercial license is required. We ship thin wrapper images that
  inherit these terms. See <https://github.com/opendatalab/MinerU/blob/master/LICENSE.md>.
- **Open WebUI** (`open-webui`) — "Open WebUI License" — modified BSD-3-Clause with a branding-preservation clause. The
  "Open WebUI" name/logo may not be altered or removed, except in deployments serving ≤50 end-users in any rolling
  30-day window. Larger deployments need a commercial license. Not OSI-approved. See
  <https://github.com/open-webui/open-webui/blob/main/LICENSE>.
- **Attu** (`attu`) — Apache-2.0 up to v2.5.x; the upstream re-licensed to a proprietary terms from **v2.6.0** onward.
  We pin to `≤v2.5.x` to stay on the open-source line. Re-evaluate before bumping past 2.5.
- **Neo4j Community Edition** (`neo4j`) — GPL-3.0. Run as a separate network service; GPL has no network-copyleft
  (unlike AGPL), so it does not propagate to our code. The Neo4j Enterprise edition uses a different commercial license
  — do **not** switch images.
- **Langfuse** (`langfuse-web`, `langfuse-worker`) and **LiteLLM** (`litellm`) — core MIT, but each repo has an `ee/` or
  `enterprise/` subtree under a separate commercial license. We deploy only the OSS edition; the proprietary features
  are not built into the images we use.

## Reference

- Root `LICENSE` — Apache License 2.0 (canonical text).
- `LICENSE_REPORT.md` — generated report of third-party dependency licenses. Refreshed via `generate-license.sh`.
- `licenses.config.json` — configures the report generator (allow-listed licenses, package paths).
