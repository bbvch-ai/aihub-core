from collections.abc import Mapping
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from swiss_ai_hub.core.infrastructure.litellm.hosting_location import HostingLocation
from swiss_ai_hub.core.infrastructure.litellm.model_capability import ModelCapability

HOSTING_LOCATION_KEY = "aihub_hosting_location"
HOSTING_LOCATION_REQUIREMENT = "hosting_location"


class ModelRequirements(BaseModel):
    """What a model must offer to be offered and saved in one model picker.

    Stricter than `ModelGatedCheckbox` on purpose: that gates a feature on a model already chosen, this decides what
    may be chosen. So a flag counts only when it is true (LiteLLM reports an unset one as null), and a model whose
    location is missing or unknown fails a location requirement. It reads a plain `model_info` mapping, not the
    API's DTO, so core does not depend on the API.
    """

    model_config = ConfigDict(frozen=True)

    capabilities: Annotated[
        frozenset[ModelCapability],
        Field(default_factory=frozenset, description="Capabilities the model must all support."),
    ]
    hosting_locations: Annotated[
        frozenset[HostingLocation] | None,
        Field(None, min_length=1, description="Where the model may run; any location when unset."),
    ]

    @field_serializer("capabilities")
    def _sorted_capabilities(self, capabilities: frozenset[ModelCapability]) -> list[ModelCapability]:
        """A set has no stable order across processes, and the announced form is stored and compared. Instance methods
        on purpose: events dump with `serialize_as_any`, which skips staticmethod field serializers in Pydantic 2.13 and
        left the set to reach the event's JSON as its Python repr."""
        return sorted(capabilities)

    @field_serializer("hosting_locations")
    def _sorted_hosting_locations(
        self, hosting_locations: frozenset[HostingLocation] | None
    ) -> list[HostingLocation] | None:
        return None if hosting_locations is None else sorted(hosting_locations)

    def unmet_by(self, model_info: Mapping[str, Any]) -> list[str]:
        """The requirements this model fails, by name: each missing capability, then `hosting_location`."""
        unmet = [
            capability.value
            for capability in sorted(self.capabilities)
            if model_info.get(capability.model_info_key) is not True
        ]
        if self.hosting_locations is not None and model_info.get(HOSTING_LOCATION_KEY) not in self.hosting_locations:
            unmet.append(HOSTING_LOCATION_REQUIREMENT)
        return unmet

    def admits(self, model_info: Mapping[str, Any]) -> bool:
        return not self.unmet_by(model_info)
