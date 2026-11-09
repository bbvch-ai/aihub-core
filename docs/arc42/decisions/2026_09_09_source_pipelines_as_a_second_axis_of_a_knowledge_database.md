# Source Pipelines Are a Second Axis of a Knowledge Database

## Context

A knowledge database declares which ingestion pipeline processes it and how: the pipeline announces a configuration
form, the API validates against it, the database stores one configuration object, and the pipeline reads it per run
(`2026_09_04_ingestors_announce_their_configuration_form`). How files get *into* a database was untouched by that
decision. Manual upload through the UI was the only self-service path, and the one automated path — the rclone Stage-1
factory — bound a bucket, a remote and a credential set at deploy time. Connecting a SharePoint site meant a new Dagster
code location, a compose service and `RCLONE_<SOURCE>_*` environment variables, and in practice no such code location
was ever deployed. Two syncs into one bucket shared partition identity by naming convention only, the class of bug #1236
hit.

The two backlog issues for this (#1721, #1722) were written before the ingestor decision and described a per-namespace
"sync source". Under that decision a per-namespace source cannot coexist with one ingestor per database: a database
whose namespaces are partly synced and partly uploaded has no single owner of its content, and the ingestion pipeline
maps folders to namespaces on its own. The question was therefore where a source belongs and how one deployed sync
pipeline serves many databases with different credentials.

## Decision Drivers

1. **Whoever owns a setting declares it.** A source pipeline's backend options and credentials are its business; the
   platform should render and validate them without knowing what they are, exactly as it does for ingestors.
2. **One deployment, N databases.** Adding a source to a database must not need a code location, a compose service or an
   environment variable.
3. **Stage 1 and Stage 2 stay separate.** The document ingestion pipeline is the single writer of the doc and vector
   stores; a source pipeline must not become a second one.
4. **Credentials are secrets.** They are entered once, stored encrypted, never read back, and rotate without a redeploy.
5. **A synced database has one owner of its content.** Manual edits to a synced corpus are either re-synced or removed
   on the next run, so they must not be offered.

## Alternatives Considered

1. **A namespace-level source, as the issues described.** Rejected: it conflicts with one ingestor per database (driver
   5\) and would require a second announced form keyed on the namespace plus namespace-aware partition identity, while
   the ingestion pipeline already turns a data lake's top-level folders into namespaces for free.

2. **The sync pipeline as an ingestor of its own (`IngestorType.SYNC`) that owns whole databases.** Rejected on driver
   3: to own a database it would have to run the Stage-2 graph as well, duplicating the ingestion pipeline per source
   type, or the database would have two owners.

3. **Per-call rclone connection strings instead of registered remotes.** Rejected: the credentials would travel in every
   `fs` parameter, in rclone's error logs and in the `--rc-serve` download URL.

4. **A registration record per rclone backend (`rclone_onedrive`, `rclone_sftp`, …) with flat forms.** Simpler UI, but
   every deployment-global name derives from one token per pipeline, and six tokens for one code location would break
   that invariant.

## Decision

**A knowledge database has two independent axes — its ingestor and its source — and a source pipeline announces itself,
is configured, and is resolved per run exactly like an ingestion pipeline.**

1. **`BucketEntity.source` and `source_configuration`** sit next to `ingestor` and `configuration`. No source means
   manual upload; there is no "unassigned" token. The source configuration is replaceable after creation, because
   credentials rotate, while the ingestor configuration stays create-time only.

2. **Source pipelines register into `source_pipelines`** the way ingestors register into `ingestors`: a sensor upserts
   labels, form and schema derived from one `SourcePipelineConfig(Form)` subclass. The API offers only registered
   sources and validates a submission through the same chain as the ingestor form. Ingestor and source tokens reserve
   each other, because both kinds of pipeline name their Dagster jobs after their token and the single-flight guard
   matches runs by job name across code locations.

3. **One `rclone` code location fills every database whose source names it.** Its asset graph carries no bucket, remote
   or credential. The target database travels in the `aihub/bucket` run tag on the observe and remove path and in the
   composite `{bucket}|{remote path}` partition key on the write path; one dynamic-partition registry is shared and
   reconciled per bucket, which closes the #1236 class structurally. The database's remote is rebuilt in the rclone
   daemon from the stored configuration on every run (`config/create` with `obscure` and `nonInteractive`), so a
   credential edit applies on the next run and the daemon, which keeps no config file, needs no operator action after a
   restart. Six rclone backends share one configuration class whose option groups are shown for the selected backend.

4. **Namespaces are generated.** Files land at `s3://{database}/{top-level folder}/…`; the ingestion pipeline maps the
   first path segment to a namespace as it always did. Files directly at the root of the source are skipped and counted
   visibly. A sourced database refuses manual upload, hand-made namespaces and manual document deletion, and may be
   deleted as a whole. The `auto_sync` flag retires in favour of `source`.

5. **The source pipeline talks to the ingestion pipeline the way the API does.** After every written or removed file it
   publishes a `SourceUpdatedEvent` on the owning ingestor's subject through the shared `SourceUpdatedPublisher` moved
   from the API into core, so the ingestion pipeline ingests within its sensor interval instead of at the next daily
   observation. The source pipeline never touches the doc store or the vector store.

6. **Secrets never leave the API.** Secret fields are recognised by their `Password` element, encrypted with the shared
   `SecretEncryptionService` before persisting, returned as a mask, and restored from the stored row when a client
   resubmits the mask. The pipeline decrypts them per run with the same key. Since the 2026-11-06 amendment the pipeline
   also writes one kind of secret: an OAuth token rclone refreshed.

## Consequences

### Positive

- A database is created with a source from the UI and starts syncing with no deployment or environment change; its
  credentials rotate the same way.
- Two databases synced from the same or different sources never share partitions, remotes or files.
- A second source pipeline type registers with its own token and coexists with `rclone` and with every ingestor.
- The deploy-time rclone factory, the seven source templates and the `RCLONE_<SOURCE>_*` environment loading are gone.

### Trade-offs

- **A daily schedule is the only trigger of a sync.** Files reach the ingestion pipeline within a minute of being
  synced, but the sync itself runs once a day; an on-demand trigger is a follow-up.
- **Only the observation writes a refreshed OAuth token back** (2026-11-06 amendment). Write and removal runs reset the
  token to the stored value; a token they refresh is used for that run and dropped.
- **Root-level files are never synced.** A source whose files sit directly in the chosen root folder ingests nothing
  until the files are moved into a folder; the observation reports how many were skipped.
- **A database once sourced keeps its content when the source is cleared.** Clearing only stops the sync; the files stay
  until the database is deleted or the ingestion pipeline is told otherwise.
- **The `local` backend is deployment-gated.** It reads the rclone container's own filesystem, so it is offered and run
  only where `RCLONE_LOCAL_SOURCE_ROOT` names a directory, and a database's root path is confined to it per run.
- **The MS-Graph SharePoint and local-filesystem deploy-time factories remain.** They have no deployed consumer either;
  retiring them is a separate decision.

## Related Decisions

- `2026_06_18_rag_pipeline_route_per_run` — one deployment serving every database, and the per-run routing this decision
  extends to Stage 1.
- `2026_09_04_ingestors_announce_their_configuration_form` — the registration and configuration mechanism this decision
  applies to source pipelines.
- `2026_07_18_self_service_knowledge_deletion` — the teardown flow a sourced database now also goes through.

## Amendment 2026-11-06: refreshed OAuth tokens are written back

rclone refreshes an expired access token in its in-memory daemon only, and every run rebuilt the remote from the stored
token. Microsoft rotates the refresh token on every refresh, so a pasted OneDrive or SharePoint token died once its
original refresh token expired (#1862). The pipeline is now a second writer of one secret:

- **The observation lists through a remote private to its run** (`{source}_{bucket}_obs_{run id}`), built from one read
  of the row. After the data versions it reads the token back (`config/get`) and, if rclone refreshed it, stores it
  encrypted with an atomic compare-and-set: the row must still use this source and backend, not be `deleting`, and hold
  exactly the ciphertext the run read. A user's edit in between wins. A token that lost its refresh token is refused.
  Only this run can refresh the private section, so a concurrent run on the shared remote can never put an older grant
  back.
- **Write and removal runs keep the shared `{source}_{bucket}` remote** and never write back.
- **The private remote is deleted when the run ends.** The cleanup sensor deletes one left behind by a killed run once
  Dagster reports that run finished; a killed run stays started until run monitoring ends it, up to about two hours.
- **OneDrive token mode sends `token_url`.** rclone's OneDrive setup checks the drive with a client that has no token
  URL (`onedrive.go:612`, v1.71.2, still on master), so an expired access token failed every `config/create` with
  `Post "": unsupported protocol scheme`: token-mode sources stopped about an hour after the token was pasted. The URL
  is rclone's own login host for the region, then the tenant (`common` without one), quoted. It is never stored.

**Consequences.** Google Drive does not rotate refresh tokens, so only the access token and its expiry are saved there.
Writing back replaces the stored ciphertext, so a source dialog opened before a write-back holds a mask that no longer
matches and is refused with a 400 until the page is reloaded (`2026_09_14_secret_mask_carries_identity_handle`), at most
once per database per day. rclone logs RC request and reply bodies, tokens included, at `DEBUG`; the daemon runs at
`INFO` and must stay there (`--rc-no-auth` stays dev-only, since `options/set` could raise the level at runtime).
