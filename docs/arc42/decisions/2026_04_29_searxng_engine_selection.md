# SearXNG engine selection: privacy and Swiss/European focus

## Context

Swiss AI-Hub replaced Jina (a paid US-hosted API) with a self-hosted [SearXNG](https://docs.searxng.org/) meta-search
aggregator as the default web search backend for Open-WebUI. SearXNG forwards each query to a configurable set of
upstream engines (~330 engine modules ship with the image, ~70 enabled by default) and merges their results.

The default engine list optimises for result coverage at the cost of two trade-offs that matter to a platform marketed
on data sovereignty:

- **Egress surface**: every search fans out to dozens of upstream providers, most of them Big Tech US services. The set
  is undocumented from the customer's perspective and changes silently when the SearXNG image is upgraded.
- **Result quality variance**: many of the default engines (Yandex, Baidu, niche file-search backends, US-only news
  sites) are irrelevant to a Swiss/European audience and pollute the merged results.

We need an explicit, audited engine list that we can document in the network requirements and defend in compliance
reviews.

## Decision Drivers

- *Privacy alignment with Swiss AI-Hub's data-sovereignty positioning* — outbound traffic should be predictable and lean
  toward providers that publicly commit to no tracking.
- *European/Swiss preference where it does not hurt result quality* — given comparable engines, prefer
  EU/UK/Swiss-jurisdiction providers over US-jurisdiction ones.
- *Index diversity over upstream redundancy* — combining engines that all proxy the same upstream (e.g., DuckDuckGo and
  Bing both surface Bing results) wastes the meta-search benefit. Prefer engines with genuinely independent indexes.
- *Documented and stable egress* — the network requirements page must list a fixed set of outbound hostnames; an
  explicit `keep_only` list pins this.
- *No hard regression in result quality* — losing direct access to Google and Bing must be compensated by engines that
  proxy or substitute their coverage.

## Decision

Configure `infra/configs/searxng/settings.yml` with `use_default_settings.engines.keep_only` enumerating exactly eight
engines:

| Engine     | Jurisdiction | Role                                                  |
| ---------- | ------------ | ----------------------------------------------------- |
| Brave      | US           | Independent crawler/index, no tracking                |
| DuckDuckGo | US           | Mature no-tracking; proxies Bing for breadth          |
| Mojeek     | UK           | Truly-independent index (not proxying Google or Bing) |
| Qwant      | France/EU    | EU-jurisdiction, GDPR-native                          |
| Startpage  | Netherlands  | Anonymized Google results (Google quality, no Google) |
| Wikidata   | non-profit   | Structured knowledge graph                            |
| Wikipedia  | non-profit   | Encyclopedic lookup                                   |

**Explicitly excluded engines** (and the reason):

- *Google, Bing* — worst privacy posture among the candidates, US-jurisdiction Big Tech. Result coverage is preserved
  indirectly: Startpage proxies Google with tracking stripped, DuckDuckGo proxies Bing.
- *Yandex* — Russian-jurisdiction; problematic in EU compliance and geopolitical contexts.
- *Baidu, 360search* — Chinese-jurisdiction, censored, irrelevant audience.
- *All specialised category engines* (images, videos, news subengines, code search, file search, etc.) — Open-WebUI's
  web search feature only consumes general-category results; the specialised engines add egress with no consumer.

**Engines we considered but cannot use** today:

- *Marginalia* (🇸🇪) — Swedish indie crawler, would have been an excellent fit for long-form/technical content. The
  upstream SearXNG engine module is `disabled-by-default` and requires a per-deployment API key obtained via
  https://about.marginalia-search.com/article/api/. Re-evaluate once we provision an API-key flow.
- *Swisscows* (🇨🇭) — would have been the most natural fit; no SearXNG engine module exists.
- *Ecosia* (🇩🇪) — proxies Bing without offering value over our existing Bing-derived coverage; no native SearXNG module
  either.
- *Kagi* — paid commercial service, no SearXNG module.

## Consequences

- *Predictable, auditable egress*: the seven engine hostnames are documented in
  `docs/docs/2_platform/3_deployment_guide/7_network_requirements/`. Customers reviewing outbound firewall rules see a
  stable set rather than ~70 silently-changing defaults.
- *Stronger privacy posture*: removing Google and Bing direct, combined with retaining Startpage (anonymising proxy) and
  DuckDuckGo (no-tracking), preserves coverage while eliminating the two largest tracking touchpoints.
- *Slight loss of fringe-query coverage*: queries that previously matched Yandex or Baidu (e.g.,
  Russian/Chinese-language sources) will return fewer results. Acceptable for a Swiss/EU-targeted platform.
- *Maintenance overhead*: the engine list is now a project artefact that must be reviewed when SearXNG is upgraded. The
  pinned image tag (`infra/deployment/compose-config.yml`) makes this an intentional bump rather than a silent drift.
- *Image-search and news-search are intentionally absent*: Open-WebUI does not currently expose category-aware search to
  end-users. If that changes, the engine list must be revisited (e.g., add `qwant images`, `wikipedia images`, or
  news-category engines from the same providers).
- *Swisscows-shaped gap*: a future Swiss-specific engine (Swisscows or other) added to SearXNG upstream should be
  evaluated for inclusion; this ADR should be revisited at that point.
