from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import WebFetchFailureReason


class NavigationOutcome(BaseModel):
    """What `RequestGuard` decided about a page's main document. `page.goto` cannot say it: all it sees is an
    aborted navigation, whether the guard refused a 404, a PDF or an internal redirect target."""

    rejection: Annotated[
        WebFetchFailureReason | None, Field(description="Why the document was refused, if it was.")
    ] = None
    redirect_to: Annotated[
        str | None, Field(description="Where the document redirected to, for the fetcher to open as a new page.")
    ] = None
