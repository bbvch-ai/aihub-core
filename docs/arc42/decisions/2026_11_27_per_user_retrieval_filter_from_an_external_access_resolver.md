# Per-User Retrieval Filter from an External Access Resolver

## Context

Some organizations keep document permissions in a system of their own, a data hub or a document management system, and
often their SharePoint permissions are not set properly in the first place. They want the AI Hub to answer each person
only from the documents that system allows, without copying its permissions into AI Hub roles and without embedding a
document once per group.

What the platform had:

- `restrict_to_user_access` narrows retrieval to the **namespaces** a user may read, so permissions are per collection,
  not per document.
- `RAGStartEvent.additional_filters` and `MetadataFilterPair` filter by **equality** (or "contains" for list values) on
  values a publisher sets, never by user.
- Chat clients forward no user token to agents (OpenWebUI sends the platform's own bearer), so an agent cannot hand a
  verifiable user credential to a third system.

The first consumer is the Swiss LCDM Hub, which keeps who may see what in role data filters on adaptor knowledge codes
and writes every document into the AI Hub knowledge with its code in the frontmatter (`lcdm_knowledge_code`).

## Decision Drivers

- **One authority**\
  The external system decides. The AI Hub keeps no copy of its permissions, so a change there takes effect on the next
  question, without re-embedding.
- **Off by default**\
  Deployments without such a system keep today's behaviour, and no request goes out.
- **Never open on doubt**\
  A missing user, a slow or failing resolver, an unreadable answer must end in no access, never in an unfiltered search.
- **Provider-agnostic**\
  aihub-core must not know the LCDM. The contract is small enough for any system to implement.
- **Same trust model as MCP**\
  Admin-set URLs are guarded against pointing inside the platform, and secrets in profiles are encrypted.

## Decision

`RAGAgentConfig.external_access_filter` (`ExternalAccessFilterConfig | None`, default `None`) lets an agent profile name
an external access resolver. When it is set, `RAGAgent.retrieve_step` asks the resolver which values of one metadata key
the asking user may see and adds `metadata_key IN values` to every retriever of the run.

- **Contract.** `GET <resolver_url>` with `Authorization: Bearer <api_key>` (a `Password` field, encrypted at rest),
  `X-AIHub-User-Email` and `X-AIHub-Tenant` of the run's user, whom the API verified. Answer: `{"values": [...]}`.
- **Filter.** `MetadataFilterPair` accepts a list of texts, translated to `key IN [...]` OR
  `array_contains_any(key, [...])` for Milvus, so scalar and list metadata both match.
- **Deny on doubt.** No user or no e-mail, a resolver error, a timeout, a non-200, a payload without `values`, a URL the
  host guard refuses: the run answers with `InaccessibleKnowledge`. A failure is never cached; an answer is cached per
  resolver URL, tenant and user for `cache_ttl_seconds` (default 60, 0 for none).
- **Host guard.** `PublicHostGuard` checks the URL before every call. Internal hosts need
  `EXTERNAL_ACCESS_FILTER_ALLOWED_PRIVATE_HOSTS`, and redirects are not followed, because a profile editor sets the URL
  and the API key travels with the request.
- **Carried-over sources.** The two grounding nodes a RAG run carries into the next turn of a thread
  (`do_read_carried_grounding_nodes`) are checked against the current answer too
  (`ExternalAccessFilters.still_visible`), so a revoked permission takes effect on the very next turn.
- **Deployment.** `rag_agent` and `expert_rag_agent` get `AIHUB_CONFIG_ENCRYPTION_KEY` (to decrypt the API key) and the
  `egress` network (a resolver usually lives outside the platform).

## Consequences

- **+** Per-document permissions from an existing system, maintained only there, with each document embedded once.
- **+** Existing profiles and deployments are unchanged; the feature costs nothing until a profile switches it on.
- **−** Every question makes one resolver call (or one per TTL). The resolver's latency adds to the answer's.
- **−** The resolver trusts the AI Hub to name the user (API key plus e-mail), as the LCDM trusts its technical user
  with `X-LCDM-On-Behalf-Of`. The e-mail must be unique in the resolver's user model.
- **−** Only the RAG agent family applies it. The knowledge tools of other blueprints (Universal Agent's
  `search_knowledge`, the knowledge document tools) do not, so a profile that needs the filter must use a RAG agent.
- **−** The answer still sees the conversation: a model may repeat what an earlier turn of the same chat showed, and
  user memory may name the titles of documents seen before. Neither retrieves new content.
- **−** Documents without the metadata key are found by no one once the filter is on.

Validated end to end on 2026-11-26/27 with the Swiss LCDM Hub (LCDM tickets 3591 and 3594) on a dev deployment: three
documents with different codes, four permission sets, resolver outage. Every case answered as expected.
