# LLM Cost Cap and UsageLimits Enforcement

**Status**: Proposed **Severity**: P0 (LLM cost runaway risk, multi-tenant SaaS block) **Drives**: DTC-1 in
[Details §17.5 Denial of Service](../02_architecture_review_details.md#175-denial-of-service),
[§22.5 Cost Optimization](../02_architecture_review_details.md#225-cost-optimization)

## Context

The `UsageLimits` class exists in the codebase (`packages/core/swiss_ai_hub/core/auth/usage/usage_limits.py:181-208`)
but is **not wired into any middleware**.

Specifically:

- `UsageLimits.check_and_raise()` method exists, increments a counter in Redis, raises HTTPException 429 if exceeded.
- `RoleUsageLimit` model defines pattern matching (`agent.>`, `llm.*`), limit (request count), period.
- The code path exists BUT: no controller, middleware, or decorator calls `check_and_raise()` before processing the
  request.

Consequences:

- LLM calls via the LiteLLM proxy: unbounded.
- A single abusive tenant can burn the platform's entire LLM budget.
- `LLMCostEvent` tracks after the call (reactive), no pre-check.
- `OpenaiCompletionHandler`, `AgentCompletionHandler` do not check budget before calling the LLM.
- No per-tenant hard cost cap.
- No pre-flight cost estimation for an agent run.

Attacker / accident scenarios:

1. An attacker crafts an adversarial prompt loop (AITL recursion has no depth limit, see BR-1).
2. An application bug accidentally sends 10000 requests/min.
3. A customer dev tests on prod credentials with a high-cost model (gpt-4o).
4. A compromised API key.

Cost calculation: 1 request to GPT-5 tier = ~$0.01-0.05. 1000 requests/min × 60 min × 24h = 1.4M requests/day × $0.03
average = **\$42,000/day spend** from one tenant. No hard stop.

Moreover: MCP tool calls (`packages/agent/swiss_ai_hub/agent/mcp/mcp_tool_schemas.py:68`) call external MCP servers and
can incur cost (data API, search API, etc.) that is NOT tracked in `LLMCostEvent`.

## Decision Drivers

- **Cost protection**: Hard cap per tenant, per run, per period.
- **Multi-tenant fairness**: one tenant cannot kill the platform budget.
- **Transparency**: customers see their own spend (showback).
- **Pre-flight estimation**: reject expensive operations before sinking cost.
- **Performance**: enforcement does not add high latency to the hot path.
- **Flexibility**: different tenants have different limits (free tier, paid tier, enterprise).
- **Auditability**: log every quota-exceeded event for forensics.

## Decision

Wire `UsageLimits` into middleware and the service layer. Add pre-flight cost estimation. Implement a hard cap per tenant.

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

### Layer 3: AITL recursion limit (links to ADR-NEW-022)

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

### Alerting integration (links to ADR-NEW-032)

When a tenant reaches the warning threshold, emit an alert via AlertManager. When it reaches the hard cap, raise 429 and
notify the admin email.

### Customer dashboard (showback)

The UI displays:

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
- A single abusive tenant does not kill the platform budget.
- Customers are transparent about their spend (showback).
- Pre-flight estimation prevents sunk cost.
- MCP tool costs visible.
- Compliance auditor has evidence of cost controls.
- Multi-tenant SaaS feasible.

### Negative

- Latency increase: ~5-20ms per request for the rate-limit check (mitigated by Redis cache).
- Pre-flight estimation accuracy is not 100% (token-counting heuristic).
- Tenant budget configuration overhead (admin sets it per tenant).
- Customers need training on the quota system.
- False positives: a legitimate spike triggers 429 (needs buffer / burst allowance).

### Implementation notes

- Sprint 1: Layer 1 middleware + Redis counter.
- Sprint 2: Layer 2 LiteLLM budget service.
- Sprint 3: Layer 3 AITL limits (cross-ref ADR-NEW-022).
- Sprint 4: Layer 4 MCP tool cost tracking (cross-ref ADR-NEW-019).
- Sprint 5: TenantBudgetEntity + admin UI for budget config.
- Sprint 6: Customer dashboard (showback).

Burst allowance pattern: 2x base rate for 1 minute, then throttle back to base. Implement via a token bucket in Redis.

## References

- [Details §17.5 Denial of Service](../02_architecture_review_details.md#175-denial-of-service): UsageLimits NOT WIRED
  finding.
- [Details §22.5 Cost Optimization](../02_architecture_review_details.md#225-cost-optimization): Cost pillar evaluation.
- [Details §20.1.2 Cost cap reactive](../02_architecture_review_details.md#201-ai-safety-7-sub-concerns): Pre-flight
  estimation missing.
- `packages/core/swiss_ai_hub/core/auth/usage/usage_limits.py:181-208`: Existing class.
