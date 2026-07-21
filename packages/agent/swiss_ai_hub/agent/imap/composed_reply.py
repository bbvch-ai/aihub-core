from pydantic import BaseModel


class ComposedReply(BaseModel):
    """A composed reply draft: the raw RFC822 bytes to APPEND plus the envelope fields derived while composing.

    Returning the derived subject/recipient/in-reply-to (rather than recomputing them at the call site) keeps the
    draft's metadata and its persisted reference from drifting apart.
    """

    raw: bytes
    subject: str
    recipient: str
    in_reply_to: str | None = None
