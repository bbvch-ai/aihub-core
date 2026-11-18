# Paid Agents in an `ee/` Package under the bbv AI Hub Enterprise License

> Partially supersedes
> [`2026_06_10_relicense_sysadmin_plane_to_agpl`](./2026_06_10_relicense_sysadmin_plane_to_agpl.md): the repository is
> no longer open source as a whole. The open core keeps the two licenses that ADR set out.

## Context

The repository has been fully open source since
[`2026_06_10_relicense_sysadmin_plane_to_agpl`](./2026_06_10_relicense_sysadmin_plane_to_agpl.md): Apache-2.0 for the
runtime and SDK, AGPL-3.0-or-later for the UI, administration plane and backup service. The Universal Agent and the
Email Classification Agent now become paid features of bbv AI Hub, and more paid features are expected. Both agents
lived in the Apache-2.0 `packages/agent`, so they were published under Apache-2.0 in the `swiss-ai-hub-agent` wheel and
in their Docker images.

The license text drafted for them follows the Langfuse model: any use needs an agreement with bbv Software Services and
a valid bbv AI Hub Enterprise License; copying and modifying for development and testing is free; bbv owns
modifications; copying, publishing and distributing are otherwise forbidden. Its note names the core license `/LICENSE`
and the enterprise license `ee/LICENSE`, and states that per-package licenses take precedence over the root license.

## Decision Drivers

- *One license per artifact* — the reasoning of
  [`2026_05_19_split-sysadmin-into-proprietary-packages`](./2026_05_19_split-sysadmin-into-proprietary-packages.md): a
  wheel or an image carries exactly one license, so paid code cannot share a package with Apache code.
- *The license text as drafted* — the layout should make its wording true as it stands, without editing paths or
  overriding the per-package precedence rule in `LICENSES.md`.
- *The open core runs without it* — no open package may depend on the paid code.
- *Never published* — the license forbids publishing, so the code must stay out of PyPI.
- *A later move to a private repository* — moving one folder must be enough.
- *No migration* — saved profiles, chats, mailboxes and event history refer to agent classes, agent types and events by
  name.

## Decision

Create a root-level workspace package `ee/` (`swiss-ai-hub-ee`, module `swiss_ai_hub.ee`) with its own `LICENSE`, the
layout LiteLLM and Langfuse use for their enterprise code:

- `ee/LICENSE` holds the bbv AI Hub Enterprise License verbatim; `ee/pyproject.toml` declares
  `LicenseRef-bbv-AI-Hub-Enterprise` and the `Private :: Do Not Upload` classifier, so PyPI rejects an upload. The
  package is not in the PyPI publish list and not a dependency of the `swiss-ai-hub` meta-package.
- Both agents move with their tests, translations, entry points, templates and Dockerfiles. Their images keep their
  names and are built from `ee/app/<agent>/Dockerfile`; each image contains `ee/LICENSE`, and the compose files label
  them with the enterprise license.
- Class names, agent types and event names do not change. Only module paths change (`swiss_ai_hub.agent.agents.*` →
  `swiss_ai_hub.ee.agents.*`); nothing persists them.
- Dependencies point one way, `ee` → `packages/agent` → `packages/core`. `ee` imports the SDK only through its public
  interfaces, so `swiss_ai_hub.agent.capabilities` and `swiss_ai_hub.agent.imap` export the names the agents need. Open
  tests that used the paid agents as hosts use test-local agents instead.
- Enterprise strings resolve through `EnterpriseLocaleString`, which adds the package's translations to the agent SDK's
  — the pattern `SysadminApiLocaleString` set.
- The root `LICENSE` opens with a "Portions of this software are licensed as follows" clause naming `ee/`;
  `LICENSES.md`, `NOTICE`, `README.md`, `CONTRIBUTING.md` and the documentation describe an open-core project.

A folder inside `packages/agent` was rejected: the license paths would have to be rewritten, `packages/agent/LICENSE`
would govern it under the precedence rule, the agent wheel would need an exclusion, and its metadata would carry two
licenses.

## Consequences

- The open core is unchanged for its users: the open packages, wheels and images carry the same licenses as before.
- Both images stay public on GHCR under their names, so deployments see no change. Making them private needs new package
  names and pull credentials for every customer, and belongs to the move to a private repository.
- The default deployment still includes both agents: the generated compose files start them with every other service,
  without a profile or other opt-in, and the Kubernetes chart deploys them too. An operator without a bbv AI Hub
  Enterprise License has to remove them from the deployment; making them opt-in for licensed instances is separate work.
- Releases of both agents before this decision stay under Apache-2.0; the grant cannot be withdrawn.
- A later paid feature is licensed by moving it into `ee/`; no further license file or SPDX identifier is needed.
- CI tests, lints and scans `ee` as its own scope with its own Sonar project, and the version bump covers it.
- A CI check that fails when open code imports `swiss_ai_hub.ee` is still to come; until then the scope-boundary hook
  warns about it locally.
