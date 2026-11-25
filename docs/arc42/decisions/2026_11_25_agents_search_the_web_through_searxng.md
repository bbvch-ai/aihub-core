# Agents Search the Web Through the Platform's SearXNG

## Context

Open WebUI offers a "Web Search" toggle in every chat. For plain models it runs Open WebUI's own search against the
platform's SearXNG. For agents, the feature filter (ADR `2026_09_28_openwebui_toggles_as_requests_to_agents`) removes
the toggle from the request and forwards it to the agent, but no agent served it, so no agent showed the toggle. Issue
#1568 asks agents to search the web themselves: answer from the results, cite them, and show the search the way Open
WebUI shows its own, while the search stays a traced, cost-attributed step of the run instead of Open WebUI's own call,
which bypasses the platform.

A search is a request from inside the platform carrying words from the conversation to search engines outside it. The
model writes the queries, so an instruction hidden in a page or a file could steer what is searched for.

## Decision Drivers

- **Every search is ours to trace.** The queries and the results an answer rests on show in the event history and the
  agent trace.
- **Any client gets the same UI from the events.** Our frontend and the Open WebUI pipe render protocol events; neither
  holds search logic.
- **Off unless an admin turns it on, and only when the user asks.** A profile enables web search; the user's toggle
  allows it for one message.
- **No toggle that does nothing.** A profile with web search off shows no Web Search toggle.
- **No new service.** Reuse the SearXNG instance and the guarded browser path the platform already runs.

## Decision

### A web search capability with its own protocol events

`WebSearch` is a capability (ADR `2026_09_28_capabilities_and_the_conversational_spine`) with one call: `SearchWebEvent`
→ `WebSearchedEvent`. Both are `ControlAndDisplayEvent`s, so a run's history shows every search; the result is a
semantic event, so Langfuse shows it as a retrieval with the queries as input and the hits as its documents.
`WebSearchedEvent` carries the hits (`results`, what a client lists as the sites searched), the nodes the model reads
(`grounding_nodes`, what a client lists as sources), the context block, and the pages that could not be read.

The capability declares `chat_feature = WEB_SEARCH`. The Universal Agent offers it as the `search_web` tool, so the
model searches when it decides a question needs it; the tool loop withholds the tool while the toggle is off. The search
step checks the toggle itself too, so a blueprint calling `WebSearch.search(...)` directly cannot search for a message
whose user did not ask. Fixed-flow blueprints and a dedicated web search blueprint are a follow-up.

### SearXNG, plus the best hits read whole

`SearxngClient` (core) asks SearXNG's JSON API, one request per query (at most three per call). The hits of all queries
are taken in turns and each site is kept once, up to the profile's `max_results`. The best `read_top_results` are read
whole through `WebPageFetcher`, the Playwright path web fetch uses (ADR
`2026_10_20_agents_read_linked_web_pages_through_playwright`), so every page load passes `RequestGuard` and
`browser-proxy`. The other hits, and a page that cannot be read, reach the model as the engine's snippet, marked as one.
Each hit is one node whose id comes from its URL, as a fetched page's does, so it is cited like retrieved knowledge.

A profile's `web_search` section is nullable (ADR `2026_05_07_nullable_form_fields_over_enabled_toggle`), `null` for
stored and new profiles. It sets the result count, how many are read whole, the engines (any of those `settings.yml`
runs; none means all), language, safe search, time range and the page limits.

### Toggles that follow the profile

A capability may name the config field that switches its feature off (`chat_feature_config_field`). Discovery publishes
these per blueprint (`feature_config_fields`), and both the API's model sync and the OpenWebUI provisioner offer a
profile only the supported features whose field is set (`AgentClassEntity.features_offered_by`). The sync hash includes
each profile's features, so saving a profile with web search switched off removes its toggle at the next discovery
round. Features without such a field are offered by every profile, as before.

### Open WebUI's own search display

The pipe maps `SearchWebEvent` to a `web_search_queries_generated` status (the query chips) and `WebSearchedEvent` to a
`web_search` status with `items` ("Searched N sites" and the clickable list) plus one source per node, so citations
number as for knowledge. Any agent emitting the events gets this without a pipe change.

## Consequences

- **Queries leave the platform.** The engines see the queries the model wrote, without the user's identity. The toggle
  is the user's consent per message; no PII filtering applies to queries.
- **Favicons.** Open WebUI's result list loads each site's favicon from Google's favicon service in the user's browser,
  as it does for Open WebUI's own search.
- **Turn length.** A search waits for SearXNG's slowest engine and for the pages read whole; `read_top_results: 0`
  answers from snippets alone.
- **SearXNG has two clients.** It stays on the `backend` network, which every agent already joins; only the Universal
  Agent receives `SEARXNG_BASE_URL` today.
- **Follow-up:** web search on the fixed-flow blueprints (a query written from the conversation, gated on the toggle)
  and a dedicated Web Search Assistant.
