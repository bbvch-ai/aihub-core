# Check 04 — aggregation: `$group`, `$lookup`, `allowDiskUse`

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** **PASS** (one sub-result is "accepted", not "proven honoured" — see below)\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Script:** [`check_04_aggregation.py`](check_04_aggregation.py) · **Raw output:**
[`../logs/04_aggregation.log`](../logs/04_aggregation.log)

## Question

Are our existing aggregation pipelines reachable and correct through Beanie's aggregation API?

The pipelines themselves are ODM-independent — raw stage dictionaries sent over the wire. What this check tests is
whether **Beanie passes them through unchanged**, options included, and returns the same rows.

Two real pipelines were reproduced verbatim in shape:

1. **LLM spend**, `persisted_agent_event_entity.py:578` — `$match` → `$project` → `$group` (dedup by `event_id`) →
   `$group` (sum) → `$sort`, run with `allowDiskUse=True` (line 599).
2. **Unanswered work requests**, `persisted_process_event_entity.py:63` — a **correlated** `$lookup` using `let`,
   `$expr`, `$and`, `$in` over the same collection, then a `$size: 0` filter. The hardest `$lookup` form there is.

Seed data was built to exercise the three things the real pipeline's comments say it exists for: a **redelivered
duplicate** `event_id` that the dedup stage must collapse, events **missing** `embedding_tokens_costs` (the reason for
`$ifNull`), and an event **outside the time window** that the `$match` must exclude.

## Raw output

```
== 1. spend pipeline through Beanie, allowDiskUse=True ==
  {'_id': {'user_id': 'alice', 'tenant_id': 't1'}, 'calls': 2, 'prompt_tokens_costs': 1.5, 'completion_tokens_costs': 2.5, 'embedding_tokens_costs': 0}
  {'_id': {'user_id': 'alice', 'tenant_id': 't2'}, 'calls': 1, 'prompt_tokens_costs': 10.0, 'completion_tokens_costs': 0.0, 'embedding_tokens_costs': 0}
  {'_id': {'user_id': 'bob', 'tenant_id': 't1'}, 'calls': 1, 'prompt_tokens_costs': 3.0, 'completion_tokens_costs': 1.0, 'embedding_tokens_costs': 0}

== 3. do they agree? ==
  identical: True

== 4. assertions on the spend result ==
  alice/t1 calls=2 (expect 2: duplicate event_id collapsed)
  alice/t1 prompt=1.5 (expect 1.5)
  alice/t1 embedding=0 (expect 0.0 via $ifNull, not null)
  400-day-old event excluded: True

== 5. allowDiskUse rejected outright? ==
  accepted (no error)

== 6. correlated $lookup through Beanie ==
  unanswered: UnansweredRequest forms=[{'_event_name': 'FormB'}]

== 7. same $lookup, plain PyMongo ==
  identical: True
  expected exactly 1 unanswered (FormB): True
```

Full output in [`../logs/04_aggregation.log`](../logs/04_aggregation.log).

## Interpretation

PASS on both pipelines, and the results are **byte-identical** to the same pipelines run through a plain PyMongo
client — so Beanie is a pass-through, not a transformer.

The spend pipeline is correct in the three ways that matter, not merely non-empty:

- **Dedup works.** `alice/t1` reports `calls=2` from three seeded documents, because the redelivered duplicate
  `event_id` was collapsed by the first `$group`. A broken dedup would have reported 3 and over-billed.
- **`$ifNull` works.** `embedding_tokens_costs` came back `0`, not `null`, for events that never carried the field.
  The source comment warns that a missing operand makes `$add` return null and poison the whole sum; that does not
  happen here.
- **The time-bound `$match` works.** The 400-day-old event with cost 999.0 is absent from every row.

The **correlated `$lookup` works fully** — `let` bindings, `$expr` with `$and`, and `$in` against an array lifted from
a nested field (`$event_data.forms._event_name`) all evaluate correctly. Exactly one request is reported unanswered
(`FormB`), and the one answered by a matching work event (`FormA`) is correctly excluded. This was the single most
likely place for FerretDB to fall short, and it did not.

## The one result that is weaker than it looks

`allowDiskUse=True` was **accepted without error**. That is not the same as **honoured**. Nothing in this check proves
FerretDB spills to disk rather than silently ignoring the flag and keeping the `$group` in memory. If it is ignored,
the spend query keeps working until a deployment accumulates enough cost events to cross the 100 MB `$group` limit, and
then fails — a latent failure, not a current one.

Two things bound that risk: the pipeline is always time-bounded (the source comment says the default window is what
keeps the limit from being reached, with `allowDiskUse` as the safety net), and **this is not a regression** — the
MongoEngine path passes exactly the same flag to exactly the same server today, so the exposure is identical either
way. It is a pre-existing FerretDB question, not a Beanie one, and it should be recorded in the ADR as such rather
than counted against either option.

## Caveats

- **Tiny data set.** Six spend events and three process events. This proves semantic correctness, not behaviour at
  scale — nothing here approaches the 100 MB `$group` limit or the 33k-event staging figures cited in the source
  comment.
- Performance was not measured and must not be inferred. That is phase 3, and on an uncontended stack.
- Only these two pipelines were tested. `persisted_agent_event_entity.py` has further aggregations (lines 270, 370,
  772) that were not reproduced.
- Results were returned as raw dicts and read as `row["_id"]`, matching how the current code consumes them. Beanie's
  typed projection into a Pydantic model was not exercised and is not needed for a like-for-like port.
