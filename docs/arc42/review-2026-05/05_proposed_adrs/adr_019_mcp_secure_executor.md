# MCP Secure Executor and Tool Authorization

**Status**: Proposed **Severity**: P0+ (PII data leak via external MCP servers) **Drives**: §19.2 Concern B in
[Details §19.2 MCP Tool Call PII Bypass](../02_architecture_review_details.md#192-concern-b-mcp-tool-call-pii-bypass-critical)

## Context

MCP (Model Context Protocol) lets an agent call external tools (Jira API, Confluence search, custom internal APIs,
etc.). The platform integrates via `packages/agent/swiss_ai_hub/agent/mcp/`.

Review 2026-05 found a critical security gap:

**MCP tool calls bypass Presidio guards 100%**:

Violating data flow:

```
User message with PII
    ↓
LiteLLM proxy with Presidio mask guard (PII masked before reaching the LLM)
    ↓
LLM context (masked) → LLM generates tool call with arguments
    ↓
LLM can "rebuild" PII references in tool arguments (because it knows the business context)
    ↓
mcp_client.call_tool(name, arguments) calls the MCP server directly
    ↓ (NOT through LiteLLM proxy, NOT through Presidio)
External MCP server receives UNMASKED arguments
    ↓
PII leaked to external server (out of platform control)
```

Evidence:

- `packages/agent/.../mcp_react_agent/mcp_react_agent.py:175-180`: Tool execution logic directly calls
  `mcp_client.call_tool(tool_name, arguments)`.
- `packages/agent/swiss_ai_hub/agent/mcp/mcp_tool_schemas.py:68`: `await mcp_client.call_tool(tool_name, arguments)`
  with arguments being a JSON dict from the LLM, unfiltered.
- `packages/core/swiss_ai_hub/core/infrastructure/litellm/lite_llm_base.py:62-74`: the LiteLLM proxy only wraps LLM
  completion calls, not MCP tool calls.
- `packages/core/swiss_ai_hub/core/mcp/mcp_client_config.py:13-55`: McpClientConfig only has `name`, `url`, `api_key`,
  `headers`, `timeout`. NO authorization config, role mapping, or tenant scoping.

**Tool authorization missing**:

- Every authenticated user can call all tools the MCP server exposes.
- No per-tenant tool authorization.
- No per-user permission check before calling a tool.
- Tool discovery (`mcp_client.list_tools()`) returns the full list to every user.

**Concrete scenario**:

```
User: "I need to find customer John Smith, email john@bbv.ch, AHV 756.1234.5678.90"

1. LiteLLM Presidio mask:
   "I need to find customer <PERSON>, email <EMAIL>, AHV <AHV>"

2. The LLM sees masked input but has enough context to generate:
   tool_call = {
       "name": "search_customer_db",
       "arguments": {
           "name": "John Smith",          ← LLM "remembers" original
           "email": "john@bbv.ch",         ← LLM "rebuilds" from context
           "ahv": "756.1234.5678.90"
       }
   }

3. mcp_client.call_tool() sends straight → external MCP server
4. PII leaked to third-party
```

Compliance impact:

- GDPR Art. 32 (security of processing) violation.
- GDPR Art. 28 (processor obligations): if the MCP server is a third-party processor, a DPA is needed.
- US Cloud Act risk if the MCP server is hosted in the US.
- Healthcare HIPAA-equiv: patient data leak.

## Decision Drivers

- **Privacy compliance**: GDPR, revDSG, sectoral regulations.
- **Defense in depth**: PII sanitization at every external boundary.
- **Authorization**: Least-privilege per user, per tenant, per tool.
- **Auditability**: Log every tool call for forensics.
- **Performance**: Sanitization does not add significant latency.
- **Flexibility**: Different tenants have different tool allowlists.
- **Backward compatibility**: Existing MCP agents (MCP_ReactAgent) must still work.

## Decision

Implement `SecureMCPExecutor` wrapping `mcp_client.call_tool()`. Wire it through the agent dispatcher for every MCP
call.

### Class design

```python
# packages/agent/swiss_ai_hub/agent/mcp/secure_mcp_executor.py (NEW)
from dataclasses import dataclass
from typing import Any

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from swiss_ai_hub.core.auth.access import AccessChecker
from swiss_ai_hub.core.auth.identity import UserIdentity
from swiss_ai_hub.core.persistence.audit import AuditLogEntity
from swiss_ai_hub.core.exceptions import PermissionDeniedException, MCPCallError


@dataclass
class MCPCallResult:
    success: bool
    result: Any | None
    error: str | None
    sanitized_args: dict
    detected_entities: list[str]
    duration_ms: float


class SecureMCPExecutor:
    """
    Wraps MCP tool calls with:
    - Tool authorization check (per user, per tenant, per tool).
    - Recursive PII sanitization of arguments (Presidio).
    - Audit logging before and after the call.
    - Response sanitization before returning to the LLM.
    - Tool-level cost tracking.
    """

    DEFAULT_PII_ENTITIES = [
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
        "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS",
        # Swiss-specific (custom recognizers)
        "AHV", "CHE_UID", "SWISS_PHONE", "SWISS_POSTAL_CODE",
    ]

    def __init__(
        self,
        mcp_client,
        access_checker: AccessChecker,
        presidio_analyzer: AnalyzerEngine,
        presidio_anonymizer: AnonymizerEngine,
        user: UserIdentity,
        tenant_id: str,
        run_id: str,
        language: str = "de",
    ):
        self.mcp_client = mcp_client
        self.access_checker = access_checker
        self.analyzer = presidio_analyzer
        self.anonymizer = presidio_anonymizer
        self.user = user
        self.tenant_id = tenant_id
        self.run_id = run_id
        self.language = language

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> MCPCallResult:
        import time
        start = time.monotonic()
        detected_entities: list[str] = []

        # Step 1: Authorization check
        permission = f"aihub.user.{self.tenant_id}.mcp.{tool_name}"
        if not self.access_checker.has_access(self.user, permission):
            await self._audit("access_denied", tool_name, {}, [], time.monotonic() - start)
            raise PermissionDeniedException(
                f"User {self.user.user_id} not authorized for tool {tool_name}"
            )

        # Step 2: Recursive sanitization of arguments
        sanitized_args, args_entities = self._sanitize_recursive(arguments)
        detected_entities.extend(args_entities)

        # Step 3: Audit log BEFORE call
        await self._audit(
            "mcp.tool.call.start",
            tool_name,
            sanitized_args,
            detected_entities,
            time.monotonic() - start,
        )

        # Step 4: Execute with sanitized args
        try:
            raw_result = await self.mcp_client.call_tool(tool_name, sanitized_args)
        except Exception as e:
            await self._audit(
                "mcp.tool.call.error",
                tool_name,
                sanitized_args,
                detected_entities,
                time.monotonic() - start,
                error=str(e),
            )
            raise MCPCallError(f"Tool {tool_name} failed: {e}") from e

        # Step 5: Sanitize response before returning to the LLM
        sanitized_result, response_entities = self._sanitize_recursive(raw_result)
        detected_entities.extend(response_entities)

        # Step 6: Audit log AFTER call
        duration_ms = (time.monotonic() - start) * 1000
        await self._audit(
            "mcp.tool.call.complete",
            tool_name,
            sanitized_args,
            detected_entities,
            duration_ms,
        )

        return MCPCallResult(
            success=True,
            result=sanitized_result,
            error=None,
            sanitized_args=sanitized_args,
            detected_entities=detected_entities,
            duration_ms=duration_ms,
        )

    def _sanitize_recursive(self, obj: Any) -> tuple[Any, list[str]]:
        detected: list[str] = []

        def _walk(value):
            if isinstance(value, str):
                results = self.analyzer.analyze(
                    text=value,
                    language=self.language,
                    entities=self.DEFAULT_PII_ENTITIES,
                )
                if results:
                    detected.extend(r.entity_type for r in results)
                    return self.anonymizer.anonymize(
                        text=value,
                        analyzer_results=results,
                        operators={
                            "DEFAULT": OperatorConfig("mask", {"chars_to_mask": -1, "masking_char": "*"}),
                        },
                    ).text
                return value
            elif isinstance(value, dict):
                return {k: _walk(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_walk(v) for v in value]
            else:
                return value

        return _walk(obj), detected

    async def _audit(
        self,
        action: str,
        tool_name: str,
        args: dict,
        entities: list[str],
        duration_seconds: float,
        error: str | None = None,
    ):
        from swiss_ai_hub.core.tracing import get_current_trace_id
        import hashlib
        import json

        args_hash = hashlib.sha256(
            json.dumps(args, sort_keys=True, default=str).encode()
        ).hexdigest()

        await AuditLogEntity.write_audit_entry(
            tenant_id=self.tenant_id,
            user_id=self.user.user_id,
            user_email=self.user.email,
            action_type=action,
            resource_type="mcp_tool",
            resource_id=tool_name,
            trace_id=get_current_trace_id(),
            metadata={
                "tool_name": tool_name,
                "run_id": self.run_id,
                "args_hash": args_hash,
                "detected_pii_entities": entities,
                "duration_seconds": duration_seconds,
                "error": error,
            },
        )
```

### Integration into MCP_ReactAgent

```python
# packages/agent/swiss_ai_hub/agent/agents/mcp_react_agent/mcp_react_agent.py
# OLD (line 175-180):
result = await self.mcp_client.call_tool(tool_name, arguments)

# NEW:
secure_executor = SecureMCPExecutor(
    mcp_client=self.mcp_client,
    access_checker=ctx.access_checker,
    presidio_analyzer=ctx.presidio_analyzer,
    presidio_anonymizer=ctx.presidio_anonymizer,
    user=ctx.user,
    tenant_id=ctx.tenant_id,
    run_id=ctx.run_id,
    language=ctx.detected_language,  # From language detection (ADR-NEW-018)
)
mcp_result = await secure_executor.call_tool(tool_name, arguments)
result = mcp_result.result
```

### Tool authorization configuration

A tenant admin can configure the tool allowlist in the UI:

```python
class TenantToolAuthorizationEntity(Document):
    meta = {"collection": "tenant_tool_authorizations"}

    tenant_id = StringField(required=True)
    tool_name = StringField(required=True)
    enabled = BooleanField(default=False)
    allowed_user_roles = ListField(StringField())  # E.g., ["admin", "power_user"]
    allowed_user_ids = ListField(StringField())  # Specific users override
    cost_per_call_usd = DecimalField(default=Decimal("0"))
    max_calls_per_day = IntField(default=1000)
```

`AccessChecker.has_access()` queries this entity when checking the permission `aihub.user.{tenant}.mcp.{tool}`.

### Tool discovery filtering

`MCP_ReactAgent.init_step` discovers tools, but filters to only the tools the user has access to:

```python
all_tools = await mcp_client.list_tools()
authorized_tools = [
    t for t in all_tools
    if self.access_checker.has_access(
        user,
        f"aihub.user.{tenant_id}.mcp.{t.name}",
    )
]
# Inject only authorized tools into the LLM system prompt
```

### Custom Swiss PII recognizers

Add custom Presidio recognizers for Swiss-specific entities:

```python
# packages/core/.../presidio/swiss_recognizers.py
class AHVRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern("AHV format", r"756\.\d{4}\.\d{4}\.\d{2}", 0.9),
    ]

class CheUidRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern("CHE-UID format", r"CHE-\d{3}\.\d{3}\.\d{3}", 0.9),
    ]

class SwissPhoneRecognizer(PatternRecognizer):
    PATTERNS = [
        Pattern("Swiss +41 phone", r"\+41\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}", 0.8),
    ]
```

## Consequences

### Positive

- PII is not leaked to external MCP servers.
- GDPR Art. 32 compliance.
- Per-tenant, per-user, per-tool authorization (least-privilege).
- Audit trail for every tool call.
- Cost tracking per tool (links to ADR-NEW-012).
- Swiss PII detection (AHV, CHE-UID, Swiss phone) for regulated industries.
- Tool discovery filtered per user permission (existence not leaked).

### Negative

- Latency increases: ~50-200ms per tool call for Presidio analysis + audit write (mitigated by async audit).
- Initial setup overhead: define the tool allowlist per tenant.
- False positives: Presidio detects non-PII as PII (needs fine-tuning).
- Backward compatibility: the existing MCP_ReactAgent code path needs refactoring.
- Storage growth from audit logs (estimated 1-5 KB per call).

### Performance optimization

- Presidio analyzer cache (per process, share across requests).
- Audit write async (background task).
- Authorization check cached (per user, TTL 60s).
- Skip sanitization for tools marked "internal-trusted" (admin opt-in).

### Implementation notes

- Sprint 1: SecureMCPExecutor class + Presidio integration + basic auth check.
- Sprint 2: AuditLogEntity wiring (cross-ref ADR-NEW-011).
- Sprint 3: TenantToolAuthorizationEntity + admin UI.
- Sprint 4: Tool discovery filtering.
- Sprint 5: Swiss custom PII recognizers + per-language routing (ADR-NEW-018).
- Sprint 6: Cost tracking integration (ADR-NEW-012).

Backward compat: SecureMCPExecutor wraps the existing `mcp_client.call_tool()`. Existing code only needs to inject the
executor. Not a breaking change for the agent base API.

## References

- [Details §19.2 MCP Tool Call PII Bypass](../02_architecture_review_details.md#192-concern-b-mcp-tool-call-pii-bypass-critical):
  Full evidence and scenario.
- ADR-NEW-011 [Audit Log Entity](adr_011_audit_log_entity.md): Logging infrastructure.
- ADR-NEW-012 [UsageLimits Enforcement](adr_012_usage_limits_enforcement.md): Cost tracking.
- ADR-NEW-018 (Per-language Presidio Routing): Multi-language PII detection.
- `packages/agent/swiss_ai_hub/agent/mcp/`: Existing MCP integration code.
