# Persistence

Entities live here as documents with their repository methods as class methods: schema and data access in one class. Two
ODMs serve them while #1634 moves the platform from MongoEngine (synchronous) to Beanie (async):

- **Beanie** serves the entities listed in `BeanieInitializer.DOCUMENT_MODELS`: `AgentConfigEntityDocument` and
  `NotificationEntity` (#1961), `AgentClassEntity`, `ThreadEntity` and `DiscoveryRoundEntity` (#1962).
- **MongoEngine** serves every other entity, including `ProcessConfigEntityDocument` and `ProcessClassEntity`, which
  stay until it is decided whether Process is kept.

Both write the same document shapes to the same collections, so an entity moves on its own, without a data migration,
and the previous release can still read what the new one writes.

## Porting an entity to Beanie

1. **Model.** Subclass `beanie.Document` with typed Pydantic fields. A localised field is a
   `swiss_ai_hub.core.i18n.locale_string.LocaleString`; the MongoEngine `LocaleStringEntity` stays for the entities not
   yet ported. An embedded type that a MongoEngine entity still embeds gets a Pydantic twin with the same fields and
   methods (`agents/event_spec.py` next to `process/event_spec_entity.py`, `form/stored_config_specs.py` next to
   `form/config_specs_entity.py`); one embedded nowhere else simply becomes Pydantic (`User`, `AgentInstanceRef`). A
   source document with `strict: False` gets `model_config = ConfigDict(extra="allow")`, so fields it does not declare
   survive a write.
2. **Settings, for the shape MongoEngine wrote.**
   - `keep_nulls = False`: an unset field is left out, not stored as `null`.
   - `use_state_management = True` with `state_management_replace_objects = True`: `save_changes()` writes only the
     changed fields and rewrites a changed field whole. Without the second setting, a key removed from a dict field
     survives in storage, because Beanie writes dotted `$set` paths.
   - `indexes`: the same keys as the MongoEngine `meta`. pymongo derives the same index names
     (`agent_class_1_agent_id_1`), so `init_beanie` does not clash with indexes MongoEngine already built.
3. **Writes.** `insert()` for a new document, `save_changes()` for an update, `delete()` to remove one. Never `save()`
   or `replace()`: both rewrite the whole document.
4. **Repository methods** become `async` and keep their names, except `find_all`: Beanie's own `find_all` returns a
   query that `delete_all` relies on, so it must not be overridden (`list_all` instead). MongoEngine paths with `__`
   (`config_data__user_memory__x`) become dotted (`config_data.user_memory.x`).
5. **Signals.** Beanie has no global signals. A MongoEngine `post_save`/`post_delete` receiver becomes an
   `@after_event(Insert, Replace, Save, SaveChanges, Delete)` method on the document. Like a signal, it fires only for
   writes through a document instance, not for query-level `update`.
6. **Register** the document in `BeanieInitializer.DOCUMENT_MODELS`. Every runtime that reads it must initialise that
   list next to its MongoEngine connection: today the API lifespan, the process runner and the bot lifetime manager
   (threads are read by the agent event distributor both use).
7. **Tests.** Mark them `beanie` (see `swiss_ai_hub.core.testing.beanie_isolation`). The package's
   `beanie_document_models` fixture already returns `DOCUMENT_MODELS`. Keep a readback test that reads what the port
   writes through a replica of the old MongoEngine class, as `agents/tests/unit/test_agent_config_entity_document.py`
   does.

## Callers

A Beanie read is awaited on the event loop. What a caller needs depends on what it is:

- **An `async` caller** awaits the method. Drop any `asyncio.to_thread` hop around it.
- **A synchronous chain reached from async code** (DTO factories, validators): make the chain `async` when it is short.
  When it is long, or in code that may be removed (the Process walkthrough DTOs), load what it needs up front in one
  query and pass the result down: `AgentConfigEntityDocument.find_for_instances`.
- **A caller that also reads MongoEngine entities** (the cron scheduler's snapshot, the OpenWebUI provisioner) awaits
  the Beanie read and keeps only the MongoEngine read in a worker thread.

Pitfalls found in the first port:

- A Beanie document cannot be constructed before `init_beanie`, not even in memory. A test that builds one needs the
  `beanie_test_database` fixture.
- `init_beanie` binds the classes for the whole process to one client, and that client only works on the loop it was
  created on. The API lifespan initialises on its own loop in tests, so `clean_beanie_collections` binds again before
  every `beanie` test.
- A module-scoped API client whose requests reach a Beanie entity starts the lifespan on its own loop unless the fixture
  runs on the session loop: `@pytest_asyncio.fixture(scope="module", loop_scope="session")`, depending on
  `beanie_test_database`, with the module marked `beanie`. Which requests reach one can depend on data earlier tests
  left behind (`/my-account` lists agent profiles only once a class exists), so such a failure shows only in a full run.
- `cachetools.cached` on an `async` function caches the coroutine, which can be awaited only once. Cache the result by
  hand (`ThreadService._fetch_minimal_agent_dto`).

## Effort per port

Measured from the diffs. Wall-clock time was not measured.

| What                                        | #1961: `agent_configs`, `notifications` | #1962: `agent_classes`, `threads`, `discovery_rounds` |
| ------------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| Production files changed                    | 32                                      | 33                                                    |
| Entity call sites now awaited               | 41                                      | 62                                                    |
| Synchronous chains given a prefetch instead | 1                                       | 1 (the same Process walkthrough chain)                |
| Test files changed or added                 | 26                                      | 18                                                    |
| Runtimes that start Beanie                  | 1 (API)                                 | 3 (API, process runner, bot)                          |

Most of the work was not in the entities but in their callers: the save-path validators, the startup migrations shared
with Process, and DTO factories that read entities. Expect the waves whose entities sit behind many synchronous helpers
(threads, events) to cost more per collection than this one.
