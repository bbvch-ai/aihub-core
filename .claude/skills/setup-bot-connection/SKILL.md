---
name: setup-bot-connection
description: >-
  End-to-end guide for setting up a new bot connection: Azure App Registration,
  Bot Channels Registration, Teams/Slack channel configuration, PathEntity creation,
  DevTunnel for local dev. Use when user says 'set up a bot', 'connect bot to Teams',
  'connect bot to Slack', 'configure bot channel', 'create bot connection', 'DevTunnel setup',
  'bot local development', or 'Azure bot registration'. Covers automated and manual setup.
arguments:
  - name: channel
    description: Target channel or question (e.g., "Teams", "Slack", "local dev", "from scratch", "DevTunnel setup")
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash
---

# Bot Connection Setup Guide

Set up a new bot connection. Target channel or question via `$ARGUMENTS`.

---

## Architecture Overview

The bot connects to messaging platforms via **Azure Bot Framework**:

```
User (Teams/Slack/Web Chat)
  ↓
Azure Bot Service (cloud relay)
  ↓  HTTPS POST (JWT-authenticated)
Bot Server (aihub_bot, port 8001)
  ↓  CloudAdapter.process(request, bot)
BaseChatBot → CompletionHandler → NATS → Agent
```

**Key concept**: Each bot endpoint has a **PathEntity** in MongoDB (`bot_paths` collection) containing:
- Azure AD credentials (APP_ID, APP_PASSWORD, APP_TENANTID)
- System message template
- Slack OAuth token (for Slack channels)

---

## Prerequisites

1. **Azure CLI** installed and authenticated: `az login`
2. **Azure subscription** with permission to create App Registrations and Bot resources
3. **MongoDB/FerretDB** running (for storing PathEntity credentials)
4. **NATS server** running (for agent communication)
5. **Public endpoint** or DevTunnel for the bot server

---

## Option A: Automated Setup (Recommended)

**Script**: `aihub_bot/aihub_bot/setup_azure_bot.py`

### For Teams (Single-Tenant)

```bash
cd aihub_bot
poetry run python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/agent/chat/completions/MyAgent/my_agent_id/json" \
    --mongo-connection-string "mongodb://localhost:27017" \
    --tenant-id "your-azure-tenant-id" \
    --system-message "You are {assistant_name}. The user's name is {username}." \
    --location "westeurope" \
    --sku "F0"
```

### For Slack (Multi-Tenant)

```bash
cd aihub_bot
poetry run python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "ai-hub-slack-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/agent/chat/completions/MyAgent/my_agent_id/json" \
    --mongo-connection-string "mongodb://localhost:27017" \
    --slack-token "xoxb-your-slack-bot-token" \
    --system-message "You are {assistant_name}. The user's name is {username}."
```

**What the script does**:
1. Creates Azure AD App Registration (`az ad app create`)
2. Creates Service Principal (`az ad sp create`)
3. Resets credentials → generates APP_PASSWORD
4. Saves PathEntity to MongoDB `bot_paths` collection
5. Creates Azure Bot Resource (`az bot create`)

---

## Option B: Manual Setup (Step-by-Step)

### Step 1: Azure AD App Registration

```bash
# Create app registration
az ad app create --display-name "ai-hub-bot" --sign-in-audience "AzureADMyOrg"
# Output: { "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" }

# Create service principal
az ad sp create --id <appId>

# Generate client secret
az ad app credential reset --id <appId>
# Output: { "appId": "...", "password": "...", "tenant": "..." }
```

Save these values:
- `APP_ID` = `appId`
- `APP_PASSWORD` = `password`
- `APP_TENANTID` = `tenant` (for single-tenant/Teams)

### Step 2: Create Azure Bot Resource

```bash
az bot create \
    --app-type "SingleTenant" \
    --appid "<APP_ID>" \
    --name "ai-hub-bot" \
    --resource-group "my-resource-group" \
    --display-name "AI Hub Bot" \
    --endpoint "https://your-domain.com/api/v1/agent/chat/completions/MyAgent/my_id/json" \
    --location "westeurope" \
    --sku "F0" \
    --tenant-id "<APP_TENANTID>"
```

### Step 3: Create PathEntity in MongoDB

Use the helper script or insert directly:

```bash
# Option 1: Use add_path_entity.py
export BOT_APP_ID="<APP_ID>"
export BOT_APP_PASSWORD="<APP_PASSWORD>"
export BOT_TENANT_ID="<APP_TENANTID>"
export MONGO_CONNECTION_STRING="mongodb://localhost:27017"
cd aihub_bot && poetry run python aihub_bot/add_path_entity.py
```

```python
# Option 2: Direct MongoDB insert
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
client["aihub"]["bot_paths"].update_one(
    {"path": "/api/v1/agent/chat/completions/MyAgent/my_id/json"},
    {"$set": {
        "path": "/api/v1/agent/chat/completions/MyAgent/my_id/json",
        "credentials": {
            "APP_TYPE": "SingleTenant",  # or "MultiTenant" for Slack
            "APP_ID": "<APP_ID>",
            "APP_PASSWORD": "<APP_PASSWORD>",
            "APP_TENANTID": "<TENANT_ID>",  # None for MultiTenant
        },
        "system_message": "You are {assistant_name}. The user's name is {username}.",
        "slack_token": None,  # Set for Slack bots: "xoxb-..."
    }},
    upsert=True,
)
```

### Step 4: Configure Channel in Azure Portal

**For Teams**:
1. Azure Portal → Bot Services → your bot → Channels
2. Click "Microsoft Teams" → Configure
3. Enable messaging
4. Save

**For Slack**:
1. Create Slack App at https://api.slack.com/apps
2. Enable "Bot User OAuth Token" → copy token (`xoxb-...`)
3. In Azure Portal → Bot Services → your bot → Channels
4. Click "Slack" → Configure with OAuth redirect
5. Save the `slack_token` in PathEntity

**For Web Chat**:
1. Azure Portal → Bot Services → your bot → Channels
2. Web Chat is enabled by default
3. Copy the secret key for embedding

---

## Local Development Setup

### Using Azure DevTunnel

```bash
# Install DevTunnel CLI (one-time)
# https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/get-started

# Create tunnel
devtunnel create --allow-anonymous
devtunnel port create -p 8001
devtunnel host

# Output: https://abc123-8001.devtunnels.ms
# Use as bot endpoint: https://abc123-8001.devtunnels.ms/api/v1/agent/chat/completions/...
```

### Using Bot Framework Emulator (No Azure Required)

1. Download: https://github.com/microsoft/BotFramework-Emulator
2. Start bot locally:
   ```bash
   cd aihub_bot/playground/testing
   poetry run python main.py
   ```
3. Connect emulator to: `http://localhost:8000/api/v1/messages`
4. Leave App ID and Password **empty** for local testing
5. Send messages and inspect Activity JSON

### Using Playground Web Chat

```bash
cd aihub_bot/playground/testing
poetry run python main.py
# Open http://localhost:8000 in browser
```

---

## Bot Endpoint Patterns

Each bot type has a specific URL pattern. The path must match the PathEntity in MongoDB:

| Bot Type | Endpoint Pattern |
|----------|-----------------|
| Agent (JSON) | `/api/v1/agent/chat/completions/{agent_class}/{agent_id}/json` |
| Agent (Stream) | `/api/v1/agent/chat/completions/{agent_class}/{agent_id}/stream` |
| OpenAI (JSON) | `/api/v1/openai/chat/completions/json?model_name=<model>` |
| OpenAI (Stream) | `/api/v1/openai/chat/completions/stream?model_name=<model>` |
| Bot-in-the-Loop | `/api/v1/bot_in_the_loop/response` |

---

## System Message Templates

System messages support placeholders:
- `{username}` → replaced with the user's display name
- `{assistant_name}` → replaced with the bot's display name

Example:
```
You are {assistant_name}, an AI assistant for the Swiss AI Hub platform.
The user's name is {username}. Be helpful, concise, and professional.
Always respond in the user's language.
```

---

## Verification Checklist

After setup, verify:

- [ ] PathEntity exists in MongoDB `bot_paths` collection with correct path
- [ ] Credentials (APP_ID, APP_PASSWORD) are valid and not expired
- [ ] Azure Bot Resource endpoint URL matches your server's public endpoint
- [ ] Channel is configured in Azure Portal (Teams/Slack/Web Chat)
- [ ] Bot server is running and reachable at the endpoint URL
- [ ] NATS server is running (for agent-based bots)
- [ ] MongoDB/FerretDB is running (for conversation persistence)
- [ ] Test with Bot Framework Emulator or direct message in Teams/Slack

---

## Key Files

| File | Purpose |
|------|---------|
| `aihub_bot/aihub_bot/setup_azure_bot.py` | Automated Azure Bot provisioning |
| `aihub_bot/aihub_bot/add_path_entity.py` | CLI for adding PathEntity to MongoDB |
| `aihub_bot/aihub_bot/persistence/entities/PathEntity.py` | PathEntity model (credentials + system message) |
| `aihub_bot/aihub_bot/routes/RoutesService.py` | CloudAdapter caching per path |
| `aihub_bot/aihub_bot/routes/agent/AgentChatController.py` | Agent chat endpoints |
| `aihub_bot/aihub_bot/runners/lifetime/lifetime_manager.py` | NATS + MongoDB startup |
| `aihub_bot/playground/testing/main.py` | Local test server |

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "No credentials found for path" | PathEntity missing | Insert PathEntity in MongoDB |
| 401 Unauthorized from Azure | APP_PASSWORD expired | `az ad app credential reset --id <appId>` |
| Bot doesn't respond in Teams | Wrong endpoint URL | Update Azure Bot Resource endpoint |
| Bot doesn't respond in Slack | Missing slack_token | Add `slack_token` to PathEntity |
| "Connection refused" locally | Bot server not running | Start with `python main.py` or `make run-prod` |
| DevTunnel not forwarding | Port mismatch | Verify tunnel port matches bot server port (8001) |
