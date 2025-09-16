from dagster import ConfigurableResource


class DocStoreResource(ConfigurableResource):
    """
    This simple resources specifies the database name of a document store.
    """

    document_store_name: str
