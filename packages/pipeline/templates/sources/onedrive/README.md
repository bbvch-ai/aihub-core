# OneDrive Pipeline Template

Simple pipeline to sync OneDrive for Business documents to Swiss AI Hub data lake.

## Setup

**1. Register Azure AD App** (same as SharePoint)

- Go to https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
- Create "New registration"
- Note **Application (client) ID**
- Note **Directory (tenant) ID**
- Create client secret in "Certificates & secrets"
- Note **Client secret value** (shown once!)

**2. Grant Permissions**

- Go to "API permissions"
- Add "Microsoft Graph" → "Application permissions" → `Files.Read.All`
- Click "Grant admin consent"

**3. Configure Environment**

Copy variables from `.env.template` to your `.env` and fill in:

```bash
RCLONE_ONEDRIVE_CLIENT_ID=<Application (client) ID>
RCLONE_ONEDRIVE_CLIENT_SECRET=<Client secret value>
RCLONE_ONEDRIVE_TENANT=<Directory (tenant) ID>
```

**4. Run Pipeline**

```bash
uv run dagster dev -f pipeline.py
```
