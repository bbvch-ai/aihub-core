from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.suite.dto.ServiceDTO import ServiceDTO


class SuiteDTO(BaseModel):
    services: Annotated[list[ServiceDTO], Field(description="The services in the suite.")]
