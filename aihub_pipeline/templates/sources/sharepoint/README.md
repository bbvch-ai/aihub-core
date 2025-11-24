# SharePoint Pipeline Template

Simple pipeline to sync SharePoint documents to AI-Hub data lake.

## Setup

**1. Register Azure AD App**

- Go to https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
- Create "New registration"
- Note **Application (client) ID**
- Note **Directory (tenant) ID**
- Create client secret in "Certificates & secrets"
- Note **Client secret value** (shown once!)

**2. Grant Permissions**

- Go to "API permissions"
- Add "Microsoft Graph" → "Application permissions" → `Sites.Read.All`
- Click "Grant admin consent"

**3. Configure Environment**

Copy variables from `.env.template` to your `.env` and fill in:

```bash
RCLONE_SHAREPOINT_CLIENT_ID=<Application (client) ID>
RCLONE_SHAREPOINT_CLIENT_SECRET=<Client secret value>
RCLONE_SHAREPOINT_TENANT=<Directory (tenant) ID>
RCLONE_SHAREPOINT_SITE_URL=https://your-tenant.sharepoint.com/sites/your-site-name
```

**Site URL**: Just copy from browser address bar!

**4. Run Pipeline**

```bash
poetry run dagster dev -f pipeline.py
```

Open http://localhost:3000

