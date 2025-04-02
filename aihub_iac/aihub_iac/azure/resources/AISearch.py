from aihub_iac.azure.constants.resources import SEARCH_SERVICE


class AISearch:

    @staticmethod
    def name(project_name, location_short):
        return f"{project_name}-{SEARCH_SERVICE}-{location_short}"
