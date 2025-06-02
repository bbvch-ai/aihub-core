import uuid
from typing import Type, TYPE_CHECKING, Annotated, Callable

from fastapi import FastAPI, Body, Path, Security
from pydantic import BaseModel

from aihub_api.routes.process.AgenticProcess import AgenticProcess, HumanProcessStep, HumanTriggerInfo
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner


class AgenticProcessController(Controller):
    name = LocaleString(en="Process Controller")
    description = LocaleString(
        en="This controller dynamically mounts endpoints based on an AgenticProcess class."
    )
    icon = "lsicon:service-filled"

    def __init__(
            self,
            controller_base_route: str,
            auth: AuthHandler,
            process_class: Type[AgenticProcess],
    ):
        super().__init__(controller_base_route, auth, is_admin_only=False)
        self.process_class = process_class

    def _create_endpoint_handler(
            self,
            process_method: Callable, # Now pass the method directly
            body_model_type: Type[BaseModel],
            is_start_trigger: bool,
    ):
        """Creates the actual FastAPI endpoint handler function."""

        # Define the two possible handler structures
        async def dynamic_endpoint_start_trigger(
                user: Annotated[AuthenticatedUser, Security(self.auth)],
                payload: body_model_type = Body(...),
        ):
            process_id = str(uuid.uuid4()) # Generate a new ID for start triggers
            step_instance = HumanProcessStep[body_model_type](
                id=process_id, # Add ID here
                responsible_human=user.oid,
                data=payload,
            )
            return await process_method(step_instance)

        async def dynamic_endpoint_regular_trigger(
                process_id: Annotated[str, Path(description="The ID of the process instance")],
                user: Annotated[AuthenticatedUser, Security(self.auth)],
                payload: body_model_type = Body(...),
        ):
            step_instance = HumanProcessStep[body_model_type](
                id=process_id,
                responsible_human=user.oid,
                data=payload,
            )
            return await process_method(step_instance)

        # Select the correct handler based on the trigger type
        if is_start_trigger:
            # Set annotations for FastAPI docs (FastAPI inspects the *handler*, not the original)
            dynamic_endpoint_start_trigger.__annotations__['payload'] = body_model_type
            dynamic_endpoint_start_trigger.__annotations__['user'] = Annotated[AuthenticatedUser, Security(self.auth)]
            return dynamic_endpoint_start_trigger
        else:
            dynamic_endpoint_regular_trigger.__annotations__['payload'] = body_model_type
            dynamic_endpoint_regular_trigger.__annotations__['process_id'] = Annotated[str, Path(description="The ID of the process instance")]
            dynamic_endpoint_regular_trigger.__annotations__['user'] = Annotated[AuthenticatedUser, Security(self.auth)]
            return dynamic_endpoint_regular_trigger


    def mount(self, app: FastAPI, runner: "Runner"):
        # Create a single instance to be used for all endpoints (or create per call if state is an issue)
        process_instance = self.process_class()

        # Get all human-triggered methods and their info from the process instance
        human_triggers = process_instance.get_human_triggers()

        for trigger in human_triggers:
            # Create the specific endpoint handler for this trigger
            endpoint_handler = self._create_endpoint_handler(
                trigger.method_obj, # Pass the actual coroutine function
                trigger.body_model_type,
                trigger.is_start_trigger,
            )

            # Construct the full route path
            full_route: str
            method_specific_route = trigger.route
            if trigger.is_start_trigger:
                full_route = method_specific_route
            else:
                # Ensure a leading slash for consistency
                if not method_specific_route.startswith("/"):
                    method_specific_route = "/" + method_specific_route
                full_route = f"/{{process_id}}{method_specific_route}"

            # Generate a unique operation ID for OpenAPI docs
            op_id_base = self.base_route.strip("/").replace("/", "_")
            operation_id = f"{op_id_base}_{trigger.method_name}"
            if not trigger.is_start_trigger:
                operation_id = f"{op_id_base}_process_id_{trigger.method_name}"

            # Add the route to the controller's router
            self.router.post(
                full_route,
                tags=self.tags,
                summary=f"{'Start ' if trigger.is_start_trigger else ''}Process step: {trigger.method_name}",
                operation_id=operation_id,
                # Add response_model if known/needed, can be tricky with dynamic handlers
            )(endpoint_handler)

            log_path = f"{self.base_route}{full_route if full_route.startswith('/') else '/' + full_route}"
            print(f"Mounted dynamic endpoint: POST {log_path} for {trigger.method_name} expecting {trigger.body_model_type.__name__}")

        # Include the controller's router in the main FastAPI application
        app.include_router(self.router, prefix=self.base_route, tags=self.tags)