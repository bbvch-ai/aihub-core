# Bulk User Import from CSV & Bulk Role Assignment

**Blocked by:**
- #05 (User-Tenant-Role Assignment API)
- #07 (Frontend Admin UI)

## Description

Administrators often need to onboard many users at once, especially when migrating from another system or integrating with an Azure AD export. Currently, users must be added one at a time, and roles must be assigned individually.

We need bulk operations for:
- Importing users from CSV files (e.g., Azure AD user exports)
- Bulk assigning roles to multiple selected users
- Bulk removing users from the current tenant

## CSV Import Requirements

The CSV should contain user email, name, and optionally initial roles. The import process should:
- Create users if they don't exist (with placeholder identity until first login)
- Add users to the current tenant
- Assign specified roles
- Handle errors gracefully (report which users succeeded/failed)
- Return a summary of created, updated, and failed imports

## Bulk Role Assignment

Users should be able to:
- Select multiple users from the user list (checkboxes)
- Choose a bulk action (assign roles, remove roles, replace roles)
- Select which roles to apply
- Execute the action on all selected users

## Current Code Locations

- User controller: `aihub_api/aihub_api/routes/user/UserController.py`
- User service: `aihub_api/aihub_api/routes/user/UserService.py`
- User management page: `aihub_web/aihub_web/pages/service/users.vue`

## CSV Format Reference

Look at standard Azure AD user export formats - typically includes email, display name, and other fields. Define a simple, documented format that administrators can easily prepare.

## Definition of Done

This task is accepted when:

- [ ] Backend API endpoint accepts CSV file and imports users
- [ ] CSV parsing handles errors and validates format
- [ ] Import process adds users to current tenant with specified roles
- [ ] Import returns detailed results (success count, error messages)
- [ ] Backend API endpoint for bulk role assignment (add/remove/replace modes)
- [ ] Frontend UI for CSV upload with preview before import
- [ ] Frontend shows import progress and results summary
- [ ] User table supports multi-select with checkboxes
- [ ] Bulk actions dropdown for role operations
- [ ] Bulk operations invalidate query cache and refetch data
- [ ] Error handling for partial failures (some users fail, others succeed)

## Hints

- Consider whether to use file upload or paste CSV content - file upload is more user-friendly
- Think about the data format for the backend (base64 encoded CSV, multipart form, etc.)
- Look at PrimeVue DataTable selection examples for multi-select pattern
- The bulk operations should work within the current tenant context (from `X-Tenant-Id`)
- Consider adding a dry-run mode for CSV import (preview without committing)
