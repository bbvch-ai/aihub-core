class ResponseSchemaViolation(ValueError):
    """An answer that is not JSON, or JSON that does not match the schema the caller asked for."""
