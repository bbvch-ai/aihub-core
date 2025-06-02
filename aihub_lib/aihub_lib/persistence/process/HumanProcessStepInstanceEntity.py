from mongoengine import StringField, ListField, EmbeddedDocument, EmbeddedDocumentField, DictField

from aihub_lib.persistence.process.ProcessStepInstanceEntity import BaseProcessEntityIn, \
    BaseProcessEntityOut, ProcessStepInstanceEntity


class HumanIn(BaseProcessEntityIn):
    route = StringField(required=True)
    method = StringField(required=True, default="POST")

class HumanOut(BaseProcessEntityOut):
    users = ListField(StringField(), required=True)

class HumanTaskChoice(EmbeddedDocument):
    action_name = StringField(required=True)
    request_body_schema = StringField(required=True)
    request_endpoint = StringField(required=True)
    request_method = StringField(required=True, choices=("POST", "PUT", "DELETE"))

class HumanProcessStepInstanceEntity(ProcessStepInstanceEntity):
    task_definition_schema_name = StringField(required=True)
    possible_choices = ListField(EmbeddedDocumentField(HumanTaskChoice))
    chosen_action_name = StringField()
    chosen_action_payload_schema_name = StringField()
    chosen_action_payload = DictField()