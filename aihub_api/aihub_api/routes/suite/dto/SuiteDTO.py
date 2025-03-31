from typing import List

from pydantic import BaseModel, Field

from aihub_api.routes.suite.dto.ServiceDTO import ServiceDTO


class SuiteDTO(BaseModel):
    services: List[ServiceDTO] = Field(..., description="The services in the suite.")
