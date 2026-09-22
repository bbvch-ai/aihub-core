# Check 01 — `init_beanie` startup and index creation

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** **PASS**\
**Run:** 2026-09-22 · beanie 2.2.0 · FerretDB 2.5.0 · [`../environment.md`](../environment.md)\
**Script:** [`check_01_init_beanie.py`](check_01_init_beanie.py) · **Raw output:**
[`../logs/01_init_beanie.log`](../logs/01_init_beanie.log)

## Question

Does `init_beanie` complete against FerretDB 2.5, including creating the indexes our entities declare?

This is first because it is unskippable: Beanie creates a Document's indexes at init, on every process start. If
FerretDB rejects any index form we need, the application cannot boot — there is no workaround short of dropping the
index and losing the constraint it enforces.

The hardest case in the codebase is `AgentConfigEntityDocument`
(`packages/core/swiss_ai_hub/core/persistence/agents/agent_config_entity_document.py:20`):

```python
meta = {
    "collection": "agent_configs",
    "indexes": [
        {"fields": ("agent_class", "agent_id"), "unique": True},
        {"fields": ["agent_class"]},
    ],
}
```

A **compound unique** index plus a plain secondary index on the same collection.

## What was run

A Beanie `Document` mirroring `AgentConfigEntityDocument`'s fields and both indexes, against a dropped (absent)
collection in `aihub_beanie_spike`. The script does not stop at "did `init_beanie` raise": it reads the indexes back
from FerretDB, then attempts a genuine duplicate insert, because a silently ignored unique index is worse than a
rejected one — the constraint would be gone with nothing to notice it.

## Raw output

```
== 1. init_beanie (cold, collection absent) ==
returned without error in 0.103s

== 2. indexes as FerretDB reports them ==
{'v': 2, 'key': SON([('_id', 1)]), 'name': '_id_'}
{'v': 2, 'key': SON([('agent_class', 1), ('agent_id', 1)]), 'name': 'agent_class_1_agent_id_1', 'unique': True}
{'v': 2, 'key': SON([('agent_class', 1)]), 'name': 'agent_class_1'}

== 3. is the unique constraint actually enforced? ==
inserted spike-a
RESULT: second insert rejected -> unique index IS enforced (DuplicateKeyError)

== 4. a different agent_id on the same class must still be allowed ==
inserted spike-b (compound index behaves as compound, not as unique-on-agent_class)

== 5. init_beanie again (warm, collection and indexes exist) ==
returned without error in 0.009s -> idempotent

== 6. index count unchanged after re-init ==
['_id_', 'agent_class_1', 'agent_class_1_agent_id_1']
```

Full output in [`../logs/01_init_beanie.log`](../logs/01_init_beanie.log).

## Interpretation

PASS on every sub-question. `init_beanie` completes against FerretDB 2.5; both declared indexes exist server-side with
the correct keys; `unique: True` is reported on the compound index **and is genuinely enforced** — the duplicate
insert was rejected with `DuplicateKeyError`, so this is not a silently accepted no-op. Compound semantics are correct:
a second document sharing `agent_class` but differing in `agent_id` inserts fine, so the index is not behaving as
unique-on-first-field.

Re-initialisation is idempotent and cheap. That matters because six runners call their init on every process start, and
the API also does so on every test session.

## Recorded beyond pass/fail

- **Index list read back from the server**, not inferred from the absence of an exception — all three indexes present,
  names and key orders as declared.
- **Idempotency**: a second `init_beanie` on the existing collection returns cleanly and leaves the index set
  unchanged (`['_id_', 'agent_class_1', 'agent_class_1_agent_id_1']`).
- **Timing**: 0.103 s cold (collection absent, indexes created), 0.009 s warm. Negligible against process startup, and
  an order of magnitude cheaper warm — so the per-test-session cost is not a concern.

## Caveats

- One Document model with two indexes on one collection. A full `init_beanie` in production would register ~22 document
  models at once; this check does not measure that, and the 0.103 s figure will not scale linearly.
- Index *creation* was tested on an empty collection. Creating a unique index over an existing collection that already
  contains duplicates is a different operation, and is a real migration concern rather than a startup one.
- No TTL, partial, text or geo indexes were tested — we do not currently declare any, but a future one would need its
  own check.
