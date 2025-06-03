from aihub_iac.azure.constants.resources import COSMOS
from aihub_iac.azure.constants.suffix import DEFAULT_DOCSTORE_SUFFIX


class CosmosDocstore:
    @staticmethod
    def name(project_name, location_short):
        return f"{project_name}-{COSMOS}-{location_short}-{DEFAULT_DOCSTORE_SUFFIX}"
