from typing import Annotated, Any, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class KnowledgeCollectionSelector(PrimeVueElement):
    """
    A FormKit element for selecting collections out of the knowledge an agent elsewhere on the same form retrieves
    from.

    Renders as a multi-select whose options are the collections the agent named by `agent_ref` is configured to
    retrieve from, grouped by knowledge database. The options come from that agent rather than from the whole
    catalogue because that is the only list a selection can be made from safely: narrowing retrieval to a collection
    outside the agent's own configuration drops the retriever entirely and answers from nothing, which a check
    against the catalogue alone cannot catch.

    The output is the shape `RAGStartEvent.selected_namespaces` takes, so a selection can be handed to a delegated
    run unchanged: `list[BucketNamespacePair]`, i.e. `[{"bucket_name": ..., "namespace_name": ...}]`.

    ### Form Duality

    ```python
    class MyConfig(Form):
        knowledge_namespaces: Annotated[
            list[BucketNamespacePair] | KnowledgeCollectionSelector | None,
            Field(default=None, description="Collections replies are grounded in"),
        ] = None

        @classmethod
        def as_form(cls) -> "MyConfig":
            return cls(
                knowledge_namespaces=KnowledgeCollectionSelector(
                    label=LocaleString(en="Knowledge Collections"),
                    agent_ref="knowledge_delegation.rag_agent",
                ),
            )

    # Data mode - from submission:
    config = MyConfig(knowledge_namespaces=[BucketNamespacePair(bucket_name="kb", namespace_name="support")])
    ```

    Pair it with a nullable annotation as above: the platform renders a nullable field with an enable toggle, and
    `None` then means "every collection the agent retrieves from" while a list means "these and no others".
    """

    formkit: Annotated[
        Literal["knowledgeCollectionSelector"],
        Field(description="Knowledge collection selector element."),
    ] = "knowledgeCollectionSelector"

    agent_ref: Annotated[
        str | None,
        Field(
            description="Dot path, from the form root, of the agent selector whose configured knowledge supplies the "
            "options — e.g. 'knowledge_delegation.rag_agent'. Never prefix it with '$': FormKit compiles any schema "
            "string starting with one as an expression, so the path would be evaluated against the form data and "
            "reach the element as undefined. While it names no agent there is nothing to offer, and the element says "
            "so instead of listing collections the agent could not retrieve from.",
            alias="agentRef",
        ),
    ] = None

    placeholder: Annotated[
        LocaleString | str | None,
        Field(description="Placeholder for the multi-select"),
    ] = None

    filter: Annotated[bool, Field(description="Whether to enable filtering/search")] = True

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

    def validate_authorization(
        self,
        field_path: str,
        value: Any,
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
    ) -> list[ConfigAuthorizationViolation]:
        """Each selected collection is checked on its own — this narrows retrieval to named collections, never to a
        whole database, so access to one of them says nothing about the rest."""
        if not isinstance(value, list):
            return []

        violations: list[ConfigAuthorizationViolation] = []
        for pair in value:
            if not isinstance(pair, dict):
                continue
            database = pair.get("bucket_name")
            namespace = pair.get("namespace_name")
            if not isinstance(database, str) or not isinstance(namespace, str):
                continue
            if not access_checker.has_access_to_knowledge_namespace(database, namespace):
                violations.append(
                    ConfigAuthorizationViolation(
                        field=field_path,
                        resource_type="knowledge_namespace",
                        resource=f"{database}/{namespace}",
                        message=t(
                            "lib.common.authorization.no_access_knowledge_namespace",
                            database=database,
                            namespace=namespace,
                        ),
                    )
                )
        return violations
