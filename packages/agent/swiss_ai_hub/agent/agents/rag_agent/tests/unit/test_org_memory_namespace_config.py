"""Regression tests for issue #146: an org-memory allow-list must never brick the agent.

An admin saved a profile whose `default_tenant_namespace` was outside `allowed_tenant_namespaces`.
The API accepts that (it validates against a JSON Schema, which carries no cross-field rules), but the
agent used to reject it in `AgentConfig.model_validate` — which the dispatcher runs on every dispatched
event, before any step. The chat hung with nothing to show. Reads must stay unaffected; only a write
that actually resolves a disallowed namespace may fail.
"""

from swiss_ai_hub.core.generative_ai import LLMConfig, OrgMemoryNamespaceResolver, OrgMemoryReadConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig

# The exact combination from the issue report.
DEFAULT_NAMESPACE = "engineering"
ALLOWED_NAMESPACES = ["test", "default"]


def _config_from_the_issue() -> RAGAgentConfig:
    return RAGAgentConfig(
        agent_id="thong_document_02",
        name=LocaleString(en="bbv knowledge Swiss"),
        description=LocaleString(en="RAG agent with an org-memory allow-list"),
        llm=LLMConfig(model_name="gemma-4-31B-it"),
        retrievers=[],
        org_memory=OrgMemoryReadConfig(
            tenant_id="AIHub",
            default_tenant_namespace=DEFAULT_NAMESPACE,
            allowed_tenant_namespaces=ALLOWED_NAMESPACES,
        ),
    )


def test_default_namespace_outside_allow_list_still_yields_a_runnable_config():
    config = _config_from_the_issue()

    assert config.org_memory.default_tenant_namespace == DEFAULT_NAMESPACE
    assert config.org_memory.allowed_tenant_namespaces == ALLOWED_NAMESPACES


def test_reads_stay_scoped_to_the_allow_list():
    """This is the call `retrieve_organization_memory_step` makes for a plain chat message."""
    config = _config_from_the_issue()

    namespaces = OrgMemoryNamespaceResolver.resolve_for_search(
        requested=[],
        configured=config.org_memory.allowed_tenant_namespaces,
    )

    assert namespaces == ALLOWED_NAMESPACES
