---
title: Default Roles and New-User Role Assignment
description: Which roles every tenant starts with, what each one allows, and how to choose the roles new users receive.
---

# Default Roles and New-User Role Assignment

Every tenant starts with a set of ready-made roles, and every user who joins a tenant is given some of them
automatically. This page lists those roles, explains which ones a new user receives, and shows how to change both.

## Two kinds of roles

Swiss AI Hub has two separate layers of roles. They share the `AIHub` prefix, but they live in different systems and do
different jobs.

| Layer                    | Where it lives                       | Roles                                        | What it decides                                                                |
| ------------------------ | ------------------------------------ | -------------------------------------------- | ------------------------------------------------------------------------------ |
| **Keycloak realm roles** | Keycloak (or your identity provider) | `AIHubAccess`, `AIHubSysAdmin`               | Whether someone may log in at all, and whether they are a system administrator |
| **Application roles**    | Swiss AI Hub, per tenant             | The default roles below, plus any you create | What someone may do inside a tenant                                            |

`AIHubAccess` is the login gate: users without it are refused at login. `AIHubSysAdmin` grants system administration
(tenant lifecycle and infrastructure tools). Both are assigned in Keycloak or through your identity provider's app
roles, never in the Swiss AI Hub admin interface.

Everything else on this page is about **application roles**. Giving someone `AIHubAdmin` makes them an administrator of
one tenant; it does not make them a system administrator, and it does not let them log in without `AIHubAccess`.

## The default application roles

Each role grants one or more access rules in the `aihub.[user|admin].<resource>` grammar described in
[Permissions](../2_permissions/). `>` matches everything below that point.

| Role                  | Access rules                                       | What it allows                                                            |
| --------------------- | -------------------------------------------------- | ------------------------------------------------------------------------- |
| `AIHubUser`           | `aihub.user.>`                                     | Use everything in the tenant: assistants, knowledge, processes, services  |
| `AIHubAdmin`          | `aihub.admin.>`                                    | Administer everything in the tenant: configure, create, and delete        |
| `AIHubAgentUser`      | `aihub.user.agent.>`                               | Use every assistant, and nothing else                                     |
| `AIHubAgentAdmin`     | `aihub.admin.agent.>`                              | Administer every assistant, and nothing else                              |
| `AIHubKnowledgeUser`  | `aihub.user.knowledge.>`                           | Use every knowledge database, and nothing else                            |
| `AIHubKnowledgeAdmin` | `aihub.admin.knowledge`, `aihub.admin.knowledge.>` | Administer every knowledge database and create new ones, and nothing else |
| `AIHubProcessUser`    | `aihub.user.process.>`                             | Use every process, and nothing else                                       |
| `AIHubProcessAdmin`   | `aihub.admin.process.>`                            | Administer every process, and nothing else                                |

Points that are easy to miss:

- **User and admin access are separate.** `aihub.admin.>` does not include `aihub.user.>`. An administrator who should
  also use the tenant needs both `AIHubAdmin` and `AIHubUser`, which is why the first user receives both by default.
- **`AIHubKnowledgeAdmin` needs two rules.** `aihub.admin.knowledge.>` covers every existing database. Creating a new
  database is checked against the bare `aihub.admin.knowledge` rule, because a database that does not exist yet has no
  name a rule could match.
- **The tenant's access ceiling caps every role.** A role never grants more than its tenant allows. In a tenant whose
  ceiling excludes a model or an assistant, `AIHubAdmin` cannot reach it either. See
  [Access Control](../../16_multi_tenancy/4_access_control/).
- **Roles belong to one tenant.** Each tenant has its own copy of these roles. Editing `AIHubUser` in one tenant does
  not change it anywhere else.

### When the roles are created

The default roles are created:

- for the startup tenant, every time the API starts, and
- for a tenant a system administrator creates or configures.

Creation is idempotent. If a role already exists, the platform only **adds** access rules that the platform's definition
gained since the role was created. It never removes a rule, so rules an administrator added by hand are kept.

## What new users receive

A user becomes a member of a tenant the first time they make a request with that tenant in their login token. At that
moment the platform gives them roles:

- The **first member of a tenant** receives the roles in `AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES`.
- **Every later member** receives the roles in `AIHUB_USER_SIGNUP_REGULAR_USER_ROLES`.

"First" is counted per tenant, not per platform: every new tenant has its own first member. On initial setup this is
usually the seeded superuser.

Roles are given **once**, when the membership is created. Changing these settings later does not change the roles of
existing members. To change an existing member's roles, use
[User Management](../../16_multi_tenancy/3_user_management/).

### Changing which roles new users receive

Set the variables in your `.env` file (start from `.env.prod` for production or `.env.dev` for development). Both take a
comma-separated list of role names:

```bash
# Roles assigned to the very first user (typically admin). Comma-separated.
AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES='AIHubAdmin,AIHubUser'
# Roles assigned to regular users when they sign up (comma-separated)
AIHUB_USER_SIGNUP_REGULAR_USER_ROLES='AIHubUser'
```

The values shown are the defaults. For example, to let regular users only chat with assistants:

```bash
AIHUB_USER_SIGNUP_REGULAR_USER_ROLES='AIHubAgentUser'
```

Recreate the `api` container afterwards so it reads the new values.

**Every role you name must exist in the startup tenant.** The API checks this when it starts and refuses to start
otherwise, with an error that begins `Configured signup roles do not exist in the startup tenant`. Other tenants are
**not** checked: if a role is missing there, users joining that tenant get a role that grants nothing. When you name
custom roles, create them in every tenant.

## Turning off the default roles

The setting `AIHUB_CREATE_DEFAULT_ROLES` stops the platform from creating the default roles. It is **not** read from
`.env`: the Docker Compose template sets it to `True` directly on the `api` and `sysadmin-api` services. To turn it off,
set it to `False` on **both** services in your generated compose file. If only one is changed, the startup tenant and
tenants created later are treated differently.

Turning it off:

- does **not** delete roles that already exist, and
- stops the additive updates described above, so existing default roles no longer receive new rules from platform
  upgrades.

**Do not turn it off on a fresh installation while the signup variables still name the default roles.** No tenant would
have `AIHubUser` or `AIHubAdmin`, so the startup check fails and the API does not start. Instead:

1. Start the platform once with the default roles enabled.
2. Create your own roles in the admin interface.
3. Point `AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES` and `AIHUB_USER_SIGNUP_REGULAR_USER_ROLES` at those roles.
4. Set `AIHUB_CREATE_DEFAULT_ROLES` to `False` on both services and restart.

## Related pages

- [Authentication Setup](../1_authentication_setup/): how users, tenants, and roles are stored
- [Permissions](../2_permissions/): the access-rule grammar
- [User Management](../../16_multi_tenancy/3_user_management/): creating custom roles and changing a member's roles
- [Access Control](../../16_multi_tenancy/4_access_control/): tenant access ceilings
