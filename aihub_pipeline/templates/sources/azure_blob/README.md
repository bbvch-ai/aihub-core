# Azure Blob Storage Pipeline Template

Simple pipeline to sync Azure Blob Storage documents to AI-Hub data lake.

## Setup

**1. Get Storage Account Credentials**

- Go to Azure Portal → Storage Accounts → Your account
- Access Keys → Show keys
- Note **Storage account name** and **Key1** or **Key2**

**2. Configure Environment**

Copy variables from `.env.template` to your `.env` and fill in:

```bash
RCLONE_AZUREBLOB_NAME=azureblob
RCLONE_AZUREBLOB_TYPE=azureblob
RCLONE_AZUREBLOB_ACCOUNT=mystorageaccount
RCLONE_AZUREBLOB_KEY=your-access-key-here
```

**3. Update Pipeline**

Edit `pipeline.py` to point to your container:

```python
source_remote=f"{azureblob.name}:my-container/path/to/folder"
```

**4. Run Pipeline**

```bash
uv run dagster dev -f pipeline.py
```
