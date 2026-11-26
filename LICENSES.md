# License Overview

Swiss AI Hub is an **open-core** project. Its core is open source under a **dual-license model**: every package in
`packages/` is either Apache-2.0 or AGPL-3.0-or-later. The paid agents of bbv AI Hub live in `ee/` under the **bbv AI
Hub Enterprise License**. Each published artifact (Docker image, npm package, PyPI package) carries its own license —
the per-package `LICENSE` file is authoritative for everything in that subtree, overriding the root `LICENSE` for that
package.

The open core runs without `ee/`: no open package depends on it, and it is never published to PyPI.

## Why a dual-license model for the core

The split is intentional, and balances open collaboration with the practical needs of organizations building on the
platform:

- **Backend — Apache 2.0.** The runtime and SDK (`core`, `agent`, `api`, `bot`, `pipeline`, `process`) are where you
  build agents, workflows, and business logic. A permissive license lets you run and extend proprietary agents without
  any obligation to disclose your implementations — even when operating a modified backend as a network service.
- **UI and administration — AGPL-3.0-or-later.** Network-copyleft keeps improvements to the user-facing and
  administration applications in the community: modifications offered as a hosted service must be shared back, which
  blocks proprietary SaaS forks. The web UI (`web`), the multi-tenant administration plane (`sysadmin-api`,
  `sysadmin-web`), and the `backup` orchestration service are all AGPL for this reason.

See the **SDK Licensing** page in the documentation (Ecosystem → Certification → SDK Licensing) for the full rationale.

## Enterprise features — bbv AI Hub Enterprise License

The Universal Agent and the Email Classification Agent are paid features. They live in `ee/`, a separate workspace
package (`swiss-ai-hub-ee`) with its own `LICENSE`, and their Docker images are built from there. Using them needs an
agreement with bbv Software Services and a valid bbv AI Hub Enterprise License; copying and modifying them for
development and testing does not. A later paid feature is covered by moving it into `ee/`.

## Per-package license matrix

| Package                 | License                       | SPDX Identifier                    | Rationale                                                                                                                                    |
| ----------------------- | ----------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| _root, unsorted code_   | Apache License 2.0            | `Apache-2.0`                       | Default permissive license for the platform runtime and shared utilities.                                                                    |
| `packages/core`         | Apache License 2.0            | `Apache-2.0`                       | Shared library — must stay maximally permissive so every other package (incl. the AGPL ones) can depend on it.                               |
| `packages/agent`        | Apache License 2.0            | `Apache-2.0`                       | Agent runtime + reference agents — extension surface for SDK users.                                                                          |
| `packages/api`          | Apache License 2.0            | `Apache-2.0`                       | REST + WebSocket gateway. Tenant-admin endpoints live in `packages/sysadmin-api` (AGPL-3.0-or-later).                                        |
| `packages/bot`          | Apache License 2.0            | `Apache-2.0`                       | Collaboration-platform integrations (Teams/Slack).                                                                                           |
| `packages/pipeline`     | Apache License 2.0            | `Apache-2.0`                       | Dagster ingestion/processing pipelines.                                                                                                      |
| `packages/process`      | Apache License 2.0            | `Apache-2.0`                       | Process orchestration engine.                                                                                                                |
| `packages/web`          | GNU AGPL v3.0 (or later)      | `AGPL-3.0-or-later`                | Admin/Process UI. Network-copyleft: hosted modifications must publish source. Blocks hostile SaaS rehosts of the UI.                         |
| `packages/backup`       | GNU AGPL v3.0 (or later)      | `AGPL-3.0-or-later`                | Backup/restore orchestration + Postgres maintenance. Same SaaS-rehost protection as the frontend.                                            |
| `packages/sysadmin-api` | GNU AGPL v3.0 (or later)      | `AGPL-3.0-or-later`                | Multi-tenant administration API. Network-copyleft: hosted modifications must publish source. Blocks hostile SaaS rehosts of the admin plane. |
| `packages/sysadmin-web` | GNU AGPL v3.0 (or later)      | `AGPL-3.0-or-later`                | Multi-tenant administration UI. Network-copyleft: hosted modifications must publish source. Blocks hostile SaaS rehosts of the admin plane.  |
| `ee`                    | bbv AI Hub Enterprise License | `LicenseRef-bbv-AI-Hub-Enterprise` | Paid agents (Universal Agent, Email Classification Agent). Not open source; never published to PyPI.                                         |

## Vendored third-party files

A few third-party files are committed inside an Apache-2.0 package and keep their upstream license. Each sits next to
its own `LICENSE` file, which is authoritative for it, and a `SOURCE.json` recording where it was taken from. The
package metadata names both licenses (`license = "Apache-2.0 AND MIT"` in `packages/core/pyproject.toml`).

| Path                                                                                  | License | SPDX Identifier | Origin                                                                                      |
| ------------------------------------------------------------------------------------- | ------- | --------------- | ------------------------------------------------------------------------------------------- |
| `packages/core/swiss_ai_hub/core/generative_ai/resources/tokenizers/vendored/bge_m3/` | MIT     | `MIT`           | Tokenizer of BAAI/bge-m3 (FlagEmbedding, MIT), originating from XLM-RoBERTa (fairseq, MIT). |

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
- Root `NOTICE` — Apache-2.0 attribution notice (copyright holder + per-license breakdown).
