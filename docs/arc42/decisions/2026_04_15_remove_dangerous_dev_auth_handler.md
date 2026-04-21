# Remove `DangerousDevelopmentOnlyAuthHandler` in Favour of a Test-Only `TestAuthHandler`

## Context

`DangerousDevelopmentOnlyAuthHandler` was introduced when the platform had no identity provider of its own.
Authenticating required bringing an external directory — typically Azure AD — and wiring it into the deployment; there
was no "start the stack and log in" path for local development. The no-auth handler filled that gap: it fabricated a
constant `UserIdentity` so developers could run the API, bots, and agent playgrounds against their laptops without
provisioning AD first. It lived next to the production handlers under `swiss_ai_hub.core.auth.dependencies.*` and was
re-exported through the public `swiss_ai_hub.core.auth` interface. Its companion `DangerousDevelopmentOnlyAuthSettings`
exposed the test identity (name, email, oid, roles) as environment-variable-backed Pydantic settings.

Two platform changes obsoleted that use case and made the handler actively harmful to keep:

1. **Keycloak is now part of the default dev stack.** The recent introduction of Keycloak as the platform's bundled
   identity provider means `docker compose up` delivers a working auth flow out of the box — no external AD required.
   The "local dev without any IdP" scenario the handler was built for no longer exists; the honest path (log in to the
   local Keycloak, get a real JWT) is now shorter than the bypass path was.

2. **Keycloak became the ground truth for user and tenant existence.** Large parts of the codebase — membership checks
   (`KeycloakAdminService.is_user_member_of_tenant`, per ADRs `2026_04_15_sysadmin_implicit_admin_access` and
   `2026_04_15_superuser_added_to_every_new_tenant`), user lookups, tenant-group existence (ADR
   `2026_04_15_keycloak_as_tenant_existence_authority`), active-tenant attributes, realm-role resolution — now consult
   Keycloak directly. The no-auth handler was architecturally stuck on the wrong side of that shift: it fabricated a
   self-contained `UserIdentity` with a hardcoded `__dangerous_development_only_tenant__` that did not exist in
   Keycloak, a user that was not a member of any real Keycloak group, and roles that were not backed by any realm role.
   Making that shape work with the current code would have required mocking Keycloak at every call site the handler
   touches — which is exactly what the test fixtures already do (`_build_fake_admin()` in
   `testing/auth_utils/user_mocks.py` patches the `KeycloakAdmin` factory with a stateful in-memory fake that every
   production auth handler is already tested against). So the no-auth handler's original value proposition — "avoid
   needing to mock Keycloak" — no longer holds; the mock is required either way.

A third concern made the handler a liability rather than just a redundancy: **it was the default fallback in
`Controller.__init__`**. `self.auth: AuthHandler = auth or DangerousDevelopmentOnlyAuthHandler()` silently installed an
auth-bypass on any controller whose caller forgot to pass `auth`. `packages/bot/app/main.py` in fact used the handler
deliberately as a production placeholder because the `Controller` base required one. Co-locating test helpers with
production handlers — under the same import path, re-exported from the same public interface — normalised the exact
thing that should stay anomalous, and turned a config mistake into a silent auth bypass.

## Decision Drivers

- **Local dev now has an honest path**: Before bundling Keycloak, skipping authentication locally meant running without
  any identity at all — there was nothing to log in to. With Keycloak in the default dev stack, "start the stack and log
  in" is the short path; a no-auth shortcut no longer saves anyone meaningful time.
- **A self-contained fake identity contradicts the Keycloak-as-ground-truth model**: The platform now answers "does this
  user exist?", "is this user a member of tenant X?", "does this tenant exist?", and "does this user have the sysadmin
  realm role?" by asking Keycloak. A handler that fabricates a `UserIdentity` plus a fabricated tenant
  (`__dangerous_development_only_tenant__`) — without corresponding Keycloak records — fails every one of those checks.
  Keeping the handler functional would require mocking Keycloak at every call site it touches, which is what the test
  infrastructure already does. There is no reduction in mocking surface to defend anymore.
- **Separate safety from convenience**: A bypass-auth handler is a legitimate test tool, not a production artefact.
  Co-locating it with `KeycloakAuthHandler` under `swiss_ai_hub.core.auth` and re-exporting it through the public
  interface normalises the anomaly. Moving the replacement under `swiss_ai_hub.core.testing` — and keeping it out of the
  production auth `__all__` — makes the boundary a property of the import path, not a naming convention.
- **`Controller` must require an explicit auth handler**: The old
  `self.auth: AuthHandler = auth or DangerousDevelopmentOnlyAuthHandler()` fallback silently installed an auth-bypass
  handler whenever a caller forgot to pass `auth`. `TypeError` on `auth=None` is safer than a silent fallback, and no
  current caller relied on the fallback anyway.
- **No parallel identity configuration**: A `BaseSettings` class with environment overrides invited per-developer drift
  ("my local `DANGEROUS_DEV_ONLY_AUTH_FAKE_OID` is different from yours") for no real benefit. Plain module-level
  constants are shorter, deterministic, and impossible to misconfigure.
- **Tests exercise the real membership pipeline anyway**: `TestAuthHandler` delegates to `AuthHandler.build_identity()`
  — the fake admin (already session-autouse in `testing/auth_utils/user_mocks.py`) supplies the membership data. Tests
  catch Keycloak-first regressions instead of hiding them behind a self-contained fake.

## Decision

**Delete `DangerousDevelopmentOnlyAuthHandler` and `DangerousDevelopmentOnlyAuthSettings` entirely. Replace them with
`swiss_ai_hub.core.testing.auth_utils.TestAuthHandler` (the bypass handler) and plain module-level constants in
`test_identity.py` (`TEST_USER_OID`, `TEST_USER_NAME`, `TEST_USER_EMAIL`, `TEST_USER_ROLES`, `TEST_TENANT_ID`). Make
`Controller.__init__(auth=...)` fail loudly with `TypeError` when `auth is None` rather than silently falling back to a
bypass handler. The production bot entry point (`packages/bot/app/main.py`), which used the old handler as a
placeholder, switches to `KeycloakAuthHandler` — if the endpoint is ever reached by an external request the handler
fails closed on missing JWT.**

The namespace move is the load-bearing part of the change: `TestAuthHandler` lives under
`swiss_ai_hub.core.testing.auth_utils` and is not re-exported through `swiss_ai_hub.core.auth`. Production code cannot
import it through the auth public interface; test code imports it explicitly through the testing package. The boundary
is enforced by what is and isn't in `__all__`, not by naming conventions or comments.

## Consequences

### Positive

- No code path exists in a production image that returns a valid `UserIdentity` without validating credentials. The
  `Dangerous` name was a warning; its absence is a guarantee.
- `Controller` construction now fails loudly if the caller forgets `auth`, eliminating a class of silent bypass bugs.
- Test identity is a handful of constants with no environment-variable surface — one file to grep, one pattern to
  follow, no per-developer drift.
- Tests exercise the real Keycloak-first membership pipeline via the fake admin, catching regressions that the old
  self-contained `UserIdentity` would have hidden.

### Trade-offs

- **Local dev requires the bundled Keycloak.** Running the API, bots, or agents interactively means booting the Docker
  dev stack (which already ships Keycloak) and logging in with a real account — the no-login shortcut is gone. This is
  aligned with the broader "Keycloak is the authority" direction, but developers who had muscle memory for the bypass
  path need to switch to real logins.
- **Migration touched ~60 files** (playground tests, agent triggers, process playground, bot playground, API test
  fixture, controller base, public auth exports). The change is mechanical — imports and constructor call sites — but
  large in scope; it should be its own PR for reviewability.
- **The production bot app now requires `KEYCLOAK_URL` to be set at import time** (because `KeycloakAuthHandler`
  instantiates `KeycloakSettings` at class definition). This is consistent with every other production service; the bot
  was the outlier that leaned on the no-auth handler as a placeholder.
- **Historical documentation still mentions `DangerousDevelopmentOnlyAuthHandler`** in the 2025 superuser ADR and in the
  changelog. Those are history, not guidance, and are not rewritten.

## Related Decisions

- `2026_04_15_sysadmin_implicit_admin_access.md` — Establishes authorization-only sysadmin bypass; removing the
  membership-bypass in the old DangerousDev flow is a direct consequence of treating Keycloak as the sole membership
  authority.
- `2026_04_15_superuser_added_to_every_new_tenant.md` — Makes cross-tenant sysadmin reach work via explicit group
  membership, which `TestAuthHandler` can rely on in tests via the fake admin.
- `2026_04_15_keycloak_as_tenant_existence_authority.md` — The broader "Keycloak is the authority" line this change
  continues.
- `2025_08_11_global_superuser_authentication.md` — Historical; mentions the old handler.
