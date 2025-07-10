from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events.work_request.human.form.base.FormkitElement import FormkitElement


class HtmlElement(FormkitElement):
    el: Annotated[str, Field(description="HTML element tag name", alias="$el")]
    attrs: Annotated[dict[str, str | dict], Field(description="HTML element attributes")]
    children: Annotated[list["HtmlElement"] | str, Field(description="HTML element children")]
