# Check 12 — naive-local datetime inventory

**Phase:** 3, step 4 — code inventory, sizing the migration implied by [check 07](07_datetime_shape.md)\
**Verdict:** **PASS — the migration is small and bounded: 5 fields in 3 collections.**\
**Run:** 2026-09-22 · static analysis of the working tree at `poc/beanie-spike`

## Question

[Check 07](07_datetime_shape.md) established that the codebase mixes two datetime conventions, that BSON cannot tell
them apart, and that on this UTC+7 host the mismatch makes a live agent class read as 7 hours old — **OFFLINE** against
a 5-minute threshold. It left the sizing question open:

> How many collections hold a naive-local datetime? That count is the size of the migration.

## What was found

Every `DateTimeField` and every runtime assignment of a datetime onto a persisted field was classified.

### Naive local — the migration set

| Field                                    | Location                                     |
| ---------------------------------------- | -------------------------------------------- |
| `AgentClassEntity.first_discovered`      | `persistence/agents/agent_class_entity.py:106` |
| `AgentClassEntity.last_discovered`       | `persistence/agents/agent_class_entity.py:107` |
| `ProcessClassEntity.first_discovered`    | `persistence/process/process_class_entity.py:164` |
| `ProcessClassEntity.last_discovered`     | `persistence/process/process_class_entity.py:165` |
| `ThreadEntity.created_at`                | `persistence/messaging/entities/thread_entity.py:37` |

**Five fields, three collections** (`agent_classes`, `process_classes`, `threads`).

The first four are `DateTimeField(required=True, default=datetime.now)` — no timezone, so the host's local wall clock.
They are also assigned naive at runtime, at `agent_class_entity.py:160,161,208` and `process_class_entity.py:210,211,258`.

`ThreadEntity.created_at` is different and easy to miss: the field carries **no default at all**
(`DateTimeField(required=True)`), so a scan of field defaults alone does not flag it. It is naive because two call
sites assign `datetime.now()` — `thread_entity.py:49` and `:102`.

### Aware UTC — already correct

Twelve fields, using `datetime.now(UTC)`: `TenantMetadataEntity` (2), `UserTenantRoleEntity` (2),
`AgentConfigEntityDocument` (2), `ProcessConfigEntityDocument` (2), `NotificationEntity` (1), `IngestorEntity` (1),
and `ConversationEntity` in `packages/bot` (2).

### Neither — set by the caller

`BearerToken.expiry_date` (`DateTimeField(required=True)`, no default) is supplied by whoever mints the token and was
not traced to its call sites here.

## Interpretation

**The migration is small and bounded.** Five fields in three collections, and the two that matter operationally —
`last_discovered` on the agent and process class entities — are the pair that `is_online` reads. The other three are
`first_discovered` (informational) and `ThreadEntity.created_at` (display ordering).

**The aware-UTC majority is the argument for normalising rather than preserving.** Twelve fields already store aware
UTC, including `AgentConfigEntityDocument` — a *sibling* of `AgentClassEntity` in the same package. The codebase has
already decided which convention it wants; the five naive fields are the stragglers, not a deliberate design.

**`ThreadEntity.created_at` is the trap.** Any migration script written from a scan of field defaults would miss it,
because the naivety lives in the two assignment sites rather than the declaration. Whoever writes the normalisation
must scan assignments, not just defaults.

**Sequencing, restated with a number attached.** Check 07 concluded that normalisation must happen *before or with*
the port of the entity that owns each field, never after — because the moment one writer uses aware-UTC while another
still writes naive-local into the same collection, `is_online` is wrong for half the rows. With only three collections
involved, that is a small, self-contained data migration rather than a programme. It still has no framework to run it,
which is the dependency on issue #1152.

## Recorded beyond the count

- The naive/aware split follows package age rather than any rule: the discovery entities (`*_class_entity`) are naive,
  the config and access entities are aware. Nothing enforces either.
- `AgentClassEntity` already documents the hazard in its own docstring at `:257` and carries a dedicated unit test
  (`persistence/agents/tests/unit/test_online_at.py`) asserting the naive-local semantics — so a migration must update
  that test deliberately, not incidentally.

## Caveats

- Static analysis only, using patterns for `DateTimeField(` declarations and `X_at = datetime.now()`-style assignments.
  A datetime reaching a document through a dict, a `**kwargs` spread, or a Pydantic model dump would not be caught.
- Embedded documents were scanned with the same patterns but hold no datetime fields; this was not separately verified
  per class.
- `BearerToken.expiry_date` is unresolved — it needs its call sites traced before a normalisation script is written.
- The count is of **fields in code**, not of rows in a deployment. How much data needs rewriting depends on collection
  sizes in each tenant, which was not measured.
