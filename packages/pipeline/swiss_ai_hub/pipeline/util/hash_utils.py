import hashlib


def hash_file(file_path: str) -> str:
    """
    Hashes a file using SHA256.
    """
    hash_object = hashlib.new("sha256")
    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            hash_object.update(chunk)
    return hash_object.hexdigest()
