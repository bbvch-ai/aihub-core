# AWS S3 Pipeline Template

Simple pipeline to sync AWS S3 documents to AI-Hub data lake.

## Setup

**1. Create AWS Access Keys**

- Go to AWS IAM Console → Users → Security credentials
- Create access key
- Note **Access Key ID** and **Secret Access Key**

**2. Configure Environment**

Copy variables from `.env.template` to your `.env.dev` and fill in:

```bash
S3_NAME=s3
S3_TYPE=s3
S3_OPTION_ACCESS_KEY_ID=AKIA...
S3_OPTION_SECRET_ACCESS_KEY=your-secret-key
S3_OPTION_REGION=us-east-1
```

### Advanced Options

**Custom endpoint (MinIO, SeaweedFS, etc.):**
```bash
S3_OPTION_ENDPOINT=https://minio.example.com:9000
```

**Access Control:**
```bash
S3_OPTION_ACL=private
```

**Storage Class:**
```bash
S3_OPTION_STORAGE_CLASS=STANDARD_IA
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

Open http://localhost:3000


