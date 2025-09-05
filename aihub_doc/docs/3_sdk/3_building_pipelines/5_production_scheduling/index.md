---
title: Production Scheduling
index: 5
---

[WIP]

# Production Scheduling

Deploying pipelines to production requires careful consideration of scheduling, resource management, and operational
reliability. This section covers strategies for running AI-Hub pipelines at scale, from basic scheduling patterns to
advanced deployment configurations.

## Scheduling strategies

### Observable-driven processing (recommended)

The preferred approach uses observable assets with automation conditions to process data reactively:

```python
# Primary strategy: React to data changes
@observable_source_asset(
    key=AssetKey(["production", "data_lake"]),
    partitions_def=document_partitions,
)
def production_data_observer(context: OpExecutionContext) -> DataVersions:
    """Monitor production data lake for document changes."""
    return scan_for_changed_documents(context)

# Downstream assets process automatically
@graph_asset(
    key=AssetKey(["production", "documents"]),
    ins={"data_lake_file": AssetIn(key=AssetKey(["production", "data_lake"]))},
    automation_condition=AutomationCondition.eager(),
)
def production_documents(data_lake_file: DataLakeFile) -> RefDocDocument:
    return process_document(data_lake_file)
```

**Benefits:**

- Immediate response to data changes
- Efficient resource utilization
- Natural backpressure handling
- Scales automatically with data volume

### Scheduled processing patterns

For scenarios requiring time-based processing, use Dagster's scheduling capabilities:

```python
from aihub_pipeline.schedules.factory import daily_schedule_at, hourly_schedule

# Daily batch processing
daily_batch = daily_schedule_at(
    job=observe_source_job(observable_asset, "production"),
    hour=2,  # Run at 2 AM
    minute=0,
    timezone="UTC",
)

# Hourly incremental updates  
hourly_incremental = hourly_schedule(
    job=materialize_new_documents_job,
    minute=15,  # Run at :15 past each hour
)

# Custom schedule with cron expression
weekly_maintenance = ScheduleDefinition(
    job=cleanup_old_partitions_job,
    cron_schedule="0 3 * * SUN",  # Sunday at 3 AM
    execution_timezone="Europe/Zurich",
)
```

### Hybrid approach

Combine observable and scheduled processing for robust production systems:

```python
# Immediate processing for urgent documents
urgent_automation = (
    AutomationCondition.eager() &
    AutomationCondition.in_latest_time_window()
)

# Scheduled backup processing for missed items
backup_schedule = daily_schedule_at(
    job=full_resync_job,
    hour=4,
    minute=0,
)

defs = Definitions(
    assets=assets,
    schedules=[backup_schedule],
    sensors=[default_automation_sensor(assets)],
    # Both reactive and scheduled processing
)
```

## Resource configuration for production

### Environment-specific resources

Configure different resource settings for production environments:

```python
def production_resources() -> dict[str, ConfigurableResource]:
    """Production-grade resource configuration."""
    return {
        # High-performance document parsing
        "document_parser": DocumentParserResource(
            loader_type=LoaderType.BOTH,
            timeout=300,  # Longer timeout for complex documents
            max_retries=3,
        ),
        
        # Production vector store
        **mongo_aisearch_storage_context_resources(
            store_name="production_knowledge",
            namespace_name="main",
            connection_pool_size=20,
        ),
        
        # Production data lake
        **azure_data_lake_resources(
            account_name=os.getenv("AZURE_STORAGE_ACCOUNT"),
            container_name="production-documents",
            directory_name="processed",
            connection_timeout=60,
        ),
        
        # High-capacity embedding model
        "embedding_model": EmbeddingModelResource(
            embedding_config=EmbeddingModelConfig(
                model_name="azure/text-embedding-3-large",
                batch_size=100,
                max_concurrent_requests=10,
            )
        ),
        
        # Production language model
        "language_model": LanguageModelResource(
            llm_config=LLMConfig(
                model_name="azure/gpt-4o",
                max_tokens=4000,
                temperature=0.1,
                request_timeout=120,
            )
        ),
    }
```

### Executor configuration

Configure executors for production workloads:

```python
from dagster import multiprocess_executor, docker_executor

def production_executor():
    """Production executor with optimized settings."""
    return multiprocess_executor.configured({
        "max_concurrent": 8,  # Based on available CPU cores
        "tag_concurrency_limits": {
            "document_parsing": 4,    # Limit CPU-intensive operations
            "embedding": 6,           # Limit API rate limits
            "vector_store": 3,        # Limit database connections
        }
    })

# For containerized deployments
def docker_production_executor():
    """Docker executor for Kubernetes/container deployments."""
    return docker_executor.configured({
        "image": "your-registry/aihub-pipeline:latest",
        "container_kwargs": {
            "volumes": ["/data:/data"],
            "environment": ["ENV=production"],
            "cpu_limit": "2.0",
            "memory_limit": "4G",
        }
    })
```

## Job definitions and organization

### Structured job organization

Organize jobs by functionality and operational requirements:

```python
# Source observation jobs
observe_sharepoint_job = observe_source_job(
    observable_asset=sharepoint_observer,
    namespace_name="production",
    job_name="observe_sharepoint",
)

observe_filesystem_job = observe_source_job(
    observable_asset=filesystem_observer,
    namespace_name="production", 
    job_name="observe_filesystem",
)

# Processing jobs
process_documents_job = materialize_asset_job(
    namespace_name="production",
    job_name="process_documents",
    asset_selection=AssetSelection.keys(AssetKey(["production", "documents"])),
)

generate_embeddings_job = materialize_asset_job(
    namespace_name="production",
    job_name="generate_embeddings",
    asset_selection=AssetSelection.keys(AssetKey(["production", "nodes"])),
)

# Maintenance jobs
cleanup_job = materialize_asset_job(
    namespace_name="production",
    job_name="cleanup_old_partitions", 
    asset_selection=AssetSelection.keys(AssetKey(["production", "removed_documents"])),
)

# Health check job
health_check_job = define_asset_job(
    name="health_check",
    selection=AssetSelection.keys(AssetKey(["production", "system_health"])),
    description="Verify system health and connectivity",
)
```

### Job configurations

Configure jobs for different operational scenarios:

```python
# High-priority processing with more resources
high_priority_config = RunConfig(
    execution=ExecutionConfig(
        multiprocess=MultiprocessExecutorConfig(
            max_concurrent=12,
            tag_concurrency_limits={"urgent": 8}
        )
    ),
    resources={
        "embedding_model": EmbeddingModelResource.configured({
            "batch_size": 50,
            "max_concurrent_requests": 20,  # Higher concurrency
        })
    }
)

# Resource-constrained processing for off-peak hours
low_priority_config = RunConfig(
    execution=ExecutionConfig(
        multiprocess=MultiprocessExecutorConfig(
            max_concurrent=4,
            tag_concurrency_limits={"background": 2}
        )
    )
)
```

## Deployment patterns

### Docker containerization

Package pipelines as Docker containers for consistent deployment:

```dockerfile
# Dockerfile for pipeline deployment
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main

# Copy pipeline code
COPY aihub_pipeline/ ./aihub_pipeline/
COPY app/ ./app/

# Set environment variables
ENV DAGSTER_HOME=/app/dagster_home
ENV PYTHONPATH=/app

# Create dagster home directory
RUN mkdir -p $DAGSTER_HOME

# Expose Dagster port
EXPOSE 3000

# Run Dagster
CMD ["dagster", "dev", "-m", "app.production", "--host", "0.0.0.0", "--port", "3000"]
```

### Kubernetes deployment

Deploy pipelines on Kubernetes for scalability and reliability:

```yaml
# kubernetes/pipeline-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aihub-pipeline
  namespace: aihub-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aihub-pipeline
  template:
    metadata:
      labels:
        app: aihub-pipeline
    spec:
      containers:
      - name: pipeline
        image: your-registry/aihub-pipeline:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi" 
            cpu: "2"
        env:
        - name: DAGSTER_POSTGRES_HOST
          value: "postgresql-service"
        - name: DAGSTER_POSTGRES_DB
          value: "dagster"
        - name: AZURE_STORAGE_ACCOUNT
          valueFrom:
            secretKeyRef:
              name: azure-credentials
              key: storage-account
        ports:
        - containerPort: 3000
        livenessProbe:
          httpGet:
            path: /server_info
            port: 3000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /server_info
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: aihub-pipeline-service
  namespace: aihub-production
spec:
  selector:
    app: aihub-pipeline
  ports:
  - port: 80
    targetPort: 3000
  type: LoadBalancer
```

### Helm chart deployment

Use Helm for templated Kubernetes deployments:

```yaml
# helm/values.yaml
replicaCount: 2

image:
  repository: your-registry/aihub-pipeline
  tag: "latest"
  pullPolicy: IfNotPresent

resources:
  limits:
    cpu: 2
    memory: 4Gi
  requests:
    cpu: 1
    memory: 2Gi

env:
  DAGSTER_POSTGRES_HOST: postgresql-service
  DAGSTER_POSTGRES_DB: dagster

secrets:
  azure:
    storageAccount: "your-storage-account"
    storageKey: "your-storage-key"

ingress:
  enabled: true
  host: pipeline.your-domain.com
  tls: true

postgresql:
  enabled: true
  auth:
    database: dagster
    username: dagster
    password: secure-password
```

## Monitoring and alerting

### Health checks and sensors

Implement comprehensive monitoring:

```python
from dagster import sensor, SensorEvaluationContext, RunRequest

@sensor(job=health_check_job)
def system_health_sensor(context: SensorEvaluationContext):
    """Monitor system health and trigger checks."""
    
    # Check last successful run time
    last_run = context.instance.get_latest_run_for_job(health_check_job.name)
    
    if last_run is None or (
        datetime.utcnow() - last_run.created_timestamp > timedelta(hours=1)
    ):
        return RunRequest(
            run_key=f"health_check_{datetime.utcnow().isoformat()}",
            tags={"priority": "high", "type": "health_check"}
        )

@sensor(job=process_documents_job)
def processing_backlog_sensor(context: SensorEvaluationContext):
    """Alert when processing backlog grows too large."""
    
    # Check partition backlog
    backlog_size = get_unprocessed_partition_count()
    
    if backlog_size > 100:  # Alert threshold
        context.log.warning(f"Processing backlog: {backlog_size} partitions")
        
        # Optionally trigger additional processing capacity
        return RunRequest(
            run_key=f"backlog_processing_{datetime.utcnow().isoformat()}",
            tags={"priority": "high", "reason": "backlog_clearing"}
        )
```

### Metrics and observability

Integrate with monitoring systems:

```python
@op
def document_processing_with_metrics(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
) -> RefDocDocument:
    """Document processing with comprehensive metrics."""
    
    start_time = time.time()
    
    try:
        result = parse_document_from_data_lake(context, data_lake_file)
        
        # Success metrics
        processing_time = time.time() - start_time
        context.add_output_metadata({
            "processing_time_seconds": processing_time,
            "document_size_bytes": len(result.text.encode()),
            "word_count": len(result.text.split()),
            "status": "success",
        })
        
        # Custom metrics for external monitoring
        emit_metric("document_processing_time", processing_time, 
                   tags={"filetype": data_lake_file.filetype})
        emit_metric("document_processing_success", 1)
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        context.add_output_metadata({
            "processing_time_seconds": processing_time,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "status": "failed",
        })
        
        emit_metric("document_processing_failure", 1,
                   tags={"error_type": type(e).__name__})
        
        raise
```

## Error handling and recovery

### Retry policies

Implement robust retry mechanisms:

```python
from dagster import RetryPolicy

# Configure retry policies for different operation types
document_parsing_retry = RetryPolicy(
    max_retries=3,
    delay=60,  # 1 minute initial delay
    backoff=Backoff.EXPONENTIAL,
    jitter=Jitter.PLUS_MINUS,
)

api_call_retry = RetryPolicy(
    max_retries=5,
    delay=30,
    backoff=Backoff.LINEAR,
)

# Apply to operations
@op(
    retry_policy=document_parsing_retry,
    tags={"operation_type": "document_parsing"}
)
def resilient_document_parsing(context, data_lake_file):
    """Document parsing with automatic retries."""
    pass

@op(
    retry_policy=api_call_retry,
    tags={"operation_type": "api_call"}
)
def resilient_api_embedding(context, nodes):
    """API embedding with retry logic."""
    pass
```

### Failure isolation

Prevent cascade failures:

```python
@op
def isolated_document_processing(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
) -> RefDocDocument:
    """Process document with failure isolation."""
    
    try:
        return parse_document_from_data_lake(context, data_lake_file)
        
    except Exception as e:
        # Log error but don't fail the entire pipeline
        context.log.error(f"Failed to process {data_lake_file.uri}: {e}")
        
        # Create minimal document for downstream processing
        return RefDocDocument(
            doc_id=data_lake_file.uri,
            text="",  # Empty content
            metadata={
                "processing_error": str(e),
                "error_type": type(e).__name__,
                "processed_at": datetime.utcnow().isoformat(),
            }
        )
```

## Performance optimization

### Resource tuning

Optimize resource allocation for production workloads:

```python
# Tune concurrency based on resource constraints
production_config = {
    # CPU-intensive operations
    "document_parsing": {
        "max_concurrent": min(4, multiprocessing.cpu_count()),
        "memory_limit": "2GB",
    },
    
    # I/O-intensive operations  
    "data_lake_operations": {
        "max_concurrent": 20,
        "connection_pool_size": 10,
    },
    
    # API-rate-limited operations
    "embedding_generation": {
        "max_concurrent": 8,
        "requests_per_minute": 1000,
    },
}
```

### Caching strategies

Implement intelligent caching to reduce redundant processing:

```python
@op
def cached_document_processing(
    context: OpExecutionContext,
    data_lake_file: DataLakeFile,
) -> RefDocDocument:
    """Process document with intelligent caching."""
    
    # Check if document was already processed
    cache_key = f"{data_lake_file.uri}:{data_lake_file.modified_time}"
    
    cached_result = get_from_cache(cache_key)
    if cached_result:
        context.log.info(f"Cache hit for {data_lake_file.uri}")
        return cached_result
    
    # Process document
    result = parse_document_from_data_lake(context, data_lake_file)
    
    # Cache result for future runs
    set_cache(cache_key, result, ttl=timedelta(hours=24))
    
    return result
```

## Operational runbooks

### Common operational procedures

Document standard operational procedures:

```python
# Runbook: Emergency pipeline shutdown
def emergency_shutdown():
    """
    Emergency procedure to halt all pipeline processing.
    
    Steps:
    1. Disable all schedules
    2. Cancel running jobs
    3. Mark system as maintenance mode
    """
    pass

# Runbook: Backlog recovery
def recover_from_backlog():
    """
    Procedure to recover from large processing backlogs.
    
    Steps:
    1. Assess backlog size
    2. Scale up processing capacity
    3. Prioritize critical documents
    4. Monitor progress
    """
    pass

# Runbook: Resource exhaustion response
def handle_resource_exhaustion():
    """
    Response to resource exhaustion scenarios.
    
    Steps:
    1. Reduce processing concurrency
    2. Clear unnecessary caches
    3. Scale resources if possible
    4. Alert operations team
    """
    pass
```

## Next steps

With production scheduling mastered, complete your pipeline expertise with:

- [Pipeline observation](../6_pipeline_observation/) for monitoring and debugging production systems
