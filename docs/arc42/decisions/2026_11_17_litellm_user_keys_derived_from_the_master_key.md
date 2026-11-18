# A User's LiteLLM Key Is Derived from the Master Key, and LiteLLM Has No Public Route

## Context

Every model call the Hub makes for a user carries that user's LiteLLM key, which books the call to the user's budget
(ADR `2026_08_06_per_user_litellm_key_as_cost_attribution_carrier`). The key was `"sk-"` plus the first 16 hex
characters of `sha256(user id)`. User ids are the identity provider's subject ids and are not secret, so anyone who knew
a user's id could compute that user's key.

`litellm.${DOMAIN}` has been routed to LiteLLM since the first Docker Compose deployment. PR #2262 put the UI and the
management routes behind `oauth2proxy-litellm` and kept the OpenAI-compatible inference routes public, guarded by
LiteLLM's key check alone. A key used there reaches any model: model access rules and usage limits live in the Hub, and
LiteLLM does not scope keys to models (#1773).

The key lookup sent the key as a query parameter (`GET /key/info?key=sk-…`), so the Hub's own spans recorded it in full.
LiteLLM v1.106.4 writes `?REDACTED` into its access log instead, but anything else that logs the URL would not. That
revealed nothing while keys could be computed from the id, but becomes a leak once they cannot.

Customers run older releases, whose agents compute the old key themselves.

## Decision Drivers

- A user's key must not follow from anything other users or tenant administrators can see.
- A key used directly must give no more than the Hub would give that user.
- Users must keep working without action, and so must agents built on older releases.
- No new secret to distribute: a new environment key blocks every VM deployment until each environment repository lists
  it.
- Concurrent first requests of one user, in different processes, must still arrive at the same key, so that the existing
  race handling holds without a store.
- A LiteLLM upgrade that breaks the key lookup must fail loudly instead of quietly locking users out.

## Decision

**The key is an HMAC of the user id, keyed by the master key:** `"sk-" + HMAC-SHA256(master key, label + user id)`, all
64 hex characters. Only holders of the master key can compute it, and they can already create a key for any user, so no
component gains anything. The key stays deterministic, so provisioning needs no store and keeps its race handling.

**Each key names its generation.** An 8-hex HMAC of a fixed label under the master key goes into the key's alias
(`… - Auto Generated Key <generation>`) and its metadata (`swiss_ai_hub_key_generation`). It reveals nothing about the
master key or the keys. LiteLLM requires unique aliases and the old key keeps the old one, so the new key needs its own.
A new master key derives a new key for every user under a new generation.

**Old keys stay valid.** Keys created before, whose alias ends in `- Auto Generated Key`, are neither deleted nor
blocked, so agents on older releases keep working. Deleting them would not even hold: an older release finds its key
missing and creates it again. Blocking would break those agents until they upgrade.

**LiteLLM has no public route.** The `litellm-api` Traefik router is removed, and all of `litellm.${DOMAIN}` goes
through `oauth2proxy-litellm`. The Hub's services call `http://litellm:4000` inside the Docker network, and external
clients use the Hub's OpenAI-compatible API, which applies the Hub's access rules and limits. This reverses the part of
PR #2262 that kept the inference routes public. With the old keys still valid, it is what keeps them out of reach from
the internet. Inside the network, the code sandbox and the browser have no path to `litellm`, and most containers that
do already hold the master key.

**Keys are looked up in the request body:** `POST /v2/key/info {"keys": [key]}` replaces `GET /key/info?key=`. LiteLLM
hashes the key itself and searches live keys only, so a deleted key is not found and a blocked one is. The endpoint is
admin-only and not in LiteLLM's published schema. Any answer other than success raises, and the live test
`test_user_key_provisioning.py` in `packages/core` joins the LiteLLM upgrade checks in `infra/deployment/CLAUDE.md`.

**Spans carry no query strings.** The request hooks for `requests`, `httpx` and `aiohttp` drop the query string from the
span name and `http.url`, for any caller that puts a secret into a URL.

## Consequences

### Positive

- A user's new key cannot be computed without the master key, and two master keys give two different keys for one user.
- No request from the Hub to LiteLLM carries a key in its URL, and no span records a query string.
- No new configuration: deployments upgrade without touching their environment.
- A LiteLLM key can no longer be used from the internet to skip the Hub's access rules.

### Trade-offs

- **Old keys stay valid and can still be computed from the user id.** They work only inside the Docker network. Removing
  them is left for when no agent on an older release remains; blocking rather than deleting them then keeps older
  releases from creating them again.
- **Each active user gets a second key in LiteLLM.** Budgets and rate limits are per user, so they are unaffected; the
  per-key spend splits between the two.
- **A new master key gives every user a new key** and leaves the previous generation valid until it is removed.
- **Every holder of the master key can compute every user's key.** The holders are listed on the authentication page of
  the security documentation.
- **The lookup depends on an endpoint outside LiteLLM's published schema.** The upgrade check catches a change before
  release.
- **Clients that used hand-made LiteLLM keys on `litellm.${DOMAIN}` lose access** and move to the Hub's
  OpenAI-compatible API, or call LiteLLM from inside the Docker network.
- **Deployments on older releases keep the public route until they upgrade.** Closing it is a Docker Compose change only
  (removing the `litellm-api` labels), which operators can apply without upgrading.

## Related Decisions

- `2026_08_06_per_user_litellm_key_as_cost_attribution_carrier.md` — the per-user key this decision changes.
- `2026_10_22_litellm_follows_plain_release_tags.md` — the LiteLLM upgrade checks the key lookup test joins.
- The LiteLLM MCP gateway spike (#2116) asks which identity binds a stored per-user MCP credential. A key changes with
  the master key and older generations remain, so the LiteLLM user is the stable identity, not the key.
