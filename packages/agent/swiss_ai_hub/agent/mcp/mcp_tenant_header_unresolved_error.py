class McpTenantHeaderUnresolvedError(RuntimeError):
    """The profile forwards a tenant header but this run has no acting tenant with an external tenant id.

    Raised instead of calling the MCP server without the header: a server that scopes its data by that header
    (e.g. the LCDM MCP via ``X-LCDM-Tenant``) must never receive an unscoped request it might answer with a
    default or broader tenant's data. Runs without a user (scheduled, process, bot) and tenants without an
    external id therefore fail loudly here.
    """
