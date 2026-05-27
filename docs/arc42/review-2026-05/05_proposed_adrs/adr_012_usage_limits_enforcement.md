# LLM Cost Cap và UsageLimits Enforcement

**Status**: Proposed **Severity**: P0 (LLM cost runaway risk, multi-tenant SaaS block) **Drives**: DTC-1 trong
[Details §17.5 Denial of Service](../02_architecture_review_details.md#175-denial-of-service),
[§22.5 Cost Optimization](../02_architecture_review_details.md#225-cost-optimization)

## Context

`UsageLimits` class tồn tại trong codebase (`packages/core/swiss_ai_hub/core/auth/usage/usage_limits.py:181-208`) nhưng
**không được wire vào middleware nào**.

Cụ thể:

- `UsageLimits.check_and_raise()` method exists, increment counter trong Redis, raise HTTPException 429 nếu exceeded.
- `RoleUsageLimit` model define pattern matching (`agent.>`, `llm.*`), limit (request count), period.
- Code path tồn tại NHƯNG: không có controller, middleware, hoặc decorator nào gọi `check_and_raise()` trước khi process
  request.

Hậu quả:

- LLM calls qua LiteLLM proxy: unbounded.
- Một tenant abuse có thể đốt entire LLM budget của platform.
- `LLMCostEvent` track sau call (reactive), không pre-check.
- `OpenaiCompletionHandler`, `AgentCompletionHandler` không check budget trước khi gọi LLM.
- Không có per-tenant hard cost cap.
- Không có pre-flight cost estimation cho agent run.

Scenarios attacker / accident:

1. Attacker craft adversarial prompt loop (AITL recursion không có depth limit, xem BR-1).
2. Application bug send 10000 requests/phút accidentally.
3. Customer dev test trên prod credentials với high-cost model (gpt-4o).
4. Compromised API key.

Cost calculation: 1 request to GPT-5 tier = ~$0.01-0.05. 1000 requests/phút × 60 min × 24h = 1.4M requests/day × $0.03
average = **\$42,000/day spend** từ 1 tenant. Không có hard stop.

Hơn nữa: MCP tool calls (`packages/agent/swiss_ai_hub/agent/mcp/mcp_tool_schemas.py:68`) gọi external MCP servers, có
thể tốn cost (data API, search API, etc.) mà KHÔNG được track trong `LLMCostEvent`.

## Decision Drivers

- **Cost protection**: Hard cap per tenant, per run, per period.
- **Multi-tenant fairness**: 1 tenant không thể kill platform budget.
- **Transparency**: Customer thấy spend của riêng họ (showback).
- **Pre-flight estimation**: Reject expensive operations trước khi sink cost.
- **Performance**: Enforcement không add high latency vào hot path.
- **Flexibility**: Different tenants có different limits (free tier, paid tier, enterprise).
- **Auditability**: Log every quota exceed event cho forensics.

## Decision

Wire `UsageLimits` vào middleware và service layer. Add pre-flight cost estimation. Implement hard cap per tenant.

### Layer 1: Request-level rate limiting (middleware)

```python
# packages/core/swiss_ai_hub/core/auth/usage/rate_limit_middleware.py
from fastapi import Request, HTTPException

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    user = getattr(request.state, "user", None)
    if not user:
        return await call_next(request)

    # Map URL path to permission template
    permission_template = infer_permission_from_request(request)
    # E.g., POST /api/v1/{tenant_id}/agents/{agent_class}/{agent_id}/run
    #       -> "aihub.user.{tenant_id}.agent.{agent_class}.{agent_id}"

    usage_limits = await load_user_usage_limits(user)

    try:
        await usage_limits.check_and_raise(
            user_id=user.user_id,
            tenant_id=user.acting_within_tenant,
            permission_template=permission_template,
            cost_units=1,  # Request count
        )
    except QuotaExceededError as e:
        await AuditLogEntity.write_audit_entry(
            user_id=user.user_id,
            tenant_id=user.acting_within_tenant,
            action_type="access_denied",
            resource_type="quota",
            metadata={"reason": "rate_limit", "details": str(e)},
        )
        raise HTTPException(status_code=429, detail=str(e))

    return await call_next(request)
```

### Layer 2: LLM call budget enforcement

```python
# packages/core/swiss_ai_hub/core/infrastructure/litellm/budget_aware_llm_service.py
class BudgetAwareLiteLLMService(LiteLLMService):
    async def acompletion(self, *, tenant_id: str, run_id: str, model: str, messages: list, **kwargs):
        # Pre-flight estimation
        estimated_tokens = estimate_tokens(messages, kwargs.get("max_tokens", 1024))
        estimated_cost = compute_cost(model, estimated_tokens)

        # Check tenant budget
        current_spend = await cost_tracker.get_tenant_spend_window(tenant_id, period="day")
        tenant_budget = await tenant_config.get_max_cost_per_day(tenant_id)

        if current_spend + estimated_cost > tenant_budget:
            await AuditLogEntity.write_audit_entry(
                tenant_id=tenant_id,
                action_type="access_denied",
                resource_type="llm_budget",
                metadata={
                    "current_spend": float(current_spend),
                    "estimated_cost": float(estimated_cost),
                    "budget": float(tenant_budget),
                },
            )
            raise BudgetExceededError(
                f"Tenant {tenant_id} budget exceeded: {current_spend + estimated_cost:.2f} > {tenant_budget}"
            )

        # Check run budget
        run_spend = await cost_tracker.get_run_spend(run_id)
        run_budget = await tenant_config.get_max_cost_per_run(tenant_id)
        if run_spend + estimated_cost > run_budget:
            raise RunBudgetExceededError(...)

        # Make actual call
        response = await super().acompletion(model=model, messages=messages, **kwargs)

        # Track actual spend (reactive)
        actual_cost = compute_actual_cost(response.usage, model)
        await cost_tracker.record_spend(tenant_id, run_id, actual_cost)

        return response
```

### Layer 3: AITL recursion limit (links với ADR-NEW-022)

```python
class RunContext:
    MAX_AITL_DEPTH = 5  # Configurable per tenant
    MAX_TOTAL_LLM_CALLS_PER_RUN = 50
    MAX_TOTAL_TOKENS_PER_RUN = 100_000
```

### Layer 4: MCP tool cost tracking

```python
# packages/agent/swiss_ai_hub/agent/mcp/secure_mcp_executor.py
class SecureMCPExecutor:
    async def call_tool(self, tool_name: str, arguments: dict, ...):
        # Check tool-level quota
        tool_cost_estimate = await self.tool_registry.get_estimated_cost(tool_name)
        await self.usage_limits.check_and_raise(
            permission_template=f"aihub.user.{self.tenant_id}.mcp.{tool_name}",
            cost_units=tool_cost_estimate,
        )

        # Make call
        result = await self.mcp_client.call_tool(tool_name, arguments)

        # Emit cost event
        await self.event_publisher.publish(MCPToolCostEvent(
            tool_name=tool_name,
            tenant_id=self.tenant_id,
            user_id=self.user.user_id,
            run_id=self.run_id,
            cost=tool_cost_estimate,
            external_provider=self.tool_registry.get_provider(tool_name),
        ))

        return result
```

### Tenant budget configuration

```python
# packages/core/swiss_ai_hub/core/persistence/access/entities/tenant_budget_entity.py
class TenantBudgetEntity(Document):
    meta = {"collection": "tenant_budgets"}

    tenant_id = StringField(required=True, unique=True)

    # Hard caps
    max_cost_per_run_usd = DecimalField(default=Decimal("1.00"))
    max_cost_per_day_usd = DecimalField(default=Decimal("100.00"))
    max_cost_per_month_usd = DecimalField(default=Decimal("1000.00"))

    # Soft warnings
    warning_threshold_pct = IntField(default=80)  # Alert when 80% of budget used

    # Per-model rates can vary
    max_tokens_per_run = IntField(default=100_000)
    max_concurrent_runs = IntField(default=10)

    # Notification
    alert_email = StringField()
    alert_webhook = StringField()
```

### Alerting integration (links với ADR-NEW-032)

Khi tenant reach warning threshold, emit alert qua AlertManager. Khi reach hard cap, raise 429 và notify admin email.

### Customer dashboard (showback)

UI hiển thị:

- Current day/week/month spend per tenant
- Per-model breakdown
- Per-agent breakdown
- Per-user breakdown
- Budget remaining
- Historical trend
- Projected end-of-month spend

## Consequences

### Positive

- LLM cost predictable per tenant.
- 1 tenant abuse không kill platform budget.
- Customer transparent về spend (showback).
- Pre-flight estimation prevent sink cost.
- MCP tool costs visible.
- Compliance auditor có evidence cost controls.
- Multi-tenant SaaS feasible.

### Negative

- Latency increase: ~5-20ms per request cho rate limit check (mitigated bằng Redis cache).
- Pre-flight estimation accuracy không 100% (token counting heuristic).
- Tenant budget configuration overhead (admin set per tenant).
- Customers cần training về quota system.
- False positives: legitimate spike trigger 429 (cần buffer / burst allowance).

### Implementation notes

- Sprint 1: Layer 1 middleware + Redis counter.
- Sprint 2: Layer 2 LiteLLM budget service.
- Sprint 3: Layer 3 AITL limits (cross-ref ADR-NEW-022).
- Sprint 4: Layer 4 MCP tool cost tracking (cross-ref ADR-NEW-019).
- Sprint 5: TenantBudgetEntity + admin UI cho budget config.
- Sprint 6: Customer dashboard (showback).

Burst allowance pattern: 2x base rate cho 1 minute, sau đó throttle về base. Implement qua token bucket trong Redis.

## References

- [Details §17.5 Denial of Service](../02_architecture_review_details.md#175-denial-of-service): UsageLimits NOT WIRED
  finding.
- [Details §22.5 Cost Optimization](../02_architecture_review_details.md#225-cost-optimization): Cost pillar evaluation.
- [Details §20.1.2 Cost cap reactive](../02_architecture_review_details.md#201-ai-safety-7-sub-concerns): Pre-flight
  estimation missing.
- `packages/core/swiss_ai_hub/core/auth/usage/usage_limits.py:181-208`: Existing class.
