import hashlib

from bson import ObjectId
from bson.errors import InvalidId


def str_to_object_id(context_id: str | None) -> ObjectId:
    if not context_id:
        return ObjectId()
    try:
        return ObjectId(context_id)
    except InvalidId:
        hashed = hashlib.md5(context_id.encode()).digest()[:12]
        return ObjectId(hashed)
