# Google Drive Pipeline Template

Simple pipeline to sync Google Drive documents to AI-Hub data lake.

**⚠️ OAuth Limitation**: Google Drive requires interactive browser authorization. Choose your setup method below.

## Setup Options

### Option A: Service Account (Recommended for Workspace)

**Best for**: Google Workspace domains with admin access

**Steps:**

1. Create service account in [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Enable "Google Drive API"
3. Download JSON key file → save as `gdrive-service-account.json`
4. (Workspace only) Enable domain-wide delegation
5. Share Drive folders with service account email

**Configure:**

```bash
# .env.dev
GDRIVE_NAME=gdrive
GDRIVE_TYPE=drive
GDRIVE_OPTION_SERVICE_ACCOUNT_FILE=/secrets/gdrive-service-account.json
```

**Mount key file in docker-compose.dev.yml:**

```yaml
rclone:
  volumes:
    - ./gdrive-service-account.json:/secrets/gdrive-service-account.json:ro
```

### Option B: OAuth Token (Works for Personal Accounts)

**Best for**: Personal Gmail accounts or simpler setup

**Steps:**

1. **One-time authorization** (run on your machine):
   ```bash
   docker exec -it rclone rclone config
   # Choose: n (new remote)
   # Name: gdrive
   # Storage: drive
   # client_id: (your client ID)
   # client_secret: (your client secret)
   # Follow browser prompts to authorize
   ```

2. **Export the token**:
   ```bash
   docker exec rclone rclone config show gdrive
   ```

3. **Save to environment** (copy the `token` field):
   ```bash
   # .env.dev
   GDRIVE_NAME=gdrive
   GDRIVE_TYPE=drive
   GDRIVE_CLIENT_ID=your-client-id
   GDRIVE_CLIENT_SECRET=your-client-secret
   GDRIVE_OPTION_TOKEN={"access_token":"...","refresh_token":"..."}
   ```

**OR mount config file:**

```bash
# Export entire config
docker exec rclone cat /config/rclone/rclone.conf > ./rclone.conf

# Mount in docker-compose.dev.yml
rclone:
  volumes:
    - ./rclone.conf:/config/rclone/rclone.conf:ro
```

## Run Pipeline

```bash
make playground
```

Open http://localhost:3000

## Files

- `.env.template` - Environment variables template
- `pipeline.py` - Pipeline definition (~10 lines)
- `README.md` - This file

## Troubleshooting

**Error: "empty token found"**
- OAuth token missing or expired
- Follow Option B steps above to authorize

**Error: "Service account not authorized"**
- Share Drive folders with service account email
- OR enable domain-wide delegation (Workspace admin)

**Testing connection:**
```bash
docker exec rclone rclone lsd gdrive:
```
