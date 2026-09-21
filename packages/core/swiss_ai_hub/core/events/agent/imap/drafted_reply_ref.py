from typing import Annotated

from pydantic import BaseModel, Field


class DraftedReplyRef(BaseModel):
    """A single reply draft produced during a batch drafting run — one per source message."""

    source_uid: Annotated[
        str,
        Field(
            description="IMAP UID the source message had in the folder it was read from. A blueprint that files the "
            "message before drafting (EmailClassificationAgent) reports the pre-move UID, which no longer resolves "
            "on the server — it identifies the message within the run, not for a later fetch."
        ),
    ]
    category: Annotated[
        str | None,
        Field(
            default=None,
            description="Category the source message was classified under, when drafting followed a classification "
            "run. Null when the drafting blueprint does not classify.",
        ),
    ]
    drafts_folder: Annotated[str, Field(description="Folder the draft was appended to.")]
    draft_uid: Annotated[
        str | None,
        Field(default=None, description="IMAP UID assigned to the appended draft when the server reports APPENDUID."),
    ]
    in_reply_to: Annotated[
        str | None,
        Field(default=None, description="RFC Message-ID of the original message this draft replies to."),
    ]
    subject: Annotated[str, Field(description="Subject of the draft reply.")]
    recipient: Annotated[str, Field(description="Recipient the draft reply is addressed to.")]
