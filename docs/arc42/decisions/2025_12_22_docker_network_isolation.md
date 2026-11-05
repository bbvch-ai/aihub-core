# Adopt Docker Network Isolation Strategy

## Context

The Swiss AI Hub platform runs all Docker containers within a single default network. This flat network topology
presents security risks: if any container is compromised, an attacker gains network-level access to all other
containers, including databases and storage systems. Defense in depth requires network segmentation to limit blast
radius.

## Decision Drivers

- **Security by design**: Limit network access to only what each service requires
- **Defense in depth**: Contain breaches by segmenting network zones
- **Operational simplicity**: Balance security with maintainability

## Decision

We implement Docker network isolation using five distinct networks:

| Network   | Internal | ICC | Purpose                                    |
| --------- | -------- | --- | ------------------------------------------ |
| `proxy`   | No       | Yes | External traffic via Traefik (ingress)     |
| `backend` | Yes      | Yes | Internal application services              |
| `data`    | Yes      | Yes | Databases, caches, message broker          |
| `storage` | Yes      | Yes | SeaweedFS distributed storage              |
| `egress`  | No       | No  | Outbound internet access only (no ingress) |

Services are assigned to only the networks they require. The `internal: true` flag prevents direct external access. The
`egress` network has ICC (Inter-Container Communication) disabled, ensuring containers can only reach the internet but
not each other via this network.

**Example assignments:**

- `traefik`: proxy, backend
- `api`: proxy, backend, data, storage
- `postgres`: data
- `seaweedfs-*`: storage
- `playwright`: backend, egress (needs outbound internet for web browsing)

## Consequences

### Positive

- Network-level isolation prevents lateral movement in case of breach
- Docker enforces boundaries automatically with no performance impact
- Network assignments document service dependencies

### Negative

- Each service needs explicit network assignments
- Network issues may be harder to diagnose
- Must update assignments when adding new services

## Amendment 2026-10-20: a `browser` zone for Playwright

Playwright now reads pages users link (ADR `2026_10_20_agents_read_linked_web_pages_through_playwright`). Its agents'
URL guard cannot close DNS rebinding, because the browser resolves the name again, so Playwright no longer shares
`backend`. It sits in an internal `browser` zone with only its callers (`open-webui` and the agents that fetch pages)
and keeps `egress` for the internet: `playwright` is now on browser, egress. A new agent that fetches pages adds
`browser` to its networks.

## Amendment 2026-10-29: Playwright leaves `egress` for `browser-proxy`

`playwright` is now on `browser` only. Its one way out is `browser-proxy` (Squid), on `browser` and `egress`, which
refuses every destination whose address is not public (ADR
`2026_10_29_browser_reaches_the_internet_only_through_a_filtering_proxy`). Through `egress` the browser reached the
Docker host, the customer's network and cloud metadata, and a URL check in the agents could not stop a name resolving
there. `egress` keeps its rule: only a container that talks to the outside world itself joins it.
