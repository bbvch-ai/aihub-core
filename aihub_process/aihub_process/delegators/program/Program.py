from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Program(BaseProcessEntity):
    """
    WIP!
    """

    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"

    class Out(BaseProcessEntity.Out):
        endpoint: str
        method: str = "POST"
