from aihub_iac.azure.constants.resources import OPEN_AI


class OpenAI:
    @staticmethod
    def name(project_name, location_short):
        return f"{project_name}-{OPEN_AI}-{location_short}"
