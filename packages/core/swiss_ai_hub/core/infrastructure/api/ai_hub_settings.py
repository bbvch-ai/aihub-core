from importlib.metadata import version
from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class AIHubSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AIHUB_")

    API_DEBUG_MODE: Annotated[bool, Field(description="Debug mode for development")] = False
    VERSION: Annotated[str, Field(description="Version of the app")] = version("swiss-ai-hub-core")

    CREATE_DEFAULT_ROLES: Annotated[
        bool, Field(description="Creates default roles like AI-Hub Admin and AI-Hub User")
    ] = True

    CREATE_DEFAULT_BUCKETS: Annotated[bool, Field(description="Creates default knowledge buckets and namespaces")] = (
        True
    )

    DEFAULT_BUCKET_NAME: Annotated[str, Field(description="Name of the default knowledge bucket")] = "defaultknowledge"

    SHARED_BUCKET_NAME: Annotated[str, Field(description="Name of the shared knowledge bucket")] = "sharedknowledge"

    DEFAULT_NAMESPACE_NAME: Annotated[str, Field(description="Name of the default namespace")] = "defaultnamespace"

    SHARED_NAMESPACE_NAME: Annotated[str, Field(description="Name of the shared namespace")] = "sharednamespace"

    OPENAI_API_BASE_URL: Annotated[
        str,
        Field(
            pattern=r"^https?://.*$",
            description="Base URL of AI-Hub's OpenAI-compatible endpoint, used for Langfuse LLM connection",
        ),
    ] = "http://api:8000/api/v1/active/openai"

    INTERNAL_API_BASE_URL: Annotated[
        str,
        Field(
            pattern=r"^https?://[^/]+$",
            description="Internal base URL of the main platform API (no path), used for server-to-server calls "
            "such as the sysadmin plane proxying the access-capability catalog. Predictable per deployment: "
            "the Docker service name in compose, localhost in local dev.",
        ),
    ] = "http://api:8000"

    FRONTEND_ORIGIN: Annotated[str, Field(description="Comma separated list of origins to allow CORS")]

    _STARTUP_BANNER = """\
███████╗██╗    ██╗██╗███████╗███████╗     █████╗ ██╗    ██╗  ██╗██╗   ██╗██████╗
██╔════╝██║    ██║██║██╔════╝██╔════╝    ██╔══██╗██║    ██║  ██║██║   ██║██╔══██╗
███████╗██║ █╗ ██║██║███████╗███████╗    ███████║██║    ███████║██║   ██║██████╔╝
╚════██║██║███╗██║██║╚════██║╚════██║    ██╔══██║██║    ██╔══██║██║   ██║██╔══██╗
███████║╚███╔███╔╝██║███████║███████║    ██║  ██║██║    ██║  ██║╚██████╔╝██████╔╝
╚══════╝ ╚══╝╚══╝ ╚═╝╚══════╝╚══════╝    ╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝"""

    @property
    def startup_banner(self) -> str:
        return (
            f"\n{self._STARTUP_BANNER}\n"
            f"The open-source AI infrastructure stack for Swiss enterprises - v{self.VERSION}\n"
        )

    @property
    def primary_frontend_origin(self) -> str:
        """The primary web portal URL — the first entry of the comma-separated FRONTEND_ORIGIN."""
        return self.FRONTEND_ORIGIN.split(",")[0].strip()

    MONGO_MAIN_DB_NAME: Annotated[
        str,
        Field(
            # Must start with a letter, then letters/digits/underscores only.
            # Keeps the value safe for interpolation into Mongo URIs and commands
            # (no slashes, dots, quotes, whitespace) while still allowing
            # readable test/staging variants like ``aihub_test``.
            pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
            description="Name of mongodb database that will be used to store data",
        ),
    ] = "aihub"
