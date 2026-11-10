---
name: sync-role-docs
description: Bring the operator page on default roles and new-user role assignment (docs/docs/2_platform/11_access_management/3_default_roles/) back in line with the code. Run it whenever _DEFAULT_ROLE_DEFINITIONS in initialize_db.py, UserSignupSettings, AIHubSettings.CREATE_DEFAULT_ROLES, the signup-role validation, the first-member role logic in KeycloakAuthHandler, or the AIHUB_USER_SIGNUP_* / AIHUB_CREATE_DEFAULT_ROLES lines in .env.* or the compose template change, and whenever test_default_roles_docs_drift.py fails. Use when user says 'update the roles page', 'I added a default role', 'sync role docs', 'roles docs drift test failed', or 'did the docs keep up with the role change'. Do NOT use for creating or editing custom roles in a tenant (that is the admin UI), the access-rule grammar pages (2_permissions, 16_multi_tenancy/4_access_control — use update-doc), or agent pages (use sync-agent-docs).
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Sync Role Docs

`docs/docs/2_platform/11_access_management/3_default_roles/index.en.md` tells operators which roles every tenant starts
with, what each grants, which roles new users receive, and how to turn seeding off. Every fact on it comes from code
that never mentions the page, so `/update-doc`'s name-matching sweep does not find it.

`packages/api/playground/testing/tests/runners/test_default_roles_docs_drift.py` guards the **machine-checkable** part:
the role table (names and rules) and the two signup defaults. Everything else on the page is prose this skill keeps true
by hand.

## Step 0: Did anything role-related change?

```bash
BASE=$(git merge-base HEAD origin/main)
git diff --name-only "$BASE"...HEAD | grep -E \
  "packages/api/swiss_ai_hub/api/runners/lifetime/initialize_db.py|packages/core/swiss_ai_hub/core/infrastructure/api/(user_signup_settings|ai_hub_settings).py|packages/core/swiss_ai_hub/core/auth/dependencies/keycloak_auth_handler/keycloak_auth_handler.py|packages/sysadmin-api/swiss_ai_hub/sysadmin_api/routes/tenant_admin/tenant_admin_service.py|^\.env\.(dev|prod)$|infra/deployment/templates/docker-compose.yml.j2|infra/configs/keycloak/aihub-realm" \
  || echo "no role-related change -- stop here"
```

For the `.env.*` and compose template hits, check the diff actually touches `AIHUB_USER_SIGNUP_` or
`AIHUB_CREATE_DEFAULT_ROLES` before going on. For the realm JSON, only the `roles.realm` block matters.

## Step 1: Map each change to the page section

| Source of truth                                                                                                      | Page section                                            |
| -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `_DEFAULT_ROLE_DEFINITIONS` in `packages/api/swiss_ai_hub/api/runners/lifetime/initialize_db.py`                     | "The default application roles" table                   |
| `_reconcile_default_role_rules`, `initialize_default_roles_for_tenant` (same file)                                   | "When the roles are created"                            |
| Callers of `initialize_default_roles_for_tenant` in `packages/sysadmin-api/.../tenant_admin/tenant_admin_service.py` | "When the roles are created" (which tenants get them)   |
| `UserSignupSettings` in `packages/core/swiss_ai_hub/core/infrastructure/api/user_signup_settings.py`                 | "Changing which roles new users receive" code block     |
| `.env.dev` / `.env.prod` `# User Signup Settings` block                                                              | Same code block: it quotes the `.env` comments verbatim |
| `_resolve_roles_for_new_member` / `_ensure_membership_for_tenant` in `keycloak_auth_handler.py`                      | "What new users receive"                                |
| `_validate_signup_roles` in `initialize_db.py`                                                                       | The startup-check paragraph and its quoted error text   |
| `AIHubSettings.CREATE_DEFAULT_ROLES` + `AIHUB_CREATE_DEFAULT_ROLES` in `docker-compose.yml.j2`                       | "Turning off the default roles"                         |
| `roles.realm` in `infra/configs/keycloak/aihub-realm.*.json`, `SYS_ADMIN_ROLE` in `core/auth/realm_roles.py`         | "Two kinds of roles"                                    |

Read the changed code, then the matching section. Code is ground truth.

## Step 2: Update the page

Edit only `index.en.md`. Keep the table row format exactly — the drift test parses it:

```
| `AIHubKnowledgeAdmin` | `aihub.admin.knowledge`, `aihub.admin.knowledge.>` | Administer every knowledge database ... |
```

First cell: the backticked role name. Second: every access rule, each backticked, comma-separated. A new role in
`_DEFAULT_ROLE_DEFINITIONS` gets a new row; a role whose rules need explaining (like `AIHubKnowledgeAdmin`'s two rules)
also gets a bullet under "Points that are easy to miss". Write the "What it allows" cell for an operator, not as the
rule restated.

The signup defaults must stay as `VAR='value'` lines (single quotes, one per line), matching `.env.prod`.

## Step 3: Check the pages that repeat these facts

```bash
grep -rn "AIHUB_USER_SIGNUP\|AIHUB_CREATE_DEFAULT_ROLES\|AIHubUser\|AIHubAdmin" docs/docs --include=index.en.md \
  | grep -v 3_default_roles
```

Expected hits are `11_access_management/1_authentication_setup`, `16_multi_tenancy/2_creating_tenants`,
`16_multi_tenancy/4_access_control` and `20_security/1_authentication`. They should link to this page rather than
restate it; fix any value that now disagrees with code. Ignore `6_code_deep_dive/` — it is synced from package READMEs,
so fix the README instead.

## Step 4: Verify

```bash
cd packages/api && uv run pytest playground/testing/tests/runners/test_default_roles_docs_drift.py -q
cd ../../docs && pnpm run docs:translate   # regenerates index.de.md; needs the llm CLI
```

The test must pass. Then confirm `index.de.md` changed and its `source_sha` was updated. If `llm` is not installed, say
so and leave the German page for whoever has it — never hand-edit `index.de.md`.

## Common Mistakes

- **Changing `AIHUB_CREATE_DEFAULT_ROLES` on one service only.** The compose template sets it on both `api` and
  `sysadmin-api`; the page tells operators to change both, and must keep saying so while both seed roles.
- **Claiming the startup check covers every tenant.** `_validate_signup_roles` only checks the startup tenant. If that
  changes, update the paragraph — do not generalize it in advance.
- **Treating "first user" as platform-wide.** `_resolve_roles_for_new_member` counts members per tenant.
- **Restating the rule grammar.** The `>`/`*` semantics live in `2_permissions`; link there.
