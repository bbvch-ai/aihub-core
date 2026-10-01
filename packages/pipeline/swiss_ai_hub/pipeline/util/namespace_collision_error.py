class NamespaceCollisionError(Exception):
    """A top-level folder sanitises to a namespace name that another folder of the same database already owns.

    Raised rather than joining the two folders: a namespace stores one folder, and teardown and upload act on that
    folder only, so the newcomer's files would survive every deletion and be re-ingested.
    """

    def __init__(self, directory: str, existing_folder: str, namespace_name: str) -> None:
        super().__init__(
            f"Folder '{directory}' maps to namespace '{namespace_name}', which folder '{existing_folder}' already "
            "owns. Rename one of the two folders at the source."
        )
        self.directory = directory
        self.existing_folder = existing_folder
        self.namespace_name = namespace_name
