from dagster import ConfigurableResource


class NamespaceResource(ConfigurableResource):
    """
    This simple resources specifies in which organization the whole pipeline is running and which namespace
    is affected. Note that a Pipeline can affect multiple output pipelines, but - in most cases - should
    only process one input namespace.
    """

    name: str
    organization: str
