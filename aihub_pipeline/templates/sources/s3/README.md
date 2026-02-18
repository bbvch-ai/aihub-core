# AWS S3 Pipeline Template

Simple pipeline to sync AWS S3 documents to AI-Hub data lake.

## Setup

**1. Create AWS Access Keys**

- Go to AWS IAM Console → Users → Security credentials
- Create access key
- Note **Access Key ID** and **Secret Access Key**

**2. Configure Environment**

Copy variables from `.env.template` to your `.env` and fill in:

```bash
RCLONE_S3_NAME=s3
RCLONE_S3_TYPE=s3
RCLONE_S3_ACCESS_KEY_ID=AKIA...
RCLONE_S3_SECRET_ACCESS_KEY=your-secret-key
RCLONE_S3_REGION=us-east-1
```

### Advanced Options

**Custom endpoint (MinIO, SeaweedFS, etc.):**

```bash
RCLONE_S3_ENDPOINT=https://minio.example.com:9000
```

**Access Control:**

```bash
RCLONE_S3_ACL=private
```

**Storage Class:**

```bash
RCLONE_S3_STORAGE_CLASS=STANDARD_IA
```

**3. Update Pipeline**

Edit `pipeline.py` to point to your bucket:

```python
source_remote=f"{s3.name}:my-bucket-name/path/to/folder"
```

**4. Run Pipeline**

```bash
poetry run dagster dev -f pipeline.py
```

