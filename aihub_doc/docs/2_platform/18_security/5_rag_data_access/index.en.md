---
title: RAG Data Access Management
index: 5
---

# RAG Data Access Management

The Swiss AI Hub implements comprehensive data access controls for Retrieval-Augmented Generation (RAG) systems to ensure that sensitive information in knowledge bases is accessed only by authorized users. This document describes how the platform enforces granular access control over knowledge bases, documents, and retrieved information while maintaining the performance and functionality of RAG applications.

## Overview

RAG systems retrieve relevant information from knowledge bases to augment AI-generated responses. Without proper access controls, RAG systems could inadvertently expose sensitive information to unauthorized users. The Swiss AI Hub addresses this challenge through:

- **Namespace-based access control**: Hierarchical permissions for knowledge bases and document collections
- **Query-time filtering**: Real-time access checks during information retrieval
- **Document-level permissions**: Fine-grained control over individual documents
- **Metadata-based filtering**: Access control based on document properties
- **Audit logging**: Complete tracking of data access for compliance

## Knowledge Base Access Control Architecture

### Hierarchical Knowledge Organization

Knowledge bases are organized in a hierarchical structure that enables granular access control:

```
Company Knowledge
├── Public
│   ├── Press Releases
│   └── Product Documentation
├── Internal
│   ├── Engineering
│   │   ├── Architecture
│   │   └── Code Documentation
│   ├── HR
│   │   ├── Policies
│   │   └── Benefits
│   └── Finance
│       ├── Budgets
│       └── Reports
└── Confidential
    ├── Legal
    └── Executive
```

Each level in the hierarchy can have independent access controls, with permissions inheriting down the tree unless explicitly overridden.

### Permission Model for Knowledge Bases

Access to knowledge bases follows the platform's hierarchical RBAC system:

**Knowledge Base Permissions**:
- `aihub.user.knowledge.public` - Access to all public knowledge
- `aihub.user.knowledge.internal.hr` - Access to HR documents
- `aihub.user.knowledge.internal.hr.policies` - Access only to HR policies
- `aihub.admin.knowledge.internal.hr` - Administrative access to manage HR knowledge base

**Permission Levels**:
- **Read**: Search and retrieve documents, view content
- **Write**: Upload documents, update metadata
- **Admin**: Manage access controls, delete documents, configure knowledge base

## Query-Time Access Filtering

### Retrieval Pipeline with Access Control

When a user queries a RAG agent, the retrieval pipeline enforces access controls:

```python
async def retrieve_with_access_control(
    query: str,
    user: UserIdentity,
    access_checker: AccessChecker,
    num_results: int = 10
) -> list[Document]:
    """Retrieve documents with access control enforcement."""
    
    # Step 1: Identify accessible knowledge bases
    accessible_namespaces = await get_accessible_namespaces(
        user, access_checker
    )
    
    # Step 2: Retrieve from vector store with namespace filter
    candidate_documents = await vector_store.query(
        query_embedding=embed(query),
        namespaces=accessible_namespaces,
        num_results=num_results * 3  # Over-retrieve for filtering
    )
    
    # Step 3: Apply document-level filters
    filtered_documents = []
    for doc in candidate_documents:
        if await check_document_access(user, doc, access_checker):
            filtered_documents.append(doc)
            if len(filtered_documents) >= num_results:
                break
    
    # Step 4: Log access for audit
    await log_retrieval_access(user, filtered_documents)
    
    return filtered_documents
```

### Namespace-Based Filtering

**Vector Store Partitioning**: Documents are stored in namespace-partitioned collections:
- Each namespace corresponds to a knowledge base or sub-category
- Queries only search namespaces the user has permission to access
- Reduces search space and improves performance

**Permission Resolution**:
```python
async def get_accessible_namespaces(
    user: UserIdentity,
    access_checker: AccessChecker
) -> list[str]:
    """Get list of namespaces the user can access."""
    all_namespaces = await knowledge_service.list_namespaces()
    
    accessible = []
    for namespace in all_namespaces:
        permission = f"aihub.user.knowledge.{namespace}"
        if await access_checker.check_access(user, permission):
            accessible.append(namespace)
    
    return accessible
```

**Performance Optimization**: 
- Cache accessible namespaces per user session
- Pre-compute namespace lists for common roles
- Use efficient permission checking with wildcard support

### Document-Level Access Control

**Document Metadata**: Each document includes access control metadata:
```json
{
  "document_id": "doc_12345",
  "content": "...",
  "metadata": {
    "namespace": "internal.hr.policies",
    "classification": "internal",
    "owner": "hr_team",
    "tags": ["policy", "vacation"],
    "access_groups": ["hr", "management"],
    "created_at": "2025-01-01T00:00:00Z",
    "created_by": "hr_admin@example.com"
  }
}
```

**Access Control Checks**:
```python
async def check_document_access(
    user: UserIdentity,
    document: Document,
    access_checker: AccessChecker
) -> bool:
    """Check if user has access to a specific document."""
    
    # Check namespace permission
    namespace_permission = f"aihub.user.knowledge.{document.namespace}"
    if not await access_checker.check_access(user, namespace_permission):
        return False
    
    # Check classification level
    if document.classification == "confidential":
        confidential_permission = f"aihub.user.knowledge.confidential"
        if not await access_checker.check_access(user, confidential_permission):
            return False
    
    # Check group membership
    if document.access_groups:
        user_groups = await get_user_groups(user)
        if not any(group in user_groups for group in document.access_groups):
            return False
    
    # Check custom access rules
    if document.custom_access_rules:
        if not await evaluate_custom_rules(user, document.custom_access_rules):
            return False
    
    return True
```

## Advanced Access Control Patterns

### Attribute-Based Access Control (ABAC)

Beyond simple namespace permissions, the platform supports attribute-based access control:

**User Attributes**:
- Department: HR, Engineering, Sales, etc.
- Job Level: Junior, Senior, Executive
- Location: Switzerland, EU, Global
- Clearance Level: Public, Internal, Confidential, Secret

**Document Attributes**:
- Classification: Public, Internal, Confidential, Secret
- Department: HR, Engineering, Finance
- Retention Period: Active, Archived
- Sensitivity Tags: PII, Financial, Legal

**Access Rules**:
```python
def evaluate_abac_rule(
    user: UserIdentity,
    document: Document
) -> bool:
    """Evaluate attribute-based access control rules."""
    
    # Rule: Only same-department users can access confidential docs
    if document.classification == "confidential":
        if user.department != document.department:
            return False
    
    # Rule: Executive level required for financial documents
    if "financial" in document.tags:
        if user.job_level not in ["Executive", "Director"]:
            return False
    
    # Rule: Regional restrictions
    if document.region and document.region != user.region:
        if "global_access" not in user.permissions:
            return False
    
    return True
```

### Time-Based Access Control

**Temporary Access Grants**: Grant time-limited access to documents:
```python
class TemporaryAccessGrant:
    user_id: str
    resource: str
    granted_at: datetime
    expires_at: datetime
    granted_by: str
    reason: str

async def check_temporary_access(
    user: UserIdentity,
    document: Document
) -> bool:
    """Check for temporary access grants."""
    grants = await get_active_grants(user.id, document.id)
    
    current_time = datetime.utcnow()
    for grant in grants:
        if grant.expires_at > current_time:
            return True
    
    return False
```

**Use Cases**:
- External auditors requiring temporary access to financial documents
- Contractors working on specific projects
- Emergency access during incident response
- Cross-department collaboration on time-limited initiatives

### Context-Aware Access Control

**Access Based on Context**:
```python
async def check_contextual_access(
    user: UserIdentity,
    document: Document,
    context: AccessContext
) -> bool:
    """Check access based on request context."""
    
    # Location-based restrictions
    if document.location_restricted:
        if not await is_accessing_from_approved_location(user, context):
            return False
    
    # Time-based restrictions (e.g., business hours only)
    if document.time_restricted:
        if not is_within_business_hours(context.timestamp):
            return False
    
    # Purpose-based access (must specify reason)
    if document.requires_justification:
        if not context.access_reason:
            return False
    
    return True
```

## Data Isolation Patterns

### Multi-Tenant Knowledge Bases

For deployments serving multiple organizations:

**Tenant Isolation**: Each tenant has completely isolated knowledge bases:
```python
async def get_tenant_knowledge_bases(
    user: UserIdentity
) -> list[KnowledgeBase]:
    """Get knowledge bases for user's tenant only."""
    tenant_id = user.tenant_id
    
    # Query only knowledge bases belonging to this tenant
    knowledge_bases = await db.knowledge_bases.find({
        "tenant_id": tenant_id
    })
    
    return knowledge_bases
```

**Tenant Partitioning**:
- Separate vector store collections per tenant
- Namespace prefixing: `tenant_<id>.knowledge_base_name`
- Isolated search indices
- Separate storage buckets for document files

### Department-Specific Knowledge

**Departmental Boundaries**: Ensure users only access their department's data:
```python
async def filter_by_department(
    user: UserIdentity,
    documents: list[Document]
) -> list[Document]:
    """Filter documents to only those from user's department."""
    user_department = user.department
    
    accessible = []
    for doc in documents:
        # Allow if document is public
        if doc.classification == "public":
            accessible.append(doc)
            continue
        
        # Allow if same department
        if doc.department == user_department:
            accessible.append(doc)
            continue
        
        # Allow if user has cross-department permission
        cross_dept_perm = f"aihub.user.knowledge.{doc.department}"
        if await access_checker.check_access(user, cross_dept_perm):
            accessible.append(doc)
    
    return accessible
```

## Performance Optimization

### Caching Strategies

**Permission Cache**: Cache permission evaluation results to reduce latency:
```python
from functools import lru_cache
from datetime import datetime, timedelta

class PermissionCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache: dict[str, tuple[bool, datetime]] = {}
    
    async def check_cached(
        self,
        user_id: str,
        permission: str,
        checker: AccessChecker
    ) -> bool:
        """Check permission with caching."""
        cache_key = f"{user_id}:{permission}"
        
        # Check cache
        if cache_key in self.cache:
            result, cached_at = self.cache[cache_key]
            if datetime.utcnow() - cached_at < self.ttl:
                return result
        
        # Cache miss - check permission
        result = await checker.check_access_by_id(user_id, permission)
        self.cache[cache_key] = (result, datetime.utcnow())
        
        return result
```

**Namespace Precomputation**: Pre-compute accessible namespaces for roles:
```python
# Precomputed at login time
user_session.accessible_namespaces = await compute_accessible_namespaces(
    user, access_checker
)

# Used during retrieval
async def fast_retrieve(query: str, session: UserSession):
    """Use precomputed namespaces for faster retrieval."""
    return await vector_store.query(
        query_embedding=embed(query),
        namespaces=session.accessible_namespaces
    )
```

### Efficient Filtering Strategies

**Pre-Filter in Vector Store**: Push filtering down to the vector store level:
```python
# Inefficient: Retrieve all, filter in application
all_docs = vector_store.query(query, num_results=100)
filtered = [doc for doc in all_docs if can_access(user, doc)]

# Efficient: Filter in vector store
filtered_docs = vector_store.query(
    query,
    num_results=10,
    filter={
        "namespace": {"$in": accessible_namespaces},
        "classification": {"$in": ["public", "internal"]}
    }
)
```

**Batch Permission Checks**: Check permissions for multiple documents in parallel:
```python
async def batch_check_access(
    user: UserIdentity,
    documents: list[Document],
    access_checker: AccessChecker
) -> list[bool]:
    """Check access for multiple documents in parallel."""
    tasks = [
        check_document_access(user, doc, access_checker)
        for doc in documents
    ]
    return await asyncio.gather(*tasks)
```

## Audit and Compliance

### Retrieval Access Logging

Every document retrieval is logged for audit purposes:

```json
{
  "event_type": "rag_retrieval",
  "user_id": "user@example.com",
  "user_oid": "user-oid-456",
  "query": "vacation policy",
  "namespaces_searched": ["internal.hr.policies"],
  "documents_retrieved": [
    {
      "document_id": "doc_12345",
      "namespace": "internal.hr.policies",
      "title": "Vacation Policy 2025",
      "classification": "internal"
    }
  ],
  "num_results": 3,
  "retrieval_latency_ms": 45,
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

### Access Denial Logging

Failed access attempts are logged for security monitoring:

```json
{
  "event_type": "rag_access_denied",
  "user_id": "user@example.com",
  "user_oid": "user-oid-456",
  "attempted_namespace": "confidential.executive",
  "reason": "insufficient_permissions",
  "required_permission": "aihub.user.knowledge.confidential.executive",
  "user_permissions": ["aihub.user.knowledge.internal.*"],
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

### Compliance Reporting

**Data Access Reports**: Generate reports for compliance audits:
- Which users accessed which documents
- Frequency of access to sensitive documents
- Unauthorized access attempts
- Data access patterns by department

**Right to Access (GDPR)**: Users can request reports of their data access:
```python
async def generate_user_access_report(
    user_id: str,
    start_date: datetime,
    end_date: datetime
) -> AccessReport:
    """Generate report of user's data access for GDPR compliance."""
    
    access_logs = await db.audit_logs.find({
        "event_type": "rag_retrieval",
        "user_id": user_id,
        "timestamp": {"$gte": start_date, "$lte": end_date}
    })
    
    return AccessReport(
        user_id=user_id,
        period=(start_date, end_date),
        documents_accessed=extract_documents(access_logs),
        knowledge_bases_accessed=extract_namespaces(access_logs),
        total_retrievals=len(access_logs)
    )
```

## Best Practices

### For Administrators

- **Principle of Least Privilege**: Grant users minimum necessary access to knowledge bases
- **Regular Access Reviews**: Periodically audit who has access to sensitive knowledge bases
- **Classification Policies**: Establish clear document classification guidelines
- **Namespace Design**: Design namespace hierarchy to align with organizational structure
- **Access Monitoring**: Set up alerts for unusual access patterns to sensitive data

### For Content Managers

- **Proper Classification**: Accurately classify documents during upload
- **Metadata Completeness**: Provide complete metadata for effective access control
- **Namespace Organization**: Use consistent namespace conventions
- **Access Group Assignment**: Assign appropriate access groups to documents
- **Regular Audits**: Review document access logs to ensure appropriate usage

### For Developers

- **Query-Time Filtering**: Always apply access controls during retrieval, never rely on client-side filtering
- **Performance Testing**: Test access control performance with realistic user permission sets
- **Error Handling**: Handle access denials gracefully with informative messages
- **Logging**: Log all access control decisions for audit purposes
- **Cache Wisely**: Cache permission evaluations but respect security requirements for cache TTL

## Conclusion

The Swiss AI Hub's RAG data access management system provides enterprise-grade security for knowledge bases while maintaining the performance and functionality required for effective AI applications. Through hierarchical permissions, query-time filtering, document-level access control, and comprehensive audit logging, the platform ensures that sensitive information is protected while remaining accessible to authorized users. This approach enables organizations to confidently deploy RAG systems that leverage their complete knowledge base while maintaining strict control over data access and meeting regulatory compliance requirements.
