# Knowledge Figures in OpenWebUI Sources Served Through a Session-Checked Proxy

## Context

Ingestion stores every figure of a parsed document next to the document in its knowledge bucket
(`<folder>/__figures__/<file>/figure_<hash>.<ext>`) and indexes it as a figure node whose content is
`![Figure N](s3://bucket/key)`. Retrieval signs that reference for the model, so agents answer with the figure in view.

The OpenWebUI pipe copies the grounding nodes into the sources of the answer. OpenWebUI renders a source's text as
markdown and accepts only relative, same-origin, `data:` and http(s) image URLs (`safeImageUrl`); anything else,
`s3://` included, becomes its fallback logo. Every figure in a source therefore showed the OpenWebUI logo. The Hub's own
knowledge pages are not affected: they resolve `s3://` references with the viewer's token on every render.

Who may see a source's text is decided once, when the agent answers: the user may use the agent, and the agent
retrieves from the collections of its profile, narrowed to what the user may read only when the profile restricts
retrieval to the user's access. Profiles stored before that switch existed have it off. The text then stays in the
OpenWebUI chat, visible to everyone who can open that chat.

## Decision Drivers

- **A figure is visible exactly when its text is**\
  A user who can read a chunk's text in a source should see that chunk's figure, and nobody else. A namespace check
  diverges from this for every profile that does not restrict retrieval to the user's access.
- **A copied URL must not work on its own**\
  The URL in the chat may only show the figure to a signed-in user who is entitled to it, as cited files work in
  Microsoft 365 Copilot and Glean.
- **No expiry, no copies**\
  A figure must still show in a chat opened months later, without a copy per answer that nothing ever cleans up.
- **No new trust root**\
  The API already holds OpenWebUI's signing secret and trusts the user headers the pipe signs. Whatever identifies the
  viewer must stay within that trust.

## Decision

Figures are served by a same-origin proxy on the OpenWebUI host, and the right to see one is derived from the thread
the agent put it in.

- **URL.** The pipe rewrites each figure reference in a knowledge source to
  `/hub-figures/<tenant>/<thread_id>/<bucket>/<key>`. The path is relative, so OpenWebUI renders it, and the browser
  sends the OpenWebUI session cookie with the request. Traefik (and the k8s ingress) route `/hub-figures` on the
  OpenWebUI host to the API's figure route. The URL holds no secret.
- **Identity.** A dedicated auth handler takes the OpenWebUI session cookie, verifies its signature and expiry locally
  with the OpenWebUI secret the API already holds (so a forged cookie costs nothing), then asks OpenWebUI's own session
  endpoint whose it is, so OpenWebUI's sign-out applies. It builds the Hub identity in the tenant named in the path from
  the user's e-mail, as the signed-header handler does, refuses disabled Keycloak users and never grants sysadmin
  rights. Lookups are cached by the token's hash for a minute; the cookie is never logged.
- **Only OpenWebUI's own pages.** The route requires `Sec-Fetch-Site: same-origin` and a `Sec-Fetch-Dest` of
  `image` (the source shows it) or `document` (the user opens it in a new tab), headers browsers set themselves. The
  API allows credentialed CORS from every host of the domain, and this is its only route authenticated by an ambient
  cookie, so script on another host of the same site must not be able to read a figure; a script's request is never
  an image or a document. A URL pasted into the address bar is not same-origin and is refused as well.
- **Access, checked on every load.** The viewer may view the thread (the rule of the thread endpoints); the figure
  appears in a grounding result the agent sent to that thread, read from the events the platform already persists; and
  the viewer may still use the agent that sent it. A figure node's text comes from the document, and a markdown file
  can hold any `<figure>` reference, so a reference only counts when it lies in the figure folder of the node's own
  document. Without that, one uploaded file could make the route read figures of any bucket. The `active` tenant alias
  is refused. Results are cached per user, tenant, thread and figure for a few minutes.
- **Response.** Only figures under the `__figures__` folder are served. The object's size is checked before it is
  downloaded and its pixel count before it is decoded, a few decodes run at a time, and it is re-encoded as JPEG or PNG,
  served with `nosniff`, a `default-src 'none'; sandbox` CSP, `Cross-Origin-Resource-Policy: same-origin` and a
  private, short-lived cache. SVG and other formats are refused, and the source shows a text caption instead.
- **Routing.** The Traefik rule accepts only a tenant id, a 24-character thread id and a valid bucket name before the
  key, so no path can be steered into another API route.

Rejected:

- **Presigned S3 URLs in the chat**: they expire, and anyone holding one sees the figure until then.
- **`data:` URIs**: the figure travels with the chat and is never checked again.
- **Copies in OpenWebUI's file store**: one copy per answer, access by file owner, and nothing removes them when a chat
  is deleted.
- **A namespace check**: users of profiles without the user-access restriction would see the text and not the figure.

## Consequences

### Positive

- Figures show in every source whose text the viewer can read, also in old chats and for old knowledge databases,
  without re-ingestion.
- Opening a figure URL without an OpenWebUI session, or as someone who may not view the thread or use its agent, shows
  nothing. Losing either right hides the figure in existing chats.
- Nothing is copied or stored per answer, and no URL in a chat ever expires.

### Trade-offs

- The API now accepts OpenWebUI's session as identity on one route. Its correctness rests on OpenWebUI's session
  endpoint and cookie name, which an OpenWebUI upgrade must keep or the figures stop loading (they fail closed).
- Every figure load costs a session lookup, a thread and event read, an S3 read and a re-encode, all off the API's event
  loop and cached; the first load of a long thread is the slowest.
- Figures disappear with the thread's persisted events, so enabling event retention removes the figures of pruned
  threads.
- Viewers of a shared OpenWebUI chat who are not members of the thread see the text but not the figure.
- The route exists only where `/hub-figures` is routed: compose stages with Traefik and k8s deployments with the
  matching ingress rule, not the `dev` stage.
- Text in old chats remains a snapshot; only figures are checked again.
