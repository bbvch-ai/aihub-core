# aihub-igs: Remove Dev-Only Fake Authentication from the Production Bot Config

**Status**: Proposed (2026-05-29) **Severity**: P0 (security — authentication bypass)
**Drives**: Overview §3.7 #1 (IGS bot dev-auth in prod compose); [`../c4/igs.md`](../c4/igs.md)

## Context

The `aihub-igs` customer repo (HEAD `8eb4237`, 2026) ships a generated `docker-compose.latest.yml` whose `bot`
service (MS Teams integration, core `bot:latest` image) sets four dev-only fake-authentication environment variables:

```yaml
bot:
  environment:
    DANGEROUS_DEV_ONLY_AUTH_FAKE_NAME: ${BOT_AUTH_FAKE_NAME}
    DANGEROUS_DEV_ONLY_AUTH_FAKE_EMAIL: ${BOT_AUTH_FAKE_EMAIL}
    DANGEROUS_DEV_ONLY_AUTH_FAKE_OID: ${BOT_AUTH_FAKE_OID}
    DANGEROUS_DEV_ONLY_AUTH_FAKE_ROLES: ${BOT_AUTH_FAKE_ROLES}
```

These variables are a core debugging affordance: when set, the bot **bypasses real OIDC authentication** and treats
every request as the configured fake identity (name / email / OID / roles). The `DANGEROUS_DEV_ONLY_` prefix is the
core's own signal that this path is **not for production**.

`docker-compose.latest.yml` is the file used for the IGS deployment (Gen 2-aligned, Ansible-Pull pattern). The actual
values come from `secrets/igs.yml.vault` (Ansible Vault) and are not visible in the repo, so we cannot confirm from
source whether they are populated in the live pilot. But the variables being *wired into the production compose at all*
is the risk: a single non-empty vault value silently turns the bot into an unauthenticated endpoint that can act with
arbitrary roles (including elevated ones via `..._ROLES`).

IGS serves an **internal information-security / data-protection directive** assistant — the exact domain where an
auth-bypass is least acceptable.

## Decision Drivers

- **Auth bypass = full impersonation**: `..._ROLES` lets a faked identity assume any role; combined with `..._OID` it
  can impersonate a specific real user.
- **Fail-safe, not fail-open**: production config should make the dangerous path *impossible*, not merely *unset*.
- **Gen 2 template reuse**: IGS is the first Gen 2 customer; whatever ships here becomes the template the next Gen 2
  customer inherits.
- **Defence in depth**: the core image should also refuse to honour `DANGEROUS_DEV_ONLY_*` when `ENV`/stage is
  production, independent of customer config hygiene.

## Decision

1. **Remove the four `DANGEROUS_DEV_ONLY_AUTH_FAKE_*` keys** from the production bot service in the compose template
   (`aihub-core` `deployment/templates/docker-compose.yml.j2`) — gate them behind the `dev` stage only, so generated
   non-dev compose files never carry them. Regenerate `aihub-igs/docker-compose.latest.yml`.
2. **Core hard-guard**: the bot (and any service reading `DANGEROUS_DEV_ONLY_AUTH_*`) MUST refuse to start, or ignore
   the fake-auth path, when `ENV` is not `dev`/`local`. Log a loud warning. This makes the bypass impossible even if a
   customer re-adds the env vars.
3. **Remove the corresponding `BOT_AUTH_FAKE_*` entries** from `secrets/igs.yml.vault` (and the customer template
   vault) once step 1+2 land.
4. **CI check**: add a lint/grep gate in the compose-generation pipeline that fails if any `DANGEROUS_DEV_ONLY_*`
   variable appears in a non-dev generated compose.

## Consequences

**Positive**

- Production bot can no longer be turned into an unauthenticated, role-spoofing endpoint by a stray config value.
- The fix is defence-in-depth (template + core guard + CI), so it survives customer config drift.
- Establishes a clean baseline for every future Gen 2 customer.

**Negative**

- Local/dev workflows that relied on fake-auth for the bot must use the `dev` stage explicitly.
- Requires a coordinated core change (image guard) + template regeneration + vault edit.

**Open items**

- Confirm with the IGS ops team whether `BOT_AUTH_FAKE_*` is currently populated in the live pilot vault; if so, treat
  as an active exposure and rotate any affected sessions/tokens.
- Audit the other customer repos (B*D / C*C / Dem*scope / W*P / F*H) for the same env vars in non-dev compose.

## References

- Overview §3.7 #1 (the finding), [`../c4/igs.md`](../c4/igs.md) (IGS container diagram + observations).
- `aihub-igs/docker-compose.latest.yml` — `bot` service.
- Related: proposed `adr_NEW-005` (Secrets Management and Rotation), `adr_021` (Source-System Authentication Strategy).
