# Scope OpenWebUI Admins to Their Own Files and Chats by Default

## Context

OpenWebUI's `admin` role is granted to holders of the `AIHubSysAdmin` realm role
(`OAUTH_ADMIN_ROLES: ${OAUTH_ADMIN_ROLES_OPENWEBUI}`). Upstream OpenWebUI treats that role as unrestricted over user
content, and AI-Hub left two of the governing settings at their permissive defaults:

- `BYPASS_ADMIN_ACCESS_CONTROL` defaults to `True` upstream and AI-Hub never set it. With it on, `GET /api/v1/files/`
  and `GET /api/v1/files/search` drop the owner filter for admins, so Settings → Data Controls → Manage Files lists
  every user's uploads and every agent-generated image.
- `ENABLE_ADMIN_EXPORT` was hardcoded `True`. It exposes `GET /api/v1/chats/all/db`, which returns every user's full
  conversation content. It is not covered by `ENABLE_ADMIN_CHAT_ACCESS: False`, which AI-Hub already sets — that flag
  gates the admin chat-browsing UI, not the export endpoint.

A customer raised the file listing as a privacy concern (issue #104). Both exposures are cross-tenant: multi-tenancy
runs inside a single OpenWebUI instance, and neither the `file` nor the `user` table carries a tenant column, so an
admin's view spans every tenant on the platform.

The exposure is confined to the platform sysadmin tier. `AIHubAdmin` is a tenant-scoped *platform* role held in MongoDB
and never appears in the OIDC `roles` claim, which the `openwebui` client populates from Keycloak realm roles only. A
tenant admin therefore signs into OpenWebUI as an ordinary `user` and is filtered to their own rows in every path — the
reported behaviour requires `AIHubSysAdmin`.

## Decision Drivers

- *Least privilege* — uploads and chats contain the user content the platform exists to keep sovereign. Holding
  infrastructure administration rights is not a reason to read them.
- *Private by default* — a self-hosted platform sold on data sovereignty should not require a customer to discover and
  flip a switch before its administrators stop seeing everyone's documents.
- *Operator choice, not our judgement* — some organisations genuinely need admin oversight for support or compliance
  workflows. The behaviour must remain reachable without patching or forking.
- *Configuration over code* — OpenWebUI is consumed as an upstream image. A settings change carries no rebase burden; a
  patched image would.
- *One decision, both surfaces* — the chat export is the broader of the two exposures and is governed by the same
  concern. Fixing only the reported one would leave the larger hole open.

## Decision

**Both settings become operator-tunable environment variables, defaulted to the private setting in every stage.**

- `OPENWEBUI_BYPASS_ADMIN_ACCESS_CONTROL='false'` → `BYPASS_ADMIN_ACCESS_CONTROL`. Admins see only files they own in the
  list and search endpoints.
- `OPENWEBUI_ENABLE_ADMIN_EXPORT='false'` → `ENABLE_ADMIN_EXPORT`. `GET /api/v1/chats/all/db` returns 401 for everyone,
  including admins.

Defined in `infra/deployment/templates/docker-compose.yml.j2` as bare `${VAR}` interpolations, with the defaults in
`.env.dev` and `.env.prod` per the repository's env-var convention. Setting either to `'true'` restores upstream
behaviour for a deployment that wants it.

`ENABLE_ADMIN_CHAT_ACCESS` stays hardcoded `False` — it is already correct and no deployment has asked for it.

`BYPASS_ADMIN_ACCESS_CONTROL` is global in OpenWebUI: it also governs admin visibility of workspace models, knowledge,
prompts, tools, skills and notes. Turning it off means an admin sees those resources only where they are the owner or
hold a group grant. This is accepted as part of the same least-privilege position rather than worked around.

## Consequences

### Positive

- An OpenWebUI admin can no longer enumerate other users' files or export other users' conversations, in their own
  tenant or any other.
- Deployments needing administrative oversight keep it behind a documented, per-stage switch.
- No fork, no patched image, no upstream rebase burden.
- AI-Hub-provisioned models are unaffected in practice: they carry group-scoped access grants synced by
  `OpenWebuiProvisioner`, and the superuser is a member of every tenant group per
  [Superuser Is Added to Every Tenant at Creation Time](2026_04_15_superuser_added_to_every_new_tenant.md).

### Trade-offs

- A sysadmin who is *not* the platform superuser, and therefore not in every tenant's Keycloak group, sees a narrower
  workspace-model list than before, because AI-Hub's synced model grants are group-scoped. Measured on the dev stack:
  the superuser lost no AI-Hub model, while an admin belonging to *no* tenant group at all saw 2 of 11. A sysadmin sees
  the models of the tenants they are a member of; the mitigation is group membership, not this flag.
- OpenWebUI's built-in `arena-model` entry disappears from the admin's model list. It ships with no access grants and
  `has_access` treats an empty grant list as private, so the bypass was the only reason an admin ever saw it — regular
  users never did. AI-Hub does not use the arena feature.
- The DSAR and support workflows lose the UI path to another user's files and chats. The escape hatch is to flip the
  flag for the duration, or to go to the database directly.
- **This does not fully close admin access to file content.** `GET /api/v1/files/{id}`, its three content variants and
  `DELETE /api/v1/files/{id}` check `user.role == 'admin'` directly, with no bypass flag. An admin who obtains a file ID
  by other means can still read that file. Enumeration through the API is closed; direct access by ID is not. That gap
  needs an upstream change and is deliberately out of scope here.
- OpenWebUI admin remains a separate authorization axis from AI-Hub's `aihub.<tier>.<service>.<resource>` rules. Nothing
  in this decision changes what the AI-Hub API exposes.

Related decisions: [Restrict Langfuse Access to AIHubSysAdmin](2026_06_11_langfuse_access_restricted_to_sysadmins.md),
[AI-Hub Manages OpenWebUI Model Visibility](2026_03_05_aihub_manages_openwebui_model_visibility.md),
[Sysadmin Implicit Admin Access](2026_04_15_sysadmin_implicit_admin_access.md).
