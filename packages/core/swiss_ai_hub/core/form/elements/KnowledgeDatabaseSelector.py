from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.PrimeVueElement import PrimeVueElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class KnowledgeDatabaseSelector(PrimeVueElement):
    """
    A FormKit element for selecting multiple knowledge databases.

    Renders as a multi-select dropdown that loads database names from:
    /api/v1/knowledge/databases

    The output is a list of database names: list[str]

    ### Form Duality

    ```python
    class MyConfig(Form):
        knowledge_databases: Annotated[
            list[str] | KnowledgeDatabaseSelector,
            Field(description="Knowledge databases to query"),
        ]

        @classmethod
        def as_form(cls) -> "MyConfig":
            return cls(
                knowledge_databases=KnowledgeDatabaseSelector(
                    label=LocaleString(en="Knowledge Databases"),
                ),
            )

    # Data mode - from submission:
    config = MyConfig(knowledge_databases=["database1", "database2"])
    ```
    """

    formkit: Annotated[
        Literal["knowledgeDatabaseSelector"],
        Field(description="Knowledge database selector element."),
    ] = "knowledgeDatabaseSelector"

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
