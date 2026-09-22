# Phase 1 report — Beanie / FerretDB 2.5 compatibility gate

**Status:** not started — no check has been run yet.\
**Verdict:** *pending*\
**Evidence:** `poc/beanie-spike` @ *commit sha* · environment: see [`environment.md`](environment.md)

Write this file **only once every check in `checks/` carries a verdict.** A report written while checks are still open
is a guess with a table around it.

## Result table

| #  | Check                                 | Gate | Verdict | Note |
| -- | ------------------------------------- | ---- | ------- | ---- |
| 01 | `init_beanie` + index creation        | hard | not run |      |
| 02 | Insert, `find_one`, replace/save      | hard | not run |      |
| 03 | `find_one_and_update`                 | hard | not run |      |
| 04 | `$group`, `$lookup`, `allowDiskUse`   | hard | not run |      |
| 05 | One Document class, two databases     | cost | not run |      |
| 06 | `extra="allow"` round-trip            | cost | not run |      |
| 07 | Datetime storage shape                | cost | not run |      |
| 08 | Sync + async clients, one collection  | cost | not run |      |

**Decision rule.** Any hard-gate FAIL → **NO-GO**: the Beanie option ends and the answer to #1634 becomes "extend the
`asyncio.to_thread` pattern", recorded as such in the ADR. All hard gates PASS → **GO**: proceed to phase 2, carrying
the cost findings from 05–08 into the evaluation.

## What this proves

*pending*

## What this does NOT prove

*pending — and this section is not optional.*

A green table says: these operations worked, on these versions, with this data shape, at this scale, on this host. It
does not say Beanie works for this platform. At minimum, state here that phase 1 measured **nothing** about:

- performance or event-loop behaviour (that is phase 3)
- the 139 call sites and 35 document classes that would have to change
- test-infrastructure compatibility (loop-bound client vs `@async_test`'s `asyncio.run()` per step)
- the sync contexts in `packages/pipeline` and `packages/bot`
- FerretDB versions other than the one in `environment.md`

## Open questions carried into phase 3

*pending*

## How to reproduce

*pending — reference the scripts in `checks/` and the raw output in `logs/`.*
