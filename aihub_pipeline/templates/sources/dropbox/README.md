# Dropbox Pipeline Template

Simple pipeline to sync Dropbox documents to AI-Hub data lake.

**⚠️ OAuth Limitation**: Dropbox requires interactive browser authorization. One-time setup needed.

## Setup

**1. Create Dropbox App**

- Go to https://www.dropbox.com/developers/apps
- Create app with "Full Dropbox" access
- Note **App key** (client ID) and **App secret** (client secret)

**2. Authorize Access (One-Time)**

Run this on your machine to complete OAuth flow:

```bash
docker exec -it rclone rclone config
# Choose: n (new remote)
# Name: dropbox
# Storage: dropbox
# client_id: (paste your App key)
# client_secret: (paste your App secret)
# Follow browser prompts to authorize
```

**3. Export Token**

```bash
docker exec rclone rclone config show dropbox
```

**4. Save Configuration**

Copy the `token` field from step 3:

```bash
# .env.dev
DROPBOX_NAME=dropbox
DROPBOX_TYPE=dropbox
DROPBOX_CLIENT_ID=your-app-key
DROPBOX_CLIENT_SECRET=your-app-secret
DROPBOX_OPTION_TOKEN={"access_token":"..."}
```

**5. Run Pipeline**

```bash
poetry run dagster dev -f pipeline.py
```

Open http://localhost:3000


