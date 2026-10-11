# Attached Files' Sections and Embeddings Cached by Content

## Context

Chat clients send every file of the current message branch on every turn, and agents read an attached file again each
time it is asked about. Each read downloaded the file, looked up its parse, split it into sections and, for a file
larger than the room it is given, embedded every section and reranked a shortlist. LiteLLM caches embeddings per input
in Valkey for 24 hours, which spared the provider but not the download, the split and one round trip per batch.

Measured in a local end-to-end run (Universal Agent, 2026-10-11): a ranked PDF read took about 2.8 s per turn even with
every embedding a LiteLLM cache hit. A 60,000-row spreadsheet took about 20 s per read, and embedding all of its
sections at once sent 111 requests to Phoeniqs, which answered 20 of them with 401 and put the model group into cooldown
for every caller (aihub-core-private#325).

## Decision Drivers

- **A repeat read must be cheap**\
  Users ask several questions about the same file; the cost of a question should not grow with the file's size.
- **No new store**\
  Valkey has no `maxmemory`, and an unbounded LiteLLM cache there already stalled the counters routing depends on.
- **Isolation where it matters**\
  An upload's file id must never answer under another agent profile.
- **Never fail a read**\
  The cache serves speed, not correctness.

## Decision

`AttachedFileSectionCache` (agent package) keeps three kinds of entry in the existing `parse-cache` S3 bucket, under
`attached-files/`, expiring with the bucket's 7-day lifecycle:

1. **A record per upload**, keyed by a hash of the upload's agent-scoped location
   (`agent-files/{class}/{id}/{file id}/ {name}`). It holds the content hash, title, page count and whether the document
   can be read by page, so a later read of that upload needs no download and no parse.
2. **The sections**, keyed by a hash of the extracted text and a fingerprint of the chunking settings. Loaded sections
   are re-stamped with the current upload's document id, source, title and fresh node ids, because citations derive from
   the document id.
3. **The embeddings**, keyed by the content hash and the embedding model with its vector width, stored as float32 per
   section index. A ranking embeds at most `max_embedded_chars` of new text and adds it to the entry, so coverage of a
   very large file grows question by question.

Content-addressed entries are **not tenant-scoped**, on the same reasoning as `MineruParseCache` and
`MarkItDownParseCache`: the key can only be derived from the content itself. The per-upload record keeps the agent
scoping of the upload's location. Every read and write is best-effort: storage that cannot be reached is a miss.

## Consequences

- **Faster repeat reads**: a later read of the same upload is two small S3 reads plus ranking. The same content uploaded
  again, in another chat or by another user, costs a download and a parse-cache hit, then reuses sections and
  embeddings.
- **Retention**: extracted text and embeddings of user uploads stay in `parse-cache` for up to 7 days. The parse caches
  already keep the same text there.
- **Silent degradation**: missing S3 permissions disable the cache without an error. The `AttachedFileSectionCache.get`
  span carries a hit attribute to check after a deployment.
- **Invalidation**: a change to the chunking settings or the entry format changes the fingerprint, so old entries are
  simply not found again. A change to the parser's code needs a `FORMAT` bump to renew the sections. Embeddings carry a
  digest of the sections they were computed for and are ignored against any other, so a re-split file never pairs old
  vectors with new text.
- **Lost updates**: two rankings of the same content at once each write the embeddings they know of and the last write
  wins. Nothing is corrupted; the dropped vectors are embedded again when a later question needs them.
