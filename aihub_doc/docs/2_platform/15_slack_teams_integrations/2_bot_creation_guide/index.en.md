---
title: Bot Creation Manual Setup Guide
---

# Bot Creation Manual Setup Guide :robot: :wrench:

::: info **TL;DR - What is This Guide?**
This comprehensive manual provides **step-by-step instructions for manually creating and configuring bots** with Microsoft Teams and Slack integration. Use this guide when you need to create new bots from scratch, configure Azure Bot Framework channels, or troubleshoot existing bot deployments. It covers everything from Teams Developer Portal setup to MongoDB configuration and Slack OAuth integration.
:::

## Prerequisites :clipboard:

Before starting, ensure you have access to:

- **Microsoft Teams Developer Portal** - For creating Teams apps and bots
- **MongoDB database** with `bot_paths` collection - For storing bot configuration
- **Azure Bot Framework** - For multi-channel bot management
- **Slack Workspace** with admin permissions - For Slack integration

---

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
3. Enter the messaging endpoint URL:
   - Format: `https://your-domain.com/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
   - Or other paths like:
     - `https://your-domain.com/api/v1/openai/chat/completions`
     - `https://your-domain.com/api/v1/bitl/chat/completions`
   - This must exactly match the `path` field you'll add to MongoDB in Step 7
4. **Write down the Bot ID** for later use

::: warning Important
The messaging endpoint URL must be accessible from the internet and must exactly match the `path` field in your MongoDB configuration. Mismatches will cause bot authentication failures.
:::

### Step 4: Create Client Secret

1. In the bot configuration, find **"Client secrets"**
2. Click **"Add a client secret"**
3. **IMPORTANT**: Copy and securely save the client secret immediately
   - Secret format: `xxx~xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to view it again
4. Note the secret's expiration date

::: danger Security Warning
Client secrets are only displayed once at creation time. Store them securely in a password manager or secrets vault immediately. If lost, you'll need to generate a new secret and update your MongoDB configuration.
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

---

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

- `path`: The full API endpoint path (must match messaging endpoint URL in Step 3)
  - Examples:
    - `/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json`
    - `/api/v1/openai/chat/completions`
    - `/api/v1/bitl/chat/completions`
- `credentials`: Object containing Azure bot authentication
  - `APP_TYPE`: Authentication type (typically `"SingleTenant"`)
  - `APP_ID`: Teams app client ID from Step 6
  - `APP_PASSWORD`: Client secret from Step 4
  - `APP_TENANTID`: Microsoft 365 tenant ID from Step 6
- `system_message`: Default system message for the bot
- `slack_token`: Empty string initially (populated in Step 14)

::: tip Configuration Tip
Use descriptive path names that indicate the agent or functionality, making it easier to manage multiple bots. For example, `/api/v1/agent/chat/completions/CustomerSupportAgent/production/json` clearly identifies the bot's purpose.
:::

---

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
The Messages Tab is typically disabled when using Bot Framework, as the bot communicates through channels, group chats, and direct messages rather than the app's Messages tab.
:::

### Step 9: Configure Bot Framework Slack Channel

1. Navigate to [Bot Framework Portal](https://dev.botframework.com/)
2. Go to your bot's channels page:
   - URL format: `https://dev.botframework.com/bots/channels?id={APP_ID}&channelId=slack`
   - Replace `{APP_ID}` with your Teams app ID (from Step 6)
   - Example: `https://dev.botframework.com/bots/channels?id=aea34319-6452-4881-9872-cd4cc22c6f66&channelId=slack`
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
The Bot Framework often configures many Slack settings automatically during the OAuth flow. After completing Step 9, verify Steps 10-12 to confirm settings rather than manually configuring everything.
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
Other required scopes (channels:history, groups:history, im:history, mpim:history) may be added automatically when you subscribe to bot events in Step 12, or when you complete the Bot Framework OAuth flow.
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
If you were redirected to Slack during Step 9 and completed the installation, the event subscriptions may already be configured automatically by Bot Framework. Verify this page to confirm.
:::

### Step 12: Subscribe to Bot Events (If Needed)

::: warning Optional Step
These event subscriptions may not be necessary if the Bot Framework Slack channel handles them automatically. Check if events are already configured before adding manually.
:::

If events are not automatically configured, in the Event Subscriptions page, scroll down to **"Subscribe to bot events"** and add the following:

| Event Name | Description | Required Scope |
|------------|-------------|----------------|
| `message.channels` | A message was posted to a channel | `channels:history` |
| `message.groups` | A message was posted to a private channel | `groups:history` |
| `message.im` | A message was posted in a direct message channel | `im:history` |
| `message.mpim` | A message was posted in a multiparty direct message channel | `mpim:history` |
| `assistant_thread_started` | An App Agent thread was started | none |
| `assistant_thread_context_changed` | The context changed while an App Agent thread was visible | none |

::: info Automatic Scope Addition
When you add these events, Slack automatically adds the necessary OAuth scopes to your app configuration.
:::

Click **"Save Changes"**

### Step 13: Install Slack App to Workspace

::: tip May Already Be Complete
If you were redirected to Slack and completed the installation during Step 9, this step may already be complete. You can verify by checking if the bot already appears in your Slack workspace.
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
The Slack Bot OAuth Token provides full access to your bot's capabilities. Store it securely and never commit it to version control. Treat it with the same security as passwords and API keys.
:::

### Step 14: Add Slack OAuth Token to MongoDB

Update the bot path document in MongoDB to include the Slack OAuth token from Step 13:

```json
{
  "_id": {
    "$oid": "6908ab1edc4c571fff1d46e2"
  },
  "path": "/api/v1/agent/chat/completions/LLMWrappingAgent/dev_agent/json",
  "credentials": {
    "APP_TYPE": "SingleTenant",
    "APP_ID": "aea34319-6452-4881-9872-cd4cc22c6f66",
    "APP_PASSWORD": "rWc8Q~retZ0QjVc4QW5qLFauauB-4XoHQu_JPbIK",
    "APP_TENANTID": "37314c94-c755-48ab-85bb-acb83e492c42"
  },
  "system_message": "You are a helpful AI assistant powered by Azure OpenAI.",
  "slack_token": "xoxb-8373804641105-9833930643140-UFZqwD4D1vk3dGC6dTZo0jaT"
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
  { $set: { "slack_token": "xoxb-8373804641105-9833930643140-UFZqwD4D1vk3dGC6dTZo0jaT" } }
)
```

**Alternative: Update by _id:**

```javascript
db.bot_paths.updateOne(
  { "_id": ObjectId("6908ab1edc4c571fff1d46e2") },
  { $set: { "slack_token": "xoxb-8373804641105-9833930643140-UFZqwD4D1vk3dGC6dTZo0jaT" } }
)
```

---

## App Manifest Examples :page_facing_up:

These manifests show the complete configuration for both Slack and Teams apps. You can use these as reference or to create apps programmatically.

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
            "request_url": "https://slack.botframework.com/api/Events/aea34319-6452-4881-9872-cd4cc22c6f66",
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
- **request_url**: Format is `https://slack.botframework.com/api/Events/{APP_ID}` where `{APP_ID}` is your Teams app client ID (e.g., `aea34319-6452-4881-9872-cd4cc22c6f66`)
- **bot scopes**: All 6 scopes are required for full functionality (including `chat:write` and `assistant:write`)
- **bot_events**: All 6 events enable the bot to receive messages across all conversation types

### Teams App Manifest

```json
{
    "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.23/MicrosoftTeams.schema.json",
    "version": "1.0.0",
    "manifestVersion": "1.23",
    "id": "c872309b-a920-4c99-8362-477453200cf3",
    "name": {
        "short": "LLM Agent",
        "full": "LLM Wrapping Agent"
    },
    "developer": {
        "name": "bbv Software Services AG",
        "websiteUrl": "https://bbv.ch",
        "privacyUrl": "https://bbv.ch",
        "termsOfUseUrl": "https://bbv.ch"
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
            "botId": "aea34319-6452-4881-9872-cd4cc22c6f66",
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
        "id": "aea34319-6452-4881-9872-cd4cc22c6f66"
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

---

## Verification Checklist :white_check_mark:

After completing all steps, verify:

**Teams Configuration:**
- [ ] Teams app is published and approved
- [ ] Bot responds to messages in Teams
- [ ] Bot permissions are correctly set (Message Read/Send)
- [ ] Messaging endpoint URL is accessible

**MongoDB Configuration:**
- [ ] `bot_paths` entry exists with all required fields
- [ ] `credentials` object contains all four fields (APP_TYPE, APP_ID, APP_PASSWORD, APP_TENANTID)
- [ ] `path` field matches Teams messaging endpoint
- [ ] `system_message` is configured
- [ ] Client secret (APP_PASSWORD) is stored securely

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

---

## Troubleshooting :wrench:

### Bot Not Responding in Teams

- Verify messaging endpoint URL is correct and accessible
- Check `APP_PASSWORD` (client secret) is correct and hasn't expired
- Confirm `APP_TENANTID` and `APP_ID` are correct
- Review app permissions in Teams Developer Portal
- Ensure `path` field in MongoDB matches the messaging endpoint exactly

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

---

## Security Best Practices :shield:

1. **Never commit secrets to version control**
2. **Rotate client secrets before expiration**
3. **Use environment variables for sensitive data**
4. **Restrict MongoDB access with proper authentication**
5. **Monitor OAuth token usage for anomalies**
6. **Keep audit logs of bot path modifications**
7. **Use HTTPS for all messaging endpoints**

---

## Support :sos:

For issues or questions:

- **Teams Developer Portal**: [Microsoft Teams Documentation](https://learn.microsoft.com/en-us/microsoftteams/platform/)
- **Bot Framework**: [Azure Bot Service Documentation](https://learn.microsoft.com/en-us/azure/bot-service/)
- **Slack API**: [Slack API Documentation](https://api.slack.com/)

---

*Last Updated: November 3, 2025*