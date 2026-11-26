from typing import Annotated

from mypy_boto3_s3 import S3Client
from pydantic import BaseModel, ConfigDict, Field, SkipValidation

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity


class ApiPayloadContext(BaseModel):
    """What an event may need, beyond the caller's payload, to turn API input into its own data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    user: Annotated[UserIdentity, Field(description="The caller the event is sent on behalf of.")]
    locale: Annotated[str, Field(description="The caller's locale.")]
    agent_class: Annotated[str, Field(description="Class of the agent the event is sent to.")]
    agent_id: Annotated[str, Field(description="Instance of the agent the event is sent to.")]
    thread_id: Annotated[str | None, Field(description="Thread the event is sent in, when the caller named one.")] = (
        None
    )
    s3_client: Annotated[SkipValidation[S3Client], Field(description="Client for the agent's file bucket.")]
