class StructuredFileUnavailableError(Exception):
    """A file the source will not serve, such as one deleted or forbidden since it was listed.

    The destination skips it and the next run tries it again; every other error while reading a file fails the load,
    which dlt retries.
    """
