# Local Filesystem Pipeline Template

Simple pipeline to sync local files to Swiss AI Hub data lake using rclone.

**No Authentication Required** - Just mount a directory!

## Setup

**1. Configure Environment**

Copy variables from `.env.template` to your `.env`:

```bash
RCLONE_LOCAL_FS_NAME=local
RCLONE_LOCAL_FS_TYPE=local

# Point to your documents folder
RCLONE_DATA_PATH=/path/to/your/documents
```

**2. Configure Volume Mount**

In the rclone service configure the volume mount:

```yaml
rclone:
  volumes:
    - ${RCLONE_DATA_PATH:-/mnt/test_data}:/mnt/test_data:ro
```

**3. Run Pipeline**

```bash
uv run dagster dev -f pipeline.py
```
