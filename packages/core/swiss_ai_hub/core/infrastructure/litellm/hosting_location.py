from enum import StrEnum


class HostingLocation(StrEnum):
    """Where a model runs, as the LiteLLM config declares it in `aihub_hosting_location`.

    Keep in sync with `HOSTING_LOCATIONS` in `infra/deployment/generate_compose.py`, which rejects any other value.
    """

    LOCAL = "local"
    SWISS_CLOUD = "swiss_cloud"
    EU = "eu"
    GLOBAL = "global"
