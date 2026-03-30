# Tenant Identification via URL Path Parameter

## Context

Previously, tenant context was provided via an `x-tenant-id` HTTP header on API requests, with a fallback to a
system-wide default tenant when the header was omitted. This approach had several limitations: OpenWebUI (the chat
frontend) cannot set custom HTTP headers on API requests, the tenant context was invisible in URLs making debugging and
logging harder, and the implicit fallback to a default tenant masked misconfigured clients.

## Decision Drivers

- **URL-level tenant scoping**: Embedding the tenant in the URL makes tenant context explicit and visible in logs,
  browser history, and monitoring tools. Every request's tenant affiliation is immediately apparent.
- **OpenWebUI compatibility**: OpenWebUI routes API calls to the backend but cannot inject custom HTTP headers. A path
  parameter works naturally with OpenWebUI's URL-based routing.
- **Explicit tenant context in every request**: Removing the implicit default tenant fallback forces clients to
  explicitly declare which tenant they are operating within, eliminating silent misrouting.
- **Per-user active tenant**: Users working across multiple tenants need the system to remember which tenant they last
  selected, rather than always falling back to a global system default.

## Decision

All API routes are now mounted at `/api/v1/{tenant_id}/...` where `{tenant_id}` is a required path parameter. The
`x-tenant-id` header is no longer supported.

The `{tenant_id}` parameter accepts two formats:

- **Concrete MongoDB ObjectId**: Directly specifies the tenant (e.g., `/api/v1/507f1f77bcf86cd799439011/agents/...`)
- **`"active"` slug**: Resolves to the authenticated user's persisted active tenant (e.g., `/api/v1/active/agents/...`)

Tenant-scoped routes are mounted via a Starlette `Mount` at `/api/v1/{tenant_id}`, which captures the path parameter
before FastAPI route resolution. Health endpoints remain outside tenant scope at `/api/v1/health/`.

The active tenant is persisted per user and is never automatically updated during request resolution. It can only be
changed via a dedicated API endpoint.

## Consequences

- **Frontend uses `/api/v1/active/...`**: The frontend (OpenWebUI, Admin UI) uses the `"active"` slug for all API calls,
  relying on the backend to resolve the user's current tenant.
- **Health endpoints separated**: Health checks at `/api/v1/health/` are not tenant-scoped and do not require
  authentication.
- **No backward compatibility with header**: The `x-tenant-id` header is fully removed. All clients must migrate to the
  path parameter approach.
- **Supersedes previous ADR**: This decision supersedes the tenant resolution mechanism described in
  [Local Multi-Tenant Role Management](2025_12_25_local_role_management.md), which used the `x-tenant-id` header with a
  fallback to the default tenant.
