from aihub_iac.azure.constants.resources import STORAGE_ACCOUNT
from aihub_iac.azure.constants.suffix import DEFAULT_DATALAKE_SUFFIX


class DataLakeStorage:
    @staticmethod
    def name(project_name, location_short):
        return f"{project_name}{STORAGE_ACCOUNT}{location_short}{DEFAULT_DATALAKE_SUFFIX}"
