---
title: "Prerequisites Check"
index: 1
---

# Prerequisites: Preparing for Platform Deployment

Before deploying the Swiss AI Hub platform, ensure your infrastructure meets the minimum requirements and that you have the necessary authentication setup. This checklist ensures a smooth deployment experience.

## Hardware Requirements

The Swiss AI Hub platform requires substantial resources to run all components effectively:

**Minimum Specifications:**
- **CPU**: 8 cores
- **RAM**: 32 GB
- **Storage**: 200 GB free space
- **Network**: Stable internet connection for Docker image downloads

**Recommended Specifications:**
- **CPU**: 12+ cores for optimal performance
- **RAM**: 48+ GB for comfortable operation
- **Storage**: 300+ GB with SSD recommended for database performance
- **Network**: High-bandwidth connection for faster initial setup

::: warning Resource Impact
The platform runs multiple services simultaneously: databases (MongoDB, Redis), vector databases (Milvus), LLM proxy servers, web interfaces, and processing engines. Insufficient resources will cause service failures or poor performance.
:::

## Operating System and Software

**Operating System:**
- **Linux** (Ubuntu 20.04+ recommended and tested)
- **Docker-compatible** Linux distribution

**Required Software:**
- **Docker** (latest stable version)
- **Docker Compose** (v2.0+)
- **sudo/root access** for installation and configuration

**Network Configuration:**
- **Open ports**: 80 (HTTP), 443 (HTTPS), and any custom ports for your configuration
- **Internet access** for downloading Docker images and updates
- **Domain/DNS setup** if deploying for external access

::: tip Installation Verification
Test your Docker setup:
```bash
docker --version
docker compose --version
docker run hello-world
```
All commands should complete successfully.
:::

## Authentication Provider Setup

The Swiss AI Hub platform requires an OAuth2/OpenID Connect identity provider. This guide covers Azure Entra ID setup, but other providers like Google, Okta, or Auth0 can be used with similar configuration patterns.

### Azure Entra ID Configuration

Follow these steps to set up Azure authentication:

**Step 1: Create App Registration**

1. Navigate to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Configure the application:
   - **Name**: "Swiss AI Hub" (or your preferred name)
   - **Supported account types**: "Accounts in this organizational directory only" (or as needed)
   - **Redirect URI**: Select "Web" and enter:
     ```
     https://your-domain.com/oauth/oidc/callback
     ```
     (Replace `your-domain.com` with your actual domain or use `127.0.0.1.nip.io` for local testing)
4. Click "Register"

**Step 2: Configure API Permissions**

1. Go to "API permissions" → "Add a permission"
2. Select "Microsoft Graph" → "Delegated permissions"
3. Add these permissions:
   - `openid`
   - `profile` 
   - `email`
   - `offline_access`
   - `User.Read`
4. Select "Microsoft Graph" → "Application permissions"  
5. Add these permissions:
   - `User.ReadBasic.All`
   - `Directory.Read.All`
   - `ProfilePhoto.Read.All`
6. Click "Grant admin consent for [Your Organization]"

**Step 3: Create Client Secret**

1. Go to "Certificates & secrets" → "New client secret"
2. Add description and set expiration period
3. Click "Add" and **immediately copy the secret value** - you won't see it again
4. Save this as your `[CLIENT_SECRET]`

**Step 4: Set Up App Roles**

1. Go to "App roles" → "Create app role"
2. Create role for administrators:
   - **Display name**: `AIHubAdmin`
   - **Allowed member types**: "Users/Groups"
   - **Value**: `AIHubAdmin`
3. Create role for regular users:
   - **Display name**: `AIHubUser` 
   - **Allowed member types**: "Users/Groups"
   - **Value**: `AIHubUser`

**Step 5: Configure SPA Authentication**

1. Go to "Authentication" → "Add a platform" → "Single-page application"
2. Add these redirect URIs (replace domain as needed):
   ```
   https://your-domain.com/de/auth/callback
   https://your-domain.com/en/auth/callback
   https://your-domain.com/it/auth/callback
   https://your-domain.com/fr/auth/callback
   ```
3. Click "Save"

**Step 6: Collect Configuration Values**

From your App Registration "Overview" page, copy these values:
- **Application (client) ID** → Save as `[CLIENT_ID]`
- **Directory (tenant) ID** → Save as `[TENANT_ID]`

### Required Authentication Information

After completing Azure setup, you should have:
- `[CLIENT_ID]` - Application (client) ID
- `[CLIENT_SECRET]` - Client secret value  
- `[TENANT_ID]` - Directory (tenant) ID

You'll need these values during platform deployment configuration.
