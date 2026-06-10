# Relicense the Sysadmin Plane to AGPL-3.0-or-later (Fully Open-Source)

## Context

ADR [`2026_05_19_split-sysadmin-into-proprietary-packages`](./2026_05_19_split-sysadmin-into-proprietary-packages.md)
extracted the multi-tenant administration plane into `packages/sysadmin-api` and `packages/sysadmin-web` under a strict
proprietary "All Rights Reserved" notice (`LicenseRef-Proprietary`). Everything else was already open-source: Apache-2.0
for the runtime + SDK, AGPL-3.0-or-later for the web UI and backup orchestration.

We now want Swiss AI Hub to be **fully open-source**, with only two licenses in the repository: Apache-2.0 and
AGPL-3.0-or-later. This supersedes the proprietary-split decision: the sysadmin plane stays a separate package and
deploy artifact, but is relicensed to AGPL rather than kept proprietary.

## Decision Drivers

- *Fully open-source platform* — no "no use granted" tier; the whole platform can be self-hosted under open-source
  terms.
- *Trust in regulated Swiss markets* — a publicly auditable, fully open codebase is easier to adopt and review.
- *Keep SaaS-rehost protection* — AGPL network-copyleft on the administration plane still forces hosted modifications to
  publish source, the same protection the web UI and backup service already rely on.
- *Simpler licensing story* — two licenses (Apache-2.0 backend/SDK, AGPL-3.0-or-later user-facing + administration)
  instead of three.

## Decision

Relicense both sysadmin packages from `LicenseRef-Proprietary` to **AGPL-3.0-or-later**:

- Replace `packages/sysadmin-api/LICENSE` and `packages/sysadmin-web/LICENSE` with the verbatim GNU AGPL v3 license text
  (as used by `packages/web`).
- Set `AGPL-3.0-or-later` in `packages/sysadmin-api/pyproject.toml` and `packages/sysadmin-web/package.json`.
- **Remove the per-file `SPDX-License-Identifier` headers** from both packages instead of flipping them to AGPL. No
  other package carries per-file headers — the package-level `LICENSE` file is authoritative — so removing them makes
  the sysadmin packages consistent with the rest of the monorepo.
- Update governance docs (`LICENSES.md`, root `README.md`, `CONTRIBUTING.md`, `NOTICE`, root + per-package `CLAUDE.md`,
  arc42 chapters, the docs-site licensing pages) to describe a dual-license model with no proprietary tier.
- Update the compose generator (`infra/deployment/generate_compose.py` `OWN_IMAGE_LICENSES`) and template annotations,
  then regenerate the compose files.

The Apache-2.0 backend/SDK packages (`core`, `agent`, `api`, `bot`, `pipeline`, `process`) are unchanged.

## Consequences

- The platform is fully open-source; the sysadmin plane can be used, modified, and self-hosted under AGPL-3.0-or-later.
- The package separation is now **architectural** (separate deploy artifact, own subdomain, hard sysadmin-gated security
  boundary) rather than a licensing boundary. The Apache-2.0 → AGPL one-way embedding rule still holds: AGPL code must
  not leak back into the Apache-2.0 packages.
- The commercial-licensing path for the sysadmin plane no longer applies. Retiring any associated sales/commercial-terms
  process is a separate, non-code follow-up.
- `swiss-ai-hub-sysadmin-api` remains excluded from PyPI publishing because it ships as a Docker image, not a library —
  a packaging decision, no longer a licensing one.
- This ADR supersedes `2026_05_19_split-sysadmin-into-proprietary-packages` on the licensing question; that ADR remains
  as the historical record of the original extraction and proprietary choice.
