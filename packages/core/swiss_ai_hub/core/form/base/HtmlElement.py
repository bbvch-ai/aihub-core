from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.FormkitElement import FormkitElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class HtmlElement(FormkitElement):
    """
    https://formkit.com/essentials/schema#html-elements-el
    Flexible formkit element that can be rendered into pretty much any html element you like.
    This should NOT be used for inputs but only for displaying and structuring purposes, like
    displaying a title or a paragraph. It can also be styled - however, make sure to consider both
    light and dark mode when styling. You can use tailwind for styling, but it may break in production
    as dynamic tailwind classes might be stripped away when compiling the frontend.

    Example:
        title = HtmlElement(el="h1", children="My Title")
    """

    el: Annotated[str, Field(description="HTML element tag name", alias="$el")]
    attrs: Annotated[dict[str, str | dict], Field(description="HTML element attributes")] = {}
    children: Annotated[list[LocaleString] | list[str] | LocaleString | str, Field(description="HTML element children")]

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = self.model_copy()
        if isinstance(self_copy.children, LocaleString):
            self_copy.children = t.extract(self_copy.children)
        if isinstance(self_copy.children, list):
            for i, child in enumerate(self_copy.children):
                if isinstance(child, LocaleString):
                    self_copy.children[i] = t.extract(child)
        return self_copy
