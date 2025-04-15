from aihub_iac.azure.constants.resources import AI_SEARCH_SERVICE


class AISearch:

    @staticmethod
    def name(project_name, location_short):
        return f"{project_name}-{AI_SEARCH_SERVICE}-{location_short}"
