---
title: Prerequisites
---

# Prerequisites

This guide covers prerequisites for deploying the AI-Hub platform.

::: tip Choose Your Deployment Type
The prerequisites differ based on your deployment type:

- **Production Deployment**: Deploy to a server with a real domain name and automatic SSL certificates
- **Local Deployment**: Run on your local machine with `127.0.0.1.nip.io` and self-signed certificates

Follow only the sections relevant to your deployment type.
:::

## Common Requirements (All Deployments)

These requirements apply to both production and local deployments.

### System requirements

#### Minimum specifications

- **CPU**: 8 cores
- **RAM**: 32 GB
- **Storage**: 200 GB free space
- **Network**: Stable internet connection for Docker image downloads

#### Recommended specifications

- **CPU**: 12+ cores
- **RAM**: 48+ GB
- **Storage**: 300+ GB SSD for improved database performance
- **Network**: High-bandwidth connection for faster initial setup

::: warning
The platform runs multiple services simultaneously (databases, vector stores, LLM proxies, web interfaces, processing
engines). Systems below minimum specifications will experience service failures or degraded performance.
:::

### Software requirements

#### Operating system

- Linux (Ubuntu 20.04+ recommended and tested)
- Any Docker-compatible Linux distribution

#### Required software

- **Docker**: Latest stable version
- **Docker Compose**: v2.0 or higher
- **sudo/root access**: Required for installation and configuration

#### Network configuration

- **Open ports**: 80 (HTTP), 443 (HTTPS)
- **Internet access**: Required for Docker image downloads and updates

#### Verification

Test your Docker installation:

```bash
docker --version
docker compose --version
docker run hello-world
```

All commands must complete successfully.

### Authentication Provider Setup

The platform requires an OAuth2/OpenID Connect identity provider for both production and local deployments. This guide
documents Azure Entra ID setup. Other providers (Google, Okta, Auth0) can be configured using similar patterns.

#### Azure Entra ID setup

Complete the following steps in the Azure Portal to prepare authentication:

**Step 1: Create app registration**

1. Navigate to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Click **"New registration"**
3. Configure the registration:
   - **Name**: `Swiss AI Hub` (or your organization's naming convention)
   - **Supported account types**: Select based on requirements
     - `Accounts in this organizational directory only` (single tenant — recommended for most deployments)
   - **Redirect URI**: Leave blank (will be configured in Step 5)
4. Click **"Register"**

**Step 2: Configure token version**

The platform requires access token version 2 for proper authentication.

1. Navigate to **"Manifest"**
2. Find the `requestedAccessTokenVersion` property
3. Change the value from `null` or `1` to `2`:
   ```json
   "requestedAccessTokenVersion": 2
   ```
4. Click **"Save"** at the top of the manifest editor

::: warning
Access token version 2 is required for the platform to function correctly. Version 1 tokens are not supported and will
cause authentication failures.
:::

**Step 3: Configure API permissions**

1. Navigate to **"API permissions"** → **"Add a permission"**
2. Select **"Microsoft Graph"** → **"Delegated permissions"**
3. Add the following permissions:
   - `openid` - Required for OpenID Connect authentication
   - `profile` - Required for basic user profile information
   - `email` - Required for email address
   - `offline_access` - Required for refresh tokens
   - `User.Read` - Required for user profile reading
   - `Group.Read.All` - Required for group membership information
4. Select **"Microsoft Graph"** → **"Application permissions"**
5. Add the following permissions:
   - `User.ReadBasic.All` - Required for reading all users' basic profiles
   - `Directory.Read.All` - Required for reading directory data
   - `ProfilePhoto.Read.All` - Required for reading profile photos
6. Click **"Grant admin consent for [Your Organization]"**
7. Verify all permissions display **"Granted for [Your Organization]"** status

::: warning
All listed permissions are required for platform functionality. Missing permissions will cause authentication or
authorization failures during deployment.
:::

**Step 4: Create client secret**

1. Navigate to **"Certificates & secrets"** → **"Client secrets"** → **"New client secret"**
2. Configure the secret:
   - **Description**: Enter descriptive name (e.g., `AI-Hub Secret`)
   - **Expires**: Select expiration period (12-24 months recommended)
3. Click **"Add"**
4. **Immediately copy the secret value** to secure storage
5. Record this value as `[CLIENT_SECRET]` for deployment configuration

::: danger
The client secret value is displayed only once immediately after creation. If the value is lost, a new secret must be
created. Store in a password manager or secure vault.
:::

**Step 5: Configure app roles**

App roles enable role-based access control (RBAC) for platform users.

Create four app roles following this process:

1. Navigate to **"App roles"** → **"Create app role"**
2. Create each of the following roles:

**Administrator role:**

- **Display name**: `AIHubAdmin`
- **Allowed member types**: `Users/Groups`
- **Value**: `AIHubAdmin`
- **Description**: `Administrator access to AI-Hub platform`

**User role:**

- **Display name**: `AIHubUser`
- **Allowed member types**: `Users/Groups`
- **Value**: `AIHubUser`
- **Description**: `Standard user access to AI-Hub platform`

**Developer role:**

- **Display name**: `AIHubDeveloper`
- **Allowed member types**: `Users/Groups`
- **Value**: `AIHubDeveloper`
- **Description**: `Developer access to AI-Hub platform services`

**System Administrator role:**

- **Display name**: `AIHubSysAdmin`
- **Allowed member types**: `Users/Groups`
- **Value**: `AIHubSysAdmin`
- **Description**: `System administrator access to infrastructure tools (Dagster, SeaweedFS, Attu)`

::: tip
The `AIHubSysAdmin` role is required to access the Dagster pipeline orchestration dashboard, the SeaweedFS data lake
console at `datalake.${DOMAIN}`, and the Attu Milvus admin UI. Users without this role can still use the main AI-Hub
interface and OpenWebUI.
:::

**Step 6: Configure SPA redirect URIs**

Single-Page Application (SPA) redirect URIs are required for the main web interface with multilingual support.

1. Navigate to **"Authentication"** → **"Add a platform"** → **"Single-page application"**

2. Add redirect URIs based on your deployment type:

   **For Production:** Replace `your-domain.com` with your actual domain

   ```
   https://your-domain.com/de/auth/callback
   https://your-domain.com/en/auth/callback
   https://your-domain.com/it/auth/callback
   https://your-domain.com/fr/auth/callback
   ```

   **For Local Deployment:** Use `127.0.0.1.nip.io`

   ```
   https://127.0.0.1.nip.io/de/auth/callback
   https://127.0.0.1.nip.io/en/auth/callback
   https://127.0.0.1.nip.io/it/auth/callback
   https://127.0.0.1.nip.io/fr/auth/callback
   ```

   ::: tip
You can add both production and local URIs to the same app registration for testing purposes.
   :::

3. Configure token settings:
   - Enable **Access tokens** (used for implicit flows)
   - Enable **ID tokens** (used for implicit flows)
4. Click **"Configure"**

**Step 7: Configure web application redirect URIs**

Web application redirect URIs are required for integrated services (OpenWebUI, Dagster, Data Lake).

1. Navigate to **"Authentication"** → **"Add a platform"** → **"Web"**

2. Add redirect URIs based on your deployment type:

   **For Production:** Replace `your-domain.com` with your actual domain

   ```
   https://openwebui.your-domain.com/oauth/oidc/callback
   https://dagster.your-domain.com/oauth2/callback
   https://datalake.your-domain.com/oauth2/callback
   https://attu.your-domain.com/oauth2/callback
   ```

   **For Local Deployment:** Use `127.0.0.1.nip.io`

   ```
   https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback
   https://dagster.127.0.0.1.nip.io/oauth2/callback
   https://datalake.127.0.0.1.nip.io/oauth2/callback
   https://attu.127.0.0.1.nip.io/oauth2/callback
   ```

3. Configure token settings:

   - Enable **ID tokens** (used for hybrid flows)

4. Click **"Configure"**

::: warning Platform Type Distinction
The platform type configuration (SPA vs Web) is critical for OAuth2 flow selection:

- **SPA platform**: Language-specific callbacks (`/de/`, `/en/`, `/fr/`, `/it/`) use PKCE flow without client secret
- **Web platform**: Service callbacks (`openwebui`, `dagster`, `datalake`, `attu`) use authorization code flow with
  client secret

Misconfigured platform types will cause authentication error
`AADSTS9002326: Cross-origin token redemption is permitted only for the 'Single-Page Application' client-type`. Ensure
redirect URIs are registered under the correct platform type.
:::

**Required Authentication Information**

After completing Azure setup, you should have:

- `[CLIENT_ID]` - Application (client) ID
- `[CLIENT_SECRET]` - Client secret value
- `[TENANT_ID]` - Directory (tenant) ID

You'll need these values during platform deployment configuration.

______________________________________________________________________

## Production Deployment Prerequisites

::: danger Only for Production Deployments
**Skip this entire section if you're testing locally.** These steps are only required when deploying to a server with a
real domain name.
:::

### DNS Configuration

Configure DNS records for your domain. The platform requires **seven subdomains** pointing to your server's public IP:

- `aihub.example.com` - main web interface
- `openwebui.aihub.example.com` - chat UI
- `dagster.aihub.example.com` - pipeline orchestration
- `datalake.aihub.example.com` - data lake console
- `litellm.aihub.example.com` - litellm proxy
- `attu.aihub.example.com` - Milvus vector database UI
- `traefik.aihub.example.com` - reverse proxy dashboard

Replace `aihub.example.com` with your actual domain. Create A records or CNAMEs for all seven subdomains pointing to
your server's IP address.

::: warning DNS Requirements for SSL
- DNS records must be globally accessible for Let's Encrypt SSL certificate provisioning
- The VM must be able to resolve its own domain names (internal DNS resolution)
- Configure nameservers correctly to avoid OAuth authentication timeouts

See [network requirements](../../3_deployment_guide/7_network_requirements/) for detailed DNS configuration and
troubleshooting.
:::

______________________________________________________________________

## Local Deployment Prerequisites

::: danger Only for Local Deployment
**Skip this entire section if you're deploying to production.** These steps are only required when deploying the
platform on your local machine.
:::

### Install mkcert

For local deployment with HTTPS support, you need to install **mkcert** to generate self-signed SSL certificates that
are trusted by your browser.

::: warning
Only use self-signed SSL certificates for local development. Never use them in production or public environments.
:::

**Linux (Ubuntu/Debian):**

```bash
sudo apt install libnss3-tools
wget -O mkcert https://dl.filippo.io/mkcert/latest?for=linux/amd64
chmod +x mkcert
sudo mv mkcert /usr/local/bin/
```

**Windows:**

```powershell
# Using Chocolatey
choco install mkcert

# OR using Scoop
scoop bucket add extras
scoop install mkcert
```

**macOS:**

```bash
brew install mkcert
```

**Verify Installation:**

```bash
mkcert -version
```

::: tip What is mkcert?
**mkcert** is a tool that generates locally-trusted SSL certificates without complex configuration. It automatically
installs a local Certificate Authority (CA) in your system trust store, so certificates it generates are trusted by your
browser.
:::

______________________________________________________________________

## Next steps

Proceed to [one-command deployment](../2_one_command_deployment/) to deploy the platform using the recorded
configuration values.
