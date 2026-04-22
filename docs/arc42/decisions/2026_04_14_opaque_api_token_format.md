# Opaque `sk-<random>` Format for API Bearer Tokens

## Context

`BearerToken` originally encoded MongoDB routing metadata directly into the token string: the format
`<24-hex ObjectId>.<128-char random>` allowed `verify_token` to extract the `_id`, look the row up by primary key, and
then compare the full string. That optimization shaved one index scan, but it came with two real costs.

First, every token **leaks the ObjectId of the stored document**. A token is supposed to be opaque to the caller. The
ObjectId is not a secret per se, but embedding it couples the token format to MongoDB — if the collection is moved,
re-sharded, or the primary key representation changes, existing tokens break.

Second, the format made **externally-supplied tokens impossible**. ADR `2026_04_14_superuser_via_keycloak_realm_role`
adds a static `SUPERUSER_TOKEN` environment variable that the API materializes into the `bearer_tokens` collection at
startup. That token is set by the operator (internal services must be configured with the same value) and cannot contain
a Mongo ObjectId that will not exist until the row is inserted. The two-phase "insert, then patch token in" pattern for
user-issued tokens does not generalize.

## Decision Drivers

- **Operator-supplied tokens**: The superuser bearer token is set via env var before the document exists. The format
  must not require DB state to construct.
- **Opacity**: Tokens should be indistinguishable from random strings. No caller should be able to parse them.
- **Single verification path**: User-issued and statically-provisioned tokens should go through the same `verify_token`
  code path.
- **Misconfiguration should fail fast**: If an operator sets a malformed `SUPERUSER_TOKEN` (missing prefix, empty, wrong
  shape), the API should refuse to start, not fail on the first request.

## Decision

**All bearer tokens have the form `sk-<url-safe-random>`. `BearerToken.verify_token` does a direct, indexed lookup on
the `token` column. The `sk-` prefix is a hard requirement enforced at three layers: storage (rejected on upsert),
verification (rejected on read), and configuration (`SuperuserSettings.TOKEN` is Pydantic-validated).**

### Migration

Existing tokens in the `bearer_tokens` collection carry the old `<oid>.<random>` format. They will fail `verify_token`
on the first request after deploy because they lack the `sk-` prefix. Platform operators must either:

- Invalidate existing tokens and have users reissue them (acceptable; tokens are short-lived artifacts of the admin UI),
  or
- Run a one-shot migration that rewrites `token` values to `sk-<new-random>` and notifies users.

## Consequences

### Positive

- Tokens are opaque — no DB structure leaks through the wire format.
- One code path for all bearer tokens, regardless of origin (API-issued, env-seeded, test fixture).
- Misconfigured `SUPERUSER_TOKEN` fails at container startup with a Pydantic error, not at the first service-to-service
  call.
- `BearerToken` schema is simpler: no regex, no `bson.ObjectId` import, no two-phase save.

### Trade-offs

- Lookup is by indexed string match rather than by primary-key ObjectId. For the current token volume this is
  imperceptible; the `token` field already has a unique index.
- Existing tokens in production databases must be rotated as part of the rollout.
- The "Token mismatch" scenario — where a valid-shaped token failed the exact-match check against the row found by its
  embedded ObjectId — is no longer distinguishable from "Token not found". This is information-theoretically equivalent
  (both are "wrong secret") and the change removes a subtle fingerprinting surface.

### Related Decisions

- `2026_04_14_superuser_via_keycloak_realm_role.md` — Drives the need for operator-supplied tokens
- `2026_04_14_tenant_scoped_roles.md` — Companion refactor in the same release
