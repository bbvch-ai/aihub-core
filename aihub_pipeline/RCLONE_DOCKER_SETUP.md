# Rclone Docker Integration Setup

This guide explains how to use rclone as a Remote Control (RC) API service in the aihub-core platform.

## ✅ Architecture (Already Done!)

Rclone runs as a separate Docker service with RC API enabled:

```yaml
# docker-compose.yml
rclone:
  container_name: aihub-rclone
  image: rclone/rclone:latest
  command:
    - "rcd"
    - "--rc-addr=0.0.0.0:5572"
    - "--rc-no-auth"
  volumes:
    - ./rclone.conf:/config/rclone/rclone.conf:ro
```

**Why RC API instead of subprocess:**
- Matches existing async HTTP patterns (same as SharePointResource)
- More efficient (connection pooling, no process overhead)
- Better separation of concerns (microservice architecture)
- Cleaner codebase (async/await with aiohttp)

## 🔐 Configuration Setup

Rclone needs a config file for authentication. **Never** include secrets in the image!

### Option 1: Environment Variables (Recommended for Production)

Configure remotes via environment variables instead of config file:

```bash
# OneDrive example
export RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
export RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=your_client_id
export RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=your_client_secret
export RCLONE_CONFIG_ONEDRIVE_TOKEN='{"access_token":"...","refresh_token":"..."}'

# Google Drive example
export RCLONE_CONFIG_GDRIVE_TYPE=drive
export RCLONE_CONFIG_GDRIVE_CLIENT_ID=your_client_id
export RCLONE_CONFIG_GDRIVE_CLIENT_SECRET=your_client_secret
export RCLONE_CONFIG_GDRIVE_TOKEN='{"access_token":"...","refresh_token":"..."}'
```

**In docker-compose.yml:**

```yaml
services:
  dagster:
    build:
      context: ./aihub_pipeline
    environment:
      # OneDrive remote
      - RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
      - RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=${ONEDRIVE_CLIENT_ID}
      - RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=${ONEDRIVE_CLIENT_SECRET}
      - RCLONE_CONFIG_ONEDRIVE_TOKEN=${ONEDRIVE_TOKEN}
      # Or use .env file (recommended)
    env_file:
      - .env
```

**In .env file:**

```bash
# OneDrive Configuration
RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=your_client_id
RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=your_client_secret
RCLONE_CONFIG_ONEDRIVE_TOKEN={"access_token":"...","refresh_token":"..."}
```

### Option 2: Mount Config File (Development)

Create `rclone.conf` locally and mount it:

**1. Create config locally:**

```bash
# On your host machine
rclone config

# Follow prompts to configure OneDrive, Google Drive, etc.
# This creates ~/.config/rclone/rclone.conf
```

**2. Mount in docker-compose:**

```yaml
services:
  dagster:
    build:
      context: ./aihub_pipeline
    volumes:
      - ~/.config/rclone/rclone.conf:/home/user/.config/rclone/rclone.conf:ro
      # :ro = read-only for security
```

**3. Use in pipeline:**

```python
# playground/quick_start/rclone_onedrive_test.py
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="onedrive-test",
    source_remote="onedrive:Documents",  # Matches remote name in rclone.conf
    rclone_config_path="/home/user/.config/rclone/rclone.conf",
)
```

### Option 3: Local Filesystem (No Config Needed!)

For testing with local filesystem, no authentication required:

```python
# playground/quick_start/rclone_local_test.py
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="local-test",
    source_remote="/data/source",  # Just use path directly
    include_patterns=["*.pdf"],
)
```

**Mount local directory:**

```yaml
services:
  dagster:
    volumes:
      - /tmp/rclone-test-source:/data/source:ro
```

## 🧪 Testing the RC API Service

### 1. Start the rclone service

```bash
cd /home/user/aihub-core
docker compose -f docker-compose.dev.yml up -d rclone
```

### 2. Verify rclone service is running

```bash
docker compose -f docker-compose.dev.yml ps rclone
```

Expected output:
```
NAME            IMAGE                   STATUS
aihub-rclone    rclone/rclone:latest    Up (healthy)
```

### 3. Test RC API directly

```bash
# Get rclone version via RC API
curl -X POST http://localhost:5572/core/version

# List remotes
curl -X POST http://localhost:5572/config/listremotes
```

Expected output:
```json
{
  "version": "v1.68.2",
  "isGit": false
}
```

## 🚀 Usage in Pipeline

### Example: OneDrive to S3

**Step 1: Configure OneDrive (one-time setup)**

```bash
# On your host machine (outside Docker)
rclone config create onedrive_prod onedrive

# Follow OAuth2 flow
# Copy ~/.config/rclone/rclone.conf
```

**Step 2: Add secrets to .env**

```bash
# Get token from rclone.conf
cat ~/.config/rclone/rclone.conf

# Add to .env
RCLONE_CONFIG_ONEDRIVE_PROD_TYPE=onedrive
RCLONE_CONFIG_ONEDRIVE_PROD_CLIENT_ID=your_client_id
RCLONE_CONFIG_ONEDRIVE_PROD_CLIENT_SECRET=your_client_secret
RCLONE_CONFIG_ONEDRIVE_PROD_TOKEN='{"access_token":"...","refresh_token":"..."}'
```

**Step 3: Create pipeline**

```python
# playground/quick_start/onedrive_prod.py
from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="company-docs",
    source_remote="onedrive_prod:Documents/CompanyFiles",
    include_patterns=["*.pdf", "*.docx"],
    exclude_patterns=["**/archive/**"],
)
```

**Step 4: Run**

```bash
docker compose -f docker-compose.dev.yml up dagster
# Open http://localhost:3000
# Materialize rclone assets
```

## 🔧 Troubleshooting

### RC API Connection Refused

**Problem:** Cannot connect to http://localhost:5572

**Solution:** Check if rclone service is running:
```bash
docker compose -f docker-compose.dev.yml ps rclone
docker compose -f docker-compose.dev.yml logs rclone
```

Restart if needed:
```bash
docker compose -f docker-compose.dev.yml restart rclone
```

### "Failed to create file system: didn't find section in config file"

**Problem:** Remote not configured in rclone.conf

**Solution:** Either:
1. Add environment variables (see Option 1 above)
2. Mount rclone.conf with proper remote configuration (see Option 2 above)
3. Create remote in rclone.conf before mounting:
```bash
# On host
rclone config create onedrive_remote onedrive
# Then mount ~/.config/rclone/rclone.conf
```

### "Failed to configure token: failed to get token"

**Problem:** OAuth2 token expired in rclone.conf

**Solution:** Refresh token on host, then restart rclone service:
```bash
# On host
rclone config reconnect remote_name

# Restart service to reload config
docker compose -f docker-compose.dev.yml restart rclone
```

### HTTP 500 errors from RC API

**Problem:** rclone.conf has wrong permissions or format

**Solution:**
```bash
# Fix permissions
chmod 600 ~/.config/rclone/rclone.conf

# Check logs for details
docker compose -f docker-compose.dev.yml logs rclone
```

## 📋 Configuration Examples

### OneDrive Environment Variables

```bash
RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=your_secret_here
RCLONE_CONFIG_ONEDRIVE_TOKEN={"access_token":"ya29...","token_type":"Bearer","refresh_token":"1//...","expiry":"2025-..."}
RCLONE_CONFIG_ONEDRIVE_DRIVE_ID=b!xxxx
RCLONE_CONFIG_ONEDRIVE_DRIVE_TYPE=business
```

### Google Drive Environment Variables

```bash
RCLONE_CONFIG_GDRIVE_TYPE=drive
RCLONE_CONFIG_GDRIVE_CLIENT_ID=xxxx.apps.googleusercontent.com
RCLONE_CONFIG_GDRIVE_CLIENT_SECRET=GOCSPX-xxx
RCLONE_CONFIG_GDRIVE_TOKEN={"access_token":"ya29...","token_type":"Bearer","refresh_token":"1//...","expiry":"2025-..."}
RCLONE_CONFIG_GDRIVE_SCOPE=drive
```

### S3-Compatible (MinIO, SeaweedFS)

```bash
RCLONE_CONFIG_S3REMOTE_TYPE=s3
RCLONE_CONFIG_S3REMOTE_PROVIDER=Other
RCLONE_CONFIG_S3REMOTE_ACCESS_KEY_ID=your_access_key
RCLONE_CONFIG_S3REMOTE_SECRET_ACCESS_KEY=your_secret_key
RCLONE_CONFIG_S3REMOTE_ENDPOINT=http://seaweedfs:8333
RCLONE_CONFIG_S3REMOTE_REGION=us-east-1
```

## 🎯 Quick Start Checklist

- [x] Rclone service added to docker-compose.yml
- [x] RC API enabled on port 5572
- [x] RcloneResource uses async HTTP client
- [ ] Choose config method (env vars OR mount config file)
- [ ] Configure remote (OneDrive/GDrive/etc.)
- [ ] Start rclone service: `docker compose up -d rclone`
- [ ] Test RC API: `curl -X POST http://localhost:5572/core/version`
- [ ] Create pipeline with `default_rclone_to_datalake_definitions()`
- [ ] Run Dagster and materialize assets

## 📚 Resources

- [Rclone Docker Image](https://hub.docker.com/r/rclone/rclone)
- [Rclone Configuration](https://rclone.org/docs/#configure)
- [Environment Variables](https://rclone.org/docs/#config-file)
- [OneDrive Setup](https://rclone.org/onedrive/)
- [Google Drive Setup](https://rclone.org/drive/)
