from typing import Annotated

from pydantic import BaseModel, Field


class IssueFormUpload(BaseModel):
    """The attachment field, as GitHub's `upload` element declares it.

    Deliberately not an `IssueFormField`: a file never reaches the API inside the JSON
    submission the questions are validated against — it arrives as a multipart part — so
    treating it as one more answerable question would pull it into `submission_model()`,
    where there is nothing for it to be. Keeping it separate is what lets the definition
    own the attachment field's wording and accepted types without pretending files and
    answers travel the same way.
    """

    label: Annotated[str, Field(description="Heading shown above the picker, and above the links in the issue")]
    description: Annotated[str | None, Field(description="Guidance shown under the label")] = None
    required: Annotated[bool, Field(description="Whether at least one file must be attached")] = False
    accept: Annotated[
        list[str],
        Field(description="Lower-cased file extensions, each with its leading dot. Empty means anything."),
    ] = []

    def accepts(self, filename: Annotated[str, "Name to check, as the reporter's browser sent it"]) -> bool:
        if not self.accept:
            return True
        return any(filename.lower().endswith(extension) for extension in self.accept)
