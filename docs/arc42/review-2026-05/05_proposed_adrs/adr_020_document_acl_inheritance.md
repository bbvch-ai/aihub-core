# Document ACL Inheritance in the Vector DB

**Status**: Proposed **Severity**: P0+ (cross-user data leak via RAG) **Drives**: §19.3 Concern C in
[Details §19.3 Document ACL Inheritance](../02_architecture_review_details.md#193-concern-c-document-acl-inheritance-critical-data-leak)

## Context

Review 2026-05 found a critical gap: the ACL (Access Control List) of source documents (Jira, SharePoint, Confluence) is
**not** propagated into the Milvus vector store at ingest time. Consequence: any user with access to the RAG agent can
query and read the content of every document, including documents they have no read permission for at the source.

Scenario described by the user, confirmed:

```
1. SharePoint folder "HR-Confidential" has ACL = {hr_admin_group only}
2. Ingest pipeline uses a service account with Sites.Read.All
   → the service account can read this folder (super-admin level)
3. Pipeline parses documents, generates embeddings, inserts into Milvus
   → the Milvus collection "sharepoint" has NO ACL metadata
4. User Alice (not in hr_admin_group) asks via RAG: "Total Q1 2026 salary"
5. ChatAgent → RetrievalOrchestrator → retrieve_nodes(namespace="sharepoint")
   → returns vectors from the HR-Confidential folder
6. Alice reads confidential data she has no access to in SharePoint
```

Evidence per layer:

| Layer                 | File                                                                          | Finding                                                                            |
| --------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Jira fetch            | `pipelines/jira_to_data_lake/resources/JiraResource.py:38`                    | Service account auth; JQL only filters `project={key}`, no security level     |
| Jira model            | `lib/common/types/JiraIssue.py:1-72`                                          | No fields: security_level, project_role, creator, assignee                    |
| Jira metadata extract | `pipelines/jira_to_data_lake/ops/extract_metadata_from_jira_issue.py:1-35`    | No acl, owner                                                                 |
| Confluence fetch      | `pipelines/confluence_to_data_lake/resources/ConfluenceResource.py:21`        | Service account; does not filter page restrictions                            |
| Confluence model      | `pipelines/confluence_to_data_lake/types/ConfluencePage.py:1-22`              | No space_permissions, page_restrictions                                       |
| SharePoint fetch      | `packages/core/.../sharepoint/share_point_settings.py:1-23`                   | Azure AD app-only Sites.Read.All; does not parse folder ACL                   |
| Milvus schema         | `packages/core/.../persistence/rag/vectors/node_metadata.py:1-116`            | NO ACL, permissions, owner, viewable_by fields                                |
| RAG retrieve          | `packages/core/.../generative_ai/retrieval/retrieve_nodes.py:40-41`           | Filters only NAMESPACE and TYPE, not user permissions                         |
| CTC orchestrator      | `agents/retrieval_orchestrator_agent/.../RetrievalOrchestratorAgent.py:59-72` | Does not pass user context into retrieval                                     |
| CTC chat agent        | `agents/chat_agent/chat_agent/ChatAgent.py:9-12`                              | Does not pass user identity into retrieval                                    |

Compliance impact:

- GDPR Art. 32 (security of processing): violation.
- Swiss revDSG Art. 8 (proportionality): violation.
- ISO 27001 A.9.4 (access control): non-conformance.
- Banking FINMA, Healthcare: block.
- Auditor question "show me access control on knowledge base": cannot demonstrate.

Root cause: the service account shared key (see ADR-NEW-021) ingests everything regardless of source ACL. Fixing ACL
inheritance in the vector store is the first line of defense; fixing service-account auth is the second line.

## Decision Drivers

- **Privacy**: A user only accesses data they have permission for at the source.
- **Compliance**: GDPR Art. 32, ISO 27001 A.9.4, banking, healthcare.
- **Performance**: Filter at the vector-DB level, don't re-fetch the source per query.
- **Source-agnostic**: The pattern works for Jira, SharePoint, Confluence, and future sources.
- **Auditability**: Log every access-deny for forensics.
- **Stale ACL window**: Acceptable trade-off (daily refresh is OK for most use cases).
- **Backward compat**: Existing Milvus collections need a migration path.

## Decision

Implement an ACL metadata field in Milvus, capture the source ACL at ingest, and filter at retrieval time.

### Phase 1: Milvus metadata schema extension

```python
# packages/core/swiss_ai_hub/core/persistence/rag/vectors/node_metadata.py

# Existing constants...
NAMESPACE = "namespace"
SOURCE_ORIGIN = "source_origin"
HASH = "hash"
# ... etc

# NEW ACL-related constants
ACL = "acl"  # list[str] of principals (user IDs, group IDs, role IDs)
ACL_TYPE = "acl_type"  # "explicit" | "inherited" | "world_readable"
SOURCE_ITEM_ID = "source_item_id"  # Original ID in source system (audit)
INGESTED_BY = "ingested_by"  # Service account ID used for ingest
ACL_LAST_SYNC = "acl_last_sync"  # Timestamp the ACL was captured (for staleness check)
```

A Milvus VARCHAR field for ACL stores comma-separated principals or a JSON array (depends on Milvus version capability).
Milvus 2.4+ supports array fields with an INVERTED index.

### Phase 2: ACL capture per source connector

#### Jira (Atlassian REST API)

```python
async def fetch_jira_acl(issue_key: str, jira_client) -> list[str]:
    # GET /rest/api/3/issue/{key}?fields=security,assignee,creator,reporter
    issue = await jira_client.get_issue(issue_key, expand="renderedFields,changelog")

    acl: list[str] = []

    # Security level (per issue)
    if issue.fields.security:
        acl.append(f"jira_security_level:{issue.fields.security.name}")

    # Project roles
    project_key = issue.fields.project.key
    roles = await jira_client.get_project_roles(project_key)
    # E.g., {"Developers": [user_id1, user_id2], "Administrators": [user_id3]}
    for role_name, members in roles.items():
        for user_id in members:
            acl.append(f"jira_user:{user_id}")
        acl.append(f"jira_project_role:{project_key}:{role_name}")

    return acl
```

#### Confluence

```python
async def fetch_confluence_acl(page_id: str, confluence_client) -> list[str]:
    # GET /wiki/rest/api/content/{id}/restriction?expand=restrictions.read
    restrictions = await confluence_client.get_restrictions(page_id)

    acl: list[str] = []
    if restrictions.is_unrestricted:
        # Inherit from space
        page = await confluence_client.get_page(page_id)
        acl.append(f"confluence_space:{page.space_key}:read")
    else:
        for user in restrictions.read_users:
            acl.append(f"user:{user.account_id}")
        for group in restrictions.read_groups:
            acl.append(f"group:{group.name}")

    return acl
```

#### SharePoint

```python
async def fetch_sharepoint_acl(site_url: str, item_id: str, sp_client) -> list[str]:
    # GET /_api/web/lists/getbytitle('{list}')/items({id})/RoleAssignments
    #   ?$expand=Member,RoleDefinitionBindings
    role_assignments = await sp_client.get_role_assignments(site_url, item_id)

    acl: list[str] = []
    for assignment in role_assignments:
        principal = assignment.member
        if principal.type == "User":
            acl.append(f"sp_user:{principal.login_name}")
        elif principal.type == "SharePointGroup":
            # Expand group members
            members = await sp_client.get_group_members(principal.id)
            acl.extend([f"sp_user:{m.login_name}" for m in members])
            acl.append(f"sp_group:{principal.name}")
        elif principal.type == "SecurityGroup":
            # Azure AD group
            acl.append(f"ad_group:{principal.object_id}")
        elif principal.type == "Everyone":
            return ["world_readable"]  # Special marker

    return acl
```

### Phase 3: Pipeline integration

```python
# pipelines/jira_to_data_lake/ops/extract_metadata_from_jira_issue.py
async def extract_metadata(issue: JiraIssue, jira_client) -> dict:
    acl = await fetch_jira_acl(issue.key, jira_client)
    return {
        SOURCE_ORIGIN: "jira",
        HASH: hash(issue),
        SOURCE_ITEM_ID: issue.key,
        ACL: acl,                                       # NEW
        ACL_TYPE: "explicit" if acl else "world_readable",  # NEW
        ACL_LAST_SYNC: datetime.utcnow().isoformat(),   # NEW
        INGESTED_BY: settings.SERVICE_ACCOUNT_ID,       # NEW
        # ... existing fields
    }
```

### Phase 4: RAG retrieval filter by user ACL

```python
# packages/core/swiss_ai_hub/core/generative_ai/retrieval/retrieve_nodes.py
async def retrieve_nodes(
    query: str,
    namespace: str,
    user: UserIdentity,                  # NEW required
    tenant_id: str,                       # NEW required
    additional_filters: list[MetadataFilterPair] | None = None,
    top_k: int = 10,
) -> list[Node]:
    # Compute the user's principals from Keycloak groups + roles + identity links
    user_principals = await principal_resolver.resolve(user.user_id, tenant_id)
    # Returns: [
    #   "user:alice@bbv.ch",
    #   "jira_user:5a8b2c...",
    #   "sp_user:alice@bbv.ch",
    #   "group:engineering",
    #   "ad_group:xxx-yyy",
    #   "world_readable",  # Always include
    # ]

    # Milvus filter expression
    # Note: exact syntax depends on Milvus version
    acl_filter = MetadataFilter(
        key=ACL,
        value=user_principals,
        operator="array_contains_any",  # Milvus 2.4+
    )

    filters = [
        MetadataFilter(key=NAMESPACE, value=namespace),
        acl_filter,
    ]
    if additional_filters:
        filters.extend(additional_filters)

    nodes = await milvus.search(
        query_embedding=embed(query),
        filter=combine_filters(filters),
        top_k=top_k,
    )

    # Audit log if any results filtered out
    if nodes_filtered_count > 0:
        await AuditLogEntity.write_audit_entry(
            tenant_id=tenant_id,
            user_id=user.user_id,
            action_type="access_denied",
            resource_type="rag_documents",
            metadata={
                "query_hash": hash(query),
                "namespace": namespace,
                "filtered_count": nodes_filtered_count,
            },
        )

    return nodes
```

### Phase 5: Update agents to pass user context

```python
# agents/chat_agent/chat_agent/ChatAgent.py
event = RetrievalAgentInTheLoopRequestEvent(
    query=question,
    user=run_context.user,        # NEW required
    tenant_id=run_context.tenant, # NEW required
)
```

### Phase 6: ACL refresh strategy (Daily Dagster sensor)

```python
# packages/pipeline/.../sensors/acl_sync_sensor.py (NEW)
@asset(
    automation_condition=AutomationCondition.cron("0 2 * * *"),  # Daily 2 AM
)
async def daily_acl_sync(context, source_type: str):
    """
    Re-sync ACL from the source system for every ingested document.
    Detect: source-side permission change → update Milvus metadata.
    """
    for document in milvus.scan(namespace=source_type):
        fresh_acl = await fetch_acl(document.source_item_id, source_type)
        if fresh_acl != document.metadata[ACL]:
            await milvus.update_metadata(
                document.id,
                {ACL: fresh_acl, ACL_LAST_SYNC: datetime.utcnow().isoformat()},
            )
            # Audit log
            await AuditLogEntity.write_audit_entry(
                action_type="acl_sync",
                resource_type=source_type,
                resource_id=document.source_item_id,
                metadata={"old_acl": document.metadata[ACL], "new_acl": fresh_acl},
            )
```

### Principal Resolver

```python
# packages/core/swiss_ai_hub/core/auth/principal_resolver.py (NEW)
class PrincipalResolver:
    """
    Map UserIdentity → list of principals matching source-system formats.
    Handles identity linking (one user has multiple identities across systems).
    """
    async def resolve(self, user_id: str, tenant_id: str) -> list[str]:
        principals = ["world_readable"]  # Always include public docs

        # Internal user ID
        principals.append(f"user:{user_id}")

        # Keycloak groups → AD groups + JIRA users + SP users
        keycloak_user = await keycloak_admin.get_user(user_id)
        groups = await keycloak_admin.get_user_groups(user_id)
        for group in groups:
            principals.append(f"group:{group.name}")

        # Identity links (federated identities)
        identities = keycloak_user.federated_identities
        for identity in identities:
            if identity.identity_provider == "azure_ad":
                principals.append(f"ad_user:{identity.user_id}")
                principals.append(f"sp_user:{identity.user_email}")
            elif identity.identity_provider == "jira":
                principals.append(f"jira_user:{identity.user_id}")
            elif identity.identity_provider == "confluence":
                principals.append(f"confluence_user:{identity.user_id}")

        # Roles
        for role in keycloak_user.realm_roles:
            principals.append(f"role:{role}")

        return principals
```

## Consequences

### Positive

- A user can only query documents they have permission for at the source.
- GDPR Art. 32, ISO 27001 A.9.4 compliance.
- Cross-user data-leak risk eliminated for RAG.
- Audit log on every access-deny.
- Source-agnostic pattern, extensible to new sources.
- Enterprise customers (banking, healthcare) feasible.

### Negative

- Performance: Milvus filter increases query latency (estimated +5-50ms, depends on selectivity).
- Storage overhead: ACL metadata adds ~100-500 bytes per document (~5% increase total).
- Source ACL fetch overhead: N API calls per ingest (Confluence N+1 problem mitigation needed).
- Stale ACL window: between daily syncs, a source-side permission revoke is not reflected immediately.
- Migration: existing Milvus collections need an ACL backfill (one-time job).
- Identity-linking complexity: Keycloak federated identities must be configured correctly.
- SharePoint complexity: nested group membership, inherited permissions from the parent folder.

### Mitigation for concerns

- **Performance**: Pre-compute user principals at login, cache 1 hour in Redis. Index the ACL field in Milvus with an
  INVERTED type.
- **Confluence N+1**: Bulk fetch restrictions API (`/wiki/rest/api/content/{ids}/restriction`).
- **Stale ACL**: Sync daily by default; a customer can configure hourly for high-security namespaces.
- **Migration**: A backfill job marks old documents `world_readable` initially; admins re-ingest critical namespaces.
- **Defense in depth**: Pair with ADR-NEW-021 (per-user OAuth) to minimize service-account scope.

### Implementation notes

- Sprint 1: Phase 1 (schema) + Phase 4 (retrieval filter with `world_readable` default).
- Sprint 2: Phase 2 + 3 for the Jira connector.
- Sprint 3: Phase 2 + 3 for the Confluence connector.
- Sprint 4: Phase 2 + 3 for the SharePoint connector.
- Sprint 5: Phase 5 update agents.
- Sprint 6: Phase 6 daily sync + Principal Resolver.
- Sprint 7: Backfill existing data.

Migration strategy: New collections enable the ACL filter immediately. Old collections are marked `world_readable`
(existing behavior) for a non-breaking change. Admins trigger re-ingest of critical namespaces with ACL capture.

## References

- [Details §19.3 Document ACL Inheritance](../02_architecture_review_details.md#193-concern-c-document-acl-inheritance-critical-data-leak):
  Full evidence and scenario.
- ADR-NEW-021 (Source-System Authentication Strategy): Service account vs per-user OAuth - root cause fix.
- ADR-NEW-011 [Audit Log Entity](adr_011_audit_log_entity.md): Logging access deny events.
- Milvus 2.4 array field documentation: https://milvus.io/docs/array_data_type.md
- SharePoint REST API role assignments:
  https://learn.microsoft.com/en-us/sharepoint/dev/sp-add-ins/sharepoint-add-ins-rest-api-permissions
