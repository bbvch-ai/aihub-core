from typing import Annotated, Self

from fastapi import Depends, File, Form, Security, UploadFile
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.incident import IncidentContext, IncidentSettings
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.incident.dependencies.use_incident_client import use_incident_client
from swiss_ai_hub.api.routes.incident.dependencies.use_optional_incident_client import use_optional_incident_client
from swiss_ai_hub.api.routes.incident.dto.created_incident_dto import CreatedIncidentDTO
from swiss_ai_hub.api.routes.incident.dto.incident_availability_dto import IncidentAvailabilityDTO
from swiss_ai_hub.api.routes.incident.dto.incident_form_dto import IncidentFormDTO
from swiss_ai_hub.api.routes.incident.github_issue_client import GitHubIssueClient
from swiss_ai_hub.api.routes.incident.incident_service import IncidentService


class IncidentController(Controller):
    """Reporting a problem with the platform.

    Both endpoints authenticate only, deliberately: every other controller gates on
    ``aihub.user.service.<name>``, which a narrowly scoped role such as ``AIHubAgentUser`` does not
    carry. Being unable to report a bug because of an access rule is a worse failure than the
    alternative, and there is nothing to protect here — the endpoints read a static form and write
    into a repository nobody else can reach.

    Global rather than tenant-scoped, for two reasons: the reporter's tenant comes from their token
    rather than the path, and ``SuiteService`` turns every tenant-scoped controller into an app tile in
    the navigation rail — which reporting a bug is not.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.incident.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.incident.description")
    icon = "mage:exclamation-circle"

    def __init__(self, *, auth: AuthHandler, route: str = "/incidents", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    def get_incident_availability(self, route: str = "/availability") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_incident_availability(
            _: Annotated[UserIdentity, Security(self.authenticated_user())],
            client: Annotated[GitHubIssueClient | None, Depends(use_optional_incident_client)],
        ) -> IncidentAvailabilityDTO:
            """Says whether reporting is configured here, so the UI shows the button only where it leads somewhere."""
            return IncidentAvailabilityDTO.from_client(client)

        return self

    def get_incident_form(self, route: str = "/form") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_incident_form(
            user: Annotated[UserIdentity, Security(self.authenticated_user())],
            _: Annotated[GitHubIssueClient, Depends(use_incident_client)],
        ) -> IncidentFormDTO:
            """Returns the report form with everything the platform already knows filled in."""
            tenant = user.acting_within_tenant
            context = IncidentContext(
                tenant=f"{tenant.name} ({tenant.id})" if tenant else "",
                reporter_name=user.name,
                reporter_email=user.email,
            )
            return IncidentService.form(context, IncidentSettings())

        return self

    def create_incident(self, route: str = "") -> Self:
        @self.router.post(route, tags=self.tags, status_code=201)
        async def create_incident(
            user: Annotated[UserIdentity, Security(self.authenticated_user())],
            client: Annotated[GitHubIssueClient, Depends(use_incident_client)],
            submission: Annotated[str, Form(description="Answers to the form, as a JSON object")],
            attachments: Annotated[list[UploadFile], File(description="Files to file with the report")] = [],
        ) -> CreatedIncidentDTO:
            """Files the report as an issue, with any attachments committed alongside it.

            Multipart rather than the presigned-PUT flow the other uploads use: those hand the
            browser an S3 URL, and the destination here is GitHub, which issues no such URL.
            """
            return await IncidentService.create(
                user=user,
                submission_json=submission,
                attachments=attachments,
                client=client,
                settings=IncidentSettings(),
            )

        return self
