# A Pipeline Owns Its Own Configuration and Announces It

## Context

A knowledge database is processed by whichever ingestion pipeline owns it. Which pipelines exist is already discovered
at runtime: a deployed pipeline registers an id and a label, and the create-database dialog offers what it finds.

How a database is processed was not discovered. Each setting a pipeline needed was held by the platform as a field on
the create request, a column on the database record, and a hand-written control in the dialog. Two settings existed on
that basis, the text model and the embedding model.

This makes every further setting expensive and puts it in the wrong place. A crawl depth for a web-scrape pipeline, a
source connection for a sync pipeline, per-database enrichment switches, a separate vision model: each one costs a
change to the API, the frontend and the generated client, for a decision that belongs to the pipeline. A deployment that
ships its own pipeline cannot add a setting at all, because it cannot change the platform.

Agent blueprints do not have this problem. An agent publishes what it can be configured with, the API validates
submissions against that declaration, and the frontend renders it without knowing any field names. Nothing in that
machinery is specific to agents beyond the names of its parts.

## Decision Drivers

1. **Whoever owns a setting should declare it.** Adding a knob to a pipeline should be a change to that pipeline, with
   no platform release behind it.
2. **One mechanism for configuration, not two.** The platform already turns a declaration into a rendered, validated,
   localized form. A second mechanism for pipelines would drift from the first and carry its own bugs.
3. **An offer implies a promise.** If a database can be created for an ingestor, something must be running that ingests
   it.
4. **Upgrades change nothing for existing databases.** Corpora already indexed must keep being processed exactly as
   before, without re-embedding.
5. **Some checks only the platform can make.** A pipeline cannot know which models a deployment serves or which of them
   the person creating the database is allowed to use.

## Alternatives Considered

1. **Keep adding a field per setting.** Rejected: it is the status quo whose cost this decision is about, and it leaves
   a deployment's own pipeline permanently unable to add one.

2. **Give pipelines a free-form settings object with no declaration.** Simple to store, but nothing could render a
   sensible form or reject a bad value, so mistakes would surface as failed ingestion runs hours later instead of as a
   rejected dialog.

3. **Build a configuration mechanism specific to ingestors.** Rejected on driver 2. The agent stack already handles
   nested sections, repeated entries, optional groups, model pickers and translations. Reimplementing a subset would
   mean two half-answers.

4. **Announce the declaration over the event bus, as agents do.** Attractive for symmetry, but pipelines already publish
   their registration through the shared database, and Dagster code locations are not event subscribers. Adding a second
   transport for the same fact buys nothing.

5. **Let the API keep a built-in declaration for the pipeline the platform ships.** Rejected: it splits the code into a
   privileged path and a general one, and the privileged path can offer an ingestor that nothing is running.

## Decision

**A pipeline declares what its databases can be configured with, and the platform renders and validates that declaration
without knowing what is in it.**

1. **The declaration travels with the registration.** A pipeline already tells the platform that it exists. It now also
   says what a database of its kind can be configured with, in two forms: the controls to render, and a schema to
   validate against. Both come from one class in the pipeline, so they cannot disagree.

2. **Pipelines reuse the agent configuration stack rather than a parallel one.** The base class for a pipeline's
   configuration is the sibling of the one agents use, and the schema helper that was named for agents is now named for
   what it does. Every form element, the renderer, the validator and the authorization walk are shared. A pipeline that
   wants a repeated section or an optional group gets it for free.

3. **The pipeline the platform ships has no special status.** It registers through the same path as a third-party one,
   and its labels travel on its record like everyone else's. Nothing is offered in the dialog until a pipeline has
   registered, which is what makes an offer a promise (driver 3).

4. **A database stores one configuration object, not a column per setting.** The platform holds it without interpreting
   it. The two model columns retire into that object, so a setting has one home rather than a column and a form field
   that can disagree.

5. **The platform still polices the choices only it can see.** When a declaration says a field picks a model, the API
   checks that the model exists, suits that slot, and is one the caller may use. An embedding model must also state its
   vector width, because a collection's dimension is derived from it and a wrong width corrupts search silently. The API
   never learns a pipeline's field names; it recognizes the kind of control instead.

6. **Processing choices are resolved per run, not per deployment.** The deployment settings become defaults that
   pre-fill the dialog and cover databases that stored no choice of their own. Because a database can now switch
   enrichment steps on or off, those steps stay in the graph for everyone and decide per run whether they have work.
   Building a different graph per database was the alternative, and it would make one deployment's pipeline shape depend
   on the databases that happen to exist.

## Consequences

### Positive

- A pipeline adds a setting by declaring a field. It appears in the dialog, is validated, and reaches the pipeline at
  run time with no platform change. The web-scrape and sync pipelines now have a place to put their own settings.
- Two pipelines with different declarations coexist, and each database is held to the declaration of its own.
- Enrichment steps, the model that refines tables and an optional vision model are chosen per database instead of per
  deployment, so an expensive recipe no longer has to apply to every corpus in the installation.
- Knowledge databases carry translated names and descriptions, as agent profiles do.

### Trade-offs

- **A pipeline that is not running offers nothing.** The dialog is empty until a pipeline registers, which takes one
  sensor tick after it starts. This is the intended reading of driver 3, but it does mean a broken pipeline looks like a
  missing feature to whoever opens the dialog.
- **A registration without a declaration is ignored.** An older pipeline image registers labels only. Offering it would
  render an empty form and accept a configuration nothing could check, so it is skipped until that pipeline is upgraded.
- **The embedding model becomes a cross-package contract.** Retrieval still reads a model from the agent rather than
  from the database, so the write path and the query path can still disagree. The gap was already open, and this
  decision moves where the answer lives without closing it.
- **Every field a pipeline declares is a public interface.** Renaming one is a breaking change for the databases that
  stored it, and nothing stops a pipeline author from making that mistake.
- **A description is now required.** The identity fields come from the shared base class, which requires both, while the
  old dialog treated the description as optional.
- **Defaults are declared twice.** The environment gives the pipeline its defaults, and the same values pre-fill the
  dialog. A deployment that sets one and not the other gets a dialog that suggests something different from what an old
  database falls back to.

## Related Decisions

- `2026_06_18_rag_pipeline_route_per_run` established one deployment serving every database and the registration record
  this decision extends.
- `2026_08_31_per_database_models_and_embedding_contract` introduced the two model columns. Its choice of columns is
  superseded here, its rule that a collection's dimension is derived from the embedding model is kept.
- `2026_01_07_enable_dynamic_agent_configuration_ui` and `2026_06_15_correct_dynamic_config_form_behaviour` built the
  configuration stack that pipelines now share.
