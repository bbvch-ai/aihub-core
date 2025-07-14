from typing import Annotated

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement


class HtmlElement(FormkitElement):
    el: Annotated[str, Field(description="HTML element tag name", alias="$el")]
    attrs: Annotated[dict[str, str | dict], Field(description="HTML element attributes")] = {}
    children: Annotated[list[LocaleString] | list[str] | LocaleString | str, Field(description="HTML element children")]

    def in_locale(self, t: LocaleHandler) -> "HtmlElement":
        self_copy = self.model_copy()
        if isinstance(self_copy.children, LocaleString):
            self_copy.children = t.extract(self_copy.children)
        if isinstance(self_copy.children, list):
            for i, child in enumerate(self_copy.children):
                if isinstance(child, LocaleString):
                    self_copy.children[i] = t.extract(child)
        return self_copy
