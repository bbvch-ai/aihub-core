---
name: debug-pipeline
description: >-
  Debug a Dagster pipeline by analyzing failed materializations, sensor issues, partition problems,
  resource configuration errors, and IO manager failures. Use when a pipeline run fails, sensors
  stop firing, assets don't materialize, or rclone/S3/Milvus connections fail.
arguments:
  - name: issue
    description: Description of the pipeline issue (e.g., "asset won't materialize", "sensor not firing", "S3 connection failed", "partition stuck")
allowed-tools: Read, Grep, Glob, Bash
---

# Debug Pipeline — Troubleshooting Guide

Investigate the pipeline issue described via `$ARGUMENTS`.

Follow the diagnostic steps below systematically. Read the referenced files to understand the code patterns, then help
identify the root cause.

---

## Step 1: Understand the Pipeline Structure

Read the pipeline's definition file to understand which assets, resources, sensors, and schedules are configured.

**Key entry point**: The `Definitions` object in the pipeline module (usually `__init__.py` or a file using
`definitions_util.py` factories).

```
Read: aihub_pipeline/aihub_pipeline/util/definitions_util.py
Read: aihub_pipeline/playground/__init__.py
```

Check:
- Which `default_*_definitions()` factory is used?
- What assets are included?
- What resources are configured?
- Are sensors and schedules present?

---

## Step 2: Diagnose by Symptom

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
   - Check `max_partitions` limit — if exceeded, some partitions are deferred

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
   - Data versions are content-based — if file content didn't change, no version change
   - Read: `aihub_pipeline/aihub_pipeline/ops/data_lake/data_version_by_partition_for_data_lake_files.py`

3. **Partition limit reached**: `max_partitions` caps how many partitions are processed per run
   - Default: 1000 partitions per observation
   - If more files exist, they'll be picked up in subsequent runs

### Sensor Not Firing

**Check automation sensor**:
```
Read: aihub_pipeline/aihub_pipeline/sensors/factory.py
```
- Is `default_automation_sensor(assets)` in the `Definitions.sensors` list?
- Is `minimum_interval_seconds` appropriate? (default: 60s)
- Check Dagster UI: Sensors tab → is the sensor status "Running"?

**Check NATS sensor**:
```
Read: aihub_pipeline/aihub_pipeline/sensors/nats/nats_document_uploaded_sensor.py
```
- Is NATS reachable? Check `NATS_ENDPOINT` env var
- Is the JetStream stream created? (poller creates it on first run)
- Are `SourceUpdatedEvent` messages being published?
- Check consumer name uniqueness

### S3/MinIO Connection Issues

**Symptoms**: `botocore.exceptions.ClientError`, `EndpointConnectionError`

**Check settings**:
```
Grep for: class S3StorageSettings
Read: aihub_lib/aihub_lib/infrastructure/s3/S3StorageSettings.py
```

| Env Variable | Purpose |
|-------------|---------|
| `S3_ENDPOINT` | MinIO endpoint URL |
| `S3_ACCESS_KEY` | Access key |
| `S3_SECRET_KEY` | Secret key |
| `S3_REGION` | Region (default: us-east-1) |

**Common issues**:
- MinIO not running: `docker compose ps minio`
- Bucket doesn't exist: create via MinIO console or `mc mb`
- Wrong endpoint: inside Docker use `http://minio:9000`, not `localhost`

### Milvus Connection Issues

**Symptoms**: `MilvusException`, connection timeout

**Check settings**:
```
Grep for: class MilvusSettings
Read: aihub_lib/aihub_lib/infrastructure/milvus/MilvusSettings.py
```

| Env Variable | Purpose |
|-------------|---------|
| `MILVUS_URL` | Milvus endpoint |
| `MILVUS_TOKEN` | Auth token |
| `MILVUS_DIMENSION` | Default embedding dimensions |

**Common issues**:
- Milvus not running: `docker compose ps milvus`
- Dimension mismatch: embedding model dimensions must match collection dimensions
- Collection not found: auto-created on first insert, but check collection name

### MongoDB/FerretDB Connection Issues

**Symptoms**: `ConnectionFailure`, `OperationFailure`

**Check settings**:
```
Grep for: class MongoSettings
Read: aihub_lib/aihub_lib/infrastructure/mongo/MongoSettings.py
```

**Common issues**:
- FerretDB not running: `docker compose ps ferretdb`
- Database name mismatch: derived from bucket name via `get_db_name_from_bucket_name()`
- Read: `aihub_pipeline/aihub_pipeline/util/bucket_utils.py`

### Rclone Connection Issues

**Symptoms**: `ClientConnectorError`, `403 Forbidden`, remote not found

**Check settings**:
```
Read: aihub_lib/aihub_lib/infrastructure/rclone/RcloneSettings.py
Read: aihub_pipeline/aihub_pipeline/resources/rclone/RcloneClient.py
```

| Env Variable | Purpose |
|-------------|---------|
| `RCLONE_URL` | RC API endpoint |
| `RCLONE_RC_USER` | Auth username |
| `RCLONE_RC_PASS` | Auth password |

**Common issues**:
- Rclone service not running: `docker compose ps rclone`
- Remote not configured: check `rclone_config_dict` or `rclone config` in container
- OAuth token expired: re-authenticate the remote
- Wrong `--rc-serve` flag: required for file downloads

### Embedding Failures

**Symptoms**: `RetryPolicy` exhausted, `ValidationError` in embed_nodes

```
Read: aihub_pipeline/aihub_pipeline/ops/nodes/embed_nodes.py
```

**Common issues**:
- LiteLLM endpoint unreachable
- Token limit exceeded: document too large after chunking
- Batch splitting: on `ValidationError`, batch is recursively split in half
- After 6 retries with exponential backoff, op fails permanently

### Document Parsing Failures

**Symptoms**: `parse_document_from_data_lake` fails

```
Read: aihub_pipeline/aihub_pipeline/ops/data_lake/parse_document_from_data_lake.py
Read: aihub_pipeline/aihub_pipeline/resources/parser/DocumentParserResource.py
```

**Common issues**:
- Docling service not running (if using remote Docling)
- Unsupported file type
- Corrupted file content
- Large file timeout

---

## Step 3: Check Docker Infrastructure

```bash
# Check which services are running
docker compose -f docker-compose.dev.yml ps

# Check specific service logs
docker compose -f docker-compose.dev.yml logs minio --tail=50
docker compose -f docker-compose.dev.yml logs ferretdb --tail=50
docker compose -f docker-compose.dev.yml logs milvus --tail=50
docker compose -f docker-compose.dev.yml logs rclone --tail=50
docker compose -f docker-compose.dev.yml logs nats --tail=50
```

---

## Step 4: Check Dagster UI

**Access**: http://localhost:3000 (playground) or http://localhost:3002 (production)

### What to Check

| Section | What to Look For |
|---------|-----------------|
| **Assets** | Materialization status, latest run, partition status |
| **Runs** | Failed runs → expand for error logs and stack traces |
| **Sensors** | Running status, last tick, evaluation errors |
| **Schedules** | Running status, next scheduled tick |
| **Resources** | Configuration values (check for missing/wrong values) |

---

## Step 5: Run Pipeline Locally

```bash
cd aihub_pipeline
poetry shell

# Start playground (Dagster dev server)
make playground
# or
poetry run dagster dev -m playground

# Access Dagster UI at http://localhost:3000
```

### Trigger Manually

In Dagster UI:
1. Go to **Assets** tab
2. Select the observable source asset
3. Click **Observe** to trigger source observation
4. Downstream assets will auto-materialize if versions changed

### Check Logs

In Dagster UI:
1. Go to **Runs** tab
2. Click on the failed run
3. Expand each step to see logs
4. Look for ERROR level entries

---

## Step 6: Common Error Patterns

### "No partition definition found for the upstream asset"

IO manager can't find partition info. Check:
- Asset has `partitions_def` set
- IO manager handles both partitioned and non-partitioned cases
- Upstream asset is actually partitioned

### "Expected a DataLakeFile or a list of DataLakeFiles"

S3DataLakeIOManager received wrong type. Check:
- Asset's `io_manager_key` matches the correct IO manager
- Op return type matches IO manager expectations

### "Cannot connect to host minio:9000"

S3/MinIO unreachable. Check:
- MinIO Docker service is running
- `S3_ENDPOINT` env var is correct
- Network connectivity between Dagster and MinIO containers

### "No nodes found for document after retrying for 30 seconds"

VectorStoreIOManager eventual consistency timeout. Check:
- Milvus is healthy and accepting queries
- Nodes were actually inserted (check Milvus collection)
- Document ID conversion (URI → hash) is consistent

### "Rclone remote not found"

```
Read: aihub_pipeline/aihub_pipeline/resources/rclone/RcloneResource.py
```
- Remote not configured in rclone
- `rclone_config_dict` not provided or malformed
- Remote name doesn't match `source_remote` prefix

---

## Key File Reference for Debugging

| Category | File |
|----------|------|
| **Pipeline factory** | `aihub_pipeline/aihub_pipeline/util/definitions_util.py` |
| **Resource factory** | `aihub_pipeline/aihub_pipeline/resources/factory.py` |
| **Partition utils** | `aihub_pipeline/aihub_pipeline/util/partition_utils.py` |
| **Automation** | `aihub_pipeline/aihub_pipeline/automation/all_deps_completed.py` |
| **Automation sensor** | `aihub_pipeline/aihub_pipeline/sensors/factory.py` |
| **NATS sensor** | `aihub_pipeline/aihub_pipeline/sensors/nats/nats_document_uploaded_sensor.py` |
| **S3 IO Manager** | `aihub_pipeline/aihub_pipeline/io/S3DataLakeIOManager.py` |
| **Vector IO Manager** | `aihub_pipeline/aihub_pipeline/io/VectorStoreIOManager.py` |
| **Doc Store IO Manager** | `aihub_pipeline/aihub_pipeline/io/DocStoreIOManager.py` |
| **Rclone IO Manager** | `aihub_pipeline/aihub_pipeline/io/RcloneIOManager.py` |
| **Embed nodes (retry)** | `aihub_pipeline/aihub_pipeline/ops/nodes/embed_nodes.py` |
| **Document parser** | `aihub_pipeline/aihub_pipeline/resources/parser/DocumentParserResource.py` |
| **Rclone client** | `aihub_pipeline/aihub_pipeline/resources/rclone/RcloneClient.py` |
| **Rclone resource** | `aihub_pipeline/aihub_pipeline/resources/rclone/RcloneResource.py` |
| **S3 settings** | `aihub_lib/aihub_lib/infrastructure/s3/S3StorageSettings.py` |
| **Milvus settings** | `aihub_lib/aihub_lib/infrastructure/milvus/MilvusSettings.py` |
| **Rclone settings** | `aihub_lib/aihub_lib/infrastructure/rclone/RcloneSettings.py` |
| **NATS settings** | `aihub_lib/aihub_lib/infrastructure/nats/NatsSettings.py` |
| **Bucket → store name** | `aihub_pipeline/aihub_pipeline/util/bucket_utils.py` |
| **Executor** | `aihub_pipeline/aihub_pipeline/executors/factory.py` |
