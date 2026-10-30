# The Browser Reaches the Internet Only Through a Filtering Proxy

## Context

ADR `2026_10_20_agents_read_linked_web_pages_through_playwright` lets agents read the pages a user links. Its URL guard
(`UrlSafetyPolicy`) resolved every host in the agent and refused names leading to a non-public address; Playwright sat
on the internal `browser` zone and on `egress`.

On staging, every link failed as "the page does not exist". The fetching agents are on internal networks only
(`backend`, `data`, `storage`, `browser`), and Docker gives a container without a non-internal network no outside DNS.
The guard's lookup failed and was reported, failing closed, as not found. Dev never showed it: there the agents run on
the host, and the template makes no network internal. Reproduced on Docker 29.3.1: `getaddrinfo("en.wikipedia.org")` in
a container on an internal network only gives `Temporary failure in name resolution`, and resolves once the container
also joins `egress`.

The lookup was also weaker than it looked. The agent resolved the name and the Playwright server resolved it again, so a
name answering with a public address first and a private one second (DNS rebinding) passed. The `browser` zone keeps a
page away from the platform's containers, but through `egress` the browser still reached the Docker host, the customer's
network and the cloud metadata service (`169.254.169.254`). The guard was the only thing in front of those, and
rebinding got past it.

## Decision Drivers

- **Fix the feature on every compose deployment**, without giving agents an internet connection to look up names.
- **Judge the address the connection is made to.** A check that resolves the name separately from the connection can be
  raced; only the component that connects can close that.
- **Fail closed.** If the filtering component is down or misconfigured, nothing must load.
- **Follow the platform's network pattern.** A container that talks to the outside world has `egress`; its callers reach
  it by service name on internal networks.
- **Nothing for Open WebUI to change.** Its web loader uses the same Playwright server.
- **Small and well known.** One container with a few lines of configuration, a component customers' IT departments
  recognise.

## Decision

### `browser-proxy`: Playwright's only way out

Playwright loses `egress` and keeps only `browser`. A new service, `browser-proxy` (Squid 7.6 on Alpine 3.23, the
project-managed image `browser-proxy:7.6-1` built from `infra/deployment/docker/browser-proxy/`), sits on `browser` and
`egress`. The fetching agents open their browser context with `proxy={"server": PLAYWRIGHT_PROXY_URL}`
(`http://browser-proxy:3128`, a template constant like `PLAYWRIGHT_WS_URL`; no `.env` key). The Playwright server
connects to the proxy, so the name resolves on the `browser` network in every stage, dev included.

Squid resolves each name itself, refuses the request when any of its addresses is not global (`acl not_public dst`, IPv4
and IPv6 ranges), and connects to an address it checked. Nothing else on the browser's side can reach the internet:
without the proxy, every request fails.

Three configuration choices were forced by the prototype (Playwright 1.63 against Squid 6.12), and hold unchanged on
Squid 7.6:

- **`CONNECT` is allowed to every safe port, not only 443.** `route.fetch`, which the request guard uses for every
  request, tunnels plain `http://` through the proxy with `CONNECT` as well. With Squid's default, every `http://` link
  was refused.
- **Error pages are empty.** On a refused `CONNECT`, Playwright's proxy client replays only what it read together with
  the headers. When the body arrived in a separate packet, about half the refusals surfaced as `Route.fetch: aborted`
  instead of a 403. With empty bodies, 26 of 26 refusals arrived as `403` with `X-Squid-Error: ERR_ACCESS_DENIED`.
- **IPv4-mapped IPv6 is not in the ACL.** Squid stores IPv4 addresses in that form, so `::ffff:0:0/96` would match all
  of IPv4; the IPv4 ranges cover it. `::/128` parses as any address, so the unspecified and loopback addresses are
  written `::/127`.

Squid's cache-manager page is refused to everyone (`http_access deny manager`): the proxy is reachable from every
container on `browser`. Sites see neither the platform's addresses nor the proxy (`forwarded_for delete`, `via off`).
The access log, on stdout, records the host and port of each request (never the path, since every request is a tunnel),
so refused attempts are visible in the container log.

### The agent no longer resolves names

`UrlSafetyPolicy` keeps only what the URL itself shows: schemes, internal names (`localhost`, names without a dot, the
`.local`/`.internal`/`.localhost`/`.home.arpa` suffixes), non-global IP literals including NAT64 and 6to4, and URLs
Python and the browser could read as different hosts. Those are refused before any request, with a clear reason. A name
is left to the proxy. The check is synchronous and stateless (`UrlSafetyPolicy.check(url)`).

`RequestGuard` reads the proxy's answer: `X-Squid-Error: ERR_ACCESS_DENIED` is reported as a blocked host and
`ERR_DNS_FAIL` as not found, so the proxy's 403 never reads as the site denying access.

### Open WebUI is unchanged

Open WebUI's `SafePlaywrightURLLoader` routes every request of the page and performs it itself, from `open-webui`, with
an address check at connection time, then hands the response to the browser. It never uses Playwright's own network, so
it needs no proxy.

## Alternatives Considered

- **Give the fetching agents `egress`.** Fixes the lookup in an hour, and adds little exposure on its own, since an
  agent can already browse anywhere through Playwright. But the race between the agent's lookup and the browser's
  remains, and the host, the customer's network and cloud metadata stay one rebinding away.
- **Drop the lookup and rely on the `browser` zone.** No compose change, but a public name pointing at a private address
  (`169.254.169.254.nip.io`) would be fetched from inside the deployment.
- **A DNS forwarder for the agents.** A new container that answers lookups only. It still leaves the race open, so it is
  as weak as giving agents `egress`, with more to run.
- **Host firewall rules (DOCKER-USER) refusing private ranges for Playwright.** Closes the race without a container, but
  lives outside this repository (the playbook), needs a fixed subnet, and where the rules are missing, nothing is
  blocked.
- **Smokescreen instead of Squid.** Built for exactly this, with private ranges denied by default, but it is not an
  Alpine package, so we would build it from its Go sources and maintain that. Squid is one (`squid-7.6-r0`, pinned in
  the Dockerfile), its `dst` ACL does the same job, and it is widely known.
- **Squid 6.12 on Alpine 3.22.** The first image used it. Upstream fixes only 7.x now, and 6.12 has 11 published
  advisories. None applies to this configuration (no ICP, HTCP, SNMP, ESI, `cache_peer`, ICAP or FTP, empty error
  pages, and every request a `CONNECT` tunnel), but the next one might not need any of those.

## Consequences

### Positive

- Web fetch works on every compose deployment: the agents need no outside DNS.
- The address is judged where the connection is made, so rebinding, a name pointing at a private address, the Docker
  host, the customer's network and cloud metadata are all refused, for the browser and every request a page makes. In
  the prototype, a private canary server received no request across nip.io names, a name with a public and a private
  address, and repeated rebinding attempts.
- It fails closed: with the proxy stopped, or its name gone, nothing loads.
- `playwright` is now on one internal network only, like `open-terminal` and `presidio-analyzer`.

### Negative

- **One more container and project-managed image.** `make -C infra/deployment build-and-push-browser-proxy-image`
  publishes it; it must be in ghcr before a stage pulls it.
- **A proxy outage looks like unreadable pages**, reported per link as an error or a timeout, not as a platform fault.
  The healthcheck and `restart: always` cover it operationally.
- **Hosts visited end up in the logs.** The access log lists the host and port of every request the browser makes, and
  the playbook's collector ships container output. `access_log none` turns it off.
- **Dev does not prove the isolation.** Dev networks are not internal, so Playwright still has a direct route out there
  (the guard sends every request through the proxy regardless). The `local` stage is where the isolation is verified.
- **k8s is not covered yet.** The Helm chart (aihub-k8s) needs the same: the proxy, or a NetworkPolicy refusing private
  ranges for the Playwright pod.
- **Any new client of the Playwright server** must either pass the proxy, like the agents, or fetch requests itself,
  like Open WebUI; otherwise it reads nothing.
