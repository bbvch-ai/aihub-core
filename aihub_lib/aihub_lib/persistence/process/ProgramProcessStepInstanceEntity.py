from mongoengine import StringField, URLField, DictField

from aihub_lib.persistence.process.ProcessStepInstanceEntity import BaseProcessEntityIn, \
    BaseProcessEntityOut, ProcessStepInstanceEntity


class ProgramIn(BaseProcessEntityIn):
    route = StringField(required=True)
    method = StringField(required=True, default="POST")

class ProgramOut(BaseProcessEntityOut):
    endpoint = URLField(required=True)
    method = StringField(required=True, default="POST")



class ProgramProcessStepInstanceEntity(ProcessStepInstanceEntity):
    work_request_schema_name = StringField() # Pydantic model name of the ProgramWorkRequest
    work_request_payload = DictField()

    work_response_schema_name = StringField() # Pydantic model name of the ProgramWork
    work_response_payload = DictField()
