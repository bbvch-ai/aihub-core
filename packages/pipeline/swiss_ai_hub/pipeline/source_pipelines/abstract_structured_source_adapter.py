import abc
from typing import Annotated, Any, ClassVar

from dlt.extract import DltSource
from swiss_ai_hub.core.form import Form
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.pipeline.types.structured_file_reference import StructuredFileReference
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

KIND_REF = "structured_source_kind"


class AbstractStructuredSourceAdapter[TOptions: Form](abc.ABC):
    """How one kind of structured source (Jira, Confluence, ...) is read and turned into markdown files.

    The pipeline knows no source system: it runs the adapter's dlt source and writes whatever files the adapter makes
    of the records. Records become files while they are extracted, because dlt normalises rows before loading and
    coerces ISO timestamps into datetimes the frontmatter cannot render.
    """

    OBJECT_KEY_COLUMN: ClassVar[str] = "_aihub_object_key"
    MARKDOWN_COLUMN: ClassVar[str] = "_aihub_markdown"
    FILE_COLUMN: ClassVar[str] = "_aihub_file"
    FILES_SEEN: ClassVar[str] = "files_seen"
    """Resource-state key of an adapter's map from a file's object key to its fingerprint. A file the destination
    could not read is removed from every such map before the state is saved, so the next run tries it again."""

    kind: ClassVar[str]
    display_name: ClassVar[LocaleString]
    """The application's name as the source-kind dropdown shows it; the kind token is what gets stored."""
    layout_version: ClassVar[int] = 1
    """Raise when ``to_record_file`` changes where or how records are written: the cursor alone would never rewrite
    the records it already passed."""

    @staticmethod
    def shown_for(kind: str) -> str:
        """``condition_if`` for every element of a kind's options form, so its group shows only for that kind."""
        return f"$get({KIND_REF}).value === '{kind}'"

    @classmethod
    @abc.abstractmethod
    def options_form(cls) -> TOptions:
        """The kind's options in form mode, every element carrying ``condition_if=shown_for(kind)``."""

    @abc.abstractmethod
    def dlt_source(self, options: TOptions) -> DltSource:
        """The records to sync, incremental on their last update. Credentials arrive here, never through dlt's config.

        Only the resources whose records become files may be selected: every selected resource is mapped to files.
        """

    @abc.abstractmethod
    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile | StructuredFileReference:
        """The file one record is written as; a pure function of the record, so an unchanged record is skipped. A
        reference to a binary file is downloaded by the destination through ``read_file``."""

    def read_file(
        self,
        options: Annotated[TOptions, "The database's decrypted options"],
        reference: Annotated[StructuredFileReference, "A file this adapter's source offered"],
    ) -> bytes:
        """The content of a file this adapter offered. Raises ``StructuredFileUnavailableError`` for a file the source
        will not serve, which is skipped and tried again next run; any other error fails the load."""
        raise NotImplementedError(f"The {self.kind} source offers no files.")

    @abc.abstractmethod
    def list_record_paths(self, options: TOptions) -> set[str]:
        """Object key of every record currently in scope, each built with ``StructuredRecordFile.object_key_for``.

        Raises instead of returning a partial set, because whatever is not listed is removed from the database. It
        must not read the incremental state: listing runs after the sync, whose cursor would hide older records.
        """

    def file_source(self, options: TOptions) -> DltSource:
        """The adapter's source with each record carrying the file it is written as.

        The record keeps all its fields, so the incremental cursor and the primary key dlt de-duplicates on still
        resolve after the mapping.
        """
        source = self.dlt_source(options)
        for resource in source.selected_resources.values():
            resource.add_map(self._with_file)
        return source

    def _with_file(self, record: dict[str, Any]) -> dict[str, Any]:
        record_file = self.to_record_file(record)
        if isinstance(record_file, StructuredFileReference):
            return {
                **record,
                self.OBJECT_KEY_COLUMN: record_file.object_key,
                self.FILE_COLUMN: record_file.model_dump_json(),
            }
        return {
            **record,
            self.OBJECT_KEY_COLUMN: record_file.object_key,
            self.MARKDOWN_COLUMN: record_file.render().decode(),
        }
