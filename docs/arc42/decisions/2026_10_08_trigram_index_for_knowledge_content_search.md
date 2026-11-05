# Trigram Index for the Knowledge Content Search

## Context

The content search (`KnowledgeContentSearch`, #1024) finds every knowledge document whose parsed text contains a term or
matches a regex. It scans: FerretDB evaluates `$regex` on every row of the knowledge database's `documents-data`
collection. That costs about 1–1.5 s per 500 MB of text on lz4 rows and grows linearly with the corpus, against a 5 s
budget per call.

FerretDB stores each collection as a DocumentDB table, `documentdb_data.documents_<collection_id>`, with the document as
one BSON column. It translates `$regex` into an operator on the whole document, so no PostgreSQL index can serve it.
Measured on dev, a `pg_trgm` GIN index over `documentdb_core.bson_get_value_text(document, '__data__.text')`:

| Measure                                | Result                                                               |
| -------------------------------------- | -------------------------------------------------------------------- |
| Size on real text (books, parsed PDFs) | 7–9% of the text                                                     |
| Online build (`CONCURRENTLY`)          | about 1 minute per 500 MB; reads unchanged, writes wait up to 200 ms |
| Rare term, 5,000 × 100k characters     | 12–19 ms, against 0.9–1.4 s for the scan                             |
| Common term, or common words in phrase | no gain: PostgreSQL rechecks most rows, slower than the scan         |

Reading a range of a large document had the same shape of problem: the reader loaded the whole text, and the
`text_resource` copy with it, to return a few thousand characters.

## Decision Drivers

- **Same results on every path**\
  An agent paging through results must get the same documents, totals and lines whether or not an index served them.
- **No second copy of the text**\
  A side table would need to be kept in sync with every write FerretDB makes.
- **Upgrades must not break search silently**\
  The index depends on the output of an internal DocumentDB function.
- **Least privilege**\
  Agents get no more database access than the search needs.
- **No worse than today**\
  A query the index cannot help must still be answered by the scan within the budget.

## Decision

1. **An expression index on each knowledge table.** `ferretdb_text_index_job` in the backup Dagster instance creates
   `aihub_text_trgm_<collection_id>` with `CREATE INDEX CONCURRENTLY`, runs daily at 5 AM, and drops and rebuilds an
   interrupted (invalid) build. `ferretdb_text_index_rebuild_job` rebuilds every index by hand, which only reclaims
   space.
2. **Only literal searches use it.** A regex keeps the scan. A literal becomes `ILIKE '%term%'` (`LIKE` when case
   matters) in its composed and decomposed spelling, with `%`, `_` and `\` escaped. A query needs three word characters
   in a row for a trigram; otherwise it scans.
3. **The index narrows, FerretDB decides.** The index returns candidate ids through a read-only SQL role. The search
   then runs today's FerretDB filter restricted to `_id $in` those ids, so regex semantics, namespace, pending and
   placeholder rules and `_id` ordering are exactly the scan's. The index only has to return a superset.
4. **Case folding.** PCRE2's caseless matching treats 22 groups of letters as one that PostgreSQL's `lower()` does not
   (`µ`/`μ`, `σ`/`ς`, `s`/`ſ`, Greek symbol variants, old Cyrillic forms). In a caseless query those letters become the
   `_` wildcard, except `s`, `S`, `i` and `I`.
5. **Bounded.** The index phase gets at most half the budget and never more than 0.5 s, and gives up beyond 500
   candidates; the scan then answers. Any unusable state falls back to the scan per database: no role, wrong password,
   unreachable server, missing, invalid or unstamped index.
6. **Guarded against DocumentDB upgrades.** Each run of the job first checks `bson_get_value_text` against a canary
   text: it must return the text whole, wrapped in quotes, with nothing escaped. On a mismatch it fails and stamps
   nothing. Each index is stamped with `COMMENT 'documentdb_core <extversion>'`; the search ignores an index whose stamp
   is not the running version, and the job rebuilds such an index before stamping it again.
7. **Least privilege.** `ferretdb-init` (a one-shot container on every deploy) creates the login role
   `aihub_text_search` with `KNOWLEDGE_TEXT_INDEX_PASSWORD`, `USAGE` on the DocumentDB schemas and `SELECT` on the
   collection catalog. The job grants it `SELECT` on each knowledge table it indexes, and on nothing else. It also needs
   `USAGE` on `documentdb_api_internal`, because DocumentDB's planner hooks look up functions there by name; that schema
   has no `SECURITY DEFINER` functions.
8. **Snippets in the database where it pays.** The reader cuts `start`/`end` ranges with `$substrCP`/`$strLenCP` in a
   FerretDB aggregate, matching Python's slice semantics in code points. Matching lines stay in Python, but candidates
   are loaded one at a time, so a page holds one document's text at a time. Computing lines in the database
   (`$regexFindAll`) was quadratic in the number of matches, and a capped variant was only on par with Python.

Rejected alternatives:

- **A side table with a copy of the text**, kept in sync by triggers or by the pipeline: a second copy of the largest
  data in the system, and every FerretDB write path to keep consistent.
- **Milvus `PHRASE_MATCH`**: the analyzer setting is fixed per collection at creation, so existing databases need a
  migration (about 3 minutes per 100k chunks plus an index of ~40% of the text); it matches whole words within one
  chunk, not substrings across a document.
- **FerretDB `$text`**: its cursor silently drops results on long documents.
- **Folding the variant letters to one form inside the index** (a function over the 24 variant code points): exact, but
  made every recheck and build 1.6× slower, documents containing one such letter 2.6× slower and Greek text 10× slower,
  for letters German and English users rarely meet.

## Consequences

### Positive

- Selective literal searches answer in tens of milliseconds instead of a full scan, independent of corpus size.
- Results are identical on both paths; the integration tests compare them field by field.
- Reading a range of a 6 MB document takes 38 ms and under 1 MB of memory in the agent.
- No new copy of any data; FerretDB keeps owning every write.

### Trade-offs

- **The scan still answers** common terms, regexes, queries without a trigram (such as `Käse`, whose decomposed form
  splits into `Ka` and `se`) and anything during or after an upgrade until the job has run. A common term costs up to
  0.5 s more than before, spent finding out that the index cannot help.
- **One known gap:** a caseless query with `s` does not find a document that spells it as the long `ſ` through the
  index, while the scan would. It only occurs in historic Fraktur texts.
- **A second access path to FerretDB's data**, outside FerretDB, through `aihub_text_search`. It is read-only and
  limited to the knowledge tables, but it depends on DocumentDB's table layout, catalog and `bson_get_value_text`, which
  the canary and the version stamp guard.
- **Disk and write cost:** the index adds 7–9% of the text, and every insert or update of a document updates it.
- **A new secret,** `KNOWLEDGE_TEXT_INDEX_PASSWORD`, must be added to every deployment's environment before this version
  is deployed; `validate_env` rejects a missing key. An empty value turns the index off.
- **After a `postgres_ferretdb` image bump** the content search scans until the next 5 AM run, or until
  `ferretdb_text_index_job` is launched by hand.
