from typing import Annotated

from pydantic import BaseModel, Field


class IncidentContext(BaseModel):
    """What the platform knows about a report before the reporter types anything.

    Every field name is a question `id` in incident_form.yml — that naming is the
    whole contract between the two files, which is why renaming a field here
    without renaming the question there stops it being prefilled. Values are
    offered, not imposed: the reporter can see and correct all of them, so nothing
    read back out of a submission is authoritative. The two facts that must not be
    guessable — who reported it and from which tenant — are taken from the caller's
    token and written into the issue separately.
    """

    occurred_at: Annotated[str, Field(description="When the problem happened, as the reporter's local time")] = ""
    tenant: Annotated[str, Field(description="Tenant display name and id")] = ""
    version: Annotated[str, Field(description="Deployed version, UI and API")] = ""
    page_url: Annotated[str, Field(description="Page the reporter was on")] = ""
    model: Annotated[str, Field(description="Model or agent behind the answer complained about")] = ""
    conversation_id: Annotated[str, Field(description="Thread the report is about, for replaying it")] = ""
    browser: Annotated[str, Field(description="Browser and platform, shortened")] = ""
    reporter_name: Annotated[str, Field(description="Reporter's name")] = ""
    reporter_email: Annotated[str, Field(description="Reporter's contact address")] = ""

    def as_prefill(self) -> dict[str, str]:
        """Only the values actually known — an empty one must not overwrite a default."""
        return {name: value for name, value in self.model_dump().items() if value}
