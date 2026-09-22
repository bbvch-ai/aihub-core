# Check 01 — `init_beanie` startup and index creation

**Gate:** hard — a FAIL ends the Beanie option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

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

## What to run

Define the equivalent Beanie Document with a `Settings.indexes` block declaring both, then `init_beanie` against a
clean spike database. Record whether the call returns, and inspect the resulting indexes server-side rather than
trusting the client's silence.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- The index list FerretDB actually reports afterwards, not just the absence of an exception — a silently ignored index
  is worse than a rejected one, because the uniqueness constraint would be gone without anyone noticing.
- Whether re-running `init_beanie` on an existing database is idempotent. Six runners call their init on every start.
- Time taken. It runs on every process boot, including in tests.

## Caveats

*not run*
