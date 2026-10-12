# Dense Search Results Below a Minimum Similarity Are Dropped Before Reranking

## Context

A dense knowledge search returns `retrieve_k` sections per database whatever they score. A question the collections do
not cover still gets its closest sections, and they all go to the reranker and into the prompt. With "every collection
the user can read", one Universal Agent search covered 21 collections in 12 databases, so a question about nothing in
them still carried dozens of unrelated sections.

Scores from bge-m3, measured on 2026-10-12 against the dev stack (cosine similarity, Milvus `IP` on vectors of norm 1):

| Corpus                                                 | Questions  | Score of the passage that answers | Best score of unrelated questions |
| ------------------------------------------------------ | ---------- | --------------------------------- | --------------------------------- |
| English test documents (contract, policies, handbooks) | 11 English | 0.586–0.77                        | 0.28–0.43                         |
| same                                                   | 11 German  | 0.505–0.725                       | 0.28–0.43                         |
| German law collections (OR, FamZWL, WBB)               | 8 German   | 0.437–0.703                       | 0.347–0.419                       |
| same                                                   | 8 English  | 0.533–0.661                       | 0.387–0.43                        |

Every answering passage ranked in the top four. The lowest one, 0.437, answered a terse German question taken from a
real chat. The two ranges almost touch, so no dense threshold separates relevant from unrelated; one can only drop what
is clearly unrelated.

Other projects: AnythingLLM drops Milvus cosine below 0.25 by default, PrivateGPT below 0.4 without a reranker after it,
FastGPT 0.4 on the reranker score, Dify 0.5 but switched off by default and forced to 0 in hybrid mode. BAAI gives no
threshold for bge-m3.

## Decision Drivers

- **Never lose the answering passage**\
  A dropped passage cannot be recovered by the reranker or the model.
- **Less noise for the reranker and the prompt**\
  Clearly unrelated sections cost reranking time and prompt room, and invite answers from the wrong document.
- **Tunable per collection**\
  Collections differ in language and chunking, which moves the scores.

## Decision

`KnowledgeRetrieverConfig.min_similarity`, default **0.35**, editable in the retriever form (0 keeps every result).
`retrieve_nodes` drops results below it:

- **Only in the Default (dense) query mode.** Hybrid scores are min-max normalised per query, so their weakest result
  always scores 0, and sparse scores are BM25; neither is a cosine similarity.
- **Before neighbours and parent summaries are fetched.** Those are added without a score of their own (`None`, `0.0`),
  so a filter after them would delete them; fetching them only for the kept results also saves the lookups.

0.35 leaves a margin of 0.087 under the lowest answering passage measured. Every caller that builds a retriever gets the
default: RAG and Expert RAG profiles (stored ones lack the field and validate to the default), the Retrieval agent, and
the Universal Agent knowledge tool and `#` references.

## Consequences

- **A question no collection covers gets no sections.** The knowledge tool tells the model nothing matched; RAG's
  sufficiency check retries with a new query or declines.
- **Clean collections lose most of their noise**: on the English documents, 10 of 16 unrelated questions returned
  nothing. Collections whose unrelated scores sit higher, such as the German law texts at 0.35–0.43, keep most of it;
  the reranker stays the judge there.
- **A different embedding model needs a new measurement.** The value is a cosine similarity of bge-m3 and means nothing
  for another model; re-run the comparison above before changing either.
