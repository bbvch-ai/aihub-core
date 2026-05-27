# Audit Log Entity và Compliance

**Status**: Proposed **Severity**: P0 (compliance fail, GDPR Art. 30, SOC2, ISO 27001 block) **Drives**: DTC-2 (no audit
log entity), BR-4 (false GDPR docs claim) trong
[Details §17.3 Repudiation](../02_architecture_review_details.md#173-repudiation),
[§20.2.3 False docs claim](../02_architecture_review_details.md#202-data-lifecycle--gdpr-reality-5-sub-concerns)

## Context

Review 2026-05 phát hiện 2 facts mâu thuẫn:

**Fact 1**: GDPR compliance documentation (`docs/docs/2_platform/21_compliance/2_gdpr/index.en.md`) tuyên bố:

> "Audit logs remain immutable" (Right to rectification section) "The platform provides audit trails, source
> attribution, and Langfuse tracing for transparency" "comprehensive audit logging, documentation capabilities, and
> traceability features"

**Fact 2**: Codebase audit trên `packages/core/swiss_ai_hub/core/persistence/` không tìm thấy:

- `AuditLogEntity` MongoEngine Document class
- Audit log collection `audit_logs` hoặc tương đương trong MongoDB schema
- Middleware hoặc interceptor capture mutations với user identity
- Audit log retention policy implementation
- API endpoints để query audit logs

`BaseDispatcher` (`packages/core/swiss_ai_hub/core/dispatcher/base_dispatcher.py`) execute steps mà không log who
triggered, when, with what input. OpenTelemetry traces có trace ID nhưng không bind user identity per-span một cách
persistent.

Existing events (PersistedAgentEventEntity, PersistedProcessEventEntity) là workflow events, không phải audit log
entries. Hơn nữa các events này có thể bị xoá hoặc modify (no write-once enforcement).

Implications:

- **GDPR Art. 30** (Records of processing activities): không có records để comply.
- **ISO 27001 A.12.4** (Logging and monitoring): non-conformant.
- **SOC 2 CC7.2** (System monitoring): audit trail missing.
- **Banking FINMA**: cannot demonstrate access controls.
- **Healthcare**: cannot trace patient data access (HIPAA-equiv).
- **Internal**: cannot answer "who deleted this tenant?", "who changed this agent config?", "who accessed this user
  data?"

Đặc biệt nghiêm trọng: docs claim "immutable audit logs" while entity không tồn tại. Đây là false claim trước audit
reviewer.

## Decision Drivers

- **Compliance**: GDPR Art. 30, ISO 27001 A.12.4, SOC 2 CC7.2, FINMA, HIPAA-equiv.
- **Trust**: Match docs claim với reality.
- **Forensics**: Trace incident root cause khi có security event.
- **Customer transparency**: Tenant admin có thể query audit log của tenant mình.
- **Performance**: Audit logging không block hot path requests.
- **Storage cost**: Audit logs có thể grow nhanh, cần retention policy.
- **Immutability**: Auditor expectation là logs cannot be modified hoặc deleted.

## Decision

Implement `AuditLogEntity` với write-once semantics và proper retention.

### Entity schema

```python
# packages/core/swiss_ai_hub/core/persistence/audit/entities/audit_log_entity.py
from mongoengine import Document, StringField, DateTimeField, DictField, IntField
from datetime import datetime

class AuditLogEntity(Document):
    """Write-once audit log entry. Cannot be modified or deleted via application code."""

    meta = {
        "collection": "audit_logs",
        "indexes": [
            {"fields": ["tenant_id", "timestamp"]},
            {"fields": ["user_id", "timestamp"]},
            {"fields": ["resource_type", "resource_id", "timestamp"]},
            {"fields": ["action_type", "timestamp"]},
            {"fields": ["trace_id"]},
            # TTL index for long-term retention compliance
            {"fields": ["created_at"], "expireAfterSeconds": 7 * 365 * 86400},  # 7 years default
        ],
    }

    # Identity
    tenant_id = StringField(required=True)
    user_id = StringField(required=True)  # Empty for system actions
    user_email = StringField()
    user_realm_roles = StringField()  # JSON-encoded list

    # Action
    action_type = StringField(required=True, choices=[
        "create", "read", "update", "delete",
        "login", "logout", "access_denied",
        "config_change", "permission_grant", "permission_revoke",
        "tenant_create", "tenant_delete",
        "data_export", "data_erasure",
        "agent_run", "process_run",
        "external_api_call", "secret_access",
    ])
    resource_type = StringField(required=True)  # "agent_config", "user", "tenant", "thread", etc.
    resource_id = StringField()  # The specific resource ID
    resource_name = StringField()  # Human-readable name for UI

    # Context
    timestamp = DateTimeField(default=datetime.utcnow, required=True)
    ip_address = StringField()
    user_agent = StringField()
    trace_id = StringField()  # OpenTelemetry trace ID for correlation
    request_id = StringField()  # HTTP request correlation
    session_id = StringField()

    # Payload (anonymized for sensitive data via Presidio)
    request_payload_hash = StringField()  # SHA-256 of request body
    response_status = IntField()
    metadata = DictField()  # Arbitrary structured data

    # Immutability enforcement
    created_at = DateTimeField(default=datetime.utcnow, required=True)
    immutable_hash = StringField(required=True)  # SHA-256 of all fields above

    @classmethod
    def write_audit_entry(cls, **kwargs) -> "AuditLogEntity":
        """Single entry point. Computes hash, prevents update."""
        entry = cls(**kwargs)
        entry.immutable_hash = entry._compute_hash()
        entry.save()  # MongoEngine save
        return entry

    def _compute_hash(self) -> str:
        # Hash all fields except immutable_hash itself
        # Use canonical JSON serialization for determinism
        import json
        import hashlib
        data = self.to_mongo().to_dict()
        data.pop("_id", None)
        data.pop("immutable_hash", None)
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        return self._compute_hash() == self.immutable_hash
```

### Middleware integration

```python
# packages/core/swiss_ai_hub/core/routes/middleware/audit_middleware.py
from fastapi import Request

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    response = await call_next(request)

    # Only audit state-changing operations
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        user = getattr(request.state, "user", None)
        if user:
            await AuditLogEntity.write_audit_entry(
                tenant_id=user.acting_within_tenant,
                user_id=user.user_id,
                user_email=user.email,
                action_type=_infer_action(request),
                resource_type=_infer_resource_type(request),
                resource_id=request.path_params.get("id"),
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                trace_id=get_current_trace_id(),
                request_id=request.headers.get("x-request-id"),
                response_status=response.status_code,
                metadata={"path": request.url.path, "method": request.method},
            )

    return response
```

### Service layer integration

State-changing operations trong service classes phải emit audit entry trực tiếp (vì middleware không capture business
logic context):

```python
class TenantAdminService:
    @staticmethod
    async def create_tenant(name: str, user: UserIdentity) -> TenantMetadataEntity:
        tenant = TenantMetadataEntity(name=name, ...)
        tenant.save()

        await AuditLogEntity.write_audit_entry(
            tenant_id=tenant.id,
            user_id=user.user_id,
            user_email=user.email,
            user_realm_roles=user.realm_roles,
            action_type="tenant_create",
            resource_type="tenant",
            resource_id=tenant.id,
            resource_name=tenant.name,
            trace_id=get_current_trace_id(),
        )
        return tenant
```

### MongoDB write-once enforcement

Application code không thể guarantee immutability nếu attacker có DB access. Để hardening:

- MongoDB role `audit_writer` chỉ có `insert` permission trên collection `audit_logs`, không có `update`, `delete`,
  `replace`.
- Application connection dùng credentials với role `audit_writer` cho audit operations.
- Backup audit_logs cross-region với immutable storage (S3 Object Lock equivalent).

### Retention

Default 7 years (đủ cho hầu hết regulatory requirements). Customizable per tenant via TTL index. Khi xoá phải go qua
admin process documented, không phải code path.

### API endpoint cho query

```python
# packages/api/swiss_ai_hub/api/routes/audit/audit_controller.py
class AuditController(TenantScopedController):
    def list_audit_entries(self):
        @self.router.get(
            "/audit-logs",
            response_model=list[AuditLogDto],
            dependencies=[Security(self.user_with_permission("aihub.admin.audit.read"))],
        )
        async def list_entries(
            tenant_id: str,
            user_id: str | None = None,
            resource_type: str | None = None,
            action_type: str | None = None,
            from_date: datetime | None = None,
            to_date: datetime | None = None,
            limit: int = 100,
        ) -> list[AuditLogDto]:
            ...
```

### Performance considerations

- Audit write asynchronous (background task) cho hot path requests.
- Indexes on `(tenant_id, timestamp)` cho per-tenant queries fast.
- Batch insert nếu high-throughput scenarios.
- Sharding by tenant_id khi multi-tenant SaaS (sau khi G1.1 tenant isolation done).

## Consequences

### Positive

- GDPR Art. 30, ISO 27001 A.12.4, SOC 2 CC7.2 compliance achievable.
- Auditor request "show me who accessed X" có answer.
- Incident forensics có data.
- Match docs claim với reality (fix BR-4 false claim).
- Tenant admin có dashboard audit log của tenant mình.
- Cross-correlate với OpenTelemetry traces qua `trace_id`.

### Negative

- Storage growth: ~1KB per entry × 10000 actions/day × 7 years = ~25 GB per tenant (manageable).
- Slight latency increase cho state-changing requests (mitigated by async write).
- Need new MongoDB role và connection management.
- Initial backfill cho legacy data impossible (chỉ có audit từ thời điểm deploy).
- Customers cần được notify về what's logged (GDPR transparency).

### Implementation notes

- Phase 1 (sprint 1): Entity + middleware + service layer integration cho core controllers.
- Phase 2 (sprint 2): MongoDB role hardening, write-once verification.
- Phase 3 (sprint 3): Tenant admin UI cho audit query, retention policy per tenant.
- Phase 4 (sprint 4): Cross-region backup immutable storage.

Sau khi accept ADR này, update GDPR docs (`docs/docs/2_platform/21_compliance/2_gdpr/index.en.md`) khi implementation
done. Update CLAUDE.md.

## References

- [Details §17.3 Repudiation](../02_architecture_review_details.md#173-repudiation): STRIDE analysis missing audit log.
- [Details §20.2.3 False docs claim](../02_architecture_review_details.md#202-data-lifecycle--gdpr-reality-5-sub-concerns):
  Docs say "audit logs immutable" but entity không tồn tại.
- ISO 27001 A.12.4 Logging and Monitoring.
- GDPR Art. 30 Records of Processing Activities.
- SOC 2 CC7.2 System Monitoring.
