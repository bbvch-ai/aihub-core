from datetime import datetime

from bson import ObjectId
from mongoengine import DateTimeField, DictField, Document, EmbeddedDocument, EmbeddedDocumentField, StringField


class BaseProcessEntityIn(EmbeddedDocument):
    meta = {"allow_inheritance": True}


class BaseProcessEntityOut(EmbeddedDocument):
    meta = {"allow_inheritance": True}


class TerminalOut(BaseProcessEntityOut):
    pass


class ProcessStepInstanceEntity(Document):
    meta = {
        "allow_inheritance": True,
        "collection": "process_steps",
        "indexes": [
            "process_instance_id",
            ("process_instance_id", "status"),
            ("process_instance_id", "initiated_at"),
            {"fields": ["process_class_name", "step_definition_name"]},
            {
                "fields": ["_cls", "status", "delegate_to.users"],
                "sparse": True,
                "cls": "HumanProcessStepInstanceEntity",
            },
        ],
    }
    process_class_name = StringField(required=True)
    process_instance_id = StringField(required=True, default=lambda: str(ObjectId()))

    step_definition_name = StringField(required=True)
    display_name = DictField()
    display_icon = StringField()
    display_description = DictField()

    input_from_config = EmbeddedDocumentField(BaseProcessEntityIn)
    delegate_to_config = EmbeddedDocumentField(BaseProcessEntityOut)

    status = StringField(required=True, choices=("RUNNING", "COMPLETED", "FAILED"))
    initiated_at = DateTimeField(default=datetime.utcnow)
    completed_at = DateTimeField()

    error_details = DictField()
