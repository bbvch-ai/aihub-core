from pydantic import BaseModel


class InboxPosition(BaseModel):
    """The highest inbox UID a run has classified, and the UID space it belongs to.

    A UID means nothing without its UIDVALIDITY: a server that renumbers the folder starts again from low UIDs, and a
    bare number would then skip all of its new mail.
    """

    uid_validity: int
    uid: int
