---
name: debug-pipeline
description: Debug a Dagster pipeline by analyzing failed materializations, sensor issues, partition problems, resource config errors, and IO manager failures. Uses Dagster MCP tools to inspect runs, assets, and errors directly. Use when user says 'pipeline failed', 'asset won't materialize', 'sensor not firing', 'S3 connection failed', 'Milvus error', 'partition stuck', 'rclone not working', 'embedding failed', 'document parsing error', or 'Dagster run failed'. Do NOT use for pipeline architecture questions (use dagster-pipelines), scaffolding new pipelines (use scaffold-pipeline), or rclone setup (use rclone-guide).
arguments:
  - name: issue
    description: Description of the pipeline issue (e.g., "asset won't materialize", "sensor not firing", "S3 connection failed", "partition stuck")
allowed-tools: Read, Grep, Glob, Bash
---

# Debug Pipeline -- Troubleshooting Guide

Investigate the pipeline issue described via `$ARGUMENTS`.

Follow the diagnostic steps below. Start with Dagster MCP tools to gather concrete error data, then investigate the
code.

______________________________________________________________________

## Step 1: Triage via Dagster MCP

Use the Dagster MCP tools to gather diagnostic data before reading code. These tools query the running Dagster instance
directly.

### 1a. Discover What's Deployed

Use `mcp__dagster__list_repositories` to see all code locations. Then use `mcp__dagster__list_assets` and
`mcp__dagster__list_jobs` with the repository location and name to understand what's running.

### 1b. Find Recent Failures

Use `mcp__dagster__recent_runs` (default limit: 10) to find failed runs. Look for runs with `FAILURE` status.

If the user hasn't provided a run ID, show them the recent failures and ask which one to investigate. If only one
failure exists, proceed with that.

### 1c. Get Detailed Error Info

Use `mcp__dagster__get_run_info` with the run ID to get:

- Run status and timestamps
- Error messages and stack traces
- Step-level failure details
- Run configuration

This replaces manually checking the Dagster UI. The error message from `get_run_info` is usually sufficient to identify
the root cause.

### 1d. Check Asset Status

Use `mcp__dagster__get_asset_info` with the asset key to check:

- Latest materialization status
- Partition status
- Upstream dependency state

If the user mentions a specific asset but not a run ID, start here. Ask the user for the asset key if it's not clear
from context.

### When to Ask the User

Ask the user for identifying information when you need it:

- **Run ID**: "Which run failed? I can see these recent failures: [list from recent_runs]"
- **Asset key**: "Which asset is failing? Here are the assets in this repository: [list from list_assets]"
- **Repository**: Only ask if multiple code locations exist (rare in dev)

______________________________________________________________________

## Step 2: Diagnose by Symptom

Use the error information from Step 1 to match against these known patterns.

### Asset Won't Materialize

**Possible causes**:

1. **Automation condition not triggered**: Check that upstream asset has a version change

   - Read: `aihub_pipeline/aihub_pipeline/automation/all_deps_completed.py`
   - Verify asset has `AutomationCondition.eager()` or `all_deps_completed`

2. **Automation sensor not running**: The sensor must be included in `Definitions`

   - Read: `aihub_pipeline/aihub_pipeline/sensors/factory.py`
   - Verify `default_automation_sensor(assets)` is in the sensors list

3. **Partition key mismatch**: Dynamic partitions may not have been created

   - Read: `aihub_pipeline/aihub_pipeline/util/partition_utils.py`
   - Check `max_partitions` limit -- if exceeded, some partitions are deferred

4. **Resource missing**: Op can't find required resource

   - Check the `resources` dict in the `Definitions` matches all `ResourceParam[T]` types in ops
   - Common missing: `table_refinement` (only added when `with_table_refinement=True`)

5. **IO Manager mismatch**: Asset output type doesn't match IO manager expectations

   - S3DataLakeIOManager expects `DataLakeFile`
   - DocStoreIOManager expects `RefDocDocument`
   - VectorStoreIOManager expects `list[TextNode]`

### Observable Asset Returns No Changes

**Possible causes**:

1. **No files in source**: The data lake / rclone remote is empty

   - Check S3 bucket contents
   - For rclone: verify remote is configured and accessible

2. **Hash unchanged**: Content hash matches previous observation

   - Data versions are content-based -- if file content didn't change, no version change
   - Read: `aihub_pipeline/aihub_pipeline/ops/data_lake/data_version_by_partition_for_data_lake_files.py`

3. **Partition limit reached**: `max_partitions` caps how many partitions are processed per run

   - Default: 1000 partitions per observation
   - If more files exist, they'll be picked up in subsequent runs

### Sensor Not Firing

**Check automation sensor**:

- Read: `aihub_pipeline/aihub_pipeline/sensors/factory.py`
- Is `default_automation_sensor(assets)` in the `Definitions.sensors` list?
- Is `minimum_interval_seconds` appropriate? (default: 60s)

**Check NATS sensor**:

- Read: `aihub_pipeline/aihub_pipeline/sensors/nats/nats_document_uploaded_sensor.py`
- Is NATS reachable? Check `NATS_ENDPOINT` env var
- Is the JetStream stream created? (poller creates it on first run)
- Are `SourceUpdatedEvent` messages being published?
- Check consumer name uniqueness

### Embedding Failures

**Symptoms**: `RetryPolicy` exhausted, `ValidationError` in embed_nodes

- Read: `aihub_pipeline/aihub_pipeline/ops/nodes/embed_nodes.py`
- LiteLLM endpoint unreachable
- Token limit exceeded: document too large after chunking
- Batch splitting: on `ValidationError`, batch is recursively split in half
- After 6 retries with exponential backoff, op fails permanently

### Document Parsing Failures

**Symptoms**: `parse_document_from_data_lake` fails

- Read: `aihub_pipeline/aihub_pipeline/ops/data_lake/parse_document_from_data_lake.py`
- Read: `aihub_pipeline/aihub_pipeline/resources/parser/DocumentParserResource.py`
- Docling service not running (if using remote Docling)
- Unsupported file type
- Corrupted file content
- Large file timeout

______________________________________________________________________

## Step 3: Check Infrastructure Connections

### S3/MinIO

**Symptoms**: `botocore.exceptions.ClientError`, `EndpointConnectionError`

Settings: `aihub_lib/aihub_lib/infrastructure/s3/S3StorageSettings.py`

| Env Variable    | Purpose                     |
| --------------- | --------------------------- |
| `S3_ENDPOINT`   | MinIO endpoint URL          |
| `S3_ACCESS_KEY` | Access key                  |
| `S3_SECRET_KEY` | Secret key                  |
| `S3_REGION`     | Region (default: us-east-1) |

Common issues: MinIO not running (`docker compose -f docker-compose.dev.yml ps minio`), bucket doesn't exist, wrong
endpoint (inside Docker use `http://minio:9000`, not `localhost`).

### Milvus

**Symptoms**: `MilvusException`, connection timeout

Settings: `aihub_lib/aihub_lib/infrastructure/milvus/MilvusSettings.py`

| Env Variable       | Purpose                      |
| ------------------ | ---------------------------- |
| `MILVUS_URL`       | Milvus endpoint              |
| `MILVUS_TOKEN`     | Auth token                   |
| `MILVUS_DIMENSION` | Default embedding dimensions |

Common issues: Milvus not running, dimension mismatch (embedding model dimensions must match collection dimensions),
collection not found (auto-created on first insert).

### MongoDB/FerretDB

**Symptoms**: `ConnectionFailure`, `OperationFailure`

Settings: `aihub_lib/aihub_lib/infrastructure/mongo/MongoSettings.py`

Common issues: FerretDB not running, database name mismatch (derived from bucket name via
`get_db_name_from_bucket_name()` in `aihub_pipeline/aihub_pipeline/util/bucket_utils.py`).

### Rclone

**Symptoms**: `ClientConnectorError`, `403 Forbidden`, remote not found

Settings: `aihub_lib/aihub_lib/infrastructure/rclone/RcloneSettings.py` Client:
`aihub_pipeline/aihub_pipeline/resources/rclone/RcloneClient.py`

| Env Variable     | Purpose         |
| ---------------- | --------------- |
| `RCLONE_URL`     | RC API endpoint |
| `RCLONE_RC_USER` | Auth username   |
| `RCLONE_RC_PASS` | Auth password   |

Common issues: Rclone service not running, remote not configured, OAuth token expired, wrong `--rc-serve` flag (required
for file downloads).

### NATS

Settings: `aihub_lib/aihub_lib/infrastructure/nats/NatsSettings.py`

Common issues: NATS not running, JetStream not enabled, stream/consumer not created.

### Docker Quick Check

```bash
# Check which services are running
docker compose -f docker-compose.dev.yml ps

# Check specific service logs
docker compose -f docker-compose.dev.yml logs <service> --tail=50
```

______________________________________________________________________

## Step 4: Common Error Patterns

### "No partition definition found for the upstream asset"

IO manager can't find partition info. Check asset has `partitions_def` set and IO manager handles both partitioned and
non-partitioned cases.

### "Expected a DataLakeFile or a list of DataLakeFiles"

S3DataLakeIOManager received wrong type. Check asset's `io_manager_key` matches the correct IO manager and op return
type matches expectations.

### "Cannot connect to host minio:9000"

S3/MinIO unreachable. Check MinIO Docker service is running, `S3_ENDPOINT` env var is correct, network connectivity
between Dagster and MinIO containers.

### "No nodes found for document after retrying for 30 seconds"

VectorStoreIOManager eventual consistency timeout. Check Milvus is healthy, nodes were actually inserted (check
collection), and document ID conversion (URI to hash) is consistent.

### "Rclone remote not found"

Read: `aihub_pipeline/aihub_pipeline/resources/rclone/RcloneResource.py`

Remote not configured in rclone, `rclone_config_dict` not provided or malformed, remote name doesn't match
`source_remote` prefix.

______________________________________________________________________

## Step 5: Re-trigger After Fix

Once the root cause is fixed, use MCP tools to verify the fix:

- **Re-materialize an asset**: Use `mcp__dagster__materialize_asset` with the asset key, repository location, and
  repository name
- **Re-launch a job**: Use `mcp__dagster__launch_run` with the job name and repository info
- **Verify success**: Use `mcp__dagster__recent_runs` and `mcp__dagster__get_run_info` to confirm the re-run succeeded
- **Terminate stuck run**: Use `mcp__dagster__terminate_run` if a run is hanging
