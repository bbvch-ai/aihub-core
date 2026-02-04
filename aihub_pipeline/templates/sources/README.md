# Pre-configured Source Templates

This directory contains pre-configured templates for common cloud storage sources.
Each template provides:

1. **Environment variable template** (`.env.template`) - Required rclone configuration
2. **Pipeline example** (`pipeline.py`) - Ready-to-use Dagster pipeline definition
3. **Setup guide** (`README.md`) - Step-by-step configuration instructions

## Available Sources

### Microsoft 365
- **SharePoint** - SharePoint Online document libraries
- **OneDrive** - Personal and Business OneDrive

### Cloud Storage
- **S3** - AWS S3, MinIO, or any S3-compatible storage
- **Azure Blob** - Azure Blob Storage
- **Google Drive** - Google Workspace and personal Drive

### Infrastructure
- **SFTP** - Secure file transfer (legacy systems, on-prem)
- **Local FS** - Mounted network shares (NFS, SMB, Azure Files)

## Usage

1. Choose your source (e.g., `sharepoint/`)
2. Copy `.env.template` variables to your `.env` file
3. Follow the `README.md` setup instructions to get credentials
4. Copy the `pipeline.py` example to your `playground/` or custom pipeline location
5. Customize patterns, bucket names, and schedules as needed

## Environment Variable Convention

All rclone source configuration uses the `RCLONE_` prefix to avoid conflicts with other tools (AWS SDK, Azure CLI, etc.):

```
RCLONE_{SOURCE}_{OPTION}=value
```

Examples:
```bash
# Azure Blob
RCLONE_AZUREBLOB_NAME=azureblob
RCLONE_AZUREBLOB_TYPE=azureblob
RCLONE_AZUREBLOB_ACCOUNT=mystorageaccount
RCLONE_AZUREBLOB_KEY=your-access-key

# S3 (won't conflict with AWS_* or S3_* vars used by boto3)
RCLONE_S3_NAME=s3
RCLONE_S3_TYPE=s3
RCLONE_S3_ACCESS_KEY_ID=AKIA...
RCLONE_S3_SECRET_ACCESS_KEY=your-secret
```

Required variables for all sources:
- `RCLONE_{SOURCE}_NAME` - Remote name used in rclone
- `RCLONE_{SOURCE}_TYPE` - Backend type (onedrive, drive, s3, azureblob, sftp, local)

All other variables are passed directly to rclone as backend-specific options.

## Understanding Namespaces and Directory Structure

**Important**: The `datalake_directory_name` parameter determines the **namespace** used in the downstream RAG pipeline 
(vector store). This affects how your data is organized and searchable.

### How it works

```
Source (SharePoint/S3/etc.) → Data Lake (container/directory/) → Vector Store (namespace)
```

- **`datalake_container_name`**: The S3 bucket/container where files are stored
- **`datalake_directory_name`** (optional): The target directory in the data lake = **namespace** in vector store

### Namespace implications for RAG

The data-lake-to-vector-store pipeline creates **one namespace per directory**. When querying, you can:
- Search within a specific namespace (scoped results)
- Search across multiple namespaces (broader results)

### Decision: Single vs. Multiple Namespaces

**Option 1: Single namespace** (specify `datalake_directory_name`):
```python
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="myproject",
    datalake_directory_name="all_docs",  # Everything goes into one namespace
    ...
)
```
All synced files end up in `myproject/all-docs/...` → namespace `"all-docs"`.
Use when: All documents should be searchable as one knowledge base.

**Option 2: Preserve source structure** (omit `datalake_directory_name`):
```python
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="myproject",
    # datalake_directory_name not set - source folders become namespaces
    ...
)
```
Source folder structure is mirrored in the data lake. Each top-level source folder becomes its own namespace.

Example: If SharePoint has:
```
/HR/policies.pdf
/HR/handbook.pdf
/Engineering/specs.pdf
/Engineering/docs/guide.pdf
```
Result in data lake:
```
myproject/HR/policies.pdf         → namespace "HR"
myproject/HR/handbook.pdf         → namespace "HR"
myproject/Engineering/specs.pdf   → namespace "Engineering"
myproject/Engineering/docs/guide.pdf → namespace "Engineering"
```
Use when: Your source is already organized into logical groupings that should be separate namespaces.

**Option 3: Multiple pipelines** (explicit control):
```python
# Pipeline 1: HR documents
defs_hr = default_rclone_to_datalake_definitions(
    datalake_container_name="myproject",
    datalake_directory_name="hr-docs",
    source_remote="sharepoint:/HR/",
    ...
)

# Pipeline 2: Engineering documents
defs_eng = default_rclone_to_datalake_definitions(
    datalake_container_name="myproject",
    datalake_directory_name="eng-docs",
    source_remote="sharepoint:/Engineering/",
    ...
)
```
Use when: You need fine-grained control, different sync schedules, or want to rename namespaces.

### Important: Root-level files

When `datalake_directory_name` is not set and your source has files at the root level (not in any folder), those files 
will **not be processed** by the RAG pipeline. Only files within directories get a namespace and are indexed.

Ensure your source structure places all files within folders, or specify a `datalake_directory_name` to wrap everything 
in a single namespace.

## Creating Custom Sources

For sources not listed here, you can configure any of the 70+ rclone-supported backends.
See the [rclone documentation](https://rclone.org/overview/) for available providers.
