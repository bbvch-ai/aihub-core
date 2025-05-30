from aihub_iac.azure.constants.resources import COSMOS
from aihub_iac.azure.modules.stores.StoresConfig import StoresConfig


class CosmosDocstore:
    @staticmethod
    def name(project_name, location_short):
        return f"{project_name}-{COSMOS}-{location_short}-{StoresConfig.DEFAULT_DOCSTORE_SUFFIX}"
