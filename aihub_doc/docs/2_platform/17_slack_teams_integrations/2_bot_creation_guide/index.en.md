---
title: Bot Creation Manual Setup Guide
---

# Bot Creation Manual Setup Guide :robot: :wrench:

::: info **TL;DR - What is This Guide?**
This comprehensive manual provides **step-by-step instructions for manually creating and configuring bots** with
Microsoft Teams and Slack integration. Use this guide when you need to create new bots from scratch, configure Azure Bot
Framework channels, or troubleshoot existing bot deployments. It covers everything from Teams Developer Portal setup to
MongoDB configuration and Slack OAuth integration.
:::

::: tip Automated Setup Available
Before proceeding with manual setup, consider using the **automated setup script** which handles most of these steps for
you:

```bash
python aihub_bot/setup_azure_bot.py \
    --resource-group "my-resource-group" \
    --bot-name "my-ai-hub-bot" \
    --token-url "https://my-domain.com" \
    --token-path "/api/v1/messages" \
    --mongo-connection-string "mongodb://localhost:27017"
```

**When to use the automated script:**

- Creating new bots for production deployment
- Standard single-bot or multi-bot configurations
- Quick setup without customization

**When to use this manual guide:**

- Troubleshooting automated setup failures
- Understanding bot configuration in detail
- Creating custom or non-standard configurations
- Learning how bot integration works

For automated setup details, see the [Azure Bot Service Integration guide](../1_setup/).
:::

## Related Documentation :books:

- **[Slack & Teams Integrations Overview](../)** - High-level concepts and business value
- **[Azure Bot Service Integration](../1_setup/)** - Automated setup guide
- **[AI-Hub Bot Developer's Guide](../../../6_code_deep_dive/aihub_bot/)** - Technical implementation details
- **[Bot-in-the-Loop Documentation](../../../3_sdk/6_feature_overview/bot-in-the-loop/)** - Human-AI collaboration
  workflows

## Key Terminology :book:

Understanding these terms is crucial for successful bot configuration:

| Term                                 | Definition                                                                                                                                                                                                                         |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bot Framework Messaging Endpoint** | The single public URL where Azure Bot Service sends ALL bot messages. Always `/api/v1/messages`. Configured in Teams Developer Portal (Step 3).                                                                                    |
| **MongoDB `path` Field**             | Internal routing path that determines which bot implementation handles a conversation. Examples: `/api/v1/agent/chat/completions/...` or `/api/v1/openai/chat/completions`. Configured in MongoDB `bot_paths` collection (Step 7). |
| **App ID / Client ID**               | Azure AD application identifier (UUID format). Same value used as Bot ID and in MongoDB `credentials.APP_ID`.                                                                                                                      |
| **Client Secret / App Password**     | Azure AD application secret. Stored in MongoDB as `credentials.APP_PASSWORD`. Expires and must be rotated.                                                                                                                         |
| **Tenant ID**                        | Microsoft 365 tenant identifier. Required for SingleTenant bots, stored as `credentials.APP_TENANTID`.                                                                                                                             |
| **Bot-in-the-Loop**                  | Pattern where AI agents request human input via Slack channels during workflow execution.                                                                                                                                          |
| **Slack Bot OAuth Token**            | Token for Slack integration (format: `xoxb-...`). Stored in MongoDB as `slack_token`.                                                                                                                                              |

::: warning Critical Distinction
**Bot Framework Messaging Endpoint** (`/api/v1/messages`) ≠ **MongoDB `path` Field** (e.g.,
`/api/v1/agent/chat/completions/...`)

These are two different concepts that serve different purposes. The messaging endpoint is where Azure Bot Service sends
messages. The `path` field determines how those messages are processed internally.
:::

## Prerequisites :clipboard:

Before starting, ensure you have access to:

- **Microsoft Teams Developer Portal** - For creating Teams apps and bots
- **MongoDB database** with `bot_paths` collection - For storing bot configuration
- **Azure Bot Framework** - For multi-channel bot management
- **Slack Workspace** with admin permissions - For Slack integration

______________________________________________________________________

## Part 1: Teams Developer Portal Setup :microsoft:

### Step 1: Create App with Basic Information

1. Navigate to [Teams Developer Portal](https://dev.teams.microsoft.com/)
2. Click **"Apps"** → **"New app"**
3. Fill in Basic Information:
   - App name
   - Short description
   - Full description
   - Developer information
   - App URLs
   - Application (client) ID (generate if needed)

### Step 2: Configure Permissions

1. Go to **"App features"** → **"Bot"**
2. Set required permissions:
   - **Message Read** in Chat/Team
   - **Message Send** in Chat/Team
3. Save permission changes

### Step 3: Create New Bot

1. In the app, navigate to **"Bot"** section
2. Click **"Set up"** or **"Create new bot"**
3. Enter the **Bot Framework messaging endpoint URL**:
   - Format: `https://your-domain.com/api/v1/messages`
   - This is the standard Azure Bot Service endpoint
   - Must be publicly accessible from the internet
   - For local development, use Azure DevTunnel or ngrok
4. **Write down the Bot ID** for later use

::: warning Bot Framework Endpoint vs MongoDB Path
**IMPORTANT DISTINCTION:**

- **Bot Framework Messaging Endpoint** (`/api/v1/messages`): The single entry point where Azure Bot Service sends ALL
  bot messages. This is configured here in Teams Developer Portal.

- **MongoDB `path` Field** (e.g., `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`): Internal routing
  path that determines which bot implementation handles the conversation. This is configured in MongoDB (Step 7) and
  allows multiple bots to coexist.

**How it works:**

1. Azure Bot Service sends message to `/api/v1/messages`
2. AI-Hub looks up the conversation's `path` in MongoDB `bot_paths` collection
3. Request is routed to the specific bot implementation

**Example:**

- Teams Developer Portal endpoint: `https://my-domain.com/api/v1/messages`
- MongoDB path for Agent Bot: `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
- MongoDB path for OpenAI Bot: `/api/v1/openai/chat/completions`

These do NOT need to match! The messaging endpoint is always `/api/v1/messages`.
:::

::: tip Local Development
For local development, expose your bot server using Azure DevTunnel:

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8000
devtunnel host
# Use the https URL (e.g., https://abc123-8000.devtunnels.ms/api/v1/messages)
```

See the [Developer's Guide](../../../6_code_deep_dive/aihub_bot/) for detailed local development setup.
:::

### Step 4: Create Client Secret

1. In the bot configuration, find **"Client secrets"**
2. Click **"Add a client secret"**
3. **IMPORTANT**: Copy and securely save the client secret immediately
   - Secret format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to view it again
4. Note the secret's expiration date

::: danger Security Warning
Client secrets are only displayed once at creation time. Store them securely in a password manager or secrets vault
immediately. If lost, you'll need to generate a new secret and update your MongoDB configuration.
:::

### Step 5: Add Bot to App

1. Navigate back to app overview
2. Confirm bot is listed under **"App features"**
3. Verify bot ID matches the one created in Step 3

### Step 6: Publish App to Organization

1. Go to **"Publish"** → **"Publish to org"**
2. Review all configurations
3. Click **"Publish"**
4. Wait for admin approval (if required)
5. Once approved, note the **App/Client ID** and **Tenant ID**

______________________________________________________________________

## Part 2: MongoDB Configuration :floppy_disk:

### Step 7: Add Bot Path Entry

Add a new document to the `bot_paths` collection with the following structure:

```json
{
  "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json",
  "credentials": {
    "APP_TYPE": "SingleTenant",
    "APP_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "APP_PASSWORD": "xxx8Q~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "APP_TENANTID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "system_message": "You are a helpful AI assistant powered by Azure OpenAI.",
  "slack_token": ""
}
```

**Required Fields:**

- `path`: The **internal routing path** for this specific bot implementation
  - **This is NOT the Bot Framework messaging endpoint** (which is always `/api/v1/messages`)
  - This determines which bot handler processes conversations
  - Examples:
    - `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json` - Agent-based bot
    - `/api/v1/openai/chat/completions` - Direct OpenAI bot
    - `/api/v1/bitl/chat/completions` - Bot-in-the-Loop bot
- `credentials`: Object containing Azure Bot authentication
  - `APP_TYPE`: Authentication type (`"SingleTenant"` or `"MultiTenant"`)
  - `APP_ID`: Teams app client ID from Step 6
  - `APP_PASSWORD`: Client secret from Step 4
  - `APP_TENANTID`: Microsoft 365 tenant ID from Step 6 (required for SingleTenant)
- `system_message`: Default system message/instructions for the bot
- `slack_token`: Empty string initially (populated in Step 14 for Slack integration)

::: tip Multi-Bot Configuration
You can have **multiple bot implementations** with different `path` values, all sharing the same Bot Framework messaging
endpoint (`/api/v1/messages`):

**Agent-based bot for customer support:**

```json
{
  "path": "/api/v1/agent/chat/completions/CustomerSupportAgent/prod/json",
  "credentials": { "APP_ID": "xxx", "APP_PASSWORD": "xxx", "APP_TENANTID": "xxx", "APP_TYPE": "SingleTenant" },
  "system_message": "You are a customer support assistant."
}
```

**OpenAI-based bot for general queries:**

```json
{
  "path": "/api/v1/openai/chat/completions",
  "credentials": { "APP_ID": "xxx", "APP_PASSWORD": "xxx", "APP_TENANTID": "xxx", "APP_TYPE": "SingleTenant" },
  "system_message": "You are a helpful AI assistant."
}
```

Each conversation is associated with one `path`, which determines its bot implementation and behavior.
:::

::: tip Configuration Tip
Use descriptive path names that indicate the agent or functionality, making it easier to manage multiple bots. For
example, `/api/v1/agent/chat/completions/CustomerSupportAgent/production/json` clearly identifies the bot's purpose.
:::

______________________________________________________________________

## Part 3: Bot Framework & Slack Integration :slack:

### Step 8: Create Slack App

1. Navigate to [Slack API Apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Give your app a name (e.g., "My Bot Name")
5. Select the workspace where you want to develop the app
6. Click **"Create App"**

### Step 8.5: Configure App Home Settings

1. Go to your Slack app's App Home settings:
   - URL format: `https://api.slack.com/apps/{SLACK_APP_ID}/app-home`
   - Replace `{SLACK_APP_ID}` with your Slack app ID
   - Example: `https://api.slack.com/apps/A09QARZNF45/app-home`
2. Under **"Show Tabs"** section:
   - Toggle **"Always show my bot as online"** to **ON**
   - Toggle **"Home Tab"** to **ON**
3. Under **"Messages Tab"** section:
   - **Leave "Messages Tab" disabled** - Bot will interact through channels and direct messages instead
   - Uncheck "Allow users to send Slash commands and messages from the messages tab" (if visible)
4. Click **"Save Changes"** if prompted

::: info Messages Tab Configuration
The Messages Tab is typically disabled when using Bot Framework, as the bot communicates through channels, group chats,
and direct messages rather than the app's Messages tab.
:::

### Step 9: Configure Bot Framework Slack Channel

1. Navigate to [Bot Framework Portal](https://dev.botframework.com/)
2. Go to your bot's channels page:
   - URL format: `https://dev.botframework.com/bots/channels?id={APP_ID}&channelId=slack`
   - Replace `{APP_ID}` with your Teams app ID (from Step 6)
   - Example: `https://dev.botframework.com/bots/channels?id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx&channelId=slack`
3. Click **"Slack"** channel or **"Configure"** if already added
4. Copy the app credentials from your Slack app (from Step 8):
   - **Client ID** (from Slack App Credentials)
   - **Client Secret** (from Slack App Credentials)
5. Paste these into the Bot Framework Slack channel configuration
6. Copy the following URLs for later use:
   - **Redirect URL** (needed for Step 10)
   - **Event Subscription URL** (needed for Step 11)
7. Click **"Save"**
8. **IMPORTANT:** After saving, you'll be automatically redirected to Slack to install/reinstall the application
   - This completes the OAuth flow
   - Follow the prompts to authorize the app
   - This may satisfy the event subscription requirements automatically

::: tip Automatic Configuration
The Bot Framework often configures many Slack settings automatically during the OAuth flow. After completing Step 9,
verify Steps 10-12 to confirm settings rather than manually configuring everything.
:::

### Step 10: Configure Slack OAuth

1. Go to your Slack app's OAuth settings:
   - URL format: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
   - Replace `{SLACK_APP_ID}` with your Slack app ID
   - Example: `https://api.slack.com/apps/A09QARZNF45/oauth`
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"**
4. Add the following scopes:
   - `chat:write` - Allows the bot to send messages
   - `assistant:write` - Allows the bot to interact with App Agents/Assistants
5. Under **"Redirect URLs"**, click **"Add New Redirect URL"**
6. Paste the **Redirect URL** from Bot Framework (Step 9)
7. Click **"Save URLs"**

::: info Automatic Scopes
Other required scopes (channels:history, groups:history, im:history, mpim:history) may be added automatically when you
subscribe to bot events in Step 12, or when you complete the Bot Framework OAuth flow.
:::

### Step 11: Configure Slack Event Subscriptions

1. Go to your Slack app's Event Subscriptions:
   - URL format: `https://api.slack.com/apps/{SLACK_APP_ID}/event-subscriptions`
   - Replace `{SLACK_APP_ID}` with your Slack app ID
   - Example: `https://api.slack.com/apps/A09QARZNF45/event-subscriptions`
2. Toggle **"Enable Events"** to ON
3. In **"Request URL"**, paste the **Event Subscription URL** from Bot Framework (Step 9)
4. Wait for URL verification (should show "Verified ✓")

::: tip Already Configured?
If you were redirected to Slack during Step 9 and completed the installation, the event subscriptions may already be
configured automatically by Bot Framework. Verify this page to confirm.
:::

### Step 12: Subscribe to Bot Events (If Needed)

::: warning Optional Step
These event subscriptions may not be necessary if the Bot Framework Slack channel handles them automatically. Check if
events are already configured before adding manually.
:::

If events are not automatically configured, in the Event Subscriptions page, scroll down to **"Subscribe to bot
events"** and add the following:

| Event Name                         | Description                                                 | Required Scope     |
| ---------------------------------- | ----------------------------------------------------------- | ------------------ |
| `message.channels`                 | A message was posted to a channel                           | `channels:history` |
| `message.groups`                   | A message was posted to a private channel                   | `groups:history`   |
| `message.im`                       | A message was posted in a direct message channel            | `im:history`       |
| `message.mpim`                     | A message was posted in a multiparty direct message channel | `mpim:history`     |
| `assistant_thread_started`         | An App Agent thread was started                             | none               |
| `assistant_thread_context_changed` | The context changed while an App Agent thread was visible   | none               |

::: info Automatic Scope Addition
When you add these events, Slack automatically adds the necessary OAuth scopes to your app configuration.
:::

Click **"Save Changes"**

### Step 13: Install Slack App to Workspace

::: tip May Already Be Complete
If you were redirected to Slack and completed the installation during Step 9, this step may already be complete. You can
verify by checking if the bot already appears in your Slack workspace.
:::

If not yet installed:

1. Go to your Slack app's installation page:
   - URL format: `https://api.slack.com/apps/{SLACK_APP_ID}/install-on-team`
   - Replace `{SLACK_APP_ID}` with your Slack app ID
   - Example: `https://api.slack.com/apps/A09QARZNF45/install-on-team`
2. Click **"Install to Workspace"** (or **"Reinstall to Workspace"** if updating)
3. Review the permissions requested
4. Click **"Allow"**
5. **IMPORTANT:** Copy the **Bot User OAuth Token** that appears
   - Format: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`
   - This is the token you'll add to MongoDB in the next step

**Alternative:** If already installed, retrieve your token from:

- **OAuth & Permissions** page: `https://api.slack.com/apps/{SLACK_APP_ID}/oauth`
- Look for **"Bot User OAuth Token"** under "OAuth Tokens for Your Workspace"

::: danger Token Security
The Slack Bot OAuth Token provides full access to your bot's capabilities. Store it securely and never commit it to
version control. Treat it with the same security as passwords and API keys.
:::

### Step 14: Add Slack OAuth Token to MongoDB

Update the bot path document in MongoDB to include the Slack OAuth token from Step 13:

```json
{
  "_id": {
    "$oid": "xxxxxxxxxxxxxxxxxxxxxxxx"
  },
  "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json",
  "credentials": {
    "APP_TYPE": "SingleTenant",
    "APP_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "APP_PASSWORD": "xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "APP_TENANTID": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
  },
  "system_message": "You are a helpful AI assistant powered by Azure OpenAI.",
  "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Slack OAuth Token Details:**

- Format: `xoxb-` followed by numbers and dashes
- Obtained from Step 13 during Slack app installation
- Replace the empty string `""` with the actual token
- Keep this token secure and never commit to version control

**To update existing document:**

```javascript
db.bot_paths.updateOne(
  { "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json" },
  { $set: { "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx" } }
)
```

**Alternative: Update by \_id:**

```javascript
db.bot_paths.updateOne(
  { "_id": ObjectId("xxxxxxxxxxxxxxxxxxxxxxxx") },
  { $set: { "slack_token": "xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx" } }
)
```

______________________________________________________________________

## App Manifest Examples :page_facing_up:

These manifests show the complete configuration for both Slack and Teams apps. You can use these as reference or to
create apps programmatically.

### Slack App Manifest

```json
{
    "display_information": {
        "name": "LLM Wrapping Agent"
    },
    "features": {
        "app_home": {
            "home_tab_enabled": true,
            "messages_tab_enabled": false,
            "messages_tab_read_only_enabled": false
        },
        "bot_user": {
            "display_name": "LLM Wrapping Agent",
            "always_online": true
        }
    },
    "oauth_config": {
        "redirect_urls": [
            "https://slack.botframework.com"
        ],
        "scopes": {
            "bot": [
                "channels:history",
                "groups:history",
                "im:history",
                "mpim:history",
                "chat:write",
                "assistant:write"
            ]
        }
    },
    "settings": {
        "event_subscriptions": {
            "request_url": "https://slack.botframework.com/api/Events/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "bot_events": [
                "assistant_thread_context_changed",
                "assistant_thread_started",
                "message.channels",
                "message.groups",
                "message.im",
                "message.mpim"
            ]
        },
        "org_deploy_enabled": false,
        "socket_mode_enabled": false,
        "token_rotation_enabled": false
    }
}
```

**Key Configuration Points:**

- **app_home**: Configuration for the app's home and messages tabs
  - **home_tab_enabled**: Set to `true` to enable Home Tab
  - **messages_tab_enabled**: Set to `false` (interaction happens through channels/DMs, not the Messages tab)
  - **messages_tab_read_only_enabled**: Set to `false`
- **always_online**: Set to `true` to show bot as always online
- **redirect_urls**: Always `https://slack.botframework.com` for Bot Framework integration
- **request_url**: Format is `https://slack.botframework.com/api/Events/{APP_ID}` where `{APP_ID}` is your Teams app
  client ID
- **bot scopes**: All 6 scopes are required for full functionality (including `chat:write` and `assistant:write`)
- **bot_events**: All 6 events enable the bot to receive messages across all conversation types

### Teams App Manifest

```json
{
    "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.23/MicrosoftTeams.schema.json",
    "version": "1.0.0",
    "manifestVersion": "1.23",
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "name": {
        "short": "LLM Agent",
        "full": "LLM Wrapping Agent"
    },
    "developer": {
        "name": "Your Organization Name",
        "websiteUrl": "https://your-domain.com",
        "privacyUrl": "https://your-domain.com/privacy",
        "termsOfUseUrl": "https://your-domain.com/terms"
    },
    "description": {
        "short": "LLMWrappingAgent",
        "full": "LLMWrappingAgent"
    },
    "icons": {
        "outline": "outline.png",
        "color": "color.png"
    },
    "accentColor": "#ffffff",
    "bots": [
        {
            "botId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "scopes": [
                "personal",
                "team",
                "groupChat"
            ],
            "isNotificationOnly": false,
            "supportsCalling": false,
            "supportsVideo": false,
            "supportsFiles": true
        }
    ],
    "validDomains": [],
    "webApplicationInfo": {
        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    },
    "authorization": {
        "permissions": {
            "resourceSpecific": [
                {
                    "name": "ChannelMessage.Read.Group",
                    "type": "Application"
                },
                {
                    "name": "ChannelMessage.Send.Group",
                    "type": "Application"
                },
                {
                    "name": "ChatMessage.Read.Chat",
                    "type": "Application"
                },
                {
                    "name": "ChatMessage.Send.Chat",
                    "type": "Application"
                }
            ]
        }
    }
}
```

**Key Configuration Points:**

- **id** and **webApplicationInfo.id**: Your Teams app client ID (APP_ID)
- **botId**: Same as your app client ID
- **scopes**: Enable bot in personal chats, teams, and group chats
- **supportsFiles**: Set to `true` to allow file uploads
- **Resource-Specific Permissions**:
  - `ChannelMessage.Read.Group` - Read messages in channels
  - `ChannelMessage.Send.Group` - Send messages in channels
  - `ChatMessage.Read.Chat` - Read messages in chats
  - `ChatMessage.Send.Chat` - Send messages in chats

### Using Manifests for App Creation

**Slack:**

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From an app manifest"**
3. Select your workspace
4. Paste the Slack manifest JSON
5. Review and create

**Teams:**

1. Download the manifest as `manifest.json`
2. Add icon files (`outline.png` and `color.png`) to the same directory
3. Zip all three files together
4. In Teams Developer Portal, click **"Import app"**
5. Upload the zip file

______________________________________________________________________

## Verification Checklist :white_check_mark:

After completing all steps, verify:

**Teams Configuration:**

- [ ] Teams app is published and approved
- [ ] Bot Framework messaging endpoint is set to `/api/v1/messages`
- [ ] Bot Framework messaging endpoint URL is publicly accessible
- [ ] Bot responds to messages in Teams
- [ ] Bot permissions are correctly set (Message Read/Send in Chat/Team)

**MongoDB Configuration:**

- [ ] `bot_paths` entry exists with all required fields
- [ ] `credentials` object contains APP_TYPE, APP_ID, APP_PASSWORD, and APP_TENANTID (for SingleTenant)
- [ ] `path` field contains internal routing path (e.g., `/api/v1/agent/chat/completions/...`)
- [ ] `path` field is DIFFERENT from Bot Framework messaging endpoint (`/api/v1/messages`)
- [ ] `system_message` is configured appropriately for bot's purpose
- [ ] Client secret (APP_PASSWORD) is stored securely and hasn't expired

**Slack Configuration:**

- [ ] Slack app is created with correct name
- [ ] App Home configured: "Always show my bot as online" toggle ON
- [ ] App Home configured: "Home Tab" toggle ON
- [ ] App Home configured: "Messages Tab" is disabled (bot interacts through channels/DMs)
- [ ] Bot token scopes `chat:write` and `assistant:write` are added in Slack OAuth settings
- [ ] Bot Framework Slack channel is configured with Client ID and Client Secret
- [ ] Saved Bot Framework configuration and completed OAuth redirect to Slack
- [ ] Redirect URL is added to Slack OAuth settings
- [ ] Event subscription URL is verified (may be automatic)
- [ ] Bot events are subscribed (may be automatic via Bot Framework)
- [ ] Slack app is installed to workspace (may have happened during Step 9 redirect)
- [ ] `slack_token` is obtained from Slack OAuth & Permissions page
- [ ] `slack_token` is added to MongoDB
- [ ] Bot responds to messages in Slack channels
- [ ] Bot responds to direct messages in Slack

______________________________________________________________________

## Troubleshooting :wrench:

### Bot Not Responding in Teams

- **Messaging Endpoint Issues:**
  - Verify Bot Framework messaging endpoint is set to `/api/v1/messages` in Teams Developer Portal
  - Ensure the endpoint URL is publicly accessible (test with curl or browser)
  - For local development, confirm Azure DevTunnel or ngrok is running
- **Authentication Issues:**
  - Check `APP_PASSWORD` (client secret) is correct and hasn't expired
  - Confirm `APP_TENANTID` and `APP_ID` match the values from Step 6
  - Verify `APP_TYPE` is set correctly (`SingleTenant` or `MultiTenant`)
- **Configuration Issues:**
  - Review app permissions in Teams Developer Portal (Message Read/Send in Chat/Team)
  - Verify MongoDB `bot_paths` entry exists with correct credentials
  - Check that `path` field in MongoDB contains a valid internal routing path
  - Ensure conversation was created with the correct `path` value

### Slack Integration Issues

- Verify `slack_token` is valid (starts with `xoxb-`)
- Check Slack app has necessary bot token scopes:
  - `chat:write` (required for sending messages)
  - `assistant:write` (required for App Agent interactions)
  - `channels:history`, `groups:history`, `im:history`, `mpim:history` (for message events)
- Verify App Home settings are configured:
  - "Always show my bot as online" should be ON
  - "Home Tab" should be ON
  - "Allow users to send Slash commands and messages from the messages tab" should be checked
- Confirm bot is added to desired Slack channels (invite bot with @botname)
- Ensure all 6 bot events are subscribed in Event Subscriptions
- Verify Event Subscription URL shows "Verified ✓"
- Check Redirect URL is correctly added in Slack OAuth settings
- Ensure `slack_token` field is not an empty string in MongoDB
- Review Bot Framework Slack channel configuration
- Reinstall Slack app if scopes were changed after initial installation (required for scope changes to take effect)

### MongoDB Connection Issues

- Verify collection name is `bot_paths`
- Check document structure matches examples above
- Ensure all required fields are present in `credentials` object
- Validate `APP_ID` and `APP_TENANTID` are in correct UUID format
- Confirm `path` field starts with `/api/`

______________________________________________________________________

## Security Best Practices :shield:

1. **Never commit secrets to version control**
2. **Rotate client secrets before expiration**
3. **Use environment variables for sensitive data**
4. **Restrict MongoDB access with proper authentication**
5. **Monitor OAuth token usage for anomalies**
6. **Keep audit logs of bot path modifications**
7. **Use HTTPS for all messaging endpoints**

______________________________________________________________________

## Support :sos:

For issues or questions:

- **Teams Developer Portal**:
  [Microsoft Teams Documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/)
- **Bot Framework**: [Azure Bot Service Documentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- **Slack API**: [Slack API Documentation](https://api.slack.com/)

______________________________________________________________________

## Next Steps :rocket:

After completing the manual bot setup:

1. **Test Your Bot**: Send a message in Teams or Slack to verify the bot responds correctly
2. **Review Logs**: Check application logs for any errors or warnings during bot interactions
3. **Configure Additional Features**: Explore [Bot-in-the-Loop](../../../3_sdk/6_feature_overview/bot-in-the-loop/) for
   human-AI collaboration
4. **Implement Custom Logic**: See the [Developer's Guide](../../../6_code_deep_dive/aihub_bot/) for custom bot
   implementations
5. **Monitor Performance**: Set up observability and monitoring for production deployments

______________________________________________________________________

*Last Updated: November 14, 2025*
