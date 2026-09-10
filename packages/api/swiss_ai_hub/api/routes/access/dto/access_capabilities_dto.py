from typing import Annotated

from pydantic import BaseModel, Field


class Capability(BaseModel):
    key: Annotated[str, Field(description="Stable identifier for this capability.")]
    label: Annotated[str, Field(description="Short human-readable action label.")]
    description: Annotated[str, Field(description="What holding this capability lets the user do.")]
    rule: Annotated[
        str | None,
        Field(description="Exact access rule that grants this capability, or null for read-only capabilities."),
    ]
    companion_rules: Annotated[
        list[str],
        Field(
            description=(
                "Rules written and removed together with `rule`. A capability needs more than one when the "
                "rule grammar cannot express it in a single rule — a `.>` rule never matches its own root, "
                "so a row meaning 'this whole resource' has to carry both forms."
            )
        ),
    ] = []
    granted: Annotated[bool, Field(description="Whether the draft rules grant every rule of this capability.")]
    locked: Annotated[
        bool,
        Field(description="Granted via a broader rule (e.g. a wildcard preset) and so cannot be toggled off here."),
    ]
    toggleable: Annotated[
        bool,
        Field(
            description="Whether ticking the box can add a rule. False for ?-wildcard guards with no concrete grant."
        ),
    ]


class CapabilityGroup(BaseModel):
    key: Annotated[str, Field(description="Stable identifier (a controller/service, a class, an instance, ...).")]
    label: Annotated[str, Field(description="Display title for the group.")]
    icon: Annotated[str | None, Field(description="Iconify icon for the group (service or class), if any.")] = None
    capabilities: Annotated[list[Capability], Field(description="Capabilities directly on this group.")] = []
    groups: Annotated[list["CapabilityGroup"], Field(description="Nested groups (e.g. classes, then instances).")] = []


class AccessCapabilitiesResponse(BaseModel):
    groups: Annotated[list[CapabilityGroup], Field(description="Top-level groups, one per controller/service.")]
