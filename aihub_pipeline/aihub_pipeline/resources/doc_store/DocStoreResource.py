from dagster import ConfigurableResource


class DocStoreResource(ConfigurableResource):
    """
    This simple resources specifies the database and namespace name of a document store.
    """

    document_store_name: str
    namespace_name: str
