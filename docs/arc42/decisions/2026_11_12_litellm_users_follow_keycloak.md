# LiteLLM Users Follow Keycloak Through a Periodic Reconciliation

## Context

The Hub creates a LiteLLM user and key for every Hub user on their first request (ADR
`2026_08_06_per_user_litellm_key_as_cost_attribution_carrier`), with budgets and rate limits from the
`LITE_LLM_PROXY_USER_*` settings. Until now it never touched them again. A changed setting reached only users created
afterwards, and a user disabled or removed in Keycloak kept a key that worked at LiteLLM. Keycloak is where users are
disabled and removed (ADR `2025_12_28_keycloak_as_identity_broker`), and it tells the Hub nothing when that happens: the
realm only logs its events, and no listener calls the Hub. Hub logins are checked against the token's signature alone,
so a disabled user's token keeps working for up to an hour, and a static API token keeps working until it expires.

Per-user budgets and rate limits set in the Hub (#2135) need the same thing: a way to change limits on users that
already exist.

LiteLLM v1.106.4, which every deployment runs, constrains the design:

- It cannot block a user. `blocked` on `/user/update` is documented as not implemented. Keys can be blocked and
  unblocked one by one.
- Sending `budget_duration` on `/user/update` restarts the user's budget period, even when the value is unchanged.
- `max_budget`, `budget_duration`, `tpm_limit` and `rpm_limit` can be set back to null. `max_parallel_requests` cannot,
  and `soft_budget` cannot be updated at all.
- It caches users and keys for 60 seconds. A budget or rate-limit change drops the cached user at once.
- `/user/delete` deletes the user and their keys, and leaves the spend logs and daily spend tables alone.
- `/user/update` replaces the user's whole metadata, and ignores an empty one.

## Decision Drivers

- **A user disabled or removed in Keycloak must lose LLM access**, without anyone acting on LiteLLM.
- **A changed limit must reach users who already exist.**
- **No false removals.** An outage or an incomplete listing must not delete or lock anyone out.
- **Leave alone what the Hub did not create**: LiteLLM's own admin, and users made by hand in its UI.
- **No new infrastructure**: no Keycloak extension, no new service.

## Decision

**The API compares LiteLLM's users with Keycloak's on an interval** (`LiteLLMUserReconciler`, every five minutes by
default). A Redis lease that expires after the interval keeps it to one run per interval across all replicas. A run
still going when its lease expires is cut off, so two runs never overlap. Like `CronScheduler`, it keeps no state of its
own and can move to aihub-daemon (#1203) unchanged.

Only users with the role `internal_user_viewer` are changed. That is the role the Hub gives every user it creates, and
nothing else in the platform uses it. Each run handles these users as follows:

- **Disabled in Keycloak:** every key that still works is blocked. The user's metadata records the hashed tokens of the
  keys the Hub blocked, written before the keys are blocked. When Keycloak lists the user as enabled again, only those
  keys are unblocked and the record is cleared, so a key an operator blocked by hand stays blocked. The Hub keeps
  handing out a blocked key rather than minting a new one, so a disabled user cannot get a working key back through the
  Hub.
- **Missing from Keycloak:** the Hub asks Keycloak for the user once more. Only a 404 counts as gone, and then the user
  is deleted from LiteLLM together with their keys.
- **Enabled:** limits that differ from the settings are pushed, and only the fields that differ. This keeps the budget
  period from restarting on every run.

Each run makes three passes: it withdraws access for all users, then restores it for re-enabled users, then changes
limits. A failure for one user stops neither its own pass nor the later ones, and the failures are raised together at
the end. So if LiteLLM rejects one user's update, a disabled or removed user still loses their key, and a re-enabled
user still gets theirs back.

LiteLLM users with no Keycloak user that the Hub did not create are listed in the API log as a warning, and never
changed. `default_user_id`, LiteLLM's built-in admin, is skipped. So are the ids in
`LITE_LLM_PROXY_USER_RECONCILE_EXEMPT_USER_IDS`, which development sets to the test identity. That identity has no
Keycloak user, and its key stays cached in test processes for hours.

`LiteLLMUserAdminService.update_limits` is the entry point for limits changed in the Hub (#2135). It sends only the
fields that differ, and LiteLLM applies them within a minute.

The alternative of reacting to Keycloak events was rejected. It needs a Keycloak extension on every deployment, and an
event lost while the API is down would never be replayed. A periodic comparison repairs itself after any outage.

## Consequences

### Positive

- A user disabled in Keycloak loses LLM access by the next run, and gets it back when enabled again.
- A user removed from Keycloak is removed from LiteLLM, and their spend stays reported.
- Changed limit settings reach existing users on the first run after the API restarts.
- LiteLLM users the Hub did not create are reported, so an operator can remove them.

### Trade-offs

- **Up to one interval of delay.** A user disabled or removed in Keycloak keeps a working key until the next run.
- **Hand-tuned limits are overwritten.** A limit an operator sets in the LiteLLM UI on a user the Hub created is reset
  to the Hub's value on the next run.
- **Soft budget and parallel-request limit apply to new users only**, because LiteLLM cannot change them later.
- **A removed user can briefly come back.** A removed user whose Hub login token is still valid can make the Hub create
  their LiteLLM user again. The next run deletes it again.
- **One full listing of Keycloak's users, LiteLLM's users and LiteLLM's keys per interval.** These are paged by 100 in
  LiteLLM, which grows linearly with the user count.
- **Keys without a LiteLLM user are only reported.** Provisioning used to leave a key without its user when LiteLLM
  refused the user for an email another user still held. Such a key carries no limits and is never blocked, so the run
  lists it in the API log with the user's state in Keycloak, and an operator removes it.
- **The role is the Hub's only mark on its users.** LiteLLM also gives `internal_user_viewer` to users its own SSO or
  SCIM creates. The platform turns on neither. If an operator turns one on, the run treats those users as the Hub's, and
  deletes those whose id is not a Keycloak user id, such as a username.
- **Coupled to key derivation (aihub-core-private#351).** Blocking relies on the Hub reusing a blocked key. If keys
  become random or rotated, a disabled user could get a fresh key between runs. Provisioning must then refuse a user the
  Hub has recorded blocked keys for.

## Related Decisions

- `2026_08_06_per_user_litellm_key_as_cost_attribution_carrier.md`: the per-user key this decision keeps in step.
- `2025_12_28_keycloak_as_identity_broker.md`: Keycloak as the place users are managed.
- `2026_11_09_acting_tenant_as_litellm_customer.md`: tenants as LiteLLM customers. Customers are not reconciled.
