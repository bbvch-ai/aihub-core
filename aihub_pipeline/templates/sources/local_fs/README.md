# Local Filesystem Pipeline Template

Simple pipeline to sync local files to AI-Hub data lake using rclone.

**No Authentication Required** - Just mount a directory!

## Setup

**1. Configure Volume Mount**

In the rclone service configure the volume mount:

```yaml
rclone:
  volumes:
    - ${RCLONE_DATA_PATH:-/mnt/test_data}:/mnt/test_data:ro
```

Set the path in your `.env`:

```bash
# Point to your documents folder
RCLONE_DATA_PATH=/path/to/your/documents
```

**2. Run Pipeline**

```bash
poetry run dagster dev -f pipeline.py
```

Open http://localhost:3000
