from typing import List

from mongoengine import DictField, Document, FloatField, IntField, StringField


class LLM(Document):
    meta = {
        "collection": "llms",
        "strict": False,
    }
    version = IntField(default=1, db_field="_version")
    name = StringField(required=True)
    type = StringField(required=True)

    api_endpoint = StringField(required=True)
    api_version = StringField(required=True)
    api_key = StringField(required=False)

    context_size = IntField(required=True)
    temperature = FloatField(required=True, default=0.0)
    model_arguments = DictField(required=False, default=None)

    text_instruction = StringField(required=False, default="")
    query_instruction = StringField(required=False, default="")

    prompt_tokens_costs_per_thousand = FloatField(required=False, default=0)
    completion_tokens_costs_per_thousand = FloatField(required=False, default=0)
    embedding_tokens_costs_per_thousand = FloatField(required=False, default=0)

    @staticmethod
    def by_name(organization_shortname: str, name: str) -> "LLM":
        return LLM.objects.using(organization_shortname).get(name=name)

    @staticmethod
    def by_names(organization_shortname: str, names: List[str]) -> List["LLM"]:
        return list(
            LLM.objects.using(organization_shortname)
            .filter(name__in=names)
            .order_by("context_size")
        )

    @staticmethod
    def all(organization_shortname: str) -> List["LLM"]:
        return list(LLM.objects.using(organization_shortname).order_by("context_size"))
