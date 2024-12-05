from typing import List, TypeVar

from lib_core.entities.LLM.chat.AzureOpenAILLMEntity import AzureOpenAILLMEntity
from lib_core.entities.LLM.chat.SelfHostedLLMEntity import SelfHostedLLMEntity
from lib_core.entities.LLM.embedding.AzureOpenAIEmbeddingEntity import (
    AzureOpenAIEmbeddingEntity,
)
from lib_core.entities.LLM.embedding.SelfHostedEmbeddingEntity import (
    SelfHostedEmbeddingEntity,
)
from lib_core.entities.LLM.LLMEntity import LLMEntity

LLMEntityType = TypeVar(
    "LLMEntityType",
    AzureOpenAILLMEntity,
    SelfHostedLLMEntity,
    AzureOpenAIEmbeddingEntity,
    SelfHostedEmbeddingEntity,
)


class LLMEntityFactory:
    @staticmethod
    def by_name(organization_shortname: str, name: str) -> LLMEntityType:
        return LLMEntity.objects.using(organization_shortname).get(name=name)

    @staticmethod
    def by_names(organization_shortname: str, names: List[str]) -> List[LLMEntityType]:
        return list(
            LLMEntity.objects.using(organization_shortname)
            .filter(name__in=names)
            .order_by("context_size")
        )

    @staticmethod
    def all(organization_shortname: str) -> List[LLMEntityType]:
        return list(
            LLMEntity.objects.using(organization_shortname).order_by("context_size")
        )
