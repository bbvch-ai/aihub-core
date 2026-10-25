class MemoryNotFoundError(LookupError):
    """Raised for a memory id that does not exist or lies outside the caller's scope.

    Both cases raise the same error so a caller cannot probe which memory ids exist in another scope.
    """

    def __init__(self, memory_id: str):
        super().__init__(f"Memory {memory_id} not found")
        self.memory_id = memory_id
