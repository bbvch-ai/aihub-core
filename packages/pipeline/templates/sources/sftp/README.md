# SFTP Pipeline Template

Simple pipeline to sync SFTP server documents to Swiss AI Hub data lake.

## Setup

**1. Get SFTP Credentials**

You need:

- **Host**: SFTP server address
- **Username**: Your account username
- **Password**: Your account password (OR SSH key file)
- **Port**: Usually 22

**2. Configure Environment**

Copy variables from `.env.template` to your `.env` and fill in:

```bash
RCLONE_SFTP_NAME=sftp
RCLONE_SFTP_TYPE=sftp
RCLONE_SFTP_HOST=sftp.example.com
RCLONE_SFTP_USER=username
RCLONE_SFTP_PASS=password
RCLONE_SFTP_PORT=22
```

**3. Update Pipeline**

Edit `pipeline.py` to point to your folder:

```python
source_remote=f"{sftp.name}:/path/to/documents"
```

**4. Run Pipeline**

```bash
uv run dagster dev -f pipeline.py
```

## Using SSH Key

Instead of password, use SSH key file:

```bash
# .env
RCLONE_SFTP_KEY_FILE=/secrets/ssh_key
# Remove RCLONE_SFTP_PASS
```

Mount key file in docker-compose.dev.yml:

```yaml
rclone:
  volumes:
    - ./ssh_key:/secrets/ssh_key:ro
```

## Advanced Options

**Known hosts file:**

```bash
RCLONE_SFTP_KNOWN_HOSTS_FILE=/secrets/known_hosts
```

**Skip symbolic links during transfer:**

```bash
RCLONE_SFTP_SKIP_LINKS=true
```

> **Note on host key verification**: By default, rclone uses the system's known_hosts file. To skip host key
> verification in development (not recommended for production), set `RCLONE_SFTP_KNOWN_HOSTS_FILE` to an empty or
> non-existent file.
