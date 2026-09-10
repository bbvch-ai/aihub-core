---
title: SDK Licensing
---

# Why the backend and UI use different licenses

Swiss AI Hub deliberately uses two open-source licenses for its two main components:

- **Backend** — Apache License 2.0
- **User interface** — GNU AGPL v3 (or later)

This split is intentional. It balances openness with the practical needs of organizations that build and deploy AI
agents on the platform. The authoritative, per-package breakdown lives in
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md); this page explains the reasoning behind it.

## Backend: Apache 2.0

The backend is where you define, configure, and run your agents, workflows, prompts, integrations, and business logic.
It is licensed under Apache 2.0 to give you maximum flexibility when deploying and extending the platform.

Many organizations consider their agents and agent logic to be proprietary intellectual property. Under a
network-copyleft license such as AGPLv3, operating a *modified* backend as a network service could require you to make
those modifications available under AGPL terms. In practice, that creates uncertainty around whether your agent
implementations and related business logic must be published.

Apache 2.0 removes that uncertainty: you can build and operate proprietary agents and backend extensions without any
concern that your implementations must be disclosed. As a permissive license it also grants explicit patent rights and
is well understood by enterprise legal teams.

This covers the platform runtime and the SDK you build on — the `core`, `agent`, `api`, `bot`, `pipeline`, and `process`
packages.

## User interface: AGPLv3

The UI is licensed under AGPLv3 to ensure that improvements to the user-facing application remain available to the
community. Organizations are free to use the UI, but if they modify the UI itself and provide it as a network service,
AGPLv3 requires those UI modifications to be shared under the same license.

This helps prevent a situation where the community maintains the UI while third parties create proprietary forks of the
interface without contributing their improvements back. The backup-and-restore orchestration service is licensed the
same way, for the same reason.

## The goal

The objective of this license split is to:

- Keep the core platform open and community-driven.
- Encourage contributions and the sharing of improvements to the UI.
- Allow organizations to build proprietary agents, workflows, and business-specific logic on top of the backend.
- Avoid creating licensing concerns around the disclosure of agent implementations.

In short, the backend remains permissively licensed to protect your ability to develop proprietary agent solutions,
while the UI uses a copyleft license to ensure that improvements to the user experience continue to benefit the broader
community.

::: tip Full per-package terms
This page explains the *why*. For the exact license that applies to each package — including the small number of
components distributed under other terms — see
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).
:::
