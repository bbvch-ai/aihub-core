# Check 02 — insert, `find_one`, replace/save

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** **PASS**\
**Run:** 2026-09-22 · beanie 2.2.0 · mongoengine 0.29.3 · FerretDB 2.5.0 ·
[`../environment.md`](../environment.md)\
**Script:** [`check_02_basic_crud.py`](check_02_basic_crud.py) · **Raw output:**
[`../logs/02_basic_crud.log`](../logs/02_basic_crud.log)

## Question

Do Beanie's basic document operations work against FerretDB 2.5, and does the stored document have the same on-disk
shape MongoEngine produces?

The floor. If this fails nothing else matters. But the second half of the question is the interesting one: an
incremental migration means both ODMs read and write the same collections for a period, so a shape difference is not
cosmetic — it decides whether incremental migration is possible at all.

## What was run

A full Beanie round-trip (insert → `find_one` → modify → `save` → re-read), then an insert of the **real**
`AgentConfigEntityDocument` through MongoEngine into the **same collection**. Both documents were then read back with a
plain synchronous PyMongo client, so neither ODM's deserialization could hide a difference. Finally each ODM was asked
to read the other's document.

## Raw output

```
== 5. raw BSON of both, read with a plain PyMongo client ==

-- written by Beanie --
  _id            ObjectId     ObjectId('6ab2218d7ffd109de49c7cc9')
  agent_class    str          'RAGAgent'
  agent_id       str          'via-beanie'
  config_data    dict         {'temperature': 0.2, 'nested': {'a': {'b': 1}}}
  created_at     datetime     datetime.datetime(2026, 9, 22, 6, 34, 53, 380000)
  description    dict         {'de': None, 'en': 'Written by Beanie', 'fr': None, 'it': None}
  icon           str          'mage:robot-modified'
  name           dict         {'de': 'Beanie-Agent', 'en': 'Beanie agent', 'fr': None, 'it': None}
  updated_at     datetime     datetime.datetime(2026, 9, 22, 6, 34, 53, 380000)

-- written by MongoEngine --
  _id            ObjectId     ObjectId('6ab2218d7ffd109de49c7ccb')
  agent_class    str          'RAGAgent'
  agent_id       str          'via-mongoengine'
  config_data    dict         {'temperature': 0.7, 'nested': {'a': {'b': 1}}}
  created_at     datetime     datetime.datetime(2026, 9, 22, 6, 34, 53, 409000)
  description    dict         {'de': None, 'en': 'Written by MongoEngine', 'fr': None, 'it': None}
  icon           str          'mage:robot'
  name           dict         {'de': 'ME-Agent', 'en': 'ME agent', 'fr': None, 'it': None}
  updated_at     datetime     datetime.datetime(2026, 9, 22, 6, 34, 53, 409000)

== 6. key-set difference ==
only in Beanie doc      : []
only in MongoEngine doc : []

== 7. cross-read: can each ODM read the other's document? ==
Beanie reading MongoEngine's doc : OK (name.en='ME agent')
MongoEngine reading Beanie's doc : OK (name.en='Beanie agent')
```

Full output in [`../logs/02_basic_crud.log`](../logs/02_basic_crud.log).

## Interpretation

PASS, and stronger than required. **The two ODMs produce byte-identical document shapes** for this entity: the key sets
are exactly equal, with nothing extra on either side. Concretely:

- **No Beanie bookkeeping field.** No revision field appeared — Beanie's optimistic concurrency is opt-in
  (`use_revision`), and left off it writes nothing of its own. This was the main shape risk and it did not
  materialise.
- **No `_cls` discriminator** on the MongoEngine document, so there is nothing for Beanie to trip over.
- **`_id` is a plain `ObjectId` in BSON from both.** Beanie exposes it in Python as `PydanticObjectId`, which is an
  `ObjectId` subclass — a Python-side type, not a storage difference.
- **Embedded documents and nested dicts are identical.** `LocaleStringEntity` serialises to the same
  `{de, en, fr, it}` dict as the nested Pydantic model, nulls included, and the nested `config_data` survives
  unchanged.

**Both ODMs read each other's documents successfully.** This is the finding that matters most for the plan: it is the
precondition for migrating entity by entity rather than big-bang, and it holds for this entity.

## Recorded beyond pass/fail

- Modify-and-save works; the changed field and the changed nested value both persisted.
- Beanie's `save()` rewrote the whole document without dropping anything.
- Timestamps come back **naive** from both ODMs (`datetime.datetime(2026, 9, 22, 6, 34, 53, ...)` with no `tzinfo`),
  although both were written as aware UTC. This is BSON's own behaviour — it stores no timezone, and PyMongo returns
  naive UTC unless the client is built `tz_aware=True`. It is not a Beanie difference, and it is the mechanism
  [check 07](07_datetime_shape.md) examines properly.

## Caveats

- **One entity.** `AgentConfigEntityDocument` has no reference fields, no list-of-embedded-documents and no
  `strict: False`. Entities that do — `ThreadEntity`, the persisted-event entities, `RoleEntity` with its embedded
  `UsageLimit` — could still differ, and checks 06 and 08 probe parts of that.
- The comparison was made on a **fresh** document written by each ODM. It does not prove that a document *migrated*
  between the two keeps its shape over repeated read-modify-write cycles; check 06 tests the dangerous version of that.
- `use_revision` was not enabled. If a later decision turns it on, the shape equality recorded here no longer holds and
  this check must be re-run.
- Cross-reads were single documents by indexed field. Query-operator parity across the full `.objects(...)` surface
  (139 call sites) is not covered here.
