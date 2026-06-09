---
name: setup-bot-connection
description: End-to-end guide for setting up a new bot connection in swiss_ai_hub.bot. Covers Azure App Registration, Bot Channels Registration, Teams/Slack channel config, PathEntity creation in bot_paths collection, and DevTunnel for local dev. Use when user says "set up a bot", "connect bot to Teams", "connect bot to Slack", "configure bot channel", "create bot connection", "DevTunnel setup", "bot local development", or "Azure bot registration". Do NOT use for bot handler code scaffolding (use scaffold-bot-handler), bot architecture questions (use bot-framework), or agent debugging (use debug-agent).
disable-model-invocation: true

allowed-tools: Read, Grep, Glob, Bash
---

# Bot Connection Setup Guide

Set up a new bot connection. Target channel or question via `$ARGUMENTS`.

______________________________________________________________________

## Before You Start

Read `packages/bot/CLAUDE.md` for full architecture, routes, and essential files.

**Key concept**: Each bot endpoint has a **PathEntity** in MongoDB (`bot_paths` collection) containing Azure AD
credentials (APP_ID, APP_PASSWORD, APP_TENANTID), system message template, and Slack OAuth token.

______________________________________________________________________

## Prerequisites

1. **Azure CLI** installed and authenticated: `az login`
2. **Azure subscription** with permission to create App Registrations and Bot resources
3. **MongoDB/FerretDB** running (for storing PathEntity credentials)
4. **NATS server** running (for agent communication)
5. **Public endpoint** or DevTunnel for the bot server

______________________________________________________________________

## Option A: Automated Setup (Recommended)

**Script**: `packages/bot/swiss_ai_hub/bot/setup_azure_bot.py`

### For Teams (Single-Tenant)

```bash
cd packages/bot
uv run python swiss_ai_hub/bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/active/agent/chat/completions/MyAgent/my_agent_id/json" \
    --mongo-connection-string "mongodb://localhost:27017" \
    --tenant-id "your-azure-tenant-id" \
    --system-message "You are {assistant_name}. The user's name is {username}." \
    --location "westeurope" \
    --sku "F0"
```

### For Slack (Multi-Tenant)

```bash
cd packages/bot
uv run python swiss_ai_hub/bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "ai-hub-slack-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/active/agent/chat/completions/MyAgent/my_agent_id/json" \
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

______________________________________________________________________

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
    --display-name "Swiss AI Hub Bot" \
    --endpoint "https://your-domain.com/api/v1/active/agent/chat/completions/MyAgent/my_id/json" \
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
cd packages/bot && uv run python swiss_ai_hub/bot/add_path_entity.py
```

```python
# Option 2: Direct MongoDB insert
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
client["aihub"]["bot_paths"].update_one(
    {"path": "/api/v1/active/agent/chat/completions/MyAgent/my_id/json"},
    {"$set": {
        "path": "/api/v1/active/agent/chat/completions/MyAgent/my_id/json",
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

______________________________________________________________________

## Local Development Setup

You can drive the bot locally from the Microsoft **Bot Framework Emulator** with **no Azure registration**, using a
dedicated local runner. (For an authentic Teams/Slack test with real identities, see *Real channel via DevTunnel +
Azure* at the end.)

> ⚠️ The old "connect the emulator to `main.py` on `:8000`" instructions do **not** work: the `microsoft-agents`
> `CloudAdapter` always performs MSAL auth (even to *receive* a message it builds a user-token client needing a real
> `TENANT_ID`, and to *reply* it signs with a bearer token). So `playground/testing/main.py` — built for the pytest
> harness, where MSAL is mocked — fails with `TENANT_ID is not set` the moment a live emulator connects. Use the runner
> below instead.

### Step 0 — The local runner (`main_local_emulator.py`)

`packages/bot/playground/testing/main_local_emulator.py` forces the SDK's built-in **unauthenticated mode**
(`use_anonymous=True` on the channel-service factory) so no Azure/token is needed, binds `0.0.0.0:8001` (reachable
across the WSL2 boundary), and can stub the user's email for the emulator (see Step 4). It is **local-only — never an
entry point for a deployed bot**. If it's missing from your checkout, create it with exactly this content:

```python
"""Local-dev entry point for driving the bot from the Bot Framework Emulator WITHOUT Azure.

Forces the SDK's unauthenticated mode (use_anonymous=True) so no MSAL/Azure token is needed, and
optionally stubs the user's email (BOT_DEV_FAKE_EMAIL) since the emulator can't do the Teams member
lookup. LOCAL EMULATOR USE ONLY — never an entry point for a deployed bot.
"""

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
import inspect  # noqa: E402


def _force_anonymous_auth() -> None:
    from microsoft_agents.hosting.core.rest_channel_service_client_factory import (
        RestChannelServiceClientFactory,
    )

    def _wrap(func):  # noqa: ANN001, ANN202
        signature = inspect.signature(func)

        async def wrapper(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
            bound = signature.bind(self, *args, **kwargs)
            bound.apply_defaults()
            bound.arguments["use_anonymous"] = True
            arguments = dict(bound.arguments)
            instance = arguments.pop("self")
            return await func(instance, **arguments)

        return wrapper

    RestChannelServiceClientFactory.create_connector_client = _wrap(
        RestChannelServiceClientFactory.create_connector_client
    )
    RestChannelServiceClientFactory.create_user_token_client = _wrap(
        RestChannelServiceClientFactory.create_user_token_client
    )


_force_anonymous_auth()


def _stub_user_email_for_emulator() -> None:
    """Resolve the user's email from BOT_DEV_FAKE_EMAIL instead of the Teams connector (no-op if unset)."""
    import os

    fake_email = os.environ.get("BOT_DEV_FAKE_EMAIL")
    if not fake_email:
        return

    from swiss_ai_hub.bot.bots.chat.completion_handler import CompletionHandler

    async def _resolve(turn_context):  # noqa: ANN001
        return fake_email

    CompletionHandler.resolve_user_email = staticmethod(_resolve)


_stub_user_email_for_emulator()

from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.routes import HealthController  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler  # noqa: E402

from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController  # noqa: E402
from swiss_ai_hub.bot.routes.openai.openai_chat_controller import OpenaiChatController  # noqa: E402
from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = SimulatedAgentBotTestRunner(agent_class="my_agent_class", agent_id="my_agent_id")
    runner.with_simple_chunk_events()
    auth = TestAuthHandler()

    runner.mount(
        HealthController(auth=auth).get_health(),
        AgentChatController(auth=auth).completions_json().completions_stream(),
        OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),
    )

    # MUST call start_simulation() — runner.run() normally does this before serving. It starts the
    # simulated agent's NATS subscribers; skip it and every chat times out waiting for a reply.
    await runner.start_simulation()

    from uvicorn import Config, Server

    server = Server(Config(app=runner.create_app(), host="0.0.0.0", port=8001, log_level="debug"))
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
```

### Step 1 — Seed a PathEntity for the endpoint

The runner serves the agent at `/api/v1/agent/chat/completions/my_agent_class/my_agent_id/json`. Seed a matching
`PathEntity` (empty credentials are fine — the runner is unauthenticated):

```bash
cd packages/bot
uv run python - <<'PY'
from dotenv import load_dotenv; load_dotenv("../../.env")
from mongoengine import connect
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.bot.persistence.entities.path_entity import Credentials, PathEntity
connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value(), uuidRepresentation="standard")
path = "/api/v1/agent/chat/completions/my_agent_class/my_agent_id/json"
PathEntity.objects(path=path).delete()
PathEntity(path=path, credentials=Credentials(APP_TYPE="MultiTenant"),
           system_message="You are a helpful local dev assistant.").save()
print("seeded", path)
PY
```

> ⚠️ Keep the `system_message` free of placeholders, or use **only one** of `{username}` / `{assistant_name}`.
> `CompletionHandler.get_system_message` calls `.format()` twice, so a message containing **both** placeholders raises
> `KeyError`.

### Step 2 — Start (or restart) the runner

```bash
# 1. stop any running instance (no-op if none)
pkill -f main_local_emulator.py

# 2. go to the testing playground
cd packages/bot/playground/testing

# 3. start it, backgrounded, logging to /tmp/bot_local.log  (serves on 0.0.0.0:8001)
uv run python main_local_emulator.py > /tmp/bot_local.log 2>&1 &
```

Watch logs with `tail -f /tmp/bot_local.log`. Requires the dev stack's MongoDB/FerretDB, NATS, and Keycloak to be
running. Re-run these three commands after changing `BOT_DEV_FAKE_EMAIL` (Step 4) — env vars are read once at startup.

**Always confirm exactly one clean instance after (re)starting** — `uv run` spawns two processes, and if you start a new
one before the old releases port 8001, the new one dies with `address already in use` while the **old instance keeps
serving** (so your `.env` change silently has no effect):

```bash
tail -5 /tmp/bot_local.log     # GOOD: "Uvicorn running on http://0.0.0.0:8001"
                               # BAD:  "address already in use" -> an old instance is still up
ss -ltnp | grep :8001          # must show exactly ONE listener
```

If you see `address already in use`, run `pkill -9 -f main_local_emulator.py`, wait until `ss -ltnp | grep :8001` is
empty, then start again.

### Step 3 — Connect the Bot Framework Emulator

Download from https://github.com/microsoft/BotFramework-Emulator/releases. **Open Bot** → URL:

```
http://localhost:8001/api/v1/agent/chat/completions/my_agent_class/my_agent_id/json
```

Leave **App ID / Password empty** → Connect → send a message.

#### WSL2 note (Windows + WSL2 only)

On **native Linux/macOS**, the emulator and bot share `localhost` — skip this section; the URL above and replies just
work. On **WSL2** (bot in Linux, emulator on Windows), `localhost` bridges neither direction:

1. **Emulator → bot:** connect via the WSL2 IP, not `localhost`. Get it with `hostname -I` (e.g. `172.23.171.112`) and
   use `http://<WSL_IP>:8001/...`. (The runner already binds `0.0.0.0`.)

2. **Bot → emulator (replies):** the emulator's reply URL is its own Windows `localhost`, unreachable from WSL2
   (`Cannot connect to localhost:<port>`). Bridge it with a devtunnel:

   a. **Find the emulator's listening port.** In the emulator's **Live Chat** tab, open the **Log** panel (right side)
   and read the line `Emulator listening on http://[::]:<port>` — e.g. `…:57705`. This port is assigned per emulator
   session, so re-check it whenever you restart the emulator. (The emulator's **Settings → Configure Tunnel** section
   also prints the exact command pre-filled with the current port, e.g. `devtunnel host -a -p 57705`.)

   b. **Host the tunnel on that port** (run **on Windows**):

   ```powershell
   # One-time only — skip if devtunnel is already installed (check with: devtunnel --version)
   winget install Microsoft.devtunnel

   # One-time only — skip if already logged in (check with: devtunnel user show)
   devtunnel user login

   # Every session — host the tunnel on the emulator's current port from step (a)
   devtunnel host -a -p <emulator-port>   # e.g. 57705
   ```

   c. **Paste the public URL into the emulator.** `devtunnel host` prints two URLs — copy the **"Connect via browser"**
   one (NOT the `-inspect` one):

   ```text
   Hosting port: 57705
   Connect via browser: https://g25mmhp5-57705.asse.devtunnels.ms          ← copy THIS
   Inspect network activity: https://g25mmhp5-57705-inspect.asse.devtunnels.ms   ← NOT this (causes 401)

   Ready to accept connections for tunnel: jolly-cat-1xpgknv.asse
   ```

   Paste it into **Settings → Configure Tunnel → Tunnel Url** → Save. Keep the `devtunnel host` window running; replies
   now route back through the tunnel.

### Step 4 — Drive the user identity (`BOT_DEV_FAKE_EMAIL`)

The bot resolves the user's email via the Teams connector (`get_conversation_member`), which the emulator does not
implement (returns `404`). To exercise identity-dependent logic (auth, Keycloak provisioning) from the emulator, set
`BOT_DEV_FAKE_EMAIL` in `.env` — the runner resolves that email directly:

```bash
# .env (gitignored, DEV ONLY)
BOT_DEV_FAKE_EMAIL='admin@your-company.com'   # a provisioned Keycloak user  -> happy path
# BOT_DEV_FAKE_EMAIL='ghost@example.com'      # an unknown email             -> UserNotProvisionedError
```

Restart the runner after changing it; leave it unset for real connector-based resolution. To fake other identity fields
for future features, add another env-gated monkeypatch in the runner (same pattern) — never in `swiss_ai_hub/`
production code.

### Emulator troubleshooting

| Symptom                                           | Cause                                          | Fix                                                                 |
| ------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------- |
| `TENANT_ID is not set` on connect                 | Ran `main.py` instead of the local runner      | Use `main_local_emulator.py` (forces anonymous auth)                |
| `No credentials found for path`                   | PathEntity missing                             | Seed it (Step 1)                                                    |
| Emulator `POST 400`, nothing in the bot log       | Emulator can't reach the bot (WSL2)            | Connect via the WSL2 IP, not `localhost`                            |
| Reply fails: `Cannot connect to localhost:<port>` | Bot (WSL2) can't reach the emulator reply URL  | Set up the devtunnel and paste the Tunnel Url                       |
| Reply `401` to `*.devtunnels.ms`                  | Pasted the `-inspect` URL, or a token was sent | Use the "Connect via browser" URL; ensure the local runner          |
| `KeyError: 'assistant_name'`                      | `system_message` uses both placeholders        | Use ≤1 placeholder in the seeded system_message                     |
| Bot 404s on `.../members/...` → generic error     | Emulator can't do the Teams member lookup      | Set `BOT_DEV_FAKE_EMAIL` to drive identity (Step 4)                 |
| 60s typing then "taking too long"                 | The simulated agent didn't reply (harness)     | Identity resolved fine; use a real agent or test a pre-agent branch |

### Real channel via DevTunnel + Azure (authentic Teams/Slack)

For a true end-to-end test (real display names, real connector emails, genuinely unprovisioned users), expose the local
bot and register it as an Azure Bot:

```bash
devtunnel host -a -p 8001     # public URL for the bot itself
```

Use that URL as the Azure Bot resource's messaging endpoint (see *Option A: Automated Setup* / `setup_azure_bot.py`
above) and enable the Teams/Slack channel in the Azure portal.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## Troubleshooting Quick Reference

| Symptom                         | Likely Cause           | Fix                                               |
| ------------------------------- | ---------------------- | ------------------------------------------------- |
| "No credentials found for path" | PathEntity missing     | Insert PathEntity in MongoDB                      |
| 401 Unauthorized from Azure     | APP_PASSWORD expired   | `az ad app credential reset --id <appId>`         |
| Bot doesn't respond in Teams    | Wrong endpoint URL     | Update Azure Bot Resource endpoint                |
| Bot doesn't respond in Slack    | Missing slack_token    | Add `slack_token` to PathEntity                   |
| "Connection refused" locally    | Bot server not running | Start with `python main.py` or `make run-prod`    |
| DevTunnel not forwarding        | Port mismatch          | Verify tunnel port matches bot server port (8001) |
