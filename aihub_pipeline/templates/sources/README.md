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

## Creating Custom Sources

For sources not listed here, you can configure any of the 70+ rclone-supported backends.
See the [rclone documentation](https://rclone.org/overview/) for available providers.
