---
title: Web search
description: How Open-WebUI fetches results from the web through the platform's self-hosted SearXNG instance, and how to customise the engine list.
---

# Web search

Open-WebUI's "web search" feature is wired to a self-hosted [SearXNG](https://docs.searxng.org/) meta-search instance
that ships with the platform. SearXNG forwards each query to a curated set of upstream search engines, merges the
results, and returns them to Open-WebUI without ever logging the user's identity to the upstream providers.

This page explains the engine set, why it was chosen, and how to change it.

## Why SearXNG

SearXNG is the privacy-aware search aggregator behind the platform's web-search feature. Compared to a single hosted
search API, it has three advantages that matter to a self-hosted, data-sovereignty-focused deployment:

- **No vendor lock-in.** Search is not bound to a single provider. Engines can be swapped without code changes.
- **No per-query cost.** SearXNG is open source and self-hosted; there is no metered API key that needs renewal.
- **Auditable egress.** The set of upstream engines is enumerated in configuration, so the outbound network surface is
  reviewable and stable.

## Active engine set

The platform ships with seven engines enabled in `infra/configs/searxng/settings.yml`. The list is privacy-first with a
Swiss/European lean, biased toward truly independent indexes:

| Engine     | Jurisdiction | Role                                                        |
| ---------- | ------------ | ----------------------------------------------------------- |
| Brave      | US           | Independent crawler/index, no tracking                      |
| DuckDuckGo | US           | Mature no-tracking policy; proxies Bing for breadth         |
| Mojeek     | UK           | Truly-independent crawler (not proxying Google or Bing)     |
| Qwant      | France/EU    | EU-jurisdiction, GDPR-native                                |
| Startpage  | Netherlands  | Anonymized Google results (Google quality without tracking) |
| Wikidata   | non-profit   | Structured knowledge graph                                  |
| Wikipedia  | non-profit   | Encyclopedic lookup                                         |

The corresponding outbound hostnames are documented in [Network requirements](../7_network_requirements/) so operators
can configure egress firewall rules.

## Engines that are not enabled

A few engines are intentionally absent from the default set, even though SearXNG supports them:

- **Google, Bing.** Direct access to Google and Bing trades meaningful privacy for marginal coverage. Coverage is
  preserved indirectly: Startpage proxies Google with tracking stripped, and DuckDuckGo proxies Bing.
- **Yandex, Baidu, 360search.** Russian and Chinese-jurisdiction engines are out of scope for a Swiss/EU-focused
  platform and raise compliance and censorship concerns.
- **Specialised category engines** (images, videos, news subengines, code search, file search). Open-WebUI's web-search
  feature only consumes general-category results today, so specialised engines would add egress with no benefit.

A few engines we would have liked to include cannot be enabled today:

- **Marginalia** (🇸🇪) — Swedish indie crawler with strong long-form content coverage. Disabled by default upstream and
  requires a per-deployment API key (see <https://about.marginalia-search.com/article/api/>).
- **Swisscows** (🇨🇭) — privacy-focused Swiss search; no SearXNG engine module exists.
- **Ecosia** (🇩🇪) — proxies Bing, no native SearXNG module.
- **Kagi** — paid commercial service, no SearXNG module.

## Customising the engine list

The active engines are controlled by the `keep_only` list in `infra/configs/searxng/settings.yml`:

```yaml
use_default_settings:
  engines:
    keep_only:
      - brave
      - duckduckgo
      - mojeek
      - qwant
      - startpage
      - wikidata
      - wikipedia
```

To add an engine, append its name to `keep_only`, regenerate the compose files (`make generate-compose`), and restart
the SearXNG container
(`docker compose -f infra/docker-compose.dev.yml --env-file .env up -d --no-deps --force-recreate searxng`). The full
upstream engine catalogue is in `/usr/local/searxng/searx/settings.yml` inside the container — running
`docker exec searxng grep "name:" /usr/local/searxng/searx/settings.yml` lists everything available.

::: warning
Some engines (Marginalia, several specialised ones) are flagged `disabled: true` upstream and require additional
configuration such as API keys. Adding them to `keep_only` alone will not enable them.
:::

::: tip
Whenever you change the engine list, update the [Network requirements](../7_network_requirements/) page so operators see
the new outbound hostnames.
:::

## Disabling web search entirely

To remove web search from the platform, set `ENABLE_WEB_SEARCH: False` in the Open-WebUI environment block in
`infra/deployment/templates/docker-compose.yml.j2`, regenerate the compose files, and recreate Open-WebUI. The `searxng`
service can then also be removed from the template if no longer needed; this drops all web-search-related outbound
network requirements.
