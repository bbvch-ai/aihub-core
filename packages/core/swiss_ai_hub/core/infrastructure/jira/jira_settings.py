from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class JiraSettings(EnvironmentSettings):
    """Deployment-level knobs of the Jira client agents read Jira with.

    The URL and the credentials are agent configuration; which internal hosts that URL may name is the deployment's
    decision, because an agent administrator sets the URL and agents can reach the platform's own services.
    """

    ALLOW_LIST_VARIABLE: ClassVar[str] = "JIRA_ALLOWED_PRIVATE_HOSTS"

    model_config = EnvironmentSettings.create_settings_config("JIRA_")

    ALLOWED_PRIVATE_HOSTS: Annotated[
        str,
        Field(
            default="",
            description="Comma-separated host names an agent's Jira URL may name although they are internal, such "
            "as a Jira Data Center reachable only on the company network. Every other internal host is refused.",
        ),
    ]

    def private_host_allow_list(self) -> frozenset[str]:
        return frozenset(host.strip().lower() for host in self.ALLOWED_PRIVATE_HOSTS.split(",") if host.strip())
