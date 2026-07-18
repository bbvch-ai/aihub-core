from typing import Literal

INTERNAL_DATALAKE: Literal["datalake"] = "datalake"
INTERNAL_KNOWLEDGE_DB: Literal["knowledge"] = "knowledge"
# Dedicated pipeline target type for knowledge teardown requests. Teardown events get their own JetStream
# stream, separate from the SourceUpdatedEvent stream, because the upload sensor naks any non-
# SourceUpdatedEvent (which would make JetStream redeliver a shared teardown event forever). This value
# MUST match the API's ``_KNOWLEDGE_TEARDOWN_TARGET_TYPE`` in knowledge_service.py.
INTERNAL_KNOWLEDGE_TEARDOWN: Literal["knowledge_teardown"] = "knowledge_teardown"
