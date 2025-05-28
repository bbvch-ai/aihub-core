import inspect
import uuid
from typing import Type, TYPE_CHECKING, Annotated, TypeVar

from fastapi import FastAPI, Body, Depends, Path, Security
from pydantic import BaseModel
from pydantic._internal._generics import get_origin, get_args

from aihub_api.routes.process.AgenticProcess import AgenticProcess, HumanProcessStep # Assuming AgenticProcess is in this path
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
            controller_base_route: str, # e.g., "/process"
            auth: AuthHandler,
            process_class: Type[AgenticProcess],
    ):
        super().__init__(controller_base_route, auth, is_admin_only=False)
        self.process_class = process_class
        # The process instance will be created in the mount method,
        # as it might need the controller_base_route for its own initialization if designed so.

    def _create_endpoint_handler(
            self,
            process_instance: AgenticProcess,
            process_method_name: str,
            body_model_type: Type[BaseModel],
            is_start_trigger: bool,
    ):
        original_method = getattr(process_instance, process_method_name)

        async def dynamic_endpoint_start_trigger(
                user: Annotated[AuthenticatedUser, Security(self.auth)],
                payload: body_model_type = Body(...),
        ):
            # Create Pydantic HumanProcessStep instance
            step_instance = HumanProcessStep[body_model_type](
                responsible_human=user.oid,
                data=payload,
            )
            return await original_method(step_instance)

        async def dynamic_endpoint_regular_trigger(
                process_id: Annotated[str, Path(description="The ID of the process instance")],
                user: Annotated[AuthenticatedUser, Security(self.auth)],
                payload: body_model_type = Body(...),
        ):
            # Create Pydantic HumanProcessStep instance
            step_instance = HumanProcessStep[body_model_type](
                id=process_id,
                responsible_human=user.oid,
                data=payload,
            )
            return await original_method(step_instance)

        # ... (Rest of _create_endpoint_handler remains the same) ...
        if is_start_trigger:
            dynamic_endpoint_start_trigger.__annotations__['payload'] = body_model_type
            dynamic_endpoint_start_trigger.__annotations__['user'] = Annotated[AuthenticatedUser, Security(self.auth)]
            return dynamic_endpoint_start_trigger
        else:
            dynamic_endpoint_regular_trigger.__annotations__['payload'] = body_model_type
            dynamic_endpoint_regular_trigger.__annotations__['process_id'] = Annotated[str, Path(description="The ID of the process instance")]
            dynamic_endpoint_regular_trigger.__annotations__['user'] = Annotated[AuthenticatedUser, Security(self.auth)]
            return dynamic_endpoint_regular_trigger


    def mount(self, app: FastAPI, runner: "Runner"):
        process_instance = self.process_class()

        for method_name, method_obj in inspect.getmembers(process_instance, predicate=inspect.iscoroutinefunction):
            if hasattr(method_obj, "_triggered_by_human") and getattr(method_obj, "_triggered_by_human"):
                method_specific_route = getattr(method_obj, "_route")
                is_start_trigger = getattr(method_obj, "_is_start_trigger", False)

                sig = inspect.signature(method_obj)
                params = list(sig.parameters.values())

                body_type: Type[BaseModel] | None = None
                found_step_param_annotation_for_warning = None

                for param in params:
                    param_annotation = param.annotation
                    if param_annotation is inspect.Parameter.empty:
                        continue

                    # --- USE Pydantic's get_origin and get_args ---
                    origin_type = get_origin(param_annotation)

                    if origin_type is HumanProcessStep:
                        found_step_param_annotation_for_warning = param_annotation
                        model_type_args = get_args(param_annotation)
                        # --- END CHANGE ---

                        if model_type_args and len(model_type_args) == 1:
                            actual_model_type = model_type_args[0]
                            # Check if it's a type or TypeVar, handle accordingly
                            if isinstance(actual_model_type, TypeVar):
                                # If it's still a TypeVar, we might not be able to determine
                                # the concrete model here easily. This *shouldn't* happen
                                # if the annotation is HumanProcessStep[Dossier].
                                print(f"Warning: Method {method_name} has a TypeVar. This setup expects concrete types.")
                                continue

                            if isinstance(actual_model_type, type) and issubclass(actual_model_type, BaseModel):
                                body_type = actual_model_type
                                break
                            else:
                                print(f"Warning: Extracted type {actual_model_type} is not a BaseModel subclass.")


                # ... (Rest of your mount method: warnings, endpoint creation, routing) ...
                if body_type is None:
                    if found_step_param_annotation_for_warning:
                        print(
                            f"Warning: Method {method_name} has a HumanProcessStep parameter, but could not extract a "
                            f"Pydantic BaseModel type from its generic argument ({found_step_param_annotation_for_warning}). Skipping."
                        )
                    else:
                        param_names_and_types = [f"{p.name}: {p.annotation}" for p in params]
                        print(
                            f"Warning: Method {method_name} is decorated for human trigger, but no suitable HumanProcessStep[BaseModel] "
                            f"parameter was found. Inspected parameters: {param_names_and_types}. Skipping."
                        )
                    continue

                endpoint_handler = self._create_endpoint_handler(
                    process_instance, method_name, body_type, is_start_trigger
                )

                full_route: str
                if is_start_trigger:
                    full_route = method_specific_route
                else:
                    if not method_specific_route.startswith("/"):
                        method_specific_route = "/" + method_specific_route
                    full_route = f"/{{process_id}}{method_specific_route}"

                op_id_base = self.base_route.strip("/").replace("/", "_")
                operation_id = f"{op_id_base}_{method_name}"
                if not is_start_trigger:
                    operation_id = f"{op_id_base}_process_id_{method_name}"


                self.router.post(
                    full_route,
                    tags=self.tags,
                    summary=f"{'Start ' if is_start_trigger else ''}Process step: {method_name}",
                    operation_id=operation_id,
                )(endpoint_handler)

                log_path = f"{self.base_route}{full_route if full_route.startswith('/') else '/' + full_route}"
                print(f"Mounted dynamic endpoint: POST {log_path} for {method_name} expecting {body_type.__name__}")

        app.include_router(self.router, prefix=self.base_route, tags=self.tags)
