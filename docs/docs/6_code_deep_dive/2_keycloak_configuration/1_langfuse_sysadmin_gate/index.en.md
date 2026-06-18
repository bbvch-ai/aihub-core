---
title: Langfuse Sysadmin Gate
description: How the custom browser flow and the Langfuse sysadmin gate are built, and the structural rules to respect when changing them
---

# Langfuse Sysadmin Gate

Langfuse logins are restricted to users with the `AIHubSysAdmin` realm role through custom authentication flows in the
`aihub` realm. The enforcement happens entirely inside Keycloak (no oauth2-proxy). It is **managed** config (see
[Keycloak Configuration](../) for the lifecycle model): the flows, the `browserFlow` binding and the authenticator
configs live in `infra/deployment/templates/configs/keycloak/managed/40-auth-flows.json.j2`, the marker scope in
`managed/20-client-scopes.json.j2`, and the scope's attachment to the `langfuse` client in `managed/30-clients.json.j2`.
The decision rationale is recorded in the ADR
`docs/arc42/decisions/2026_06_11_langfuse_access_restricted_to_sysadmins.md`.

## How the gate works

A mapper-less **marker client scope** `langfuse-sysadmin-gate` is attached as a *default* scope to the `langfuse` client
only. A conditional sub-flow (the "gate") evaluates:

1. `Condition - client scope` — is the requesting client carrying the marker scope?
2. `Condition - user role` — `AIHubSysAdmin`, **negated** (true when the user lacks the role)
3. `Deny access` — fails the login

Conditions inside a conditional sub-flow are ANDed, so the deny only fires for Langfuse logins by non-sysadmins. For
every other client the first condition is false and the gate is skipped entirely. This is what makes a realm-wide flow
safe: the per-client scoping lives in the marker scope, not in per-client flow bindings. The marker is a *default*
scope, so the condition triggers regardless of the `scope` parameter the application sends — Langfuse itself needs no
configuration for this.

The gate exists twice, because Keycloak has two non-overlapping login paths:

| Gate sub-flow               | Parent flow                             | Covers                                                         |
| --------------------------- | --------------------------------------- | -------------------------------------------------------------- |
| `langfuse-gate-browser`     | `browser-aihub` (custom browser flow)   | Existing SSO-cookie sessions and direct Keycloak logins        |
| `langfuse-gate-post-broker` | `Post Broker Login - AIHubAccess Check` | Fresh logins brokered through the external IdP (e.g. Azure AD) |

Fresh brokered logins do **not** resume the browser flow after the external redirect — the post-broker flow is the only
hook on that path, which is why both gates are required for full coverage. Sub-flows cannot be shared between parent
flows and authenticator-config aliases are realm-unique, hence two structurally identical copies with `-browser-` /
`-post-broker-` prefixed config aliases.

## Why the browser flow is replicated (`browser-aihub*` flows)

Keycloak's built-in `browser` flow is immutable (`builtIn: true`), and flows have no inheritance or include mechanism —
to add anything, the whole flow tree must be recreated and bound as the realm browser flow (realm key
`"browserFlow": "browser-aihub"`). That is what the `browser-aihub*` aliases are:

| Flow                            | Role                                                                       |
| ------------------------------- | -------------------------------------------------------------------------- |
| `browser-aihub`                 | Top level: `[REQUIRED authenticate] → [CONDITIONAL langfuse-gate-browser]` |
| `browser-aihub-authenticate`    | The built-in alternatives: cookie SSO, IdP redirector, forms               |
| `browser-aihub-forms`           | Username/password form (replica of built-in `forms`)                       |
| `browser-aihub-conditional-2fa` | Conditional OTP (replica of built-in `Browser - Conditional 2FA`)          |

The aliases carry a `browser-aihub-` prefix because flow aliases are realm-unique and the built-in names (`forms`, …)
are already taken. This mirrors what the admin console's *Copy flow* action would produce — the realm JSON just declares
the copy explicitly.

## Structural rules when changing these flows

1. **Never place a CONDITIONAL sub-flow at the same level as ALTERNATIVE executions.** Keycloak then ignores the
   alternatives and login breaks for *all* clients. This is why the authentication alternatives are nested inside the
   REQUIRED `browser-aihub-authenticate` wrapper and the gate sits next to the wrapper, not next to the alternatives.
2. **Flow `description` fields are limited to 255 characters** (database column limit) — longer values abort the whole
   realm import on a fresh start.
3. **Replicated flows receive no built-in-flow migrations.** Keycloak version upgrades will not add new executions (e.g.
   passkeys) to `browser-aihub`; review the flow on major Keycloak bumps.

## How the gate reaches running instances

The gate is **managed** config, so it reconciles on every container start without any bespoke scripting. The `aihub`
realm import seeds it on a fresh start (the flows are part of the merged realm JSON), and on every start the one-shot
`keycloak-config` service ([keycloak-config-cli](https://github.com/adorsys/keycloak-config-cli)) re-applies the
`managed/` documents over the admin API — the marker scope, its attachment to the `langfuse` client, the flows, and the
realm `browserFlow` binding. Because the realm-level `browserFlow` is set in `managed/40-auth-flows.json.j2` (not in the
bootstrap realm settings), keycloak-config-cli rebinds the custom browser flow on **every** start, which is what
activates the gate on already-initialized deployments — not just on the first `--import-realm`. Earlier revisions
reconciled the gate imperatively via `kcadm` in the entrypoint; that is retired now that the whole gate is declarative.
