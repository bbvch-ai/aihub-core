---
title: Multi-tenancy
index: 15
---

# Multi-tenancy

Multi-tenancy lets you run separate organizations on a single platform instance. Each tenant operates independently with its own users, roles, and access boundaries.

A tenant represents an organization, business unit, or customer. Users belong to one or more tenants and have different roles in each. Access rules defined at the tenant level create hard boundaries around what any user in that tenant can access.

## Why use tenants

Single-tenant mode works well when everyone in your organization should potentially access the same resources. Multi-tenancy becomes useful when you need:

**Organizational isolation**: Different business units require separate agent configurations and knowledge bases. A tenant for the finance team can access financial agents and documents while the HR tenant accesses only HR resources.

**Customer separation**: Service providers host multiple customers on one platform instance. Each customer tenant operates independently without visibility into other customers' data or agents.

**Development isolation**: Development, staging, and production environments run side-by-side with the same infrastructure. Each environment tenant has its own test data and configurations.

**Compliance requirements**: Regulations require data segregation between entities. Tenant boundaries enforce these separations at the platform level.

## How tenants work

When a user logs in, they select which tenant they're working in. The frontend includes a tenant identifier in every API request. The backend resolves the user's roles within that specific tenant and enforces the tenant's access boundaries.

Access control operates in two layers:

**User permissions** come from roles assigned within the tenant. A user with the "Agent Admin" role can manage agents, assuming the tenant allows agent access.

**Tenant boundaries** define what resources exist for that tenant at all. If a tenant's access rules permit only `agent.research.*`, no user in that tenant can access other agents regardless of their role.

Users can switch tenants without logging out. Each tenant appears as a separate workspace with its own agents, knowledge bases, and configurations.

## Default tenant

Every platform installation creates a default tenant automatically. New users join this tenant with standard roles unless configured otherwise. The default tenant has unrestricted access rules, replicating single-tenant behavior.

You can continue using only the default tenant. Multi-tenancy is opt-in through creating additional tenants.
