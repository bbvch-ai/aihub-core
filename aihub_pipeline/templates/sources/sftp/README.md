# SFTP Pipeline Template

Simple pipeline to sync SFTP server documents to AI-Hub data lake.

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
SFTP_NAME=sftp
SFTP_TYPE=sftp
SFTP_OPTION_HOST=sftp.example.com
SFTP_OPTION_USER=username
SFTP_OPTION_PASS=password
SFTP_OPTION_PORT=22
```

**3. Update Pipeline**

Edit `pipeline.py` to point to your folder:

```python
source_remote=f"{sftp.name}:/path/to/documents"
```

**4. Run Pipeline**


```bash
poetry run dagster dev -f pipeline.py
```

Open http://localhost:3000


## Using SSH Key

Instead of password, use SSH key file:

```bash
# .env.dev
SFTP_OPTION_KEY_FILE=/secrets/ssh_key
# Remove SFTP_OPTION_PASS
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
SFTP_OPTION_KNOWN_HOSTS_FILE=/secrets/known_hosts
```

**Disable host key checking (not recommended for production):**
```bash
SFTP_OPTION_SKIP_LINKS=true
```
