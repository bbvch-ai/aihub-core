from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Process(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        process_class: str
        process_id: str

    class Out(BaseProcessEntity.Out):
        pass
