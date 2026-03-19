import hashlib


def uri_to_id(uri: str) -> str:
    hash_hex = hashlib.sha256(uri.encode("utf-8")).hexdigest()
    object_id_hex = hash_hex[:24]
    return object_id_hex
