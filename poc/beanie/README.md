# Beanie evaluation spike — evidence root

Throwaway spike for [issue #1634](https://github.com/bbvch-ai/aihub-core/issues/1634), *Replace synchronous MongoEngine
with an async ODM*.

**This branch is never merged.** It exists to produce reproducible evidence for an ADR. Only the conclusions and the
headline figures travel to `main`, in `docs/arc42/decisions/`.

## What the issue asks for

Evaluate Beanie against MongoEngine for this codebase, record the decision as an ADR, and define the migration path.
Executing the migration is explicitly out of scope — it follows as sub-issues.

## Phases

The evaluation is gated: the cheapest test that can kill the Beanie option runs first.

| Phase | Work                                              | Report                 | State                     |
| ----- | ------------------------------------------------- | ---------------------- | ------------------------- |
| 1     | FerretDB 2.5 compatibility probe (go/no-go)       | `phase_1_report.md`    | **complete — verdict GO** |
| 2     | Interim `asyncio.to_thread` fix (separate branch) | PR body                | not started               |
| 3     | Full evaluation, incl. four-variant load measure  | `phase_3_report.md`    | **complete**              |
| 4     | ADR                                               | `docs/arc42/decisions` | not started               |
| 5     | Migration plan + sub-issues                       | in the ADR             | not started               |

Phase 1 is the gate. Checks 01–04 are hard gates: any FAIL ends the Beanie option and the answer becomes "extend the
`asyncio.to_thread` pattern". Checks 05–08 are cost inputs — they inform the ADR rather than kill the option.

## Phase 1 checks

| #                                      | Check                                       | Gate | Verdict            |
| -------------------------------------- | ------------------------------------------- | ---- | ------------------ |
| [01](checks/01_init_beanie.md)         | `init_beanie` startup and index creation    | hard | **PASS**           |
| [02](checks/02_basic_crud.md)          | Insert, `find_one`, replace/save            | hard | **PASS**           |
| [03](checks/03_find_one_and_update.md) | `find_one_and_update`                       | hard | **PASS**           |
| [04](checks/04_aggregation.md)         | `$group`, `$lookup`, `allowDiskUse`         | hard | **PASS**           |
| [05](checks/05_multi_db.md)            | One Document class against two databases    | cost | **PASS WITH COST** |
| [06](checks/06_extra_allow.md)         | `extra="allow"` round-trip (`strict:False`) | cost | **PASS WITH COST** |
| [07](checks/07_datetime_shape.md)      | Datetime storage shape                      | cost | **PASS**           |
| [08](checks/08_coexistence.md)         | Sync and async clients on one collection    | cost | **PASS**           |

See [`phase_1_report.md`](phase_1_report.md) for the synthesis, what the phase does **not** prove, and the three
findings that change the migration plan.

## Phase 3 checks

| #                                      | Check                                   | Gate                  | Verdict            |
| -------------------------------------- | --------------------------------------- | --------------------- | ------------------ |
| [09](checks/09_test_infrastructure.md) | Test infrastructure (loop-bound client) | hard, for feasibility | **PASS WITH COST** |
| [10](checks/10_load.md)                | Four-variant load measurement           | decides the ADR       | **`to_thread` holds** |
| [11](checks/11_sync_contexts.md)       | Sync contexts (pipeline, bot)           | cost                  | **PASS** — concern evaporates |
| [12](checks/12_datetime_inventory.md)  | Naive-local datetime inventory          | cost                  | **PASS** — 5 fields |

[`phase_3_report.md`](phase_3_report.md) holds the synthesis and the recommendation: **do not migrate now**, recorded
against criteria pre-registered before the first measurement.

Note the phase-1 entity inventory is corrected in [check 11](checks/11_sync_contexts.md): the split is 20 Document-like
+ 15 Embedded across **core and bot only**; `packages/pipeline` has zero MongoEngine entities.

## Evidence rules

These are what make this proof rather than narrative. They are not negotiable within this spike.

1. **Raw output is never edited, trimmed or paraphrased.** A summarised traceback is not evidence. Output too long to
   inline goes verbatim into `logs/` and is excerpted with a pointer to the file.
2. **Every check cites `environment.md`.** Versions are the scope of the finding — FerretDB's Mongo-compatibility
   surface moves between releases, so "it worked" without a version number is unreproducible and means nothing.
3. **A check that was not run says "not run".** It never says PASS by assumption, and it is never quietly dropped.
4. **Every report carries a "what this does NOT prove" section.** A green table says "these operations worked on this
   version with this data shape" — not "Beanie works".
5. **Verdicts are one of three:** `PASS`, `PASS WITH COST`, `FAIL`. "Mostly works" is not a verdict; say what the cost
   is or call it a failure.

## Layout

```
poc/beanie/
├── README.md            # this file
├── environment.md       # pinned versions and stack state — written once, cited by every check
├── checks/              # one file per check, independently verifiable
├── logs/                # verbatim, unedited command output
└── phase_1_report.md    # synthesis of the phase-1 checks
```

## How to reproduce

1. Bring up the dev stack (FerretDB, its PostgreSQL backend). See `infra/docker-compose.dev.yml`.
2. Record the exact versions in `environment.md` **before** running anything.
3. Run each check's script from the repo root; save its output verbatim into `logs/`.
4. Fill the check file's verdict, raw output and interpretation.
5. Write the phase report only once every check has a verdict.
