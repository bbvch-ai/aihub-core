# Box Pipeline Template

Simple pipeline to sync Box documents to AI-Hub data lake.

**⚠️ OAuth Limitation**: Box requires interactive browser authorization. One-time setup needed.

## Setup Options

### Option A: OAuth2 (Standard Authorization)

**1. Create Box App**

- Go to https://app.box.com/developers/console
- Create new app with **"Custom App"** → **"Standard OAuth 2.0"**
- Note **Client ID** and **Client Secret**

**2. Authorize Access (One-Time)**

Run this on your machine to complete OAuth flow:

```bash
docker exec -it rclone rclone config
# Choose: n (new remote)
# Name: box
# Storage: box
# client_id: (paste your Client ID)
# client_secret: (paste your Client Secret)
# Follow browser prompts to authorize
```

**3. Export Token**

```bash
docker exec rclone rclone config show box
```

**4. Save Configuration**

Copy the `token` field from step 3:

```bash
# .env.dev
BOX_NAME=box
BOX_TYPE=box
BOX_CLIENT_ID=your-client-id
BOX_CLIENT_SECRET=your-client-secret
BOX_OPTION_TOKEN={"access_token":"...","refresh_token":"..."}
```

### Option B: JWT Service Account (Enterprise Only)

**Best for**: Box Enterprise accounts, fully automated

**1. Create Box App**

- Go to https://app.box.com/developers/console
- Create new app with **"Custom App"** → **"OAuth 2.0 with JWT"**
- Download JSON config file

**2. Grant Authorization**

- In Box Admin Console, authorize the app
- Note the Service Account User ID

**3. Configure**

```bash
# .env.dev
BOX_NAME=box
BOX_TYPE=box
BOX_OPTION_BOX_CONFIG_FILE=/secrets/box-config.json
BOX_OPTION_BOX_SUB_TYPE=enterprise
```

**4. Mount config file**

```yaml
# docker-compose.dev.yml
rclone:
  volumes:
    - ./box-config.json:/secrets/box-config.json:ro
```

## Run Pipeline

```bash
make playground
```

Open http://localhost:3000
