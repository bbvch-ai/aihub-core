# Check 06 — `extra="allow"` round-trip (the `strict: False` equivalent)

**Gate:** cost input — informs the ADR, does not kill the option\
**Verdict:** not run\
**Environment:** see [`../environment.md`](../environment.md)

## Question

Does a document carrying fields the model does not declare survive a read-modify-write through Beanie **without losing
those fields**?

Four of our documents run with `strict: False` precisely because old shapes drift:

- `ThreadEntity` (`.../messaging/entities/thread_entity.py:27`)
- `PersistedAgentEventEntity` (`.../persisted_agent_event_entity.py:92`)
- `PersistedProcessEventEntity` (`.../persisted_process_event_entity.py:16`)
- `UserDashboardEntity` (`.../user/user_dashboard_entity.py:27`, `:36`, `:40`)

Loading such a document is the easy half. The half that matters is writing it back: if Beanie drops undeclared fields
on save, a single read-modify-write silently deletes production data that no code knew about — and there is no
migration framework in place to have removed it deliberately (that is issue #1152).

## What to run

Insert a document with extra fields via a raw PyMongo client, read it through a Beanie Document configured with
`extra="allow"`, modify one declared field, save, then read the raw BSON back and check whether the extra fields are
still there.

*(script + exact code — fill when run)*

## Raw output

```
not run
```

## Interpretation

*not run*

## What to record beyond pass/fail

- Whether extras survive `save()`, `save_changes()` and `replace()` — these may differ, and `replace()` is the
  dangerous one.
- Whether extras are reachable from Python after load (`model_extra`), since some of our code may need to read them.
- If extras are dropped: whether that is configurable, and if not, how many collections would need a migration before
  the swap — which turns this into a sequencing dependency on #1152.

## Caveats

*not run*
