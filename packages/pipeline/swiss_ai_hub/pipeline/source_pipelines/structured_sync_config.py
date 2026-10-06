import hashlib
import json
from typing import Annotated, Any, Self

from pydantic import Field
from swiss_ai_hub.core.form import Form, Select
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import (
    KIND_REF,
    AbstractStructuredSourceAdapter,
)

_I18N = "lib.source_pipelines.structured.config"


class StructuredSyncConfig(SourcePipelineConfig):
    """What a knowledge database filled by the structured source pipeline is configured with.

    ``source_kind`` picks the application; each offered kind adds its options as a field named after it, shown only
    while it is selected, as ``RcloneSyncConfig`` does per backend. Offering a kind takes that field plus its adapter
    in ``adapters``.
    """

    source_kind: Annotated[str | Select, Field(description="Application the records are read from.")]

    @classmethod
    def adapters(cls) -> list[type[AbstractStructuredSourceAdapter]]:
        """The kinds this pipeline offers. None ships yet; Jira and Confluence follow in #1954 and #1955."""
        return []

    @classmethod
    def as_form(cls) -> Self:
        adapters = cls.adapters()
        return cls(
            source_kind=Select(
                label=LocaleString.from_i18n_path(f"{_I18N}.source_kind.label"),
                help=LocaleString.from_i18n_path(f"{_I18N}.source_kind.help"),
                options=[{"label": adapter.display_name, "value": adapter.kind} for adapter in adapters],
                option_label="label",
                option_value="value",
                ref=KIND_REF,
                required=True,
            ),
            **{adapter.kind: adapter.options_form() for adapter in adapters},
        )

    def adapter(self) -> AbstractStructuredSourceAdapter:
        adapter_type = {offered.kind: offered for offered in self.adapters()}.get(self.source_kind)
        if adapter_type is None:
            raise ValueError(f"Structured source kind '{self.source_kind}' is not offered by this pipeline.")
        return adapter_type()

    def options(self) -> Form:
        return getattr(self, self.source_kind)

    def scope_fingerprint(self) -> str:
        """Changes with what is synced or how it is laid out, but not with a rotated credential: a new project key or
        a new file layout re-reads everything, while a new token keeps the cursors."""
        stored = self.model_dump(mode="json")
        for path in self.secret_field_paths():
            self._drop_path(stored, path.split("."))
        scope = {
            "source_kind": self.source_kind,
            "layout_version": self.adapter().layout_version,
            "options": stored.get(self.source_kind, {}),
        }
        return hashlib.sha256(json.dumps(scope, sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _drop_path(data: dict[str, Any], path: list[str]) -> None:
        *parents, leaf = path
        for key in parents:
            data = data.get(key) or {}
        data.pop(leaf, None)
