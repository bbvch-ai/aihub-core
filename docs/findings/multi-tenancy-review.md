# Multi-Tenancy Review — Finding

**Date:** 2026-05-27 (updated) **Reviewer:** Architecture audit **Scope:** `packages/core`, `packages/api`,
`packages/web`, infra (NATS, Redis, Milvus, LiteLLM) **Verdict:** ⚠️ **Partially implemented** — control plane is
tenant-aware, data plane is not.

______________________________________________________________________

## 0. CRITICAL — Verified Violations (đọc trước)

> **Platform's own arc42 documentation** (`docs/arc42/chapters/11_risks_and_technical_debt.md`) acknowledges: *"The
> platform currently operates as a **single-tenant system**. All users share one set of databases, one NATS instance,
> one Milvus collection namespace, and one set of agent configurations."*
>
> Nhưng API/auth layer **public expose multi-tenant URLs** (`/api/v1/{tenant_id}/...` via `TenantScopedController`) và
> tenant-scoped roles, tạo **false sense of isolation** cho bất kỳ customer nào có nhiều subsidiaries / business units /
> data-isolated teams trong cùng 1 org.

Các finding bên dưới đã được verify trực tiếp trong code (file path + line number kèm theo), không phải false positive:

### V1. Data layer KHÔNG có `tenant_id` trên resource entities (mở rộng từ §3)

Verified via `grep` toàn bộ `packages/core/swiss_ai_hub/core/persistence/`. Ngoài 3 entities đã list ở §3, còn thiếu
thêm:

| Entity                    | File                                        |
| ------------------------- | ------------------------------------------- |
| **`NamespaceEntity`**     | `rag/datalake/entities/namespace_entity.py` |
| **`RefDoc`** (documents)  | `rag/documents/entities/ref_doc.py`         |
| **`AgentConfigEntity`**   | `agents/agent_config_entity.py`             |
| **`ProcessConfigEntity`** | `process/process_config_entity.py`          |
| **`NotificationEntity`**  | `notification/notification_entity.py`       |

→ Tổng cộng **8 resource entities** thiếu `tenant_id`. Chỉ `RoleEntity`, `UserTenantRoleEntity`, `TenantMetadataEntity`
được tenant-scoped.

### V2. Global unique constraint trên `bucket_name` → information disclosure

`packages/core/swiss_ai_hub/core/persistence/rag/datalake/entities/bucket_entity.py`:

```python
{"fields": ["bucket_name"], "unique": True}  # global unique, KHÔNG phải (tenant_id, bucket_name)
{"fields": ["db_name"], "unique": True}      # cùng vấn đề
```

Cùng pattern ở `NamespaceEntity`. Xem chi tiết exploit ở §5 — Scenario B2.

### V3. NATS subjects KHÔNG include `tenant_id`

`packages/core/swiss_ai_hub/core/topic_managers/`:

```
Agent topic:   agent.{class}.{id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}
Process topic: process.{class}.{id}.{walkthrough_id}.{event_type}.{event_name}.{event_id}
```

Không có tenant segment trong topic pattern. Bất kỳ subscriber nào có NATS access có thể subscribe **toàn bộ events của
tất cả tenants** via wildcard `agent.>` hoặc `process.>` (xem Scenario C3).

### V4. Milvus collection shared globally

`MilvusVectorStoreConfig.collection_name` set per-agent-config, không phải per-tenant. Hai tenants' RAG agents có thể
write/query **cùng 1 Milvus collection** nếu configs đặt cùng tên. Không có tenant partition key mặc định trong schema.

### V5. `TenantScopedController` URL là cosmetic — service query KHÔNG filter tenant (finding mới)

`packages/api/swiss_ai_hub/api/routes/knowledge/knowledge_service.py:129`:

```python
buckets = BucketEntity.get_all_buckets()  # ← KHÔNG có tenant_id filter
```

URL `/api/v1/{tenant_id}/knowledge/databases` trông giống tenant-scoped, nhưng service query tất cả buckets globally rồi
chỉ filter bằng `AccessChecker` permissions. **Tenant boundary chỉ được enforce ở permission layer**, không phải data
layer. Một role config sai = full cross-tenant data leak, không có DB-layer safety net.

### Tổng kết V1–V5

| Layer trong stack                                     | Tenant-aware? |
| ----------------------------------------------------- | :-----------: |
| Keycloak (identity), Roles, URL routing               |     ✅ Có     |
| `AccessChecker` permissions                           |     ✅ Có     |
| MongoDB data entities (8 entities ở trên)             |   ❌ Không    |
| API service layer (BucketEntity.get_all_buckets v.v.) |   ❌ Không    |
| NATS subjects, Milvus collections, Redis keys         |   ❌ Không    |

Public API surface (URL paths, tenant selector, role-per-tenant) **advertise multi-tenancy**, nhưng data model bên dưới
vẫn là **single-tenant**. Với single-organization self-hosted deployment thì chấp nhận được (xem Scenario A). Với bất kỳ
deployment nào có nhiều subsidiaries / business units / data-isolated teams trong 1 org customer, đây là
**commercial-blocker** (xem Scenario B).

**Khuyến nghị tức thì**: Không market hoặc contractually commit tới multi-tenant isolation cho tới khi V1–V5 được fix.

______________________________________________________________________

## 1. Summary

The platform's **authentication & access control** layer is correctly tenant-scoped, but the **data layer** (threads,
events, buckets, cache, messaging, RAG) has **no stored tenant identifier**. Isolation today relies on implicit
query-time filters, not on schema-enforced scoping. This is acceptable for a single-organisation deployment with
cooperative tenants, but **fails for SaaS / multi-customer scenarios** and creates cross-tenant leakage risk over time.

______________________________________________________________________

## 2. What is tenant-aware (✅ strong)

| Component              | Evidence                                                            |
| ---------------------- | ------------------------------------------------------------------- |
| Tenant identity        | Keycloak `/tenants/<id>` groups are authoritative                   |
| `TenantMetadataEntity` | Stores display metadata; KC is source of truth                      |
| `UserTenantRoleEntity` | Unique `[user_id, tenant_id]`, properly scoped                      |
| `RoleEntity`           | Indexed `[tenant_id, name]`, properly scoped                        |
| `AccessChecker`        | Two-stage check: tenant rules (ceiling) ∩ user rules (floor)        |
| Active tenant          | Stored as Keycloak user attribute (`active_tenant_id`)              |
| Frontend               | Route param `[tenant]` + `useTenant()` composable + tenant switcher |
| SuperUser bootstrap    | Auto-assigned to every new tenant (commit `3fc2c69e`)               |

______________________________________________________________________

## 3. Gaps (❌ data plane is NOT tenant-aware)

Verified against source + live MongoDB (`db.threads.findOne()`, `db.buckets.findOne()`).

| Component                   | Gap                                                                  | Source proof                                        | Live proof                                                                      |
| --------------------------- | -------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------- |
| `ThreadEntity`              | No `tenant_id` field                                                 | `packages/core/.../thread_entity.py`                | `db.threads.findOne()` returns only `name`, `created_at`, `users[]`, `agents[]` |
| `PersistedAgentEventEntity` | No `tenant_id` field                                                 | `packages/core/.../persisted_agent_event_entity.py` | n/a (empty collection)                                                          |
| `BucketEntity`              | No `tenant_id` field                                                 | `packages/core/.../bucket_entity.py`                | `db.buckets.findOne()` shows `bucket_name` is global                            |
| Redis / Valkey              | No per-tenant key prefix                                             | grep on cache wrappers                              | —                                                                               |
| NATS subjects               | `agent.{class}.{id}.{thread}.{display}.{run}...` — no tenant segment | `topic_manager`                                     | wildcard subscriptions match across tenants                                     |
| Milvus                      | Tenant isolation implicit via bucket→collection routing only         | `partition_aware_milvus_vector_store.py`            | no `tenant_id` in vector metadata                                               |
| LiteLLM                     | Single shared gateway, no per-tenant virtual keys / budgets          | compose + config                                    | cost cannot be attributed per tenant                                            |

______________________________________________________________________

## 4. Concrete risks

| #   | Gap                    | Risk class                   | Severity    | Trigger                                                                                  |
| --- | ---------------------- | ---------------------------- | ----------- | ---------------------------------------------------------------------------------------- |
| 1   | `buckets` no tenant_id | RAG leakage (knowledge docs) | 🔴 Critical | Two tenants create bucket with same name → collision / cross-read                        |
| 2   | `threads` no tenant_id | Chat leakage                 | 🔴 Critical | New endpoint forgets filter; sysadmin tenant switch; thread_id guessed                   |
| 3   | `events` no tenant_id  | GDPR / audit fail            | 🟠 High     | Tenant deletion request, compliance export                                               |
| 4   | Redis no prefix        | State corruption             | 🟠 High     | Two tenants with same agent_id (e.g. `duy_onboarding_test`) overwrite each other's state |
| 5   | NATS no tenant subj    | Event leak                   | 🟠 High     | Bot integration with wildcard subscribe receives events from wrong tenant                |
| 6   | Milvus implicit        | RAG leakage                  | 🟡 Medium   | Bucket→collection refactor, edge-case routing                                            |
| 7   | LiteLLM shared         | Cost mis-attribution         | 🟡 Medium   | Per-tenant billing, rate-limit fairness                                                  |

______________________________________________________________________

## 5. What will happen if multi-tenancy is required as a hard requirement?

### Scenario A — Single-org self-host (current target)

> **Setting:** Công ty BBV tự host Swiss AI Hub, dùng cho 3 phòng ban: `hr`, `finance`, `engineering`. Mọi nhân viên đều
> là người trong nhà.

**Acceptable today** — nếu được document là known limitation, và operator chấp nhận rằng:

- Tenant boundary chỉ là "soft" (organizational, không phải security)
- Một nhân viên HR cố ý truy cập sai có thể đọc được thread của Finance — nhưng đây là vấn đề kỷ luật, không phải lỗ
  hổng SaaS
- Backup/restore là cho cả platform, không phải per-tenant

**Ví dụ cụ thể (chấp nhận được):**

- Anna ở phòng HR có thread "Onboarding Q1" với agent `duy_onboarding_test`
- Ben ở phòng Finance không biết thread_id đó, không có permission Keycloak → không vào được
- Hệ thống hoạt động đúng kỳ vọng cho use case nội bộ

______________________________________________________________________

### Scenario B — SaaS / multi-customer (KHÔNG ĐÁP ỨNG ĐƯỢC)

> **Setting:** BBV bán Swiss AI Hub như SaaS cho 3 khách hàng: Bank A, Hospital B, Law Firm C. Mỗi khách là một tenant.
> Họ là **đối thủ hoặc đối tác có conflict of interest**.

**Sẽ fail vì 3 ví dụ sau:**

**Ví dụ B1 — GDPR Right-to-Erasure fail**

- Bank A gửi yêu cầu: "Xóa toàn bộ dữ liệu của chúng tôi trong 30 ngày" (GDPR Article 17)
- Bạn cần xóa: threads, events, RAG documents, cache, audit logs của Bank A
- Mongo query bạn muốn chạy:
  ```javascript
  db.threads.deleteMany({tenant_id: "bank_a"})           // ❌ không có field này
  db.persisted_agent_events.deleteMany({tenant_id: ...}) // ❌ không có field này
  db.buckets.deleteMany({tenant_id: "bank_a"})           // ❌ không có field này
  ```
- Workaround: lần ngược qua `user_tenant_role` → user_ids → threads where users.user_id ∈ ... → events where thread_id ∈
  ... — nhiều bước, dễ sót
- **Kết quả:** Vi phạm GDPR, phạt tối đa €20M hoặc 4% doanh thu năm

**Ví dụ B2 — Bucket name collision (data leakage tức thì)**

- Cả Bank A và Hospital B đều tạo bucket tên `policies` (rất phổ biến)
- Bucket collection có unique `bucket_name`:
  ```javascript
  // Bank A tạo trước:
  { bucket_name: "policies", db_name: "policies", datalake_type: "s3" }

  // Hospital B tạo sau → ERROR "duplicate key"
  // → Hospital B biết Bank A đã có bucket tên này (information disclosure)
  // HOẶC tệ hơn: nếu code không check unique → Hospital B's documents
  // ghi vào CÙNG Milvus collection của Bank A
  ```
- RAG agent của Hospital B query `policies` → trả về policy nội bộ của Bank A
- **Kết quả:** Bệnh viện đọc được chính sách lãi suất bí mật của ngân hàng

**Ví dụ B3 — ISO 27001 audit fail**

- Auditor hỏi: "Chứng minh rằng dữ liệu của Bank A không thể bị Hospital B truy cập, dù do bug hay malicious insider"
- Bạn cần show:
  - Schema-level isolation (✅ access entities, ❌ data entities)
  - Storage-level isolation (❌ chia sẻ Mongo collection, Milvus collection, Redis namespace)
  - Network-level isolation (❌ shared NATS subjects)
- Auditor verdict: **Not certifiable as multi-tenant**
- **Kết quả:** Không bán được cho khách hàng enterprise có yêu cầu compliance

______________________________________________________________________

### Scenario C — Slow drift, even in Scenario A

> **Setting:** Giả sử BBV chỉ dùng nội bộ (Scenario A). Theo thời gian, vẫn sẽ xảy ra leakage do **fail-open by
> default**.

**Ví dụ C1 — Developer mới quên filter**

- 6 tháng sau, dev mới tên Tom join team
- Tom được giao viết endpoint `GET /api/threads/recent` — list 10 threads mới nhất của user
- Tom viết:
  ```python
  # Thiếu filter tenant — vì entity không có tenant_id, Tom không thấy lý do để filter
  threads = ThreadEntity.objects(users__user_id=current_user.id).order_by("-created_at")[:10]
  ```
- **Bug:** Nếu Anna ở phòng HR có cùng `user_id` xuất hiện trong threads của phòng Finance (vì cô ấy participate as
  user_id), endpoint trả về thread của Finance
- Code review pass vì không có pattern "luôn filter by tenant" trong codebase
- **Kết quả:** Silent leak, phát hiện 6 tháng sau khi có incident

**Ví dụ C2 — Agent name collision**

- Phòng HR tạo agent `duy_onboarding_test` để test
- Phòng Finance cũng tạo agent `duy_onboarding_test` để test (trùng tên là chuyện thường — ai cũng nghĩ ra cái tên đó)
- Redis key cho agent state:
  ```
  agent_state:duy_onboarding_test   ← chỉ 1 key, không có tenant prefix
  ```
- Khi HR's agent chạy → ghi RunContext
- Khi Finance's agent chạy → **đọc nhầm context của HR và overwrite**
- Không có exception, không có log cảnh báo
- **Kết quả:** Agent của Finance trả lời sai vì context bị nhiễm bởi conversation HR. Debug rất khó vì không có dấu hiệu
  rõ ràng.

**Ví dụ C3 — Bot integration wildcard subscribe**

- Team mới làm tích hợp Microsoft Teams cho phòng HR
- Subscriber subscribe pattern:
  ```
  agent.RAGAgent.>
  ```
  để monitor tất cả RAG agents (vì wildcard `>` match mọi suffix)
- Bot này được deploy chung cho cả công ty
- **Bug:** Bot nhận events từ RAG agent của Finance → echo nội dung tài liệu Finance ra Teams channel của HR
- Subject `agent.RAGAgent.<finance_agent_id>.<thread>.<display>.<run>.display.message.<id>` match `agent.RAGAgent.>`
- **Kết quả:** Bot leak tài liệu Finance vào channel HR. Phát hiện bởi tình cờ vì có người HR thấy nội dung lạ.

______________________________________________________________________

### Tóm lại

| Scenario                | Verdict              | Lý do                                                 |
| ----------------------- | -------------------- | ----------------------------------------------------- |
| A — Single-org nội bộ   | ✅ Acceptable        | Trust boundary là organizational, không phải security |
| B — SaaS multi-customer | ❌ **Không khả thi** | GDPR fail + bucket collision + ISO audit fail         |
| C — A theo thời gian    | ⚠️ **Sẽ drift**      | Fail-open defaults → leak âm thầm sau 3-12 tháng      |

______________________________________________________________________

## 6. Recommendations (priority order)

| #   | Action                                                                         | Effort  | Impact             |
| --- | ------------------------------------------------------------------------------ | ------- | ------------------ |
| 1   | Add `tenant_id` to `BucketEntity` + compound-unique `[tenant_id, bucket_name]` | 1d      | Eliminates risk #1 |
| 2   | Add `tenant_id` to `ThreadEntity` + migration backfill via `user_tenant_role`  | 2–3d    | Eliminates risk #2 |
| 3   | Redis/Valkey key prefix `{tenant_id}:` via wrapper client                      | 1d      | Eliminates risk #4 |
| 4   | Add `tenant_id` to `PersistedAgentEventEntity`                                 | 1d      | Eliminates risk #3 |
| 5   | NATS subject: insert tenant segment (breaking — ADR required)                  | ~1 week | Eliminates risk #5 |
| 6   | LiteLLM virtual keys + budgets per tenant (feature exists in LiteLLM)          | 3–5d    | Eliminates risk #7 |
| 7   | Milvus: store `tenant_id` in vector metadata + enforce filter at retrieval     | 3–5d    | Eliminates risk #6 |

**Cross-cutting:**

- Add a CI lint that fails when a new MongoEngine `Document` is added without a `tenant_id` field (unless explicitly
  whitelisted).
- Add an integration test "user from tenant A cannot read any resource of tenant B" exercising every endpoint.

______________________________________________________________________

## 7. Evidence appendix

### 7.1 `ThreadEntity` source (no tenant field)

```python
class ThreadEntity(Document):
    meta = {"collection": "threads", "strict": False, ...}
    name = StringField(required=True)
    created_at = DateTimeField(required=True)
    process_class = StringField(required=False)
    process_id = StringField(required=False)
    process_walkthrough_id = StringField(required=False)
    users = ListField(EmbeddedDocumentField(User))
    agents = ListField(EmbeddedDocumentField(AgentInstanceRef))
    # ← no tenant_id
```

### 7.2 Live `db.threads.findOne()`

```javascript
{
  _id: ObjectId('69fd667621397811d0c3de60'),
  name: 'Manually created thread',
  created_at: ISODate('2026-05-08T11:28:38.494Z'),
  users: [ { user_id: '3f1bf5ab-9156-4127-8656-baab6d59282d' } ],
  agents: [ { agent_id: 'duy_onboarding_test', agent_class: 'RAGAgent' } ]
}
```

### 7.3 Live `db.buckets.findOne()`

```javascript
{
  _id: ObjectId('69f0588fd0c6cefc4fc07631'),
  bucket_name: 'defaultknowledge',
  db_name: 'defaultknowledge',
  name: { de: 'defaultknowledge', en: 'defaultknowledge', fr: '...', it: '...' },
  description: { de: null, en: null, fr: null, it: null },
  auto_sync: false,
  datalake_type: 's3'
}
```

`bucket_name` is the **global** primary key — no tenant scoping.

______________________________________________________________________

## 8. Decision needed

The team must explicitly decide:

- **(a) Accept** the current "soft multi-tenancy" posture as the target — document as a known limitation, restrict
  deployment to single-org scenarios.
- **(b) Harden** to full data-plane multi-tenancy — execute the roadmap in section 6 (estimated 3–4 weeks of focused
  work, gated by an ADR).

This document is the input for that decision.
